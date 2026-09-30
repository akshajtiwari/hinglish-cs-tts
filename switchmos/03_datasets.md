# 03 — Datasets

Verified 2026-09-28 to 2026-09-30. ⚠ = not confirmed on a primary page.

## 3.1 Roles at a glance

| Data | Labels | Role |
|---|---|---|
| Human-rated TTS datasets (3.2) | MOS, MUSHRA, pairwise | Train and test the whole-clip score |
| Natural code-switched speech (3.4) | None needed | What real switches look like; source clips for minimal pairs; SwitchLM |
| Minimal pairs (built by us, `06_training.md`) | Free: "original beats edited-at-switch" | Train the local-event branch |
| Our human study (`08_human_study.md`) | Switch ratings, clip MOS | Test only |

## 3.2 Human-rated datasets

| Dataset | Languages | Size | Label | Rater IDs | Text | TTS era | License / access | Code-switched |
|---|---|---|---|---|---|---|---|---|
| **SOMOS** | en | 20k clips, 375k ratings; 4 GB | MOS | **No** | Yes | 2020 neural | CC-BY-NC-SA; Zenodo 7378801 | No |
| **BVCC** (VoiceMOS 2022) + sarulab zoomed | en | ~7k clips ⚠, 187 systems | MOS | Yes ⚠ | Yes | ≤2020 | Zenodo 10691660 (288 MB) + scripts that fetch Blizzard audio (hours); Blizzard parts non-commercial | No |
| **SpeechJudge-Data** | zh, en, **zh–en mixed** | 99K pairs, 211 GB | Preference with strength A±1/A±2; three tie types ("missing reason", "both not good", "both very good") | Yes (rater list) | Yes (target text) | Modern zero-shot (open models) | CC-BY-NC; auto-gated; splits train ~42k / dev / test (= SpeechJudge-Eval, full agreement) / other (incl. ties) | **Yes** |
| **MANGO** | hi, ta, en | 51k MUSHRA pages, 255k ratings, 987 MB | MUSHRA 0–100 (FS2, VITS, ST2, anchor, reference per page) | Yes (integer) | ⚠ | 2022–23 | CC-BY | No |
| **SpeechArenaBench** | 10 Indic | ~105k rows (validation split), 651 GB | Pairwise: A / B / Both Good / Both Bad; 6 axis ratings per clip | Yes (`user_id`) | Yes (`sentence`) | Modern commercial (7 systems) | **Card: MIT; paper: CC BY 4.0 (conflict)**; auto-gated; **vendor ToS issue (3.6)** | **Yes (78% of sentences)** |
| TTS-HP (`datapointai/tts-human-preferences-large`) | en ⚠ | 2.7k pairs, 15 raters each | Pairwise | ⚠ | ⚠ | Modern commercial (4 systems) | CC-BY, gated; vendor ToS issue | No |
| CodecMOS-Accent | en, 10 accents | 4k clips | Naturalness, similarity, accent | ⚠ | ⚠ | Modern zero-shot | Release ⚠ | No |
| VMC'26 emotional | en | ~18k | QMOS, EMOS | ⚠ | ⚠ | Recent | ⚠ | No |
| Blizzard 2008–2025 | en, zh, fr, Indic 2014/15 | varies | MOS, MUSHRA | — | Yes | Old → 2025 | Non-commercial, from CSTR | No |
| LIMMITS 23/24 | Indic | 2.4k / 4.4k clips, ~1 rating each | MOS | — | — | 2023–24 | Not public ⚠ | No |
| SingMOS-Pro | zh, ja singing | 8k | MOS | — | — | mixed | CC-BY | No |
| QualiSpeech | en | 15k | 7 dimensions + text | — | — | mixed | CC-BY-NC-SA ⚠ | No |
| SQuId | 65 locales | >1M ratings | MOS | — | — | — | Proprietary | — |
| MOS-RMBench | derived | pairs | pairwise | — | — | — | **Not released** ("in due course") | No |

**Gaps:** no public absolute-MOS dataset with code-switched speech; Hindi–English code-switched human labels exist only as SpeechArenaBench pairs.

## 3.3 SpeechArenaBench Hindi, counted by us

