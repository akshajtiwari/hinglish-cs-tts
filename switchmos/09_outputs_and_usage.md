# 09 — Outputs and usage

## 9.1 Input

Audio (any sample rate) + transcript + language pair (e.g. `hi-en`). Word language tags optional (needed only for all-Latin "romanized" text).

## 9.2 Output

```json
{
  "clip": "utt_0042.wav",
  "language_pair": "hi-en",
  "switchmos": 3.62,
  "experts": {"global": 3.9, "switch": 3.1, "artefact": 4.2},
  "switches": [
    {"words": ["लिए", "late"], "time_s": 1.84, "score": 2.9,
     "features": {"pause_ms": 12, "pre_rate_ratio": 1.02, "f0_jump_st": 0.3, "seam_prob": 0.72},
     "reason": "under-marked: no slowdown before the switch, flat pitch; seam likely"},
    {"words": ["late", "हो"], "time_s": 2.31, "score": 3.8, "reason": "natural"}
  ]
}
```

- `switchmos`: **whole-clip naturalness, the headline output** (higher = more human).
- `switches[].score`: per-switch naturalness.
- `reason`: from the interpretable features (04).

## 9.3 How it's used

| Use | How |
|---|---|
| Compare TTS systems | Same sentences and reference voice for all; report SwitchMOS (whole clip) with CER and speaker similarity; per-switch scores explain differences |
| Debug a system | Look at which switches score low and why |
| Pick a fine-tune checkpoint | Score each checkpoint on a fixed dev set |
| Filter synthetic training data | Drop clips with low scores before using them to train ASR |
| Reward / DPO for TTS | Possible, but check for gaming (e.g. inserted pauses) |

```bash
switchmos score --audio out/*.wav --transcripts out/transcripts.tsv --lang-pair hi-en --out results.jsonl
```

## 9.4 Fair-use rules

- Same model version, same sentences, same reference voice across systems.
- Report alongside CER and speaker similarity, not instead.
- Language pairs outside those tested are "untested", not "supported".
