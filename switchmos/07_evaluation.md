# 07 — Evaluation: proving it works

The equivalent of test-set accuracy for a model. Every test uses data not seen in training. Pass bars are written down before any result is seen.

## 7.1 Test battery

| # | Test | Data | Metric | Proves |
|---|---|---|---|---|
| 1 | **Switch-expert ablation** (headline) | SpeechArenaBench code-mixed pairs, held-out systems | Pairwise accuracy with vs without the switch expert | Looking at switches improves agreement with humans |
| 2 | Held-out systems | Train on some TTS systems, test on others | Pairwise accuracy; Kendall τ of system ranking vs human Bradley–Terry ranking | Not memorizing systems |
| 3 | **Held-out languages** | Leave-one-language-out across Indic–English pairs | Same | Language independence |
| 4 | **Per-switch validity** | (a) Edited pairs with known edit locations, held out; (b) our human switch study (08) | (a) Localization AUC; (b) correlation of switch scores with human switch ratings | Switch scores mean something |
| 5 | Controls | Spliced / under / over / resynthesis-only from TEST speakers | AUC; flag rates | Each failure type is caught; tool artefacts aren't |
| 6 | Label efficiency | Train with 10% → 100% of human pairs | Accuracy curve | Minimal pairs reduce human-label needs |
| 7 | Robustness | Loudness, sample rate, ±20 ms alignment jitter | Score stability (Kendall τ ≥ 0.9) | Usable in practice |
| 8 | Defect stratification | Pairs with vs without axis-rated defects | Accuracy per stratum | Not just catching noise or hallucination |

| 9 | **Standard-benchmark sanity check** | VoiceMOS 2022 (BVCC main + Mandarin OOD), VoiceMOS 2023 zero-shot, SOMOS; no retraining, with 1–5 calibration | System-level SRCC next to UTMOS | Global expert isn't broken; not overfit to Indic commercial TTS. **Expected, written in advance: SwitchMOS trails UTMOS here** (no switches; relative training; older systems) |

## 7.1b Claims ranked by expected strength (decided in advance)

| Claim | Expected likelihood | Role in paper |
|---|---|---|
| Beats UTMOS on code-mixed Hindi pairs | High (mostly shows in-domain training value) | Reported, not a contribution |
| Per-switch scores localize edited switches (AUC ≥ 0.8) | Fairly high | **Lead contribution** |
| Label efficiency (accuracy vs number of human pairs) | Fairly high | **Lead contribution** |
| Per-switch scores match human switch ratings | Moderate | Key validation |
| Switch expert improves whole-clip accuracy | Uncertain; DAMOS-style gains may be small | Secondary headline; null result reported |
| Works on held-out languages | Unknown until Phase 1 counts | Generalization claim, scoped to what's tested |
| Beats SpeechJudge on raw accuracy | Unclear, possibly not | Compete on size, locality, Indic coverage instead |

## 7.2 Baselines

| Baseline | Why |
|---|---|
| UTMOS, UTMOSv2 | Standard predictors |
| SpeechJudge-GRM (7B, 4-bit; feasibility on A16 untested) | Strongest code-switch-aware judge |
| Same model without switch expert | The real comparison |
| Duration-only | Clip length is a known confound for predictors |
| TTSDS2 (system level) | Label-free distributional baseline |
| Switch features alone (04) | Is the learned model better than the interpretable layer? |

## 7.3 Pass bars (proposed, pre-registered)

- **Primary:** switch expert improves pairwise accuracy on code-mixed held-out-system pairs, significant by paired bootstrap (p < 0.05), with no loss on monolingual pairs.
- Per-switch: localization AUC ≥ 0.8 on held-out edited pairs; significant positive correlation with human switch ratings.
- Language independence: on held-out languages, accuracy above the same-size baseline without switch expert.
- Beats UTMOS on code-mixed pairs.

## 7.4 Possible outcomes

| Outcome | Meaning |
|---|---|
| All pass | Validated switch-aware predictor |
| Switch expert helps on edits but not on SpeechArenaBench | Commercial systems' switches may already be good; per-switch scores still useful as diagnostics |
| No gain from switch expert | Whole-clip preferences don't hinge on switches: a publishable negative result |
| Fails on held-out languages | Claim narrows to trained pairs |
