#!/usr/bin/env python3
"""Count code-mixed pairs in SpeechArenaBench (Hindi) without downloading audio.

Reads only the text/metadata columns of each Parquet shard via HTTP range requests.
Code-mixed = sentence contains at least one Latin-script word AND at least one Devanagari word.
Usage (needs an HF token with the dataset gate accepted):
    uv run --with pyarrow --with huggingface_hub --with fsspec python 10_count_speecharena_codemix.py [--lang hi] [--out stats.json]
"""
import argparse, collections, json, re
import pyarrow.parquet as pq
from huggingface_hub import HfFileSystem

ap = argparse.ArgumentParser()
ap.add_argument("--lang", default="hi")
ap.add_argument("--out", default=None)
ap.add_argument("--samples", type=int, default=15)
args = ap.parse_args()

fs = HfFileSystem()
root = "datasets/ai4bharat/SpeechArenaBench"
shards = sorted(fs.glob(f"{root}/{args.lang}/*.parquet"))
COLS = ["academic_prompt_id", "sentence", "model_a", "model_b", "preference_model", "fine_grained_eval", "user_id"]
DEV = re.compile(r"[ऀ-ॿ]"); LAT = re.compile(r"[A-Za-z]")

def kind(s):
    toks = s.split()
    has_d = any(DEV.search(t) for t in toks); has_l = any(LAT.search(t) for t in toks)
    return "mixed" if (has_d and has_l) else ("latin_only" if has_l else ("dev_only" if has_d else "other"))

rows = []
for i, sh in enumerate(shards):
    with fs.open(sh, "rb") as f:
        pf = pq.ParquetFile(f)
        cols = [c for c in COLS if c in pf.schema_arrow.names]
        t = pf.read(columns=cols).to_pylist()
    rows.extend(t)
    print(f"shard {i+1}/{len(shards)}: {len(t)} rows (total {len(rows)})", flush=True)

pairs_by_kind = collections.Counter(kind(r["sentence"] or "") for r in rows)
sent = {}
for r in rows:
    sent.setdefault(r["academic_prompt_id"], r["sentence"] or "")
sents_by_kind = collections.Counter(kind(s) for s in sent.values())
systems = collections.Counter(); mixed_systems = collections.Counter(); prefs = collections.Counter()
raters, mixed_raters = set(), set()
for r in rows:
    k = kind(r["sentence"] or "")
    for m in (r["model_a"], r["model_b"]):
        systems[m] += 1
        if k == "mixed": mixed_systems[m] += 1
    prefs[str(r["preference_model"])[:40]] += 1
    raters.add(r["user_id"])
    if k == "mixed": mixed_raters.add(r["user_id"])

latin_words = [len([w for w in s.split() if LAT.search(w)]) for s in sent.values() if kind(s) == "mixed"]
out = {
    "lang": args.lang, "shards": len(shards), "pairs_total": len(rows),
    "pairs_by_kind": dict(pairs_by_kind),
    "unique_sentences": len(sent), "sentences_by_kind": dict(sents_by_kind),
    "latin_words_per_mixed_sentence": {"mean": round(sum(latin_words)/max(1,len(latin_words)),2),
                                       "min": min(latin_words, default=0), "max": max(latin_words, default=0)},
    "raters_total": len(raters), "raters_on_mixed": len(mixed_raters),
    "system_appearances": dict(systems), "system_appearances_mixed": dict(mixed_systems),
    "preference_values_top": prefs.most_common(10),
    "fine_grained_eval_examples": [r["fine_grained_eval"] for r in rows[:3]] if "fine_grained_eval" in rows[0] else None,
    "mixed_sentence_samples": [s for s in sent.values() if kind(s) == "mixed"][:args.samples],
}
print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
if args.out:
    json.dump(out, open(args.out, "w"), ensure_ascii=False, indent=2, default=str)
