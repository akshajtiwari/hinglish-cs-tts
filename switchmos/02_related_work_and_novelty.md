# 02 — Related work and novelty

Surveyed 2026-09-23 to 2026-09-30. Numbers checked against the cited papers; ⚠ marks items not verified on a primary source.

## 2.1 How naturalness is measured today

| Family | Examples | How | Limitation for us |
|---|---|---|---|
| Human tests | MOS, CMOS, MUSHRA, AB preference | People rate or compare | Slow, costly, whole-clip |
| Learned MOS predictors | UTMOS, UTMOSv2, DNSMOS, NISQA, SQuId, IndicMOS | Network imitates human scores | Whole-clip; mostly English; fail on modern and non-English speech (2.3) |
| Preference judges / reward models | SpeechJudge, MOS-RMBench models, PrefSQA | Trained on "A better than B" | Whole-clip; SpeechJudge is 7–11B |
| Reference-based | PESQ, STOI, MCD | Compare to a matching real recording | TTS has no matching recording |
| Proxies | WER/CER, speaker similarity, FAD | Intelligibility, voice match, distribution | Not naturalness |
| Label-free | SpeechLMScore, TTScore-pro, TTSDS2 | Likelihood / distance to real speech | Weak per clip (TTScore-pro SRCC ≈ 0.05 on SOMOS) |
| Local | Join cost (1990s), DAMOS, frame-level MOS | Measure or localize defects | Generic defects; DAMOS +0.007 only |

## 2.2 The state of the art beyond UTMOS

| Model | Type | Result | Source |
|---|---|---|---|
| UTMOS (2022) | SSL strong learners + weak learners, stacked | BVCC utt SRCC 0.897, sys 0.936 | 2204.02152 |
| UTMOSv2 (2024) | wav2vec2 + spectrogram CNN fusion, multi-stage, multi-dataset | VMC'24 T1 sys SRCC 0.919 vs UTMOS 0.615 | 2409.09305 |
| APG-MOS | Auditory branch + HuBERT-RVQ + w2v2 | BVCC sys SRCC 0.936 vs UTMOS 0.925 | 2504.20447 |
| DistilMOS | Layer-wise self-distillation | Zero-shot SOMOS utt 0.387 vs SSL-MOS 0.188 | 2601.13700 |
| SpeechJudge-BTRM / GRM | Qwen2.5-Omni-7B; Bradley–Terry / generative | SpeechJudge-Eval: UTMOS 53.7%, Gemini-2.5-Flash 69.1%, **BTRM 72.7%, GRM 77.2%** | 2511.07931 |
| MOS-RMBench models | Scalar / generative reward models | Scalar BT 80.0%; UTMOS 68.2% | 2510.00743 |
| PrefSQA | Dual SSL, uncertainty-aware BT | SOMOS-NM pairwise 74.7% | 2606.19597 |
| Auto-ATT | Qwen2-Audio LoRA, Chinese human-likeness | Trap-item F1 0.92 vs UTMOSv2 0.14 | 2505.11200 |
| Conversational predictor | Whisper-large-v3 | ConvTTS PCC 0.48 vs UTMOSv2 −0.19 | 2603.01467 |

VoiceMOS winners: 2023 French track won by a model trained only on non-BVCC multilingual data (0.91; UTMOS <0.35). 2024: kNN retrieval and UTMOSv2. 2026: large ensembles with listener modelling.

## 2.3 Where every current predictor fails

"Limits of reference-free metrics" (2609.13150), pairwise accuracy:

| Corpus | UTMOS | UTMOSv2 | SCOREQ | Longest-clip | Human ceiling |
|---|---|---|---|---|---|
| BVCC (older systems) | 0.892 | 0.899 | 0.909 | 0.517 | 0.887 |
| TTS-HP (clean commercial TTS) | **0.510** | **0.528** | **0.502** | 0.524 | 0.764 |

