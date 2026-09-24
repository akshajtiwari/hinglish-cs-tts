# Hinglish Code-Switched TTS — Research Docs

Project started 2026-09-23. Working title: *Natural Switches Are Not Seamless: A Switch-Localized, Human-Calibrated Metric for Code-Switched TTS, with a Hinglish Case Study.*

| Doc | What it answers |
|---|---|
| [00_initial_plan.md](00_initial_plan.md) | The original v0 brainstorm (superseded) |
| [01_idea_brief.md](01_idea_brief.md) | The idea in one page, sharpened after the survey |
| [02_novelty_assessment.md](02_novelty_assessment.md) | Is it novel? Is it important? Reviewer-eye verdict, threat table, reframing |
| [03_prior_work_and_positioning.md](03_prior_work_and_positioning.md) | Every relevant system and paper found, and where this project stands |
| [04_switch_point_evaluation.md](04_switch_point_evaluation.md) | What natural switches sound like; SDS v1 definition; human protocol; tooling |
| [05_datasets_and_licenses.md](05_datasets_and_licenses.md) | HiACC in detail; every other Hinglish speech/text corpus; licenses |
| [06_base_models_and_finetuning.md](06_base_models_and_finetuning.md) | IndicF5 facts, duration bug, recipe, compute, alternative bases |
| [07_importance_and_venues.md](07_importance_and_venues.md) | Evidence the problem matters; who uses the result; venue fit |
| [08_research_plan_and_risks.md](08_research_plan_and_risks.md) | Phases, must-run experiments, risks, next actions |
| [09_study_guide.md](09_study_guide.md) | What to learn, at what depth, with resources and checkpoints |

## Verdict in three lines

- **Fine-tuning on spontaneous Hinglish** is incremental (done for zh-en on SEAME; Orato did it for Hinglish without a paper). Keep it as the case study.
- **A switch-localized metric calibrated to real bilingual switch behaviour** is not in the literature in any language pair. Three 2026 papers circle it. Make it the paper.
- **Importance is high**: ~250 M daily code-switchers, industry markets the switch and cannot measure it, MOS predictors fail on Hindi.

## Method note

All claims were checked on 2026-09-23 against live sources (arXiv, ISCA, ACL, Zenodo, HF, GitHub). Items marked ⚠ in the docs could not be fully verified; Dhoundiyal 2023's body and IndicF5's vocab.txt are the two most important unverified items.
