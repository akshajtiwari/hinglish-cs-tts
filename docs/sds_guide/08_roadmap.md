# 08 — The ordered path, today to paper

Each phase has a goal, the work, what it produces, and a **gate**: a condition that must hold before the next phase starts. Phases marked ∥ can run in parallel with the metric track.

## Phase 0 — Decisions (before any code)
- **Goal:** settle the open questions in 09 that block early work.
- **Do:** decide the switch definition (loanwords), the romanized-input policy, the name, the primary claim.
- **Produces:** updated 09 with answers.
- **Gate:** items marked "decide in Phase 0" in 09 are answered.

## Phase 0.5 — Check the switch-aware predictor direction
- **Do:** full novelty search on code-switched MOS prediction; accept the SpeechArenaBench gate; count code-mixed Hindi pairs; inspect `fine_grained_eval`.
- **Gate:** enough code-mixed pairs (roughly ≥1,000) and no prior work that already does it → adopt the predictor framing (D16). Otherwise continue with the SDS-metric plan below, unchanged.

## Phase 0.6 — SwitchMOS data check (update 2026-09-29)
- **Do:** run `model/scripts/10_count_speecharena_codemix.py` for all 10 languages; decode the two-system and tie labels; check SpeechJudge data availability.
- **Gate:** enough code-mixed pairs per language for leave-one-language-out (target ≥500 per held-out language).

## Phase 1 — Data foundation
- **Goal:** clean, correctly split data.
- **Do:** apply the speaker re-split (04 §4.1); regenerate prepared data with it; email HiACC authors about the license; download IIT-B dataset.
- **Produces:** `hiacc_speaker_split.json`, per-role manifests.
- **Gate:** no speaker appears in two roles (checked by script).

## Phase 2 — Alignment pilot (step B1)
- **Goal:** know how precise word boundaries are.
- **Do:** align 20 REF clips; hand-label 20 switch boundaries in Praat.
- **Produces:** aligner error report.
- **Gate:** median error ≤ 25 ms, or an adapted aligner that achieves it.

## Phase 3 — Features and the natural-signature gate (B2–B3)
- **Goal:** find out whether the core idea holds.
- **Do:** implement `sds/features.py`; run on all REF speech; compare switches with ordinary boundaries per speaker.
- **Produces:** `ref_boundaries.parquet`; a short findings note with plots.
- **Gate (go/no-go):** at least two predicted effects, consistent across speakers. **If this fails, stop and rethink the premise.**

## Phase 4 — Build and freeze SDS v1 (B4–B8)
- **Goal:** a finished, frozen scorer.
- **Do:** pick hyperparameters on REF; fit reference; build dev controls; fit seam classifier; unit tests; freeze pack `hinglish-v1`; write the test plan.
- **Produces:** `sds` package, `hinglish-v1` pack, test plan committed.
- **Gate:** unit tests pass; test plan committed **before** Phase 5 starts.

## Phase 5 — Cheap tests: T1 and T2
- **Goal:** prove calibration and known-bad detection without raters.
- **Do:** score natural TEST speech; build TEST controls; score them.
- **Produces:** T1/T2 results table.
- **Gate:** T1 and T2 pass. If not, go back to Phase 4 as v2.

## Phase 6 ∥ — TTS outputs (includes the fine-tune)
- **Goal:** the audio that SDS and listeners will judge.
- **Do:** fine-tune IndicF5 on FT speakers (after you've reviewed the training code); generate the test sentences with every system, same reference voice, fixed settings; pick the fine-tune checkpoint with SDS on a dev set drawn from REF sentences.
- **Produces:** one folder of clips per system, generation settings logged.
- **Gate:** every system has audio for every test sentence.

Can start as soon as Phase 1 is done; only checkpoint selection waits for Phase 4.

## Phase 7 — Human study (06)
- **Goal:** gold labels.
- **Do:** pilot (50 clips, 3 raters) → fix → full study (~500 clips, 5–8 raters).
- **Produces:** ratings CSV.
- **Gate:** α ≥ 0.5 on the pilot before the full study.

## Phase 8 — The main test: T3, T4, T5
- **Goal:** the paper's result.
- **Do:** correlations, Steiger test vs join cost, competitor metrics, robustness, system rankings, local-vs-global comparison.
- **Produces:** results tables and figures.
- **Gate:** none. Report whatever the outcome is (05 §5.3).

## Phase 9 — Release and write
- **Do:** release `sds` package, `hinglish-v1` pack, rated clips, fine-tuned checkpoint; write the Interspeech paper.

## Rough timing (part-time)

| Phase | Weeks |
|---|---|
| 0–1 | 1 |
| 2–3 | 2 |
| 4 | 2 |
| 5 | 1 |
| 6 ∥ | 2–3 (overlaps 2–5) |
| 7 | 2 |
| 8 | 1–2 |
| 9 | 2 |
| **Total** | **~11–13 weeks** |

## The single most important gate

Phase 3. Everything else assumes real bilingual switches have a measurable signature. That's cheap to check and should be checked first.

## SwitchMOS phases (update 2026-09-29)

These follow Phase 4 (SDS layer frozen) and run alongside Phases 5–7:

| Phase | Work | Weeks |
|---|---|---|
| M1 | Encoder pilot; data loaders for SpeechArenaBench (text columns + streamed audio) | 1–2 |
| M2 | Switch-branch pretraining on controls | 1 |
| M3 | Preference training; held-out-system and held-out-language splits | 2–3 |
| M4 | Test battery (13 §13.8), including the Hinglish switch study from Phase 7 | 1–2 |

Revised total: ~15–18 weeks part-time. The SDS Phase 3 gate still comes first: if natural switches carry no measurable signature, the switch branch has little to learn from its hand-crafted features (though the learned embeddings could still help).
