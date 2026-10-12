"""Step 2.1: reproduce UTMOS on the BVCC test set (the check that the pipeline is correct).

Model: UTMOS22 strong learner from SpeechMOS (torch.hub "tarepan/SpeechMOS:v1.2.0", "utmos22_strong", MIT).
Data:  BVCC (VoiceMOS 2022 main track) test: 1,066 utterances, DATA/wav (16 kHz), MOS from test_mos_list.txt.
Check: the utterance-level SRCC should be close to the published value (about 0.897); system-level SRCC is reported too.

Every prediction is appended to predictions.csv as soon as it is computed, a rerun skips clips already scored,
the summary is saved atomically, and a run manifest (config, hardware, timing) is saved with run_log.py.

Run on the server with the baselines venv:
  PYTHONPATH=~/projects/switchmos_code/src ~/projects/baselines-venv/bin/python scripts/step2_baselines/check_utmos_on_bvcc.py \
      --bvcc ~/projects/hinglish-cs-tts/datasets/bvcc/main --out ~/projects/hinglish-cs-tts/analysis/step2/utmos_bvcc [--limit 20]
"""
import argparse
import csv
import json
import time
from pathlib import Path

import soundfile
import torch

from switchmos import files
from switchmos import run_log
from switchmos.eval import metrics

PUBLISHED_UTT_SRCC = 0.897


def read_mos_list(path):
    """Read 'utterance,mos' lines into a list of (utterance, mos) pairs."""
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                utt, mos = line.split(",")
                rows.append((utt, float(mos)))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bvcc", required=True, help="BVCC main folder (contains DATA/)")
    parser.add_argument("--out", required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--limit", type=int, default=0, help="score only the first N clips (trial run)")
    args = parser.parse_args()

    bvcc = Path(args.bvcc).expanduser()
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    test = read_mos_list(bvcc / "DATA" / "sets" / "test_mos_list.txt")
    if args.limit:
        test = test[:args.limit]

    pred_path = out / "predictions.csv"
    done = {}
    if pred_path.exists():
        with open(pred_path) as f:
            for row in csv.DictReader(f):
                done[row["utt"]] = float(row["pred"])

    device = "cpu"
    if args.device.startswith("cuda") and torch.cuda.is_available():
        device = args.device
    config = {
        "model": "tarepan/SpeechMOS:v1.2.0 utmos22_strong",
        "device": device,
        "n_clips": len(test),
        "limit": args.limit,
    }
    datasets = {"bvcc": {"split": "test", "list": "DATA/sets/test_mos_list.txt"}}
    run_dir = run_log.start_run("utmos_bvcc_test", config, seed=0, root=out / "runs", datasets=datasets)
    print(f"{len(test)} test clips, {len(done)} already scored, device {device}", flush=True)

    model = torch.hub.load("tarepan/SpeechMOS:v1.2.0", "utmos22_strong", trust_repo=True)
    model = model.to(device).eval()
    is_new = not pred_path.exists()
    start_time = time.time()
    with open(pred_path, "a", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["utt", "pred"])
        for n, (utt, _) in enumerate(test):
            if utt in done:
                continue
            wav, sr = soundfile.read(bvcc / "DATA" / "wav" / utt, dtype="float32")
            if wav.ndim > 1:
                wav = wav.mean(axis=1)
            with torch.no_grad():
                score = float(model(torch.from_numpy(wav).unsqueeze(0).to(device), sr).item())
            writer.writerow([utt, f"{score:.6f}"])
            f.flush()
            done[utt] = score
            if (n + 1) % 100 == 0:
                print(f"  {n + 1}/{len(test)} scored, {time.time() - start_time:.0f}s", flush=True)

    utts = [utt for utt, _ in test]
    pred = [done[utt] for utt in utts]
    true = [mos for _, mos in test]
    # file names look like sys64e2f-utt9c183cd.wav
    systems = [utt.split("-")[0] for utt in utts]
    report = metrics.regression_report(pred, true, systems)
    report["published_utt_srcc"] = PUBLISHED_UTT_SRCC
    report["difference_to_published"] = report["utt_srcc"] - PUBLISHED_UTT_SRCC
    report["device"] = device
    report["seconds"] = round(time.time() - start_time, 1)
    files.save_text(out / "summary.json", json.dumps(report, indent=2))
    run_log.finish_run(run_dir, metrics=report, outputs=[str(pred_path), str(out / "summary.json")])
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
