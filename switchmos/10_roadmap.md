# 10 — Roadmap: ordered steps with gates

| Phase | Work | Output | Gate to continue | Weeks |
|---|---|---|---|---|
| **0. Decide** | Name, claims, framing (11) | Decisions recorded | Owner signs off | 0.5 |
| **1. Data check** | Count code-mixed pairs in the other 9 languages; decode two-system and tie labels; confirm HiACC split | Data table | Enough languages with ≥500 code-mixed pairs | 1 |
| **1.5 Room-for-improvement check** | Fine-tune a plain encoder with Bradley–Terry on SpeechArenaBench Hindi (held-out systems). Then (a) compare accuracy on code-mixed vs monolingual pairs, matched for sentence length; (b) check whether switch features (04) explain the plain model's *errors* on code-mixed pairs; (c) accuracy vs number of switches | Go/no-go note | Switch features explain a meaningful share of the plain model's errors. If not, the whole-clip headline is dropped and the paper leads with per-switch localization and label efficiency | 1 |
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

**Most important early gates:** Phase 1.5 (is there room for a switch expert?), Phase 2 (can we build minimal pairs?), and Phase 3 (do real switches carry a signature?). All three are cheap and decide the design. Phase 1.5 can run alongside Phase 1.
