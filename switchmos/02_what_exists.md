# 02 — What exists, and what is new

## Current "does it sound human?" scores

| Family | Examples | How | Limitation for us |
|---|---|---|---|
| Human tests | MOS, CMOS, MUSHRA, AB preference | People rate or compare clips | Slow, costly, whole-clip |
| Learned MOS predictors | UTMOS, UTMOSv2, DNSMOS, NISQA, SQuId, IndicMOS | A network imitates human scores | Whole-clip; mostly English; UTMOS ρ = 0.26 with humans on Hindi, ~chance on modern TTS pairs |
| Preference judges | SpeechJudge (7B), MOS-RMBench, PrefSQA | Trained on "A better than B" | Whole-clip; SpeechJudge is huge |
| Reference-based | PESQ, STOI, MCD | Compare to a matching real recording | TTS has no matching recording |
| Proxies | WER/CER, speaker similarity, FAD | Intelligibility, voice match, distribution | Not naturalness |
| Label-free | SpeechLMScore, TTScore-pro, TTSDS2 | Likelihood or distance to real speech | Weak per clip (TTScore-pro SRCC ≈ 0.05 on SOMOS) |
| Local | Join cost (1990s), DAMOS, frame-level MOS | Measure or localize defects | Generic defects, not language switches; DAMOS gained only +0.007 |

## What made UTMOS / UTMOSv2 work (their ablations)

- Rater and domain embeddings: the biggest single effect in UTMOS.
- Staged training (train parts → freeze → fuse → fine-tune): the biggest effect in UTMOSv2.
- Ranking/contrastive loss: works even without regression loss.
- Diverse modern-TTS training data.
- Not the multi-level stacking (+0.006), not the phoneme encoder (hurt on large data).

## Closest prior work

| Work | Overlap | Gap SwitchMOS fills |
|---|---|---|
| **SpeechJudge** (ICLR 2026) | Naturalness judge trained on 99K preference pairs incl. **Mandarin–English code-switched** clips | No per-switch scores; not Indic; 7B parameters; drops ties; L2-English raters on mixed clips |
| SpeechArenaBench paper (Interspeech 2026) | 120K Indic preferences incl. code-mixed | Only an XGBoost over human axis ratings; no audio model |
| DAMOS (2026) | Localize defects, fuse into MOS | Generic distortions, small gain |
| Frame-level MOS (Interspeech 2025) | Local quality | Local scores contaminated by global context |
| LCG (EMNLP 2026) | Evaluates the switched phrase locally | Accent only; no learned metric |
| MagpieTTS-LF (Interspeech 2026) | Pitch/energy jump at chunk boundaries | Not switches; not validated |
| Join cost (unit selection era) | Boundary discontinuity | Assumes smaller jump = better |

## What is new (verified by search, 2026-09-29)

1. **Per-switch scores** inside a naturalness predictor. Not found anywhere.
2. **Training on edited minimal pairs** (same clip, only the switch regenerated). No quality predictor has done this.
3. **First predictor trained on SpeechArenaBench / Indic preferences.** The dataset is unused so far (public since April 2026; expect competition).
4. **Tie-aware preference training.** Every prior work drops ties.
5. **Leave-one-language-out generalization** across Indic–English pairs.
6. **Small model** (30–300M vs 7B).

**Not claimed:** "first code-switched naturalness predictor" (SpeechJudge covers Mandarin–English).

## Why this wasn't done before

MOS came from telephony (one number per call). Unit-selection join costs measured seams, then were dropped when neural TTS removed explicit joins. Code-switched TTS spent years just getting it to work. The finding that real switches are *marked* sits in phonetics journals. And the enabling pieces are recent: HiACC (2025), MMS alignment (2023), SpeechArenaBench (2026).
