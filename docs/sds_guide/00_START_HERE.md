# SDS Guide — start here

This folder explains the Switch Discontinuity Score (SDS) from zero, in the order you need it. Read the files in number order. Each one answers one question.

| File | Question it answers |
|---|---|
| 01_the_ml_analogy.md | If SDS were a normal ML model, what is the training data, the model, the test set, and the accuracy? |
| 02_what_sds_outputs.md | What goes in, what comes out, and how to read the numbers |
| 03_the_core_engine.md | What runs every single time anyone scores a clip |
| 04_building_the_core.md | How the core is built ("trained") before anyone uses it |
| 05_proving_it_works.md | How we decide "yes, this is now a real score" |
| 06_human_study.md | The listening test, in detail |
| 07_using_sds.md | How we and others use it after release |
| 08_roadmap.md | The full ordered path from today to paper, with gates |
| 09_open_decisions.md | Crucial things not yet decided, with a recommendation for each |
| 10_glossary.md | Every term used here, in plain words |
| 11_existing_scores.md | MOS, UTMOS, and every other current "does it sound human" score, and what each misses |
| 12_why_each_choice.md | One-line reason for every technical choice (16 kHz, 8 kHz, 25 ms, …) |
| **13_switchmos.md** | **The adopted direction:** the language-independent, switch-aware naturalness predictor |

> **Direction update (2026-09-29): the project now builds SwitchMOS** (working name), a language-independent, UTMOS-style naturalness predictor with a whole-clip score plus per-switch scores. **Read `13_switchmos.md` first.**
>
> How this guide fits: files 01–10 describe **SDS, the switch-diagnostics layer**. It is not dropped. It becomes SwitchMOS's switch branch and the explanation of its scores. Where a file below talks about "the score", read it as "the SDS switch-diagnostics layer".
>
> | Layer | Learned from | Output |
> |---|---|---|
> | SDS switch diagnostics (01–10) | Natural code-switched speech | Per-switch percentiles, flags, diagnosis |
> | **SwitchMOS** (13) | Human pairwise preferences, 10 languages | Whole-clip score + per-switch scores |

## SDS in five sentences

1. SDS is a measuring tool. You give it a Hinglish audio clip and its transcript. It tells you whether the moments where the speaker switches between Hindi and English sound like a real bilingual person.
2. It learns what "real" looks like from recordings of real Hinglish speakers. That is its only training data.
3. At scoring time, it measures the same things in your clip (pauses, speed, pitch, loudness, spectral jumps at each switch) and asks how far they sit from the real-speaker pattern.
4. It returns three numbers per clip (switch naturalness, ordinary-boundary naturalness, seam likelihood) plus a plain diagnosis such as "under-marked: no slowdown before the English word".
5. We only call it a score after it passes tests: it must agree with bilingual listeners better than existing measures do.

## The one idea that makes it new

Real bilinguals do **not** switch smoothly. They slow down before the switch, and they say the switched word longer and with more pitch movement. So a good TTS should reproduce that signature, not erase it. SDS measures distance from the human signature, not distance from "perfectly smooth".

## A correction discovered while writing this guide

HiACC's shipped train/val/test splits are **not** speaker-disjoint. All 24 adult speakers appear in all three, despite the readme. Any plan that says "use HiACC val speakers as the reference" is therefore wrong. We re-split by speaker ourselves; see 04_building_the_core.md §4.1.
