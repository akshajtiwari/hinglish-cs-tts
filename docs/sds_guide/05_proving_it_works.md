# 05 — Proving it works: when is it "a score"?

SDS becomes a score when it passes a pre-registered test battery on data it has never seen. This is the equivalent of reporting test-set accuracy for a model.

All tests use **TEST speakers** or **TTS outputs**, never REF speakers.

## 5.1 The test battery

| Tier | Test | Data | Metric | Pass bar (pre-registered) |
|---|---|---|---|---|
| **T1 Calibration** | Does real speech look real? | Natural speech, TEST speakers | Median switch percentile; in-range rate | median 40–60; in-range 0.85–0.95 |
| **T2 Known-bad detection** | Does each part catch what it claims? | Controls built from TEST speakers | | |
| | seam part vs spliced | spliced vs natural | AUC; precision, recall, F1 at the dev-chosen threshold | AUC ≥ 0.90 |
| | switch part vs under-marked | flattened vs natural | AUC; marking = "under" rate | AUC ≥ 0.80; ≥70% flagged "under" |
| | switch part vs over-marked | exaggerated vs natural | AUC; marking = "over" rate | AUC ≥ 0.80; ≥70% flagged "over" |
| | tool artifacts | resynthesis-only vs natural | difference in scores | not significant |
| **T3 Human agreement** (primary) | Does it agree with listeners? | ~500 TTS switch clips, 5–8 bilingual raters | see 5.2 | see 5.2 |
| **T4 Robustness** | Is it stable? | TTS clips | rank correlation under ±20 ms jitter; ranks with IIT-B reference pack | Kendall τ ≥ 0.9 (jitter); ≥ 0.7 (IIT-B) |
| **T5 Usefulness** | Does it show something MOS can't? | System rankings | ranking by SDS vs by utterance MOS | reported, not a pass bar |

Thresholds for T1, T2, and T4 are our proposals, written down now. T3's bar is the paper's main claim.

## 5.2 The human-agreement test (T3), precisely

1. **Rater reliability first.** Krippendorff's α on the switch ratings. This is the ceiling: no metric can agree with raters better than raters agree with each other. Target α ≥ 0.5.
2. **Correlation.** Spearman ρ between SDS-switch and mean human switch rating, per clip. Also as a partial correlation controlling for the clip's whole-sentence MOS, so SDS isn't just re-detecting bad audio.
3. **The same for every competitor:** raw join cost, MagpieTTS-LF boundary discontinuity, CMI_speech, Whisper language-ID confidence, duration-abnormal rate, UTMOS, NISQA discontinuity, IndicMOS, CER.
4. **The pass bar:** SDS's correlation is significantly higher than raw join cost's, by Steiger's test for dependent correlations (both share the same human ratings), p < 0.05, with bootstrap 95% confidence intervals resampling raters and clips.
5. **Secondary:** word-identification-in-noise accuracy after the switch should be lower where SDS says a switch is under-marked.

## 5.3 Possible outcomes and what each means

| Outcome | Meaning | What we do |
|---|---|---|
| T1–T4 pass | SDS is a validated Hinglish switch metric | Release v1, write the paper |
| T1/T2 pass, T3 fails | SDS detects our constructed errors but listeners care about something else | Report honestly; study which features listeners track; SDS v2 |
| T3 ties with join cost | The natural-reference idea adds nothing over plain seam measurement | Paper becomes "join cost is enough"; still a publishable negative result |
| T1 fails | Reference doesn't generalize across speakers | More reference data (cross-fitting, IIT-B), fewer groups |
| B3 gate failed earlier | Natural switches don't carry a signature | Premise changes; never reach testing |

## 5.4 The moment it becomes "a score"

All three are true:
1. The reference pack is frozen and versioned.
2. T1, T2, and T3 pass on data never seen during building.
3. The code, reference pack, rated clips, and test results are public, so anyone can reproduce the numbers.

## 5.5 Proving SwitchMOS works (update 2026-09-29)

Full battery in `13_switchmos.md` §13.8. The pass conditions:
1. **Switch-branch ablation:** beats the same model without the switch branch on code-mixed pairs, no loss on monolingual pairs.
2. **Held-out systems:** pairwise accuracy and system-ranking agreement hold on TTS systems not seen in training.
3. **Held-out languages:** leave-one-language-out across the 10 Indic languages.
4. **Switch-score validity:** per-switch scores correlate with the Hinglish switch-focused human ratings (study in 06).
5. **Baselines:** reported against UTMOS, SpeechJudge-GRM zero-shot, duration-only, and SDS alone.

The SDS tests T1–T4 above still apply to the diagnostics layer.
