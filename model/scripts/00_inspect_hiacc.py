#!/usr/bin/env python3
"""Inspect the HiACC corpus layout, audio stats, transcripts and code-switch labels.

Stdlib only, so it runs anywhere. Usage:
    python model/scripts/00_inspect_hiacc.py data/HiACC
"""
import collections
import json
import statistics
import sys
import wave
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "data/HiACC")
if not root.exists():
    sys.exit(f"{root} not found")

print(f"== tree (depth 3) under {root}")
for p in sorted(root.rglob("*")):
    rel = p.relative_to(root)
    if len(rel.parts) <= 3 and (p.is_dir() or rel.parts[-1].endswith((".csv", ".json", ".txt", ".md"))):
        print("  ", rel, "(dir)" if p.is_dir() else f"{p.stat().st_size} B")

print("\n== audio")
by_split = collections.defaultdict(list)
srs, chans, widths = collections.Counter(), collections.Counter(), collections.Counter()
for w in root.rglob("*.wav"):
    try:
        with wave.open(str(w)) as f:
            sr, ch, sw, n = f.getframerate(), f.getnchannels(), f.getsampwidth(), f.getnframes()
    except Exception as e:  # noqa: BLE001
        print("  unreadable:", w, e)
        continue
    dur = n / sr
    key = "/".join(w.relative_to(root).parts[:3])
    by_split[key].append(dur)
    srs[sr] += 1; chans[ch] += 1; widths[sw * 8] += 1
tot = 0.0
for k, d in sorted(by_split.items()):
    s = sum(d); tot += s
    print(f"  {k:40s} n={len(d):5d}  hours={s/3600:6.2f}  mean={statistics.mean(d):5.2f}s  "
          f"min={min(d):5.2f}  max={max(d):6.2f}  median={statistics.median(d):5.2f}")
print(f"  TOTAL hours={tot/3600:.2f}   sample rates={dict(srs)}  channels={dict(chans)}  bits={dict(widths)}")

print("\n== transcripts (first 5 found)")
txts = sorted(root.rglob("*.txt"))
print("  count:", len(txts))
for t in txts[:5]:
    print("  ", t.relative_to(root), "->", t.read_text(encoding="utf-8", errors="replace").strip()[:120])

print("\n== annotation / metadata files")
for p in sorted(root.rglob("*.json")) + sorted(root.rglob("*.csv")):
    print("  ", p.relative_to(root), p.stat().st_size, "B")
    try:
        if p.suffix == ".json":
            obj = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(obj, dict):
                k = next(iter(obj)); print("     keys:", len(obj), "| first:", k, "->", json.dumps(obj[k], ensure_ascii=False)[:200])
            elif isinstance(obj, list):
                print("     items:", len(obj), "| first:", json.dumps(obj[0], ensure_ascii=False)[:200])
        else:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            print("     header:", lines[0][:160]); print("     row1  :", lines[1][:160] if len(lines) > 1 else "")
    except Exception as e:  # noqa: BLE001
        print("     (could not parse)", e)
