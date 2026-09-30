# 10 — Roadmap

**Hard deadline: Interspeech 2027 papers due Feb 9, 2027** (São Paulo). From 2026-10-01 that is ~19 weeks. ICASSP 2027 has passed. The plan below fits 19 weeks only if the cut-list is applied when a gate slips.

Before any phase starts, clear the blockers in `12_pre_implementation_checklist.md` (vendor terms, SpeechArenaBench licence, data access).

## Schedule

| Weeks (from Oct 1) | Dates | Phase | Work | Gate |
|---|---|---|---|---|
| 0 | by Oct 3 | **0. Blockers** | Checklist section L (licences/ToS), email AI4Bharat, rotate HF token, repo visibility | Training-data decision recorded |
| 1–2 | Oct 1–14 | **1. Data** | Download and harmonize SOMOS, BVCC (+ Blizzard audio scripts), SpeechJudge-Data, MANGO, SpeechArenaBench, MUCS Hi–En; common schema; confirm label semantics; count code-mixed pairs in all 10 languages | Every dataset loads; splits fixed |
| 3–4 | Oct 15–28 | **2. Baselines** | UTMOS, UTMOSv2, Distill-MOS, SCOREQ, SHEET, SpeechJudge-GRM on the suite; reproduce UTMOS BVCC utt SRCC ≈0.897; error analysis on code-mixed pairs | Published numbers reproduced |
| 5–8 | Oct 29–Nov 25 | **3. Global model v1** | Encoder pilot; caching; semantic + acoustic branches; conditioning; mixed objectives; data-mix ablations | Beats UTMOSv2 on a dev split of modern / Indic pairs |
| 5–10 | Oct 29–Dec 9 | **4. Local branch** (parallel) | Alignment pilot and natural-signature check (04 §4.6); IndicF5 region-editing feasibility; minimal pairs; SwitchLM; integrate; ablation | Gain on code-switched dev pairs, or keep as diagnostic |
| 9–11 | Nov 26–Dec 16 | **5. Human study** | Ethics, recruitment, pilot (50 clips), active-learning rounds (~500) | Rater agreement α ≥ 0.5 |
| 11–14 | Dec 10–Jan 6 | **6. Evaluation** | Full suite, robustness, reward-hacking (best-of-N) test, all baselines | Pre-registered criteria evaluated |
| 15–18 | Jan 7–Feb 3 | **7. Writing** | Paper, figures, release prep (code, model card, splits, ratings) | Internal review done |
| 19 | Feb 4–9 | **Submit** | Final checks; submit | — |

## Cut-list (apply in this order if a gate slips)

1. Drop the optional IndicF5 fine-tuned test voice.
2. Drop SwitchLM (keep hand-crafted switch features + minimal pairs).
3. Replace IndicF5 region-editing minimal pairs with DSP-only controls (splice, pitch reset, wrong duration).
4. Reduce the human study to the pilot size plus one active-learning round (~200 clips).
5. Drop the spectrogram branch (semantic branch only).
6. Drop out-of-domain probes (conversational, emotional).
7. Keep, whatever happens: whole-clip model, baselines, modern + Indic + code-switched evaluation, local-branch ablation.

## After this roadmap

Stage 2 (all Indic–English, leave-one-language-out as a full study) and stage 3 (more language pairs, more local events). See `01_problem_and_idea.md`.
