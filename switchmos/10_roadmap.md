# 10 — Roadmap: ordered steps with gates

| Phase | Work | Output | Gate to continue | Weeks |
|---|---|---|---|---|
| **0. Decide** | Name, claims, framing (11) | Decisions recorded | Owner signs off | 0.5 |
| **1. Data check** | Count code-mixed pairs in the other 9 languages; decode two-system and tie labels; confirm HiACC split | Data table | Enough languages with ≥500 code-mixed pairs | 1 |
| **2. Feasibility** | IndicF5 region editing on Hinglish (Latin tokens); time per edit on A16; 20-pair listening check that edits sound worse; SpeechJudge-GRM 4-bit on one A16 | Feasibility note | Editing works and edits are perceptibly worse; otherwise drop edits, use DSP controls only | 1 |
| **3. Switch features** | Alignment pilot (20 files, hand-check boundaries); feature code; natural-signature check (04 §4.2) | Feature pipeline; findings | Boundary error ≤25 ms; signature present (else learned-only switch expert) | 2 |
| **4. Precompute** | Encoder features, alignments, features for all data | Feature cache | — | 1 |
| **5. Minimal pairs** | Generate edited pairs + controls at scale | Pair dataset | Human check passed | 1–2 |
| **6. SwitchLM** | Train label-free switch model | Surprisal feature | — | 1 |
| **7. SwitchMoE** | Stages 2–5 (06) | Trained model | Beats no-switch-expert on dev | 2–3 |
| **8. Human study** | Pilot → active-learning rounds | Switch ratings | α ≥ 0.5 on pilot | 2 |
| **9. Evaluate** | Full battery (07) | Results | — (report whatever happens) | 1–2 |
| **10. Release + paper** | Model, code, ratings; Interspeech paper | Public release | — | 2 |

**Total:** ~14–18 weeks part-time. Phases 3–6 can overlap.

**Optional, parallel:** fine-tune IndicF5 on HiACC FT speakers (scripts in `../model/`), as an extra test system and a case study of "does real conversational data fix switches".

**Most important early gates:** Phase 2 (can we build minimal pairs?) and Phase 3 (do real switches carry a signature?). Both are cheap and decide the design.
