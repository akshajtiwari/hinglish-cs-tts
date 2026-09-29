# 11 — Open decisions and risks

## Decisions

| # | Question | Recommendation | When |
|---|---|---|---|
| D1 | Name | "SwitchMOS" (working). Alternatives: CS-MOS, SNAP | Phase 0 |
| D2 | Primary claim | Switch-aware predictor beats the same model without switch expert on code-switched speech; per-switch scores validated | Phase 0 |
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
| Minimal-pair model learns "was edited", not "unnatural" | Medium | Same vocoder on both; non-switch edit controls; human check |
| Edits don't sound worse | Medium | Human check in Phase 2; fall back to DSP controls |
| IndicF5 can't edit regions / mishandles Latin | Medium | Test in Phase 2; alternatives: F5 base, VoiceCraft |
| Gains small (as DAMOS) | Medium | Headline on code-mixed subset; per-switch validity is a contribution on its own |
| Clip-length confound | Known | Duration-only baseline; length-matched analysis |
| Competition on SpeechArenaBench | Rising | Move fast; public repo exposure (D9) |
| A16 speed | Known | Precompute features; reduce sampling steps for editing |
| Too few code-mixed pairs in some languages | Unknown | Phase 1 count; restrict leave-one-out to languages with enough |
| License mixing (NC corpora) | Low | Keep NC data out of released model training, or release model as research-only |
