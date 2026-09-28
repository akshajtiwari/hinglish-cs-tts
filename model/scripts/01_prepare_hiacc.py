#!/usr/bin/env python3
"""Build F5-TTS training CSVs from HiACC.

Reads the adult (and optionally children) splits, filters short clips, resamples
16 kHz -> 24 kHz mono with ffmpeg, derives per-token language from script, and
writes  <out>/<split>.csv  with the F5-TTS "audio_file|text" format, plus a
JSONL manifest carrying duration, speaker, mixed flag and switch count.

Stdlib + ffmpeg only. Usage:
    python model/scripts/01_prepare_hiacc.py --corpus data/Corpus --out data/hiacc24k \
        [--children] [--min-sec 0.8] [--max-sec 20] [--oversample-mixed 2]
"""
import argparse
import csv
import json
import re
import shutil
import subprocess
import wave
from pathlib import Path

DEV = re.compile(r"[ऀ-ॿ]")
LAT = re.compile(r"[A-Za-z]")


def token_lang(tok: str) -> str:
    if DEV.search(tok):
        return "hi"
    if LAT.search(tok):
        return "en"
    return "other"


def switches(text: str):
    langs = [token_lang(t) for t in text.split()]
    langs = [l for l in langs if l != "other"]
    n = sum(1 for a, b in zip(langs, langs[1:]) if a != b)
    return n, ("hi" in langs and "en" in langs)


def read_transcripts(path: Path, prefix: str) -> dict:
    out = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(rf"^({prefix}\d+\.wav),\s*(.*)$", line.strip())
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def wav_seconds(p: Path) -> float:
    with wave.open(str(p)) as f:
        return f.getnframes() / f.getframerate()


def resample(src: Path, dst: Path, sr: int = 24000):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(src),
                    "-ac", "1", "-ar", str(sr), "-sample_fmt", "s16", str(dst)], check=True)


def merge_consecutive(recs, target_sec, out_dir: Path, gap_ms=200, max_sec=20.0):
    """Greedily join consecutive clips (sorted by filename) of the same speaker until >= target_sec."""
    import struct
    merged, buf = [], []

    def flush():
        if not buf:
            return
        if len(buf) == 1:
            merged.append(buf[0]); buf.clear(); return
        name = f"{buf[0]['speaker']}_{Path(buf[0]['audio_file']).stem}_{Path(buf[-1]['audio_file']).stem}.wav"
        dst = out_dir / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        sr = None
        with wave.open(str(dst), "wb") as wo:
            for i, r in enumerate(buf):
                with wave.open(r["audio_file"]) as wi:
                    if sr is None:
                        sr = wi.getframerate(); wo.setnchannels(1); wo.setsampwidth(2); wo.setframerate(sr)
                    if i:
                        wo.writeframes(b"\x00\x00" * int(sr * gap_ms / 1000))
                    wo.writeframes(wi.readframes(wi.getnframes()))
        merged.append({**buf[0], "audio_file": str(dst.resolve()),
                       "text": " ".join(r["text"] for r in buf),
                       "duration": round(sum(r["duration"] for r in buf) + gap_ms / 1000 * (len(buf) - 1), 3),
                       "mixed": any(r["mixed"] for r in buf), "switches": sum(r["switches"] for r in buf),
                       "merged_from": len(buf)})
        buf.clear()

    for r in sorted(recs, key=lambda r: Path(r["audio_file"]).name):
        if buf and (r["speaker"] != buf[0]["speaker"] or sum(b["duration"] for b in buf) + r["duration"] > max_sec):
            flush()
        buf.append(r)
        if sum(b["duration"] for b in buf) >= target_sec:
            flush()
    flush()
    return merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="data/Corpus")
    ap.add_argument("--out", default="data/hiacc24k")
    ap.add_argument("--children", action="store_true", help="also include children subset")
    ap.add_argument("--min-sec", type=float, default=0.8)
    ap.add_argument("--max-sec", type=float, default=20.0)
    ap.add_argument("--oversample-mixed", type=int, default=1, help="repeat mixed clips N times in train.csv")
    ap.add_argument("--sr", type=int, default=24000)
    ap.add_argument("--merge-to-sec", type=float, default=0.0,
                    help="train split only: concatenate consecutive same-speaker clips (200 ms gap) until >= this many seconds; 0 = off")
    args = ap.parse_args()
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found")

    corpus, out = Path(args.corpus), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    groups = [("adult", "AD", corpus / "adult" / "transcription", "combined_output_changed_{}_output.txt")]
    if args.children:
        groups.append(("children", "CH", corpus / "children" / "transcript", "{}_output.txt"))

    totals = {}
    for split in ("train", "val", "test"):
        rows, manifest = [], []
        for grp, prefix, tdir, pattern in groups:
            tx = read_transcripts(tdir / pattern.format(split), prefix)
            adir = corpus / grp / "audio" / f"{split}_split"
            for wav in sorted(adir.glob("*.wav")):
                text = tx.get(wav.name)
                if not text:
                    continue
                sec = wav_seconds(wav)
                if sec < args.min_sec or sec > args.max_sec:
                    continue
                nsw, mixed = switches(text)
                dst = out / "wavs" / grp / split / wav.name
                resample(wav, dst, args.sr)
                rec = {"audio_file": str(dst.resolve()), "text": text, "duration": round(sec, 3),
                       "speaker": wav.name[:4], "group": grp, "mixed": mixed, "switches": nsw}
                manifest.append(rec)
        if split == "train" and args.merge_to_sec > 0:
            manifest = merge_consecutive(manifest, args.merge_to_sec, out / "wavs" / "merged_train", max_sec=args.max_sec)
        for rec in manifest:
            reps = args.oversample_mixed if (split == "train" and rec["mixed"]) else 1
            rows.extend([rec] * reps)
        with open(out / f"{split}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="|", quoting=csv.QUOTE_NONE, escapechar="\\")
            w.writerow(["audio_file", "text"])
            for r in rows:
                w.writerow([r["audio_file"], r["text"].replace("|", " ")])
        with open(out / f"{split}.jsonl", "w", encoding="utf-8") as f:
            for r in manifest:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        hrs = sum(r["duration"] for r in manifest) / 3600
        mixed_hrs = sum(r["duration"] for r in manifest if r["mixed"]) / 3600
        totals[split] = (len(manifest), len(rows), hrs, mixed_hrs)
        print(f"{split:5s} clips={len(manifest):5d} rows_in_csv={len(rows):5d} hours={hrs:5.2f} mixed_hours={mixed_hrs:5.2f}")
    json.dump({k: {"clips": v[0], "csv_rows": v[1], "hours": round(v[2], 3), "mixed_hours": round(v[3], 3)} for k, v in totals.items()},
              open(out / "summary.json", "w"), indent=2)


if __name__ == "__main__":
    main()
