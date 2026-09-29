# 02 — What goes in, what comes out

## 2.1 Input

| Input | Required | Notes |
|---|---|---|
| Audio file | yes | Any sample rate, mono or stereo. SDS resamples internally |
| Transcript | yes | The exact text that was spoken or synthesized. Hindi in Devanagari, English in Latin |
| Per-word language tags | optional | Needed only if the transcript is all-Latin "romanized Hinglish" (e.g. "mujhe office late ho gaya"), where script can't tell the language |
| Reference pack version | optional | Defaults to the current frozen Hinglish reference, e.g. `hinglish-v1` |

## 2.2 Output, three levels

### Per boundary (every adjacent word pair)

```json
{
  "clip": "sys_A/utt_0042.wav",
  "boundary": 3,
  "words": ["लिए", "late"],
  "type": "switch",
  "direction": "hi->en",
  "position": "mid-phrase",
  "features": {"pause_ms": 12, "pre_rate_ratio": 1.02, "lengthening": 0.93,
               "f0_jump_st": 0.3, "f0_range_ratio": 0.88, "energy_jump_db": 0.4,
               "mcd_jump": 6.9, "kl_jump": 1.4},
  "switch_pct": 91,
  "marking": "under",
  "seam_prob": 0.72,
  "diagnosis": "under-marked: no slowdown before the switch, switched word not lengthened, flat pitch; seam likely"
}
```

### Per clip

```json
{"clip": "sys_A/utt_0042.wav", "n_switches": 4, "n_ordinary": 3,
 "sds_switch": 78, "sds_boundary": 55, "sds_seam": 0.41,
 "in_range_rate": 0.50, "marking_counts": {"under": 2, "natural": 2, "over": 0}}
```

### Per system (averaged over a test set)

```json
{"system": "sys_A", "clips": 300, "switches": 1044,
 "sds_switch": {"median": 74, "ci95": [70, 78]},
 "sds_boundary": {"median": 58, "ci95": [55, 61]},
 "sds_seam": {"mean": 0.33, "ci95": [0.30, 0.36]},
 "in_range_rate": {"value": 0.61, "ci95": [0.57, 0.65]},
 "marking": {"under": 0.31, "natural": 0.61, "over": 0.08}}
```

## 2.3 How to read each number

| Number | Scale | Natural speech gets | Better is |
|---|---|---|---|
| `switch_pct` / `sds_switch` | 0–100 percentile of natural switches | ~50 on average | **closer to 50 or lower**; high = more unusual than real speakers |
| `sds_boundary` | 0–100, same idea for ordinary word joins | ~50 | lower |
| `seam_prob` / `sds_seam` | 0–1 probability the boundary is a splice | low, ~0.05–0.1 | lower |
| `in_range_rate` | share of switches within the natural 90% range | ~0.90 by construction | **higher**, max meaningful ≈ 0.90 |
| `marking` | under / natural / over | mostly natural | natural |

**Headline number:** `in_range_rate`. It reads like accuracy: "61% of this system's switches fall inside the range real bilinguals produce; real speech gets 90%." The three part-scores explain *why*.

## 2.4 The four readings of two numbers

| Boundary | Switch | Meaning |
|---|---|---|
| natural | natural | Human-like throughout |
| natural | unusual | The Hinglish-specific failure: fine inside each language, wrong at the switch |
| unusual | ~natural | Seams everywhere; switch only looks OK relative to equally bad neighbours |
| unusual | unusual | Broken overall |

## 2.5 What SDS does not tell you

- Whether the words are right. Use CER/WER.
- Whether the voice matches the reference speaker. Use speaker similarity.
- Overall audio quality or noise. Use MOS or a listening test.
- Anything about a clip with no switches, except the boundary and seam parts.

SDS is reported **next to** those, never instead of them.
