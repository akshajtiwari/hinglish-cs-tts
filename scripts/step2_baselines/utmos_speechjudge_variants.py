"""Why does UTMOS get 59.3% on the SpeechJudge test pairs here but 53.7% in the SpeechJudge paper (Table 2)?

The SpeechJudge authors publish no script for this baseline and do not describe its input handling, so this scores
the same 2,000 clips under input variants a user could plausibly have used, and reports accuracy per subset next to
the paper's numbers (regular 54.0 on 400 pairs, expressive 53.5 on 600, total 53.7).

Variants (all with UTMOS22 strong from SpeechMOS v1.2.0, loaded as in score_baselines.py):
  native       the file at its own rate (24 kHz); SpeechMOS resamples to 16 kHz inside. This is our setting.
  librosa_16k  resampled to 16 kHz with librosa first
  as_16k       the 24 kHz samples passed as if they were 16 kHz, with no resampling (a common mistake)
  peak_norm    peak scaled to 0.95
  rms_norm     RMS scaled to 0.05 (about -26 dBFS)
  trimmed      leading and trailing silence cut (librosa.effects.trim, top_db 40)
Equal scores count half. Interval: sentence-cluster percentile bootstrap, 2,000 draws, seed 15 (as in the paper).
"native" must reproduce the saved scores; the script prints the largest difference.

Each variant's scores are saved as <out>/<variant>.csv as soon as it is done, and a variant whose file exists is
not scored again. The summary goes to <out>/summary.json.

Run (server, tmux):
  PYTHONPATH=src ~/projects/baselines-venv/bin/python scripts/step2_baselines/utmos_speechjudge_variants.py \\
      --root ~/projects/hinglish-cs-tts/datasets --scores ~/projects/hinglish-cs-tts/analysis/step2/scores \\
      --out ~/projects/hinglish-cs-tts/analysis/step2/utmos_speechjudge_variants
"""
import argparse
import csv
from pathlib import Path

import numpy

from switchmos import files, run_log
from switchmos.audio import load_audio

VARIANTS = ["native", "librosa_16k", "as_16k", "peak_norm", "rms_norm", "trimmed"]
PAPER = {"regular": 54.0, "expressive": 53.5, "total": 53.7}
ROUNDS = 2000
SEED = 15


def prepare(variant, path):
    """(waveform, the sample rate given to UTMOS) for one file and one variant."""
    if variant == "librosa_16k":
        return load_audio(path, target_sr=16000)
    wav, sr = load_audio(path)
    if variant == "native":
        return wav, sr
    if variant == "as_16k":
        return wav, 16000
    if variant == "peak_norm":
        return wav * (0.95 / max(numpy.abs(wav).max(), 1e-9)), sr
    if variant == "rms_norm":
        return wav * (0.05 / max(float(numpy.sqrt(numpy.mean(wav ** 2))), 1e-9)), sr
    if variant == "trimmed":
        import librosa
        return librosa.effects.trim(wav, top_db=40)[0], sr
    raise ValueError(f"unknown variant {variant!r}")


def credit(score_a, score_b, label):
    """1 when the judge's higher score is on the human winner, 0.5 for equal scores, else 0."""
    if score_a == score_b:
        return 0.5
    if (score_a > score_b) == (label == "A"):
        return 1.0
    return 0.0


def read_pairs(root):
    """The 1,000 test pairs from the exam table, each with its subset (regular or expressive) from the raw parquet."""
    import pyarrow.parquet
    subset = {}
    for path in sorted((root / "speechjudge").glob("test-*.parquet")):
        for row in pyarrow.parquet.read_table(path, columns=["index", "subset"]).to_pylist():
            subset[f"speechjudge:{row['index']}"] = row["subset"]
    with open(root / "_exam" / "pairs_speechjudge.csv") as f:
        pairs = list(csv.DictReader(f))
    for pair in pairs:
        pair["subset"] = subset[pair["pair_id"]]
    assert len(pairs) == 1000, f"expected 1,000 test pairs, found {len(pairs)}"
    return pairs


def read_scores(path):
    with open(path) as f:
        return {row["path"]: float(row["score"]) for row in csv.DictReader(f)}


def score_variant(model, variant, paths, device, out_path):
    """Score every file under one variant and save path,score to out_path (written once, at the end)."""
    import torch
    lines = ["path,score"]
    for path in paths:
        wav, sr = prepare(variant, path)
        with torch.no_grad():
            score = float(model(torch.from_numpy(numpy.ascontiguousarray(wav, dtype="float32")).unsqueeze(0).to(device), sr).item())
        lines.append(f"{path},{score:.6f}")
    files.save_text(out_path, "\n".join(lines) + "\n")


def accuracy_report(pairs, scores):
    """Accuracy (%) per subset and in total, with a sentence-cluster bootstrap interval for the total."""
    credits = numpy.array([credit(scores[p["path_a"]], scores[p["path_b"]], p["label"]) for p in pairs])
    report = {}
    for name in ["regular", "expressive"]:
        chosen = numpy.array([p["subset"] == name for p in pairs])
        report[name] = round(100 * float(credits[chosen].mean()), 1)
    report["total"] = round(100 * float(credits.mean()), 1)
    sentences = sorted({p["sentence_id"] for p in pairs})
    index = {sentence: i for i, sentence in enumerate(sentences)}
    cluster = numpy.array([index[p["sentence_id"]] for p in pairs])
    rng = numpy.random.default_rng(SEED)
    draws = []
    for _ in range(ROUNDS):
        weights = numpy.bincount(rng.integers(0, len(sentences), len(sentences)), minlength=len(sentences))[cluster]
        draws.append(100 * float((weights * credits).sum() / weights.sum()))
    report["total_ci95"] = [round(float(x), 1) for x in numpy.quantile(draws, [0.025, 0.975])]
    report["ties"] = int(sum(scores[p["path_a"]] == scores[p["path_b"]] for p in pairs))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--root", type=Path, required=True, help="datasets folder (speechjudge/ and _exam/)")
    parser.add_argument("--scores", type=Path, required=True, help="folder with the saved utmos.csv")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()

    import torch
    device = args.device if args.device.startswith("cuda") and torch.cuda.is_available() else "cpu"
    args.out.mkdir(parents=True, exist_ok=True)
    run_dir = run_log.start_run("utmos_speechjudge_variants", vars(args), seed=0, root=args.out / "runs")
    pairs = read_pairs(args.root.expanduser())
    paths = sorted({p["path_a"] for p in pairs} | {p["path_b"] for p in pairs})

    model = torch.hub.load("tarepan/SpeechMOS:v1.2.0", "utmos22_strong", trust_repo=True).to(device).eval()
    summary = {"paper": PAPER, "pairs": len(pairs), "files": len(paths), "variants": {}}
    for variant in VARIANTS:
        out_path = args.out / f"{variant}.csv"
        if not out_path.exists():
            score_variant(model, variant, paths, device, out_path)
        summary["variants"][variant] = accuracy_report(pairs, read_scores(out_path))
        print(variant, summary["variants"][variant], flush=True)

    saved = read_scores(args.scores.expanduser() / "utmos.csv")
    native = read_scores(args.out / "native.csv")
    summary["native_max_abs_diff_vs_saved"] = max(abs(native[p] - saved[p]) for p in paths)
    summary["saved"] = accuracy_report(pairs, saved)
    print("native vs saved scores, largest difference:", summary["native_max_abs_diff_vs_saved"])
    files.save_json(args.out / "summary.json", summary)
    run_log.finish_run(run_dir, metrics=summary, outputs=[str(args.out / "summary.json")])


if __name__ == "__main__":
    main()
