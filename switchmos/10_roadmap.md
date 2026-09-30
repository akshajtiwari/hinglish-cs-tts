# 10 — Roadmap

| Phase | Work | Output | Gate | Weeks |
|---|---|---|---|---|
| **1. Docs reframe** | Whole-clip headline across all docs; survey doc | Consistent docs | — | done 2026-09-30 |
| **2. Data** | Download and harmonize SOMOS, BVCC(+sarulab), SpeechJudge-Data, MANGO, SpeechArenaBench on the server; common schema (clip, system, rater, dataset, label type); count code-mixed pairs in all 10 languages; decode two-system and tie labels | Unified data store + loaders | Every dataset loads; splits fixed | 2 |
| **3. Baselines** | Run UTMOS, UTMOSv2, DNSMOS, SpeechJudge-GRM (4-bit) on the full suite (07); error analysis on code-mixed pairs | Numbers to beat; where each fails | Reproduce UTMOS BVCC utt SRCC ≈0.897 before trusting anything | 1–2 |
| **4. Global model v1** | Encoder pilot; semantic + acoustic branches; conditioning; mixed objectives; data-mix ablations | Whole-clip model | Beats UTMOSv2 on a dev split of modern/Indic pairs | 3–4 |
| **5. Local-event branch** | Switch features (04); feasibility of IndicF5 region editing; minimal pairs; SwitchLM; integrate; with/without ablation | Full model | Gain on code-switched dev pairs, or keep as diagnostic only | 3–4 |
| **6. Human switch study** | Pilot (50 clips) → active-learning rounds (~500) | Switch ratings | Rater agreement α ≥ 0.5 | 2 |
| **7. Evaluate, release, write** | Full suite; robustness; reward-hacking test; release model, code, splits, ratings; Interspeech paper | Paper + release | — | 3 |

**Total:** ~16–20 weeks part-time. Phases 4 and 5 overlap after the first global model exists.

**Cheapest decisive steps first:** baselines (phase 3) show exactly where UTMOS/UTMOSv2 fail on our data. The encoder pilot and data-mix ablations (phase 4) show how much of the win comes from data alone.

**Optional, parallel:** fine-tune IndicF5 on HiACC FT speakers (scripts in `../model/`) as an extra modern Hinglish test system.

**Later stages:** stage 2 (all Indic–English, leave-one-language-out) and stage 3 (more language pairs and more local events). See `01_problem_and_idea.md`.
