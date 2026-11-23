"""Step 2.3: score every exam audio file with one baseline scorer.

Scorers (each used exactly as its authors ship it):
  utmos       UTMOS22 strong (torch.hub tarepan/SpeechMOS:v1.2.0, utmos22_strong)
  utmosv2     UTMOSv2 (utmosv2.create_model(pretrained=True))
  distillmos  Distill-MOS (distillmos.ConvTransformerSQAModel, 16 kHz waveform in, MOS out)
  scoreq      SCOREQ no-reference, synthetic domain (scoreq.Scoreq(data_domain="synthetic", mode="nr"))
Resumable: scores are appended to <out>/<scorer>.csv and flushed after each file; a rerun skips files already scored.
Files that fail are written to <out>/<scorer>_errors.csv and skipped, so one bad file never stops the run.
UTMOSv2 crops its input at random, so its scores change from run to run. With --seed, every chunk of files is seeded
from (seed, chunk number), and the chunks are cut from the whole list, so a run that is stopped and resumed gives the
same scores as one that is not. Keep --chunk, --workers and the list the same between runs that should match.
Each call writes a run manifest (arguments, seed, hardware) to <out>/runs/.

Run (server):
  PYTHONPATH=src ~/projects/baselines-venv/bin/python scripts/step2_baselines/score_baselines.py --scorer utmos \
      --list ~/projects/hinglish-cs-tts/datasets/_exam/audio_list.csv --out ~/projects/hinglish-cs-tts/analysis/step2/scores
"""
import argparse
import csv
import os
import shutil
import time
from pathlib import Path

import torch

from switchmos import run_log
from switchmos.audio import load_audio


def load_model(name, device):
    """Load one of the four scorers."""
    if name == "utmos":
        model = torch.hub.load("tarepan/SpeechMOS:v1.2.0", "utmos22_strong", trust_repo=True)
        return model.to(device).eval()
    if name == "utmosv2":
        import utmosv2
        return utmosv2.create_model(pretrained=True, device=device)
    if name == "distillmos":
        import distillmos
        return distillmos.ConvTransformerSQAModel().to(device).eval()
    if name == "scoreq":
        import scoreq
        return scoreq.Scoreq(data_domain="synthetic", mode="nr")
    raise ValueError(f"unknown scorer {name!r}")


def score_file(name, model, path, device):
    """Score one audio file with the given scorer and return the score as a float."""
    if name == "utmos":
        wav, sr = load_audio(path)
        with torch.no_grad():
            return float(model(torch.from_numpy(wav).unsqueeze(0).to(device), sr).item())
    if name == "utmosv2":
        return float(model.predict(input_path=str(path), device=device, verbose=False))
    if name == "distillmos":
        wav, _ = load_audio(path, target_sr=16000)
        with torch.no_grad():
            return float(model(torch.from_numpy(wav).unsqueeze(0).to(device)).item())
    if name == "scoreq":
        return float(model.predict(test_path=str(path)))
    raise ValueError(f"unknown scorer {name!r}")


def open_csv_for_append(path, header):
    """Open a CSV file for appending; write the header first if the file is new."""
    is_new = not path.exists()
    f = open(path, "a", newline="")
    writer = csv.writer(f)
    if is_new:
        writer.writerow(header)
    return f, writer


def error_text(error):
    """Short text for the errors file, like 'ValueError: bad header'."""
    return f"{type(error).__name__}: {str(error)[:200]}"


def print_progress(done, total, start_time, errors):
    """Print how many files are done, the speed and the time left."""
    rate = done / (time.time() - start_time)
    minutes_left = (total - done) / rate / 60
    print(f"  {done}/{total} ({rate:.1f} files/s, about {minutes_left:.1f} min left), {errors} errors", flush=True)


def put_first(paths, first):
    """Move paths that contain first[0] to the front, then first[1], and so on; keep the list order otherwise."""
    groups = []
    for _ in range(len(first) + 1):
        groups.append([])
    for path in paths:
        position = len(first)
        for i, text in enumerate(first):
            if text in path:
                position = i
                break
        groups[position].append(path)
    ordered = []
    for group in groups:
        ordered.extend(group)
    return ordered


def make_chunks(paths, done, chunk, seed):
    """[(chunk number, files)] still to score. Without a seed, the files not done yet are cut into chunks.
    With a seed, the chunks are cut from the whole list, so a resumed run meets the same chunks (and seeds) as an
    uninterrupted one; a chunk with any file missing is scored whole."""
    chunks = []
    if seed is None:
        todo = [path for path in paths if path not in done]
        for number, start in enumerate(range(0, len(todo), chunk)):
            chunks.append((number, todo[start:start + chunk]))
        return chunks
    for number, start in enumerate(range(0, len(paths), chunk)):
        part = paths[start:start + chunk]
        for path in part:
            if path not in done:
                chunks.append((number, part))
                break
    return chunks


