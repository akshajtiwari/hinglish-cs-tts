# 01 — Problem, thesis, research questions

## The problem

- Automatic naturalness predictors (UTMOS, 2022) replaced many listening tests and became a standard number in speech papers.
- They no longer track human judgment on today's systems:
  - Clean commercial TTS: UTMOS 0.51, UTMOSv2 0.53 pairwise agreement with humans (chance 0.50, human ceiling 0.76).
  - Modern zero-shot TTS: UTMOS 53.7% on SpeechJudge-Eval.
  - French: UTMOS below 0.35 system correlation (VoiceMOS 2023).
  - Indian languages: off-the-shelf SSL-MOS at 0.29 utterance correlation.
  - Conversational speech: UTMOSv2 correlates *negatively*.
- Code-switched speech (e.g. Hinglish, "मुझे office के लिए late हो गया"), everyday for hundreds of millions of people, has no automatic naturalness measure at all, and its characteristic failures happen at the switch.

## Thesis

Perceived naturalness depends on **global quality** and on **local events**: language switches, seams, names, numbers. Current predictors fail for two reasons:
1. They are trained on narrow, old, mostly English data.
2. They pool the whole clip uniformly, so brief local problems are averaged away.

So a better predictor needs a **diverse, mixed-objective training mix** and an **explicit local-event branch**.

## The key insight about switches

Real bilinguals don't switch perfectly smoothly. They slow down before a switch and say the switched word longer, with more pitch movement. Listeners use these cues. So the local-event branch measures how far a switch departs from the human pattern, not how "smooth" it is.

## Research questions

| # | Question | Role |
|---|---|---|
| **RQ1** | Can a predictor trained on a diverse mix of absolute-MOS and pairwise data beat UTMOS and UTMOSv2 on modern, Indic, and code-switched naturalness, while staying competitive on classic benchmarks? | **Headline** |
| RQ2 | Does adding local-event (switch) evidence improve whole-clip accuracy on code-switched speech without hurting monolingual speech? | Key ablation |
| RQ3 | Can synthetic minimal pairs replace human labels for local events? | Label efficiency |
| RQ4 | Does it generalize to unseen languages and unseen TTS systems? | Generalization |

## What we build

- **SwitchMOS**: one whole-clip naturalness score, like UTMOS, plus per-event scores with plain-language reasons.
- A released evaluation suite and a small human-rated set of switch clips.
- An Interspeech paper.

## Scope

- **Stage 1 (this project):** whole-clip naturalness with strength on Hindi–English; evaluated on classic English benchmarks, modern pairwise sets, 10 Indic languages, and Mandarin–English.
- **Stage 2:** full Indic–English coverage, leave-one-language-out.
- **Stage 3:** more language pairs and more local events (names, numbers, long-form chunk joins).
- **Not in scope:** human-vs-AI detection; building a TTS system; fully romanized Hinglish without language tags; noise/recording-quality assessment.

## Why not just copy UTMOS

Its own ablations show its multi-level stacking barely helped (+0.006). What mattered was listener and domain information, staged training, and matching training data. Later work adds pairwise objectives and spectrogram fusion. We build on those, add the local-event branch, and train on far more modern and multilingual data than UTMOS had.
