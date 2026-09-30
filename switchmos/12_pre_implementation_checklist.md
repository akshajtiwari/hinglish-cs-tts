# 12 — Pre-implementation checklist

Every point to think through, research, or decide before writing training code. Each item says **why it matters**, **how to resolve it** (search / test / decide / ask), **when** (roadmap week, see `10_roadmap.md`), and **status**.

Status: **BLOCKER** (must clear before the phase starts) · **OPEN** · **PARTIAL** (some facts known) · **VERIFIED** (checked 2026-09-30, source given) · **DONE**.

---

## L — Licences and terms of service (clear first)

| # | Question | Why it matters | How to resolve | When | Status |
|---|---|---|---|---|---|
| L1 | Can SpeechArenaBench audio be used to **train** a quality judge? To **test** one? | Its audio came from commercial APIs. Sarvam §10.5 forbids using output to "develop, train, test, fine-tune… any machine learning… system"; ElevenLabs forbids ML training/testing datasets; Google, Cartesia, OpenAI forbid "competing models". SAB is our main Indic and code-switched training source | Email AI4Bharat (dataset authors) about vendor permissions; get an institutional legal read; decide among: (a) eval-only, (b) exclude restricted vendors' clips, (c) own preference data from open TTS | Week 0 | PARTIAL · **mitigation decided**: open-data training, SAB tier A+B test-only, tier C excluded (`03_datasets.md` §3.6b). Remaining: send `outreach/` emails; legal read on tier B testing |
| L2 | SpeechArenaBench licence: MIT (HF card) or CC BY 4.0 (paper)? | Determines attribution and redistribution terms | Ask AI4Bharat; record answer | Week 0 | OPEN |
| L3 | TTS-HP (`datapointai/tts-human-preferences-large`) usable? | Same vendor-ToS issue; it's the key "clean commercial TTS" test set | Same route as L1; test-only if permitted | Week 0 | PARTIAL (dataset CC-BY, gated; VERIFIED exists) |
| L4 | Release terms of our model | Trained on NC data (SOMOS NC-SA, SpeechJudge NC, Blizzard NC); NC-SA share-alike implications for weights | Release under a research-only licence; model card listing datasets and terms | Week 15 | PARTIAL (research-only decided) |
| L5 | HiACC licence conflict: CC BY (Zenodo) vs CC BY-NC (paper) | Local-branch training data | Email HiACC authors; treat as NC meanwhile (compatible with research-only) | Week 1 | OPEN |
| L6 | Can we redistribute derived artefacts (cached features, minimal pairs, our ratings)? | Release plan | Features from NC data stay NC; our ratings of open-TTS clips can be CC-BY | Week 15 | OPEN |

## F — Research framing

| # | Question | Why | How | When | Status |
|---|---|---|---|---|---|
| F1 | Final RQs and claim order | Paper structure; what "success" means | Fixed in `01_problem_and_idea.md` and `07_evaluation.md` §7.3 | — | DONE |
| F2 | Venue and deadline | Schedule | Interspeech 2027, São Paulo, papers due **Feb 9, 2027**; ICASSP 2027 deadline (Sep 23, 2026) passed. https://interspeech2027.org/ | — | VERIFIED |
| F3 | Name collision "SwitchMOS" | Avoid confusion | Web search: none found. Still check GitHub, PyPI, Hugging Face | Week 1 | PARTIAL |
| F4 | Scoop monitoring | SpeechArenaBench unused but tagged `bradley-terry`, `code-mixing`; public repo indexed | Semantic Scholar alerts on 2604.21481 and 2511.07931; arXiv keyword alerts; decide repo visibility (O9) | Week 0 | OPEN |
| F5 | Pre-registration | Credibility of claims | Commit criteria (`07_evaluation.md` §7.3) with a timestamp before phase 6 | Week 10 | OPEN |
| F6 | Page budget | Interspeech is 4 pages + references | Plan 2 tables + 2 figures; appendix via release | Week 15 | OPEN |

## D — Data access

