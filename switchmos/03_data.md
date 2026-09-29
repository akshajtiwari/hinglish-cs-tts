# 03 — Data

## 3.1 Roles at a glance

| Data | Labels | Role |
|---|---|---|
| **SpeechArenaBench** (AI4Bharat) | Human pairwise preferences + 6 axis ratings | Train the clip score; test on held-out systems and languages |
| **Natural code-switched speech** (HiACC, MUCS, CS-YODAS, …) | None needed | Learn what real switches look like; source clips for minimal pairs |
| **Minimal pairs** (built by us) | Free: "original beats edited-at-switch" | Train the per-switch scores |
| **Our human study** | Switch ratings, clip MOS | Test only (per-switch validity) |
| **TTS outputs we generate** | — | Extra test systems not in SpeechArenaBench |

## 3.2 SpeechArenaBench

- Hub: `ai4bharat/SpeechArenaBench`. MIT license, gated with automatic approval (accepted).
- 10 languages: bn, gu, hi, kn, ml, mr, or, ta, te, ur. 120K+ pairs overall, ~1,900 raters, 7 systems (Gemini 2.5 Pro TTS, GPT-4o-mini TTS, ElevenLabs v3, Sonic 3, Speech 2.8 HD, Bulbul v3 Beta, IndicF5).
- 78% of all benchmark sentences are code-mixed (4,164 / 5,357).

**Hindi, counted by us** (text columns only, `../model/scripts/10_count_speecharena_codemix.py`):

| Item | Value |
|---|---|
| Pairs | 16,694 (9,290 sentences, 242 raters) |
| **Code-mixed pairs** (Devanagari + Latin words) | **4,035**, 2,493 sentences, 198 raters |
| Devanagari-only / Latin-only pairs | 11,281 / 1,378 |
| English words per mixed sentence | mean 7.4 (1–35) |
| Ties | 677 |
| Two systems named as preferred | several hundred (e.g. 403 for one combination); meaning to be confirmed |
| Axis ratings per clip | noise, liveliness, voice quality, expressiveness, hallucinations, intelligibility (1–5); early rows look near-binary |

The code-mixed count is a **lower bound**: English written in Devanagari counts as Hindi.

**To do:** count the other 9 languages (needed for leave-one-language-out; target ≥500 code-mixed pairs per held-out language).

## 3.3 Natural code-switched speech (no labels needed)

| Corpus | Pair | Hours | Style | License |
|---|---|---|---|---|
| **HiACC** | Hi–En | 5.2 (3.2 adult) | Read + spontaneous, phone mic, token-level language labels | CC BY 4.0 (Zenodo) / BY-NC (paper) |
| **MUCS 2021** (OpenSLR 104) | Hi–En; **Bn–En** | ~95; ~53 | Technical lectures; some English in Devanagari; noisy alignment | CC BY-SA 4.0 |
| **CS-YODAS** | Hindi (21 h context, 6.3 h CS) + 6 others | 313 total | YouTube, spontaneous | CC BY-NC 4.0 |
| IndicVoices / Vaani | Many Indic | Very large; CS not labelled | Extempore / spontaneous | CC BY 4.0, gated |
| ASCEND | Cantonese/Mandarin–En | 10.6 | Conversation | CC BY-SA 4.0 |
| Bangor Miami | Es–En | ~35 | Conversation, word language tags | GPL-3.0 |

What matters is the number of **switch events**, not hours. HiACC adult alone has 3,569 switches.

## 3.4 HiACC speaker split (important)

HiACC's shipped train/val/test splits **share all 24 adult speakers**. We use our own speaker-disjoint roles (`../model/configs/hiacc_speaker_split.json`):

| Role | Speakers | F/M | Minutes | Switches | Used for |
|---|---|---|---|---|---|
| FT | 12 | 4/8 | 96 | 1,695 | Optional IndicF5 fine-tune case study |
| REF | 6 | 3/3 | 45 | 970 | Reference statistics for switch features; source clips for minimal pairs |
| TEST | 6 | 3/3 | 51 | 904 | Human study and test controls only |

`AD63` has audio but no metadata; metadata lists `AD65` with no audio; treated as one speaker.

## 3.5 Word-level language tags

- Where Hindi is Devanagari and English is Latin (HiACC, most SpeechArenaBench text): **script = language**.
- Where English appears in Devanagari (MUCS, some SpeechArenaBench): a word-level tagger, mBERT/MuRIL fine-tuned on FIRE 2013 + COMI-LINGUA (~95–96 F1). IndicLID is sentence-level; don't use it.
- Note: COMI-LINGUA's frequently quoted 94.90 for aya is NER; its LID F1 is 87.15 (best model 94.75).
