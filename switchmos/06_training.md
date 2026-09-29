# 06 — Training

## 6.1 Stages (staged training was UTMOSv2's biggest factor)

| Stage | Trains | Data | Loss |
|---|---|---|---|
| **0. Precompute** | — | Encoder features, alignments, switch features for all audio | — |
| **1. SwitchLM** | Label-free switch-likelihood model | Natural code-switched speech | Masked / autoregressive prediction of word-level prosody |
| **2. Switch expert** | Switch expert | Minimal pairs (6.2) + controls (04 §4.3) | Ranking: natural > edited-at-switch; "no preference" for non-switch edits vs resynthesized originals; control classification; frame loss on edited span |
| **3. Global + artefact experts** | Global and artefact experts | SpeechArenaBench (+ optionally English MOS sets) | Bradley–Terry with ties |
| **4. Gate** | Gate only (experts frozen) | SpeechArenaBench | Bradley–Terry with ties; gate diversity regularizer |
| **5. Joint fine-tune** | Everything, low learning rate | SpeechArenaBench + minimal pairs | All of the above, weighted |

## 6.2 Building minimal pairs (the key new ingredient)

1. Take a natural code-switched clip (REF speakers, MUCS, CS-YODAS).
2. Pick a switch; mark a window around it.
3. Regenerate only that window with a speech-editing TTS (IndicF5 / F5 infilling: context frames kept, window regenerated) or apply a DSP change (wrong duration, pitch reset, accent-mismatched re-render).
4. **Pass both original and edited through the same vocoder.** Editing re-vocodes the whole clip, so without this the model learns "was vocoded", not "unnatural".
5. **Negative control:** also edit a non-switch word; the model must *not* prefer the original there. This stops it from simply detecting edits.
6. Human check on ~200 pairs that edited-at-switch really sounds worse.

Scale: tens of thousands of switch windows × several edit types. Generation is the bottleneck: estimated days across 4 A16s at reduced sampling steps (to be benchmarked).

## 6.3 Losses

- **Bradley–Terry:** P(A preferred) = σ(s_A − s_B). Beats regression for preference data (MOS-RMBench: 80.0% vs 75.8%).
- **Davidson ties:** uses tied pairs (677 in Hindi) instead of discarding them, which all prior work does.
- **Agreement weighting:** pairs weighted by rater agreement where available.
- **Auxiliary:** axis ratings, control class, edit-span localization.

## 6.4 Splits

- By **system** (train on some TTS systems, test on others), by **language** (leave-one-out), and by **rater** and **sentence**.
- HiACC speakers by role (03 §3.4). TEST speakers never used in training.

## 6.5 Compute on 4×A16 (16 GB each, ~1/6 of an RTX 3090 per GPU)

- Precompute encoder features once; train experts on cached features.
- Mixed precision (fp16 / bf16); DDP across 4 GPUs.
- Stages 1–4 fit comfortably; stage 5 with a partially unfrozen encoder needs small batches.
- Minimal-pair generation is the largest time cost.
