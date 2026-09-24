# 05 — Datasets and Licenses

Status: verified 2026-09-23 via Zenodo (page + REST API), PMC full text, HuggingFace cards/API, OpenSLR, arXiv. Items marked ⚠ could not be fully verified.

## 5.1 HiACC — primary fine-tuning candidate

Singh, Singh & Kadyan, *Data in Brief* 2025, DOI 10.1016/j.dib.2025.111886.
Zenodo v2: https://zenodo.org/records/15551669 (v1: https://zenodo.org/records/15315469). Open-access text: https://pmc.ncbi.nlm.nih.gov/articles/PMC12329218/

| Item | Value |
|---|---|
| Total | 5.24 h segmented audio, 5,176 segments, 44 speakers |
| Adults | 3.22 h, 3,318 segments, 24 speakers (15 M / 9 F), ages 19–42 |
| Children | 2.04 h, 1,858 segments, 20 speakers (10 M / 10 F), ages 10–14 |
| Per-speaker | ~5–15 min usable; sessions 6–23 min (adults), 5–11 min (children), single sitting |
| Style | Mix of **spontaneous** (daily-life questionnaire, image description) and **read** (story reading). Read/spontaneous proportions NOT reported ⚠ |
| Segmentation | Read: at line ends. Spontaneous: at prosodic pauses (Praat) |
| Recording | Samsung smartphone, Play-Store recorder app; mono WAV 16 kHz 16-bit |
| Environment | Adults: university computer lab. Children: classroom near roads/playground; audible vehicle/outdoor noise |
| Transcripts | One .txt per utterance. Devanagari for Hindi, Latin for English. Verbatim. **Whisper-seeded, then manually corrected** |
| Code-switch labels | `annotations/code_switched_labels.json` — token-level Hindi/English per utterance. Also `speaker_info.csv`, `sentence_stats.csv` |
| CS statistics | Adults: 16,172 Hi / 16,307 En tokens, CMI 25.9%, 1,095 intra-sentential switches. Children: 9,976 / 2,599, CMI 21.1%, 1,091 switches |
| Time alignment | **Segment level only.** No word timestamps |
| Splits | 70/20/10 train/test/val, speaker-independent |
| Files | `Corpus.zip` 531.6 MB, MD5 `dd6cc9354e1dee5e2f25bc5243df88ac`; layout `HiACC/{Adult,Children}/{metadata,audio/{train,test,val},transcripts,annotations}` |
| ASR baselines | Whisper-medium WER 16% (adult) / 18% (child); XLS-R-300M 38/40; MMS-1B-all 31/36 |
| License | **Conflict** ⚠: Zenodo metadata says CC BY 4.0 (both versions); paper's Specifications Table says CC BY-NC 4.0. Academic fine-tuning is permitted under either. Email authors before any commercial derivative |
| Ethics | UPES ethics approval REF-1002; no PII |

**TTS suitability.**
- Multi-speaker with ~8 min/speaker: cannot build a speaker voice, but fine for adapting a reference-conditioned zero-shot model (IndicF5) to the code-switch text→acoustics mapping.
- 16 kHz smartphone audio caps effective bandwidth at 8 kHz; IndicF5 outputs 24 kHz. Acceptable for adaptation, not for fidelity gains.
- Whisper-seeded transcripts: flow-matching TTS is sensitive to transcript errors. Budget a manual pass on the 3,318 adult segments (1–2 days), and use forced-alignment score to prune.
- Use **adult subset only** for the main fine-tune. Children: slower rate (153.8 vs 172.6 wpm), noisier; reserve for a robustness ablation.
- Speaker-independent test split + token-level LID = exactly what a switch-point evaluation needs.

## 5.2 Other Hindi–English speech corpora