| # | Dataset | Route and facts | When | Status |
|---|---|---|---|---|
| D1 | SOMOS | Zenodo 7378801, `somos.zip` 4.0 GB, CC-BY-NC-SA; transcripts yes; **no listener IDs** | Week 1 | VERIFIED |
| D2 | BVCC (VoiceMOS 2022) + sarulab zoomed | Zenodo 10691660 (288 MB) + included scripts fetch Blizzard audio (hours, no request found); zoomed set via VMC'24 registration | Week 1 | PARTIAL |
| D3 | SpeechJudge-Data | HF `RMSnow/SpeechJudge-Data`, 211 GB, CC-BY-NC, auto-gated; test split = SpeechJudge-Eval | Week 1 | VERIFIED |
| D4 | MANGO | HF `ai4bharat/MANGO`, 987 MB, CC-BY | Week 1 | VERIFIED |
| D5 | SpeechArenaBench | HF, ~651 GB all languages; gate accepted; Hindi 16,694 rows | Week 1 (after L1) | PARTIAL |
| D6 | MUCS Hi–En | OpenSLR 104, 7.3 GB train + 443 MB test, CC BY-SA | Week 1 | VERIFIED |
| D7 | HiACC | Already on laptop and server; checksum verified | — | DONE |
| D8 | CodecMOS-Accent, VMC'26 emotional | Release status unknown | Week 2 | OPEN |
| D9 | Download time | ~900 GB total; measure server bandwidth; stream only needed SAB languages first | Week 1 | OPEN |

## S — Data semantics (check before writing loaders)

| # | Question | Why | How | When | Status |
|---|---|---|---|---|---|
| S1 | SAB multi-system `preference_model` values | Wrong labels poison training | Cross-check with paper ("A / B / Both Good / Both Bad") and axis ratings on sample rows | Week 1 | PARTIAL |
| S2 | Tie handling across datasets | Davidson loss needs consistent ties | SAB: "Tie / No Preference" + Both Good/Bad; SpeechJudge: three tie types in "other" split; decide mapping | Week 1 | PARTIAL |
| S3 | SpeechJudge strength (A+1 vs A+2) | Strength-aware loss | Map to margin or weight | Week 3 | VERIFIED (labels exist) |
| S4 | Rater IDs per dataset | Listener embedding | SAB `user_id` ✓, SpeechJudge rater list ✓, MANGO `Rater_ID` ✓, BVCC ✓ ⚠, **SOMOS ✗** → "unknown rater" token | Week 1 | PARTIAL |
| S5 | Transcripts per dataset | Local branch needs alignment | SAB `sentence` ✓, SpeechJudge `target_text` ✓, SOMOS ✓, BVCC ✓ ⚠, MANGO ⚠ | Week 1 | PARTIAL |
| S6 | Sample rates and durations | Resampling; length confound | Inspect a sample of each; resample to 16 kHz for encoders | Week 1 | OPEN |
| S7 | MANGO MUSHRA normalization | Page-relative 0–100 scores | Normalize within page (reference/anchor), or convert pages to pairwise comparisons | Week 3 | OPEN |
| S8 | System overlap across datasets | Held-out-system splits must not leak (IndicF5 appears in SAB; F5/CosyVoice in SpeechJudge) | Build a system registry across datasets | Week 2 | OPEN |
| S9 | Code-mixed counts in all 10 SAB languages | Held-out-language test needs ≥500 pairs per held-out language | Run `model/scripts/10_count_speecharena_codemix.py --lang <x>` (text columns only, ~12 min each) | Week 1 | PARTIAL (Hindi: 4,035) |
| S10 | English written in native script | Script-based switch detection misses it | Word-level tagger (mBERT/MuRIL on FIRE 2013 + COMI-LINGUA); measure miss rate on a hand-checked sample | Week 6 | OPEN |
| S11 | Duplicate sentences across splits | Leakage | Split by sentence ID (`academic_prompt_id` in SAB) | Week 2 | OPEN |

## E — Evaluation setup

