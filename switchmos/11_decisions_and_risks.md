# 11 — Open decisions and risks

## Decisions

| # | Question | Recommendation | When |
|---|---|---|---|
| D1 | Name | "SwitchMOS" (working). Alternatives: CS-MOS, SNAP | Phase 0 |
| D2 | Primary claim | **Decided 2026-09-30:** whole-clip predictor beats UTMOS/UTMOSv2 on modern, Indic, and code-switched speech, competitive on classic benchmarks. Switch branch = key ablation and secondary output | Done |
| D2b | Licence | **Decided 2026-09-30:** research-only model; full data mix incl. SOMOS, BVCC, SpeechJudge, Blizzard | Done |
| D3 | Loanwords ("office", "phone") | Count as switches, tag them, report with and without | Phase 0 |
| D4 | Romanized all-Latin input | v1 requires mixed script or tags; word-level LID in v2 | Phase 0 |
| D5 | Encoder | Pilot mHuBERT-147 vs XLS-R vs MMS-300M on dev pairs | Phase 4 |
| D6 | Two-system preference labels | Read card/paper; treat as ties if they mean "both good" | Phase 1 |
| D7 | Phrase-boundary rule | Pause ≥150 ms or punctuation; check on 50 hand labels | Phase 3 |
| D8 | Edit types for minimal pairs | Infill regeneration, duration change, pitch reset, accent-mismatched re-render | Phase 2 |
| D9 | Repo visibility | Public repo is indexed by search engines; consider private until submission | Now |
| D10 | Ethics / rater pay | Consent form; fair pay; check institutional approval | Before Phase 8 |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Model learns system identity, not quality (only 7 systems) | High | Held-out-system splits; add our own systems as tests |
| Rating scales clash across datasets (MOS, MUSHRA, pairwise) | Medium | Dataset embeddings with per-dataset bias; staged training |
| Commercial-API audio (SpeechArenaBench) under restrictive terms of service | Medium | Legal check before release; research-only licence |
| Win comes only from data, not design | Medium | Ablation: our model trained on UTMOS's data only |
| Reward hacking when used as a TTS reward | Medium | Explicit reward-optimization test (07) |
| Minimal-pair model learns "was edited", not "unnatural" | Medium | Same vocoder on both; non-switch edit controls; human check |
| Edits don't sound worse | Medium | Human check in Phase 2; fall back to DSP controls |
| IndicF5 can't edit regions / mishandles Latin | Medium | Test in Phase 2; alternatives: F5 base, VoiceCraft |
| Switch-branch gains small (as DAMOS) | Medium | Whole-clip headline unaffected; switch branch reported as ablation and diagnostic |
| Clip-length confound | Known | Duration-only baseline; length-matched analysis |
| Competition on SpeechArenaBench | Rising | Move fast; public repo exposure (D9) |
| A16 speed | Known | Precompute features; reduce sampling steps for editing |
| Too few code-mixed pairs in some languages | Unknown | Phase 1 count; restrict leave-one-out to languages with enough |
| Minimal pairs need natural code-switched audio, which exists openly only for Hindi and Bengali | Known | For the other 8 languages, build pairs from SpeechArenaBench's synthetic clips using only clearly-worse DSP edits (splice, pitch reset, wrong duration); infill edits stay natural-speech-only. The switch expert's transfer to unseen languages is then itself a result |
| Plain fine-tuned encoder already handles code-mixed pairs well | Unknown | Phase 1.5 check before building minimal pairs |
| Code-mixed sentences are longer/harder, confounding comparisons | Known | Length-matched comparisons; error-explanation analysis in Phase 1.5 |
| License mixing (NC corpora) | Low | Keep NC data out of released model training, or release model as research-only |