- Also: UTMOSv2 0.118 system correlation on modern zero-shot TTS (2603.24430); UTMOS <0.35 on French (VMC'23); SSL-MOS 0.285 on Indic LIMMITS (IndicMOS); UTMOS reportedly penalizes code-switched transitions humans accept (LCG, 2609.01016 ⚠ argued, not controlled).
- Using a single predictor as an RL reward got hacked (held-out UTMOS 4.51 → 1.23); a composite held.

## 2.4 What drives gains (from ablations)

| Lever | Effect |
|---|---|
| Training-data diversity / multi-dataset | **Largest** |
| Multi-stage training | Large (UTMOSv2 0.919 → 0.710 without) |
| Pairwise / Bradley–Terry objective | Large on clean TTS (80% vs 76% regression) |
| Fine-tuned audio-LLM judge | Moderate (+4.5 over BTRM); expensive |
| Listener / domain conditioning | Moderate (UTMOS OOD 0.871 → 0.825 without) |
| SSL + spectrogram fusion | Moderate |
| Retrieval / kNN | Moderate |
| Ensembling / stacking | Small (UTMOS stacking +0.006) |
| Phoneme / text conditioning | Small or negative |

## 2.5 Code-switched TTS and its evaluation

- **Methods (2016–2026):** Hinglish Festival voices (Sitaram & Black 2016); Indic bilingual HTS (Thomas et al., Interspeech 2018); Mandarin–English Tacotron and PPG work (2019–2020); CS-LLM (ASRU 2025); Flipkart Hinglish Tacotron2 (Joshi & Garera 2023); IndicF5 (AI4Bharat 2025); UniCoM, CS-FLEURS (2025).
- **Evaluation used:** almost always whole-utterance MOS/CMOS, CER, speaker similarity.
- **Local evaluation, 2026:** LCG (EMNLP 2026) rates accent of the embedded phrase; MagpieTTS-LF (Interspeech 2026) measures pitch/energy jumps at chunk boundaries; Yeo et al. CMI_speech is a frame-level language-mixing index. None scores switch naturalness against human behaviour.
- **Perception:** code-switched TTS sentences are less intelligible than monolingual ones regardless of engine (Méndez Kline & Zellou 2025).

## 2.6 Closest threats

| Work | Overlap | How we differ |
|---|---|---|
| **SpeechJudge** (ICLR 2026) | Preference-trained naturalness judge incl. Mandarin–English mixed clips | Indic + multilingual mix; local-event branch; 10–25× smaller; uses ties |
| SpeechArenaBench paper (Interspeech 2026) | Indic preferences incl. code-mixed | Only XGBoost over human axis ratings; no audio model |
| IndicMOS (Interspeech 2024) | Indic MOS predictor | Old data; no code-mixing; no modern systems |
| DAMOS (2026) | Localize then fuse | Generic distortions; we anchor on linguistic events |
| UTMOSv2 | Multi-dataset, multi-stage, fusion | English-centric; near chance on commercial TTS |

## 2.7 What is new

1. **A whole-clip naturalness predictor trained on a broad multilingual mix** (English, Mandarin, 10 Indic languages, code-switched; absolute MOS, MUSHRA, and pairwise). Headline.
2. **First predictor trained on SpeechArenaBench** (subject to the licence question in `03_datasets.md` §3.6).
3. **A local-event branch** scoring language switches inside a naturalness predictor.
4. **Local branch trained on edited minimal pairs.** No quality predictor has done this.
5. **Tie-aware preference training** (Davidson); prior work drops ties.
6. **Leave-one-language-out generalization** across Indic languages.
7. **Practical size.**

**Not claimed:** first code-switched naturalness judge (SpeechJudge covers Mandarin–English); replacing UTMOS on old English benchmarks; human-vs-AI detection.

## 2.8 Why this wasn't done earlier

MOS came from telephony (one number per call). Unit-selection join costs measured seams, then were dropped when neural TTS removed explicit joins. Code-switched TTS spent years just getting it to work. The finding that real switches are *marked* sits in phonetics journals. The enabling pieces are recent: HiACC (2025), MMS alignment (2023), SpeechJudge-Data (2025), SpeechArenaBench (2026).

## 2.9 Venues

| Venue | Fit | Date |
|---|---|---|
| **Interspeech 2027** (São Paulo) | Primary: predictor papers and VoiceMOS work appear here | **Papers due Feb 9, 2027** |
| ICASSP 2027 (Toronto) | — | Deadline passed (Sep 23, 2026) |
| NeurIPS Datasets & Benchmarks | If the released eval suite / rated set is the headline | ~May 2027 ⚠ |
| VoiceMOS Challenge / Interspeech special session | Propose a code-switched track | Next edition ⚠ |
| CALCS workshop (ACL/NAACL) | Code-switching community; no TTS papers in 2025 | ⚠ |

## 2.10 Sources

UTMOS 2204.02152 · UTMOSv2 2409.09305 · APG-MOS 2504.20447 · DistilMOS 2601.13700 · Distill-MOS 2502.05356 · SpeechJudge 2511.07931 · MOS-RMBench 2510.00743 · PrefSQA 2606.19597 · Auto-ATT 2505.11200 · Conversational predictor 2603.01467 · Limits 2609.13150 · I2D 2603.24430 · VMC'23 2310.02640 · VMC'24 2409.07001 · VMC'26 2609.13792 · MOS-Bench 2411.03715 · IndicMOS (Interspeech 2024) · DAMOS 2608.21176 · Frame-level MOS 2508.10374 · TTScore 2509.20485 · LCG 2609.01016 · MagpieTTS-LF 2606.18485 · Yeo et al. 2606.19381 · SpeechArenaBench 2604.21481 · Méndez Kline & Zellou, Frontiers CS 2025 · Thomas et al., Interspeech 2018 · Joshi & Garera 2312.01103 · Interspeech 2027 https://interspeech2027.org/ · ICASSP 2027 https://2027.ieeeicassp.org/call-for-papers/