Text columns only (`model/scripts/10_count_speecharena_codemix.py`; stats in `results/speecharena_hi_stats.json`):

| Item | Value |
|---|---|
| Pairs | 16,694 (9,290 sentences, 242 raters) |
| **Code-mixed pairs** (Devanagari + Latin words) | **4,035**, 2,493 sentences, 198 raters |
| Devanagari-only / Latin-only | 11,281 / 1,378 |
| English words per mixed sentence | mean 7.4 (1–35) |
| "Tie / No Preference" | 677 |
| Two systems named together | several hundred (e.g. 403 for one pair); probably "Both Good" / "Both Bad", to confirm |
| Axis ratings | noise, liveliness, voice_quality, expressiveness, hallucinations, intelligibility (1–5); early rows near-binary |

Code-mixed count is a lower bound (English in Devanagari counts as Hindi). Other 9 languages: not yet counted.

## 3.4 Natural code-switched speech

| Corpus | Pair | Hours | Notes | License |
|---|---|---|---|---|
| **HiACC** | Hi–En | 5.2 (3.2 adult) | Phone mic, 16 kHz; read + spontaneous; utterance labels only; see 3.5 | CC BY 4.0 (Zenodo) / BY-NC (paper) |
| **MUCS 2021** (OpenSLR 104) | Hi–En; Bn–En | ~95; ~53 | Technical lectures; English in Latin (paper); 7.3 GB Hi–En train | CC BY-SA 4.0 |
| CS-YODAS | Hindi 21 h context (6.3 h CS) + 6 others | 313 total | YouTube | CC BY-NC 4.0 |
| IndicVoices / Vaani | many Indic | large; CS unlabelled | Extempore | CC BY 4.0, gated |
| ASCEND | Cantonese/Mandarin–En | 10.6 | Conversation | CC BY-SA 4.0 |
| Bangor Miami | Es–En | ~35 | Conversation, word language tags | GPL-3.0 |

## 3.5 HiACC facts (inspected 2026-09-28)

- `Corpus.zip` 531,628,684 bytes, MD5 `dd6cc9354e1dee5e2f25bc5243df88ac`; layout `adult|children/{audio/{train,val,test}_split, transcription|transcript, annotations, metadata}`.
- Adult: 24 speakers, 3,318 clips, 3.22 h; median clip 3.0 s; all 16 kHz mono 16-bit.
- Only **1.46 h** of adult speech is actually mixed (37% of clips); 42% pure English (often read prompts), 22% pure Hindi. 3,569 switches.
- Transcripts: `ADxxxxx.wav, text`; Devanagari Hindi, Latin English, no digits; all 118 characters are in IndicF5's vocab.
- **The shipped train/val/test splits share all 24 speakers** despite the readme. We use our own speaker-disjoint roles (`../model/configs/hiacc_speaker_split.json`):

| Role | Speakers | F/M | Minutes | Switches | Use |
|---|---|---|---|---|---|
| FT | 12 | 4/8 | 96 | 1,695 | Optional IndicF5 test voice |
| REF | 6 | 3/3 | 45 | 970 | Natural-switch reference; minimal-pair source |
| TEST | 6 | 3/3 | 51 | 904 | Human study and test controls only |

`AD63` has audio but no metadata; metadata lists `AD65` with no audio; treated as one speaker.

## 3.6 Licences and vendor terms of service (BLOCKER)

- **Research-only model (decided).** SOMOS, BVCC/Blizzard, SpeechJudge are non-commercial.
- **SpeechArenaBench and TTS-HP audio came from commercial APIs.** Vendor terms restrict ML use of outputs:
  - Sarvam §10.5: no using output to "develop, train, test, fine-tune… any machine learning… system" without written permission.
  - ElevenLabs: no use as ML training or testing data; no competing models (⚠ from search snippets).
  - Google Gemini API: no developing competing models.
  - Cartesia §4.2: no using output to develop competing models.
  - OpenAI: no developing competing models (⚠ page not fetched).
  - MiniMax: ⚠ unverified.
