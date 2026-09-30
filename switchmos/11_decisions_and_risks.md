# 11 — Decisions and risks

## Decided

| # | Decision | Date |
|---|---|---|
| D1 | Working name **SwitchMOS** (no collision found in web search; GitHub/PyPI to check) | 2026-09-29 |
| D2 | **Headline:** a whole-clip naturalness predictor that beats UTMOS/UTMOSv2 on modern, Indic, and code-switched speech; classic benchmarks as no-harm checks | 2026-09-30 |
| D3 | Switch scoring is a **built-in local-event branch**: key ablation and secondary output, not the headline | 2026-09-30 |
| D4 | **Research-only licence** for the released model (allows SOMOS, BVCC, SpeechJudge, Blizzard) | 2026-09-30 |
| D5 | HiACC used with **our speaker-disjoint split** (FT 12 / REF 6 / TEST 6); shipped splits share all speakers | 2026-09-29 |
| D6 | Old documents deleted; recoverable at git tag `archive-pre-consolidation` | 2026-09-30 |
| D7 | `model/` kept as the IndicF5 editing and test-voice toolkit | 2026-09-30 |
| D8 | Target venue **Interspeech 2027** (due Feb 9, 2027) | 2026-09-30 |

## Open

| # | Question | Recommendation | By |
|---|---|---|---|
| O1 | **Can SpeechArenaBench / TTS-HP audio be used for training, or only testing, given vendor ToS?** | Ask AI4Bharat; legal read; meanwhile plan with open-model data (SpeechJudge, MANGO) and treat SAB as eval-first | Week 0 |
| O2 | SpeechArenaBench licence: MIT (card) vs CC BY 4.0 (paper) | Ask AI4Bharat | Week 0 |
| O3 | Meaning of multi-system `preference_model` labels | Confirm against "Both Good / Both Bad" | Week 1 |
| O4 | Multilingual encoder | Pilot w2v-BERT 2.0 / mHuBERT-147 / XLS-R on dev pairs, weighted by A16 memory | Week 5 |
| O5 | Feature caching strategy | Cache a layer subset or learned-weighted sum per stage (see checklist M2) | Week 5 |
| O6 | Loanwords ("office", "phone") as switches | Count them, tag them, report with and without | Week 5 |
| O7 | Fully romanized Hinglish | Out of scope for v1 | — |
| O8 | Reward-hacking test scope | Best-of-N reranking with IndicF5 (cheap) instead of RL | Week 11 |
| O9 | Repo visibility | Public and indexed; consider private until submission | Now |
| O10 | Ethics approval and rater pay | Check institutional requirement early (lead time) | Week 2 |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| **Vendor ToS forbid training on SpeechArenaBench audio** | High | O1; open-model training data; SAB for evaluation; own preference data from open TTS if needed |
| **Deadline (19 weeks) too tight** | High | Cut-list in `10_roadmap.md`; parallel phases |
| Model learns system identity (only 7 systems in SAB) | High | Held-out-system splits; add SpeechJudge and MANGO systems; our own test voices |
| Win comes only from data, not design | Medium | Ablation: our model trained on UTMOS's data only |
| Rating scales clash (MOS, MUSHRA, pairwise) | Medium | Dataset embeddings with per-dataset bias; staged training |
| Local branch gains small (as DAMOS) | Medium | Whole-clip headline unaffected; branch reported as ablation and diagnostic |
| Minimal-pair model learns "was edited" | Medium | Same vocoder on both; non-switch edit controls; listening check |
| IndicF5 can't edit regions or mishandles Latin | Medium | Feasibility test early; DSP-only controls as fallback |
| Reward hacking | Medium | Explicit test; recommend composite use |
| Compute: A16 is slow; caching storage | Medium | Measure throughput in week 1; cache selectively |
| Scoop (SpeechArenaBench public since April 2026; public repo) | Rising | Move fast; O9 |
| Clip-length confound | Known | Longest-clip baseline; length-matched analysis |
| MOS-RMBench unavailable | Known | Rebuild pairs or drop |
| SOMOS has no rater IDs | Known | Rater embedding only where IDs exist; "unknown rater" token otherwise |