| # | Question | Why | How | When | Status |
|---|---|---|---|---|---|
| E1 | Fixed public splits for classic sets | Comparability | MOS-Bench / SHEET (github.com/unilight/sheet, MIT; splits listed in its README sheet) | Week 3 | PARTIAL |
| E2 | SpeechJudge-Eval | Main modern pairwise test | Test split of SpeechJudge-Data (full-agreement pairs) | — | VERIFIED |
| E3 | MOS-RMBench | Planned test | **Not released**; rebuild pairs from BVCC/SOMOS with its recipe, or drop | Week 3 | VERIFIED (unavailable) |
| E4 | TTS-HP | Clean commercial test where all predictors fail | Available (gated, CC-BY); L3 | Week 3 | PARTIAL |
| E5 | Held-out systems and languages | Generalization claims | Choose after S8/S9; keep ≥2 systems and ≥2 languages out | Week 2 | OPEN |
| E6 | Human ceiling | Context for accuracies | From multi-rater agreement (SAB, SpeechJudge, TTS-HP 15 raters/pair) | Week 4 | OPEN |
| E7 | Length confound | Longest-clip heuristic scores 0.52 on clean TTS | Report it as a baseline; length-matched subsets | Week 4 | OPEN |
| E8 | Statistics | Significance with few systems | Paired bootstrap over pairs/raters; Steiger for dependent correlations; per-held-out-system results | Week 10 | OPEN |
| E9 | Reward-hacking test | Safe to use as reward | Best-of-N reranking of IndicF5 outputs by each judge, verified by held-out metrics/humans (cheaper than RL) | Week 11 | OPEN |

## B — Baselines

| # | Baseline | Availability | When | Status |
|---|---|---|---|---|
| B1 | UTMOS | `torch.hub.load("tarepan/SpeechMOS:v1.2.0","utmos22_strong",trust_repo=True)`, MIT, 16 kHz | Week 3 | VERIFIED |
| B2 | UTMOSv2 | `pip install git+https://github.com/sarulab-speech/UTMOSv2.git`, MIT | Week 3 | VERIFIED |
| B3 | Distill-MOS | `pip install distillmos`, 16 kHz | Week 3 | VERIFIED |
| B4 | SCOREQ | `pip install scoreq` (ONNX) | Week 3 | VERIFIED |
| B5 | APG-MOS | Released checkpoint (Google Drive), 16 kHz, no licence stated | Week 3 | VERIFIED |
| B6 | SHEET | `torch.hub.load("unilight/sheet:v0.2.5","sheet_ssqa")` | Week 3 | VERIFIED |
| B7 | DNSMOS, NISQA | DNS-Challenge `dnsmos_local.py`; NISQA weights CC-BY-NC-SA | Week 3 | PARTIAL |
| B8 | SpeechJudge-GRM / BTRM | HF `RMSnow/*`, ~11B total, CC-BY-NC, `transformers==4.52.3`; **4-bit on one 16 GB A16 untested** | Week 3 | PARTIAL |
| B9 | DistilMOS (2601.13700), SAMOS | No public checkpoints found | — | VERIFIED (unavailable) |
| B10 | Reproduction gate | UTMOS BVCC utt SRCC ≈0.897 must reproduce before trusting the pipeline | Week 4 | OPEN |

## M — Model design

| # | Question | Why | How | When | Status |
|---|---|---|---|---|---|
| M1 | Encoder | Multilingual transfer vs A16 memory | Pilot w2v-BERT 2.0 (~600M), mHuBERT-147 (~95M), XLS-R-300M on a dev slice; measure accuracy and memory | Week 5 | OPEN |
| M2 | **Feature caching** | All-layer caching is infeasible: 24 layers × 1024 dims × 50 frames/s × 2 bytes ≈ 2.5 MB per second of audio → ~4 TB for 500 h | Cache ≤4 selected layers or a frozen learned-weighted sum (~0.1–0.4 MB/s → 180–700 GB for 500 h); or compute on the fly for the final fine-tune | Week 5 | OPEN |
| M3 | Spectrogram branch weights | UTMOSv2 used ImageNet EfficientNetV2 | EfficientNet-B0 ImageNet weights for memory | Week 6 | OPEN |
| M4 | Scale reconciliation | MOS 1–5, MUSHRA 0–100, pairwise | Per-dataset bias + scale; MUSHRA as within-page pairs | Week 6 | OPEN |
| M5 | Loss weights | Balance heads | Start equal; tune on dev; report | Week 7 | OPEN |
| M6 | Tie model | Use ties | Davidson extension of Bradley–Terry | Week 6 | DONE (decided) |
| M7 | Clips without switches | Most training clips | Learned "no events" vector; local branch contributes nothing | Week 7 | DONE (decided) |
| M8 | Clip length limits | Memory; SAB long sentences | Crop/segment at ~10–15 s for training; full clip at inference with chunk pooling | Week 5 | OPEN |