- **Open question:** whether these bind downstream users of a third-party dataset, and whether a quality *judge* counts as a "competing model". Needs AI4Bharat's view and a legal read.
- **Mitigation options** (decide before training; `12_pre_implementation_checklist.md` item L1):
  1. Use SpeechArenaBench for **evaluation only**, or drop restricted vendors' clips from training.
  2. Build our own Hindi/code-mixed preference data from **open TTS systems** (IndicF5, Indic Parler, open multilingual models), rated by our raters.
  3. Lean on SpeechJudge-Data (outputs of open models) and MANGO (open models) for training.

## 3.6b Data strategy: vendor tiers + evaluation-only + open training data (2026-09-30)

**Vendor tiers** (our reading of each clause; to be confirmed by a legal read):

| Tier | Systems in SpeechArenaBench | Clause | Use |
|---|---|---|---|
| **A: open** | IndicF5 (MIT) | None | Train and test |
| **B: "no competing models" only** | Gemini 2.5 Pro TTS (Google), GPT-4o-mini TTS (OpenAI), Sonic 3 (Cartesia) | Forbid developing models that compete with the service; a naturalness judge is arguably not competing | **Test only** (conservative); training only if the legal read clears it |
| **C: explicit ML ban or unknown** | Bulbul v3 (Sarvam §10.5: no train/test), ElevenLabs v3 (no ML training/testing datasets), Speech 2.8 HD (MiniMax, unverified) | Forbid ML train/test, or unknown | **Excluded** unless written permission (emails in `outreach/`) |

**What survives, Hindi** (`results/speecharena_hi_pairs_by_system.json`):

| Pair tiers | All Hindi pairs | Code-mixed pairs |
|---|---|---|
| A–B | 1,540 | 409 |
| B–B | 2,904 | 750 |
| **Usable (no tier C)** | **4,444 (27%)** | **1,159 (29%)** |
| Any tier C (excluded) | 12,250 | 2,876 |
| If Sarvam grants permission (+ Bulbul vs A/B) | +1,5xx ⚠ | +866 → **2,025** |

**Combined strategy:**
1. **Train only on open data** (no commercial-vendor audio): SOMOS, BVCC (+ sarulab), SpeechJudge-Data (outputs of open models, incl. zh–en mixed), MANGO (Hindi/Tamil, open systems), Blizzard 2014/2015 Indic MOS (six Indic languages; old systems; non-commercial research), plus minimal pairs and controls from HiACC and MUCS.
2. **Test on SpeechArenaBench tier A + B pairs only**, never trained on. Tier C is not used at all unless permission arrives.
3. **Optional ablation:** if the legal read allows, add tier B pairs to training and report the difference.

**Why this is a stronger design, not just a safer one:** every SpeechArenaBench system becomes *unseen* in training, so the headline result becomes "trained without any commercial-vendor audio, generalizes to modern commercial Indic and code-switched TTS". It also removes the risk of the model learning system identity.

**Costs and mitigations:**
- Indic training signal is thinner (MANGO hi/ta, old Blizzard Indic, minimal pairs). Mitigation: multilingual encoder; if Indic accuracy falls short, add our own ratings of open voices (route 4) as a targeted top-up.
- Test set is smaller: 1,159 Hindi code-mixed pairs still gives a 95% confidence interval of about ±2.9 points on pairwise accuracy; count the other 9 languages the same way (S9).
- Tier B testing still needs confirmation that *evaluation* use is permitted (their clauses target competing models, not testing).

## 3.7 Language tagging

- Devanagari = Hindi, Latin = English where scripts are consistent (HiACC, most SpeechArenaBench Hindi, MUCS per its paper).
- English in native script needs a word-level tagger: mBERT/MuRIL fine-tuned on FIRE 2013 + COMI-LINGUA (~95–96 F1). IndicLID is sentence-level; don't use it. COMI-LINGUA's often-quoted 94.90 for aya is NER; its LID F1 is 87.15 (best 94.75).
- The other 9 SpeechArenaBench languages use their own scripts (incl. Urdu Perso-Arabic); script-change detection extends directly.

## 3.8 Training mix and test sets

See `06_training.md` §6.1 and `07_evaluation.md` §7.1. Holdouts: whole TTS systems, whole languages, raters, sentences; public MOS-Bench / SHEET splits for classic sets.