| Corpus | Hours | Spk | Style | CS annotation | License / access | URL |
|---|---|---|---|---|---|---|
| **MUCS 2021 Hi-En** (OpenSLR 104) | 89.86 train + 5.18 test | ⚠ not stated | spontaneous technical lectures (spoken tutorials); CS mostly technical vocabulary | none beyond transcripts; vocab 17,877; 16 kHz | **CC BY-SA 4.0, direct download** (7.3 GB) | https://www.openslr.org/104/ · https://navana-tech.github.io/MUCS2021/data.html · https://www.isca-archive.org/interspeech_2021/diwan21_interspeech.html |
| IITG-HingCoS | 7,005 utt / 71 spk (arXiv); 25 h / 9,251 sent (journal) | 71 | read, telephone 8 kHz | mixed-script text | ⚠ no public download found; contact IIT Guwahati | https://arxiv.org/abs/1810.00662 |
| MSR India Hi-En conversational | ~50 h, ~500 spk | ~500 | conversational | — | ⚠ never publicly released | https://arxiv.org/abs/1906.09426 |
| IIITH-HE-CM | 11 h, 8,804 utt | 142 | read | English written in Devanagari | ⚠ availability not stated | https://www.isca-archive.org/sltu_2018/rambabu18_sltu.pdf |
| IndicVoices (AI4Bharat) | 23.7K h / 11.2K transcribed, 22 langs; 76% extempore, 15% conversational | 51K | mostly extempore; prompts deliberately colloquial/code-mixed | ⚠ English-word script convention not documented | CC BY 4.0, gated | https://huggingface.co/datasets/ai4bharat/IndicVoices · https://arxiv.org/abs/2403.01926 |
| IndicVoices-R | 1,704 h, 22 langs | 10,496 | extempore, cleaned for TTS | verbatim + normalized | CC BY 4.0, gated | https://huggingface.co/datasets/ai4bharat/indicvoices_r |
| Rasa | 1,145 h; Hindi 50.8 h | 2/lang | studio, expressive read | none | CC BY 4.0, gated | https://huggingface.co/datasets/ai4bharat/Rasa |
| Vaani (IISc/ARTPARK/Google) | ~31K h; Hindi transcribed 963 h | 156K | spontaneous image description | Benchmark V1.0 (10.9 h Hindi) transcribes English in both scripts | CC BY 4.0, gated | https://huggingface.co/datasets/ARTPARK-IISc/Vaani · https://huggingface.co/datasets/ARTPARK-IISc/Vaani-Benchmark-V1.0 · https://arxiv.org/abs/2603.28714 |
| Lahaja | 12.5 h Hindi | 132 | read + extempore benchmark | — | CC BY 4.0, gated | https://huggingface.co/datasets/ai4bharat/Lahaja |
| Svarah | ~10 h Indian English | 117 | benchmark | English only | ⚠ | https://huggingface.co/datasets/ai4bharat/Svarah |
| Kathbath | 1,684 h, 12 langs | 1,218 | read | — | CC0, gated | https://huggingface.co/datasets/ai4bharat/Kathbath |
| Gramvaani (OpenSLR 118) | 1,000 h unlabelled + ~105 h labelled Hindi | — | spontaneous telephone | — | ⚠ license not stated | https://www.openslr.org/118/ |
| Shrutilipi | 6,457 h, 12 langs | — | read news | — | CC BY 4.0 | https://huggingface.co/datasets/ai4bharat/Shrutilipi |
| SPRING-INX | ~2,000 h, 10 langs | — | mixed | — | CC BY 4.0 | https://arxiv.org/abs/2310.14654 |
| SwitchLingua_audio (NeurIPS 2025) | 80+ h, 11 langs incl. Hindi | 174 | ⚠ | — | CC BY-NC 4.0, gated + agreement | https://huggingface.co/datasets/Shelton1013/SwitchLingua_audio · https://arxiv.org/abs/2506.00087 |
| agarwalayushi/hinglish (2026 aggregate) | 2,264 h | 6,304 | mixed aggregate (NPTEL, Kathbath, IndicTTS, CV, Mann Ki Baat, "ujs" ⚠) | utterance-level `<hi-en>` tag | CC BY 4.0, ungated | https://huggingface.co/datasets/agarwalayushi/hinglish |
| DISPLACE 2024 | 158 h far-field + 12 h close | — | conversational, code-switched | — | ⚠ challenge terms | https://arxiv.org/abs/2406.09494 |

**Takeaway.** The only *spontaneous* Hindi-English speech with explicit token-level code-switch labels you can download today is HiACC. Scale-up paths without labels: MUCS Hi-En (90 h, CC BY-SA, direct) and Hindi extempore from IndicVoices / Vaani (CC BY, gated).

## 5.3 Hindi–English code-mixed TEXT corpora (for test sentences)

| Dataset | Content | Script | Token LID? | Access |
|---|---|---|---|---|
| **COMI-LINGUA** (2025) | 125K+ expert-annotated: LID, matrix language, POS, NER, MT | Devanagari + Roman | **Yes** | https://huggingface.co/datasets/LingoIITGN/COMI-LINGUA · https://arxiv.org/abs/2503.21670 |
| LinCE | social media; CALCS LID scheme | Roman | Yes | https://aclanthology.org/2020.lrec-1.223.pdf (⚠ site unreachable at check) |
| GLUECoS | LID, POS, NER, SA, QA, NLI, MT | Roman (+some Dev.) | Yes (LID/POS/NER) | https://github.com/microsoft/GLUECoS |
| SentiMix (SemEval-2020 T9) | 20K tweets, word LID | Roman | Yes | https://aclanthology.org/2020.semeval-1.100/ |
| HinGE | human + rule-generated Hinglish, parallel Hi/En | Roman | No | https://huggingface.co/datasets/LingoIITGN/HinGE |
| CMU Hinglish DoG | 9,960 dialogue turns | Roman | No | https://huggingface.co/datasets/festvox/cmu_hinglish_dog (CC BY-SA 3.0) |
| PHINC | 13,738 sentences + En translations | Roman | No | via https://aclanthology.org/2021.ranlp-srw.3.pdf |
| Hinglish-TOP (Google) | 10K human semantic-parsing queries | Roman | No | https://github.com/google-research-datasets/Hinglish-TOP-Dataset |
| L3Cube-HingCorpus | 52.9M Twitter sentences | Roman | No | https://arxiv.org/abs/2204.08398 |

**Note.** Almost all text corpora are Roman-script. IndicF5 wants Devanagari for Hindi tokens, so per-token LID → script policy is required before synthesis (IndicXlit, Apache-2.0). COMI-LINGUA and HiACC's own JSON are the two sources with Devanagari + explicit LID. For the held-out test set, prefer HiACC test split (spontaneous, spoken-style) plus a COMI-LINGUA sample (broader vocabulary) so generalization beyond HiACC vocabulary is measured.

## 5.4 Recommended data plan

1. **Main fine-tune set:** HiACC adult (3.22 h), manually re-checked, alignment-pruned, upsampled to 24 kHz, mixed ~1:1 with clean Hindi (Rasa Hindi or IndicVoices-R Hindi, CC BY) to protect acoustic quality.
2. **Held-out eval:** HiACC speaker-independent test split (spontaneous style) + ~100 COMI-LINGUA sentences (scripted, broad vocab) + the harrrshall 30-sentence set (for direct comparability with the prior baseline).
3. **Robustness ablation:** HiACC children subset.
4. **Scale-up path (declared in paper):** MUCS Hi-En filtered by alignment score and code-mix density.
5. **License actions:** email HiACC authors to resolve CC BY vs CC BY-NC; record the answer in this file.