## X — Local-event branch

| # | Question | Why | How | When | Status |
|---|---|---|---|---|---|
| X1 | Aligner accuracy on natural and synthetic speech | Features need ≤25 ms boundaries | Hand-label 20 HiACC switches; also 20 TTS switches | Week 5 | OPEN |
| X2 | Natural-signature check | Premise of switch features | 04 §4.6 on HiACC REF speakers | Week 6 | OPEN |
| X3 | IndicF5 region editing | Minimal pairs | F5 `speech_edit.py` logic on IndicF5 (context mel copied, span regenerated); needs character alignment; test Latin tokens | Week 5 | OPEN |
| X4 | Edit cost on A16 | Budget | Time 20 edits at 16 and 32 sampling steps | Week 5 | OPEN |
| X5 | Do edits sound worse? | Pairs must teach something | 20-pair listening check | Week 6 | OPEN |
| X6 | Same-vocoder control | Avoid learning "was vocoded" | Pass originals through the vocoder too; non-switch edit controls | Week 6 | DONE (designed) |
| X7 | Switch detection in all 10 scripts | Local branch across languages | Script change per language pair incl. Urdu Perso-Arabic; S10 for transliteration | Week 6 | OPEN |
| X8 | SwitchLM data | Label-free signal | MUCS Hi–En (D6) + HiACC REF; drop if short on time (cut-list) | Week 7 | OPEN |

## H — Human study

| # | Question | Why | How | When | Status |
|---|---|---|---|---|---|
| H1 | Ethics approval | Required at many institutions; lead time | Check institutional process now | Week 2 | OPEN |
| H2 | Recruitment and pay | 5–8 Hindi–English bilinguals | Personal networks / campus / Karya-style platforms; fair hourly pay | Week 6 | OPEN |
| H3 | Interface | Excerpt + full-sentence playback, region marking | webMUSHRA or a small Gradio app | Week 8 | OPEN |
| H4 | Stimuli licence | Clips must be shareable | Use open-TTS outputs and HiACC TEST speakers; avoid restricted-vendor audio (L1) | Week 8 | OPEN |
| H5 | Pilot gate | Rater agreement | Krippendorff's α ≥ 0.5 on 50 clips | Week 9 | OPEN |

## C — Compute and infrastructure

| # | Question | Why | How | When | Status |
|---|---|---|---|---|---|
| C1 | A16 throughput | Plan realism (A16 ≈ 1/6 of an RTX 3090 per GPU) | Benchmark encoder forward pass (clips/s) per candidate encoder | Week 1 | OPEN |
| C2 | Disk | ~900 GB datasets + caches | 4.6 TB free on server; plan directories; delete raw audio after caching if needed | Week 1 | PARTIAL |
| C3 | Server sharing | Other users ran GPU stress tests and have an `aws_ml` project | Agree GPU schedule; check `nvidia-smi` before jobs | Week 0 | OPEN |
| C4 | Environment | Reproducibility | Server venv `hinglishtts` (pyenv 3.11.16, torch 2.8 cu128) exists; add `switchmos` package env; pin versions | Week 1 | PARTIAL |
| C5 | Job hygiene | Long runs | tmux sessions, logs under `logs/`, checkpoints under `checkpoints/` | Week 1 | OPEN |
| C6 | Experiment tracking | Compare ablations | TensorBoard or W&B; config files + seeds per run | Week 3 | OPEN |
| C7 | Code layout | Maintainability | `switchmos/` stays docs; code in a new `src/switchmos/` package with `data/`, `features/`, `models/`, `train/`, `eval/`, tests | Week 1 | OPEN |

## G — Security and hygiene

| # | Item | Action | Status |
|---|---|---|---|
| G1 | Hugging Face token was pasted in chat | **Rotate it** at huggingface.co/settings/tokens; update laptop and server token files | OPEN |
| G2 | Repo is public and indexed | Decide visibility (O9) | OPEN |
| G3 | No secrets in the repo | `.gitignore` covers data, checkpoints, venvs; never commit tokens | DONE |
| G4 | `.gitignore` pattern `data/` matches any `data/` folder | Keep tracked result files outside `data/` directories (e.g. `switchmos/results/`) | DONE |

---

## Minimum to clear before week 1 work starts

L1, L2, F4, C3, G1.
