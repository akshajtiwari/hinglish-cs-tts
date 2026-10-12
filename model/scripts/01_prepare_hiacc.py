#!/usr/bin/env python3
"""Build F5-TTS training CSVs from HiACC.

Reads the adult (and optionally children) splits, drops clips that are too short or too long,
resamples 16 kHz -> 24 kHz mono with ffmpeg, finds the language of each word from its script,
and writes <out>/<split>.csv in the F5-TTS "audio_file|text" format, plus a JSONL manifest
with duration, speaker, mixed flag and switch count.

Standard library + ffmpeg only. Usage:
    python model/scripts/01_prepare_hiacc.py --corpus data/Corpus --out data/hiacc24k \
        [--children] [--min-sec 0.8] [--max-sec 20] [--oversample-mixed 2]
"""
import argparse
import csv
import json
import shutil
import subprocess
import wave
from pathlib import Path


def has_devanagari(text):
    """True if the text has a Devanagari character (U+0900 to U+097F)."""
    for ch in text:
        if "ऀ" <= ch <= "ॿ":
            return True
    return False


def has_latin(text):
    """True if the text has an English letter A-Z or a-z."""
    for ch in text:
        if ch.isascii() and ch.isalpha():
            return True
    return False


def token_lang(token):
    """'hi' for a Devanagari word, 'en' for a Latin word, 'other' for anything else."""
    if has_devanagari(token):
        return "hi"
    if has_latin(token):
        return "en"
    return "other"


def switches(text):
    """Return (number of hi/en language changes between words, whether both languages appear)."""
    langs = []
    for token in text.split():
        lang = token_lang(token)
        if lang != "other":
            langs.append(lang)
    n_switches = 0
    for i in range(1, len(langs)):
        if langs[i] != langs[i - 1]:
            n_switches += 1
    return n_switches, ("hi" in langs and "en" in langs)


def read_transcripts(path, prefix):
    """Read lines like 'AD0001.wav, some text' into {file name: text}."""
    out = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        name, comma, text = line.strip().partition(",")
        digits = name[len(prefix):-len(".wav")]
        if comma and name.startswith(prefix) and name.endswith(".wav") and digits.isdecimal():
            out[name] = text.strip()
    return out


def wav_seconds(path):
    """Duration of a wav file in seconds."""
    with wave.open(str(path)) as f:
        return f.getnframes() / f.getframerate()