def score_utmosv2_in_chunks(chunks, done, out, device, pred_path, err_path, seed=None, workers=4):
    """UTMOSv2 one file at a time ran at 0.3 files/s on the shared GPUs (14.5 h for the exam).
    Its batched mode, predict(input_dir=...), reads every .wav in a folder, so each chunk of files
    gets a folder of links (all exam audio is .wav). Scores are saved after every chunk, so a
    shutdown loses at most one chunk. A chunk that fails is scored file by file, so a bad file is
    logged and skipped like in the other scorers. Only files not in done are written."""
    model = load_model("utmosv2", device)
    links = out / "utmosv2_links"
    start_time = time.time()
    errors = 0
    total = 0
    for number, part in chunks:
        total += len(part)
    finished = 0
    pred_file, pred_writer = open_csv_for_append(pred_path, ["path", "score"])
    err_file, err_writer = open_csv_for_append(err_path, ["path", "error"])
    for number, part in chunks:
        if seed is not None:
            # 100,000 chunks per seed is far more than any list needs, so no two (seed, chunk) share a seed
            run_log.set_seed(seed * 100000 + number)
        shutil.rmtree(links, ignore_errors=True)
        links.mkdir()
        original_path = {}
        for i, path in enumerate(part):
            link_name = f"{i:05d}.wav"
            os.symlink(path, links / link_name)
            original_path[link_name] = path
        rows = []
        try:
            results = model.predict(input_dir=links, device=device, batch_size=16, num_workers=workers, verbose=False)
            for result in results:
                rows.append((original_path[Path(result["file_path"]).name], result["predicted_mos"]))
        except Exception:
            # find the bad file(s): score this chunk one file at a time
            rows = []
            for path in part:
                try:
                    rows.append((path, model.predict(input_path=path, device=device, verbose=False)))
                except Exception as error:
                    errors += 1
                    err_writer.writerow([path, error_text(error)])
                    err_file.flush()
        for path, score in rows:
            if path not in done:
                pred_writer.writerow([path, f"{float(score):.6f}"])
        pred_file.flush()
        finished += len(part)
        print_progress(finished, total, start_time, errors)
    pred_file.close()
    err_file.close()
    shutil.rmtree(links, ignore_errors=True)
    print(f"utmosv2: done in {time.time() - start_time:.0f}s, {errors} errors", flush=True)


def score_one_by_one(name, todo, device, pred_path, err_path):
    """Score the files one at a time, saving each score as soon as it is computed."""
    model = load_model(name, device)
    start_time = time.time()
    errors = 0
    pred_file, pred_writer = open_csv_for_append(pred_path, ["path", "score"])
    err_file, err_writer = open_csv_for_append(err_path, ["path", "error"])
    for n, path in enumerate(todo, start=1):
        try:
            score = score_file(name, model, path, device)
            pred_writer.writerow([path, f"{score:.6f}"])
            pred_file.flush()
        except Exception as error:
            # record the bad file and carry on
            errors += 1
            err_writer.writerow([path, error_text(error)])
            err_file.flush()
        if n % 500 == 0:
            print_progress(n, len(todo), start_time, errors)
    pred_file.close()
    err_file.close()
    print(f"{name}: done in {time.time() - start_time:.0f}s, {errors} errors", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scorer", required=True, choices=["utmos", "utmosv2", "distillmos", "scoreq"])
    parser.add_argument("--list", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--first", default="", help="comma-separated path substrings to score first, e.g. speecharena_votes,speechjudge")
    parser.add_argument("--workers", type=int, default=4, help="UTMOSv2 data-loading processes (its spectrograms are made on the CPU)")
    parser.add_argument("--chunk", type=int, default=500, help="UTMOSv2 files per saved chunk")
    parser.add_argument("--seed", type=int, default=None, help="UTMOSv2: seed for its random crops (see the top of this file)")
    args = parser.parse_args()

    device = "cpu"
    if args.device.startswith("cuda") and torch.cuda.is_available():
        device = args.device
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    pred_path = out / f"{args.scorer}.csv"
    err_path = out / f"{args.scorer}_errors.csv"

    with open(args.list) as f:
        paths = [row["path"] for row in csv.DictReader(f)]
    if args.limit:
        paths = paths[:args.limit]
    done = set()
    if pred_path.exists():
        with open(pred_path) as f:
            done = {row["path"] for row in csv.DictReader(f)}
    first = [text for text in args.first.split(",") if text]
    paths = put_first(paths, first)
    todo = [path for path in paths if path not in done]
    print(f"{args.scorer}: {len(paths)} files, {len(done)} already scored, {len(todo)} to do, device {device}", flush=True)
    if not todo:
        return
    run_dir = run_log.start_run(args.scorer, vars(args), seed=args.seed or 0, root=out / "runs")
    if args.scorer == "utmosv2":
        chunks = make_chunks(paths, done, args.chunk, args.seed)
        score_utmosv2_in_chunks(chunks, done, out, device, pred_path, err_path, seed=args.seed, workers=args.workers)
    else:
        score_one_by_one(args.scorer, todo, device, pred_path, err_path)
    run_log.finish_run(run_dir, outputs=[str(pred_path), str(err_path)])


if __name__ == "__main__":
    main()
