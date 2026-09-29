# SwitchMOS

**A language-independent, switch-aware naturalness predictor for code-switched speech.**

This folder is self-contained and describes the current project from scratch (as of 2026-09-29). The older `../docs/` folder is the history of how we got here.

## The idea in one paragraph

People in India mix Hindi and English inside one sentence ("मुझे office के लिए late हो गया"). Text-to-speech systems now get the words right but often sound wrong exactly where the language switches. Every existing automatic quality score (MOS predictors like UTMOS) scores the whole clip and is blind to this, and UTMOS is close to a coin flip on modern TTS. SwitchMOS is a predictor that gives **one "how human does this sound" score for the whole clip plus a score for every language switch**, works across language pairs, and learns mostly from real bilingual speech and automatically built "before/after" pairs rather than from expensive human ratings.

## Read in this order

| # | File | Question it answers |
|---|---|---|
| 01 | `01_problem_and_idea.md` | What problem, why it matters, what we build |
| 02 | `02_what_exists.md` | Current quality scores, closest prior work, what is new |
| 03 | `03_data.md` | Every dataset, its role, and the numbers |
| 04 | `04_switch_features.md` | Finding switches and measuring them (the interpretable layer) |
| 05 | `05_architecture.md` | The model |
| 06 | `06_training.md` | How it is trained, stage by stage |
| 07 | `07_evaluation.md` | How we prove it works |
| 08 | `08_human_study.md` | The small listening study |
| 09 | `09_outputs_and_usage.md` | What it outputs and how people use it |
| 10 | `10_roadmap.md` | Ordered steps from today to paper, with gates |
| 11 | `11_decisions_and_risks.md` | Open decisions and risks |
| 12 | `12_glossary.md` | Every term in plain words |
| 13 | `13_study_plan.md` | What to learn to work on this |

## Status

- Direction adopted; nothing trained yet.
- Data confirmed: 4,035 code-mixed Hindi preference pairs in SpeechArenaBench.
- Novelty checked: code-switched predictors exist (SpeechJudge, Mandarin–English), but none scores switches, none trains on edited minimal pairs, none trains on SpeechArenaBench.
- Next: three feasibility checks (IndicF5 region editing, edit speed on A16, do edits sound worse) and counting code-mixed pairs in the other 9 languages.