def resample(src, dst, sr=24000):
    """Convert a wav to mono 16-bit at `sr` Hz with ffmpeg (skipped if the output already exists)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(src),
                    "-ac", "1", "-ar", str(sr), "-sample_fmt", "s16", str(dst)], check=True)


def clip_file_name(rec):
    """Sort key: the file name of the clip."""
    return Path(rec["audio_file"]).name


def join_clips(group, out_dir, gap_ms):
    """Write the clips of `group` into one wav, with gap_ms of silence between them, and return its record.
    A group of one clip is returned unchanged."""
    if len(group) == 1:
        return group[0]
    first = group[0]
    last = group[-1]
    name = f"{first['speaker']}_{Path(first['audio_file']).stem}_{Path(last['audio_file']).stem}.wav"
    dst = out_dir / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    sr = None
    with wave.open(str(dst), "wb") as out_wav:
        for i, rec in enumerate(group):
            with wave.open(rec["audio_file"]) as in_wav:
                if sr is None:
                    sr = in_wav.getframerate()
                    out_wav.setnchannels(1)
                    out_wav.setsampwidth(2)
                    out_wav.setframerate(sr)
                if i > 0:
                    silence = b"\x00\x00" * int(sr * gap_ms / 1000)
                    out_wav.writeframes(silence)
                out_wav.writeframes(in_wav.readframes(in_wav.getnframes()))

    texts = []
    mixed = False
    n_switches = 0
    for rec in group:
        texts.append(rec["text"])
        if rec["mixed"]:
            mixed = True
        n_switches += rec["switches"]
    # sum() on purpose: since Python 3.12 it adds floats more exactly than a += loop
    seconds = sum([rec["duration"] for rec in group])
    joined = dict(first)
    joined["audio_file"] = str(dst.resolve())
    joined["text"] = " ".join(texts)
    joined["duration"] = round(seconds + gap_ms / 1000 * (len(group) - 1), 3)
    joined["mixed"] = mixed
    joined["switches"] = n_switches
    joined["merged_from"] = len(group)
    return joined


def merge_consecutive(recs, target_sec, out_dir, gap_ms=200, max_sec=20.0):
    """Join consecutive clips (sorted by file name) of the same speaker until a group lasts >= target_sec.
    A group is closed early when the speaker changes or when the next clip would pass max_sec."""
    merged = []
    group = []
    group_seconds = 0
    for rec in sorted(recs, key=clip_file_name):
        if group and (rec["speaker"] != group[0]["speaker"] or group_seconds + rec["duration"] > max_sec):
            merged.append(join_clips(group, out_dir, gap_ms))
            group = []
            group_seconds = 0
        group.append(rec)
        group_seconds = sum([r["duration"] for r in group])
        if group_seconds >= target_sec:
            merged.append(join_clips(group, out_dir, gap_ms))
            group = []
            group_seconds = 0
    if group:
        merged.append(join_clips(group, out_dir, gap_ms))
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
    ap.add_argument("--split-file", default=None,
                    help="JSON with speaker lists FT/REF/TEST; replaces HiACC's shipped splits (which are NOT speaker-disjoint). "
                         "Outputs FT/REF/TEST csv+jsonl; merging and oversampling apply to FT only.")
    ap.add_argument("--merge-to-sec", type=float, default=0.0,
                    help="train split only: concatenate consecutive same-speaker clips (200 ms gap) until >= this many seconds; 0 = off")
    args = ap.parse_args()
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found")

    corpus = Path(args.corpus)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    # (group, file prefix, transcript folder, transcript file name pattern)
    groups = [("adult", "AD", corpus / "adult" / "transcription", "combined_output_changed_{}_output.txt")]
    if args.children:
        groups.append(("children", "CH", corpus / "children" / "transcript", "{}_output.txt"))

    # 1. collect every usable clip from all shipped splits
    pool = {}
    for split in ("train", "val", "test"):
        recs = []
        for group, prefix, transcript_dir, pattern in groups:
            transcripts = read_transcripts(transcript_dir / pattern.format(split), prefix)
            audio_dir = corpus / group / "audio" / f"{split}_split"
            for wav in sorted(audio_dir.glob("*.wav")):
                text = transcripts.get(wav.name)
                if not text:
                    continue
                sec = wav_seconds(wav)
                if sec < args.min_sec or sec > args.max_sec:
                    continue
                n_switches, mixed = switches(text)
                dst = out / "wavs" / group / split / wav.name
                resample(wav, dst, args.sr)
                recs.append({
                    "audio_file": str(dst.resolve()),
                    "text": text,
                    "duration": round(sec, 3),
                    "speaker": wav.name[:4],
                    "group": group,
                    "mixed": mixed,
                    "switches": n_switches,
                })
        pool[split] = recs

    # 2. assign clips to output sets: by speaker role (preferred) or by HiACC's shipped splits (legacy)
    if args.split_file:
        with open(args.split_file) as f:
            roles = json.load(f)
        speaker_role = {}
        for role in ("FT", "REF", "TEST"):
            for speaker in roles[role]:
                speaker_role[speaker] = role
        all_recs = []
        for split_recs in pool.values():
            all_recs.extend(split_recs)
        unknown = set()
        for rec in all_recs:
            if rec["speaker"] not in speaker_role:
                unknown.add(rec["speaker"])
        if unknown and not args.children:
            raise SystemExit(f"speakers missing from split file: {sorted(unknown)}")
        sets = {}
        for role in ("FT", "REF", "TEST"):
            sets[role] = [rec for rec in all_recs if speaker_role.get(rec["speaker"]) == role]
        train_key = "FT"
    else:
        sets = pool
        train_key = "train"

    totals = {}
    for split, manifest in sets.items():
        if split == train_key and args.merge_to_sec > 0:
            manifest = merge_consecutive(manifest, args.merge_to_sec, out / "wavs" / f"merged_{split}", max_sec=args.max_sec)
        rows = []
        for rec in manifest:
            repeats = 1
            if split == train_key and rec["mixed"]:
                repeats = args.oversample_mixed
            rows.extend([rec] * repeats)
        with open(out / f"{split}.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="|", quoting=csv.QUOTE_NONE, escapechar="\\")
            writer.writerow(["audio_file", "text"])
            for rec in rows:
                writer.writerow([rec["audio_file"], rec["text"].replace("|", " ")])
        with open(out / f"{split}.jsonl", "w", encoding="utf-8") as f:
            for rec in manifest:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        seconds = sum([rec["duration"] for rec in manifest])
        mixed_seconds = sum([rec["duration"] for rec in manifest if rec["mixed"]])
        hours = seconds / 3600
        mixed_hours = mixed_seconds / 3600
        totals[split] = {"clips": len(manifest), "csv_rows": len(rows), "hours": round(hours, 3), "mixed_hours": round(mixed_hours, 3)}
        print(f"{split:5s} clips={len(manifest):5d} rows_in_csv={len(rows):5d} hours={hours:5.2f} mixed_hours={mixed_hours:5.2f}")
    with open(out / "summary.json", "w") as f:
        json.dump(totals, f, indent=2)


if __name__ == "__main__":
    main()
