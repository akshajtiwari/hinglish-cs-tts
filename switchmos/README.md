# SwitchMOS

**A whole-clip naturalness predictor that beats UTMOS where it fails (modern, Indian-language, and code-switched speech), with built-in scoring of local events such as language switches.**

This folder is the project's only documentation. Earlier documents (from previous directions) were removed on 2026-09-30 and remain recoverable at git tag `archive-pre-consolidation`.

## The idea in one paragraph

Automatic "how human does this voice sound?" predictors such as UTMOS became the standard for judging synthetic speech. But they were trained on old, mostly English data, and on today's clean commercial voices they are close to a coin flip (51–54% agreement with humans, against a human ceiling of ~76%), and weaker still on Indian languages and mixed-language speech. SwitchMOS is a new predictor of **whole-clip naturalness**:
- trained on a broad mix of existing human ratings (absolute scores and "A vs B" preferences across English, Mandarin, Hindi, Tamil, and 8 more Indian languages);
- built with the design choices published ablations show matter most;
- with one new ingredient: a **local-event branch** that looks at language switches, feeds that evidence into the overall score, and explains where a clip sounds unnatural.

## Read in this order

| # | File | Question it answers |
|---|---|---|
| 00 | `00_committee_proposal.md` | The whole idea for a non-specialist committee |
| 01 | `01_problem_and_idea.md` | Problem, thesis, research questions, scope, stages |
| 02 | `02_related_work_and_novelty.md` | Current scores, state of the art beyond UTMOS, where predictors fail, what drives gains, prior work, novelty, venues |
| 03 | `03_datasets.md` | Every human-rated dataset, natural code-switched corpora, HiACC facts and split, **licences and vendor terms (blocker)** |
| 04 | `04_local_events.md` | Why switches are marked; finding and measuring them; controls |
| 05 | `05_architecture.md` | The model, and why each part |
| 06 | `06_training.md` | Data mix, stages, losses, minimal pairs, compute |
| 07 | `07_evaluation.md` | Test suite, baselines, pre-registered criteria |
| 08 | `08_human_study.md` | Small listening study for per-switch validity |
| 09 | `09_outputs_and_usage.md` | Outputs and usage |
| 10 | `10_roadmap.md` | Week-by-week schedule to Interspeech 2027, gates, cut-list |
| 11 | `11_decisions_and_risks.md` | Decided, open, and risks |
| **12** | **`12_pre_implementation_checklist.md`** | **Everything to think through, research, or decide before coding** |
| 13 | `13_why_each_choice.md` | One-line reason for every technical choice |
| 14 | `14_study_plan.md` | What to learn, with verified video links |
| 15 | `15_infrastructure.md` | GPU server, environment, IndicF5 toolkit and recipe |
| 16 | `16_glossary.md` | Terms |
| — | `results/speecharena_hi_stats.json`, `results/speecharena_hi_pairs_by_system.json` | Counted SpeechArenaBench Hindi statistics and pairs per system combination |
| — | `outreach/email_ai4bharat.txt`, `outreach/email_sarvam.txt` | Draft emails on licence and permission |

## Decided

- **Headline:** beat UTMOS/UTMOSv2 on modern, Indic, and code-switched naturalness; classic benchmarks as no-harm checks.
- **Switch scoring:** built-in branch, ablation, and secondary output; not the headline.
- **Licence:** research-only model.
- **Venue:** Interspeech 2027 (papers due **Feb 9, 2027**).

## Status (2026-09-30)

- Docs consolidated; nothing trained yet.
- **Vendor-terms blocker handled by design:** train only on open data; SpeechArenaBench (tier A+B systems) is a held-out test set (`03_datasets.md` §3.6b). Emails to AI4Bharat and Sarvam drafted in `outreach/`.
- **Before week 1:** send the emails and get a legal read on tier B testing (L1–L2), scoop monitoring (F4), server GPU schedule (C3), rotate the Hugging Face token (G1).
- Then: download and harmonize datasets; reproduce UTMOS/UTMOSv2/SpeechJudge baselines.
