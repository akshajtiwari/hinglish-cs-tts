# 08 — Human study

SpeechArenaBench supplies clip-level labels. No dataset labels individual switches, so we run one small study to test per-switch scores.

## 8.1 Design

| Item | Plan |
|---|---|
| Language | Hinglish |
| Raters | 5–8 screened Hindi–English bilinguals, headphones, paid fairly, consent form |
| Stimuli | ~500 short excerpts (~1.5 s) centred on a switch, full sentence on click |
| Sources | Natural TEST-speaker speech, spliced controls, SpeechArenaBench systems, plus systems not in it (IndicF5 fine-tune, Orato, Indic Parler) |
| Selection | **Active learning:** choose switches where the model is most uncertain, in ≥2 rounds (gains appear from round 2) |
| Tasks | Switch naturalness 1–5; click where the sentence sounds wrong; subset: word identification after the switch in noise; subset: whole-sentence MOS |

## 8.2 Pilot first

50 excerpts, 3 raters. Check instructions are understood and rater agreement (Krippendorff's α) ≥ 0.5 before the full study.

## 8.3 Analysis

- Correlation of per-switch scores with switch ratings (Spearman), also controlling for whole-sentence MOS.
- Compare against switch features alone and against baselines.
- Released: excerpts + anonymized ratings.
