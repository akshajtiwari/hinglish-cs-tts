# SwitchMOS

**A whole-clip naturalness predictor that beats UTMOS where it fails (modern, Indian-language, and code-switched speech), with built-in scoring of local events such as language switches.**

This folder is self-contained and describes the current project (reframed 2026-09-30). The older `../docs/` folder is the history of how we got here.

## The idea in one paragraph

Automatic "how human does this voice sound?" predictors such as UTMOS became the standard for judging synthetic speech. But they were trained on old, mostly English data, and on today's clean commercial voices they are close to a coin flip (UTMOS 51–54% pairwise agreement with humans, against a human ceiling of ~76%). They are weaker still on Indian languages and on speech that mixes languages. SwitchMOS is a new predictor of **whole-clip naturalness**:
- trained on a diverse mix of existing human-labelled datasets, both absolute scores and "A vs B" preferences;
- built with the architectural choices published ablations show matter most;
- given one new ingredient: a **local-event branch** that looks at language switches (and later other local trouble spots). It feeds evidence into the overall score and explains where a clip sounds unnatural.

## Read in this order

| # | File | Question it answers |
|---|---|---|
| 00 | `00_committee_proposal.md` | The whole idea for a non-specialist committee |
| 01 | `01_problem_and_idea.md` | Problem, thesis, research questions, scope |
| 02 | `02_what_exists.md` | Current quality scores and closest prior work |
| 14 | `14_sota_and_datasets.md` | **Evidence:** state of the art beyond UTMOS, where it fails, what drives gains, every human-labelled dataset |
| 03 | `03_data.md` | Code-switched data specifics (SpeechArenaBench counts, HiACC split) |
| 04 | `04_switch_features.md` | Finding and measuring switches (the local-event layer) |
| 05 | `05_architecture.md` | The model |
| 06 | `06_training.md` | Training data mix and stages |
| 07 | `07_evaluation.md` | How we prove it beats UTMOS |
| 08 | `08_human_study.md` | Small listening study for per-switch validity |
| 09 | `09_outputs_and_usage.md` | Outputs and usage |
| 10 | `10_roadmap.md` | Ordered steps with gates |
| 11 | `11_decisions_and_risks.md` | Decisions and risks |
| 12 | `12_glossary.md` | Terms |
| 13 | `13_study_plan.md` | What to learn |

## Decided (2026-09-30)

- **Headline:** beat UTMOS and UTMOSv2 on whole-clip naturalness where they fail: modern, Indic, and code-switched speech. Classic benchmarks (BVCC, SOMOS) are reported as no-harm checks.
- **Switch scoring:** an extra signal and a secondary output, not the headline.
- **Licence:** research-only model, so the full data mix is allowed (SOMOS, BVCC, SpeechJudge, Blizzard are non-commercial).

## Status

- Docs reframed; nothing trained yet.
- Data located: SpeechArenaBench (4,035 code-mixed Hindi pairs counted), SpeechJudge-Data, MANGO, SOMOS, BVCC.
- Next: download and harmonize datasets on the server; reproduce UTMOS, UTMOSv2, and SpeechJudge baselines on the full evaluation suite.
