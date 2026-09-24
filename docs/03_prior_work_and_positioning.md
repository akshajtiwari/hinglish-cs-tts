# 03 — Prior Work and Where We Stand

Survey date 2026-09-23. Every entry was located and (unless flagged "abstract only") opened. Affiliations corrected vs. the v0 plan: Xue et al. 2019 is NWPU, Zhou et al. 2020 is NUS; Google's 2019 paper (Zhang et al.) is cross-lingual voice transfer, not code-switching.

## 3.1 The one-paragraph picture

Code-switched (CS) TTS is a decade-old topic (Sitaram & Black 2016; Thomas et al. 2018 at IIT Madras). Almost every paper solves *data scarcity* (how to synthesize CS speech from monolingual corpora) and evaluates with *whole-utterance* MOS/CMOS/DMOS, ASR CER, or speaker similarity. The 2025–2026 wave (LLM/flow-matching TTS) adds CS-as-ASR-augmentation papers and, very recently, three papers that look *locally* at the switch: LCG (EMNLP 2026) evaluates nativeness of the embedded phrase; MagpieTTS-LF (Interspeech 2026) defines an F0/energy boundary-discontinuity metric for chunk boundaries; Yeo et al. (2026) define a frame-level acoustic code-mixing index. **No paper defines a switch-localized acoustic discontinuity metric, normalizes it within-utterance, and validates it against human ratings of the switch moment.** On the Hinglish side, all systems train on read/studio or call-center data; none fine-tunes on an open spontaneous corpus; IndicF5's own code-mix eval is 30 sentences, intelligibility-only.

## 3.2 Code-switched TTS methods (any language pair)

| Paper | Venue | Method | CS evaluation |
|---|---|---|---|
| Sitaram & Black, *Speech Synthesis of Code-Mixed Text* — https://aclanthology.org/L16-1546/ | LREC 2016 | Festival/CLUSTERGEN Hinglish, LID + normalization | Preference tests |
| Rallabandi & Black, *On Building Mixed Lingual Speech Synthesis Systems* — https://www.isca-archive.org/interspeech_2017/rallabandi17_interspeech.html | Interspeech 2017 | Mixed-lingual from monolingual corpora, phone mapping | Subjective only |
| Chandu et al., *Mixed-Language Navigation Instructions* — https://www.isca-archive.org/interspeech_2017/chandu17_interspeech.html | Interspeech 2017 | Indic NEs in English prompts | Preference tests |
| **Thomas, Prakash, Baby, Murthy, *Code-switching in Indic Speech Synthesisers*** — https://www.isca-archive.org/interspeech_2018/thomas18_interspeech.pdf | Interspeech 2018 | Bilingual HTS Hi+En/Ta+En/Hi+Ta from monolingual data, common label set. Intro notes earlier phone-mapping gave transitions that "were not smooth" | DMOS on mono/code-mixed/code-switched sentences |
| Cao et al., *E2E CS TTS with Mix of Monolingual Recordings* — CUHK | ICASSP 2019 | Tacotron, shared/separate encoders + language embedding | MOS + ABX |
| Xue et al., *Mixed-Lingual Neural TTS with Only Monolingual Data* — https://arxiv.org/abs/1904.06063 | Interspeech 2019 | AVM + speaker/phoneme embeddings (zh/en) | Subjective naturalness / speaker consistency |
| Nakayama et al., *Speech Chain for Ja-En CS ASR and TTS* — SLT 2018 / ASRU 2019 | | Joint ASR+TTS | CER, reconstruction |
| Zhou et al., *E2E CS TTS with Cross-Lingual LM* — https://ieeexplore.ieee.org/document/9054722/ (abstract only) | ICASSP 2020 | XLM embeddings in encoder | MOS/preference |
| Cao et al., *Bilingual PPG CS TTS* — https://www1.se.cuhk.edu.hk/~hccl/publications/pub/Icassp20_cstts_camera_ready.pdf | ICASSP 2020 | Bilingual PPG bridge | MOS + AB on speaker consistency within CS utterance |
| Zhao et al., *Towards Natural Bilingual and CS TTS* — https://www.isca-archive.org/interspeech_2020/zhao20e_interspeech.html | Interspeech 2020 | Cross-lingual VC to create missing-language data | Naturalness / similarity |
| Qiang et al., *Text Enhancement for Paragraph CS TTS* — https://arxiv.org/abs/2210.11429 | ISCSLP 2021 | Cross-lingual embeddings + prosodic context | Naturalness, consistency, "prosody stability" |
| Zhang & Lin, *Cross-lingual Voice Cloning Using Low-quality CS Data* — https://arxiv.org/abs/2110.07210 | arXiv 2021 | Found CS data from non-target speakers | MOS, speaker consistency |
| **Das, Williams, Lai, *VC and CS Synthesis Using VQ-VAE*** — https://arxiv.org/abs/2203.14640 | Interspeech 2022 | Multilingual VQ-VAE | Listening tests **stratified by #switches and words-per-switch** — closest prior switch-density analysis |
| Yang, Luan, Wang, *Dynamic Language and Phonology Embedding* — https://arxiv.org/abs/2212.03435 | ICASSP 2023 | Embedding masks for L1/L2/L2-in-L1 | Naturalness/accent MOS |
| Yang et al., *Bilingual and CS TTS with Diffusion + GAN* — https://www.isca-archive.org/interspeech_2024/yang24i_interspeech.html | Interspeech 2024 | Language/speaker disentanglement | CS MOS 3.83 |
| Xu et al., *CS-LLM* — https://arxiv.org/abs/2409.10969 | ASRU 2025 | Speech LLM, synthetic CS from word-splicing monolingual corpora | WER/CER, WavLM sim, MOS 4.05 vs VALL-E X 3.36 |
| Handoyo et al., *Indonesian-English STEN-TTS + BERT LID* — https://arxiv.org/abs/2412.19043 | O-COCOSDA 2024 | Word-level LID in front-end | MOS |
| Lee et al., *UniCoM* — https://arxiv.org/abs/2508.15244 | EMNLP Findings 2025 | SWORDS word-swap + kNN-VC | Intelligibility/naturalness, downstream ASR |
| Yan et al., *CS-FLEURS* — https://www.isca-archive.org/interspeech_2025/yan25c_interspeech.pdf | Interspeech 2025 | XTTS-v2 generative (15 Hindi-X pairs) + MMS-TTS concatenative (100 ms silence at switches) | CER, UTMOS, speaker-consistency distance, alignment score; human 0–2 text naturalness |
| **Lee et al., *Phrase-Localized Language-Contrastive Guidance (LCG)*** — https://arxiv.org/abs/2609.01016 | EMNLP 2026 | Training-free guidance applied only inside the embedded phrase, attention probing to locate it | **Localized** metrics: Whisper-LID on embedded phrase, phrase-nativeness AB (N=488), global MOS. en/de/fr × ja/ko. No Hindi, no acoustic discontinuity |
| Yeo et al., *CS ASR with TTS Data Augmentation* — https://arxiv.org/abs/2601.00935 | APSIPA 2025 | **CosyVoice2 fine-tuned on SEAME (spontaneous zh-en)**, up to 100 h | UTMOS only (fine-tune *lowers* UTMOS: 2.9@10h, 3.2@100h vs 3.6 real) |
| **Yeo et al., *Code-Mixing Guided Synthetic Speech*** — https://arxiv.org/html/2606.19381 | arXiv Jun 2026 | Same + **CMI_speech**: frame-level acoustic code-mixing index as preference-learning critic | UTMOS, MER, ΔCMI vs real; no human eval |
| **Ghosh et al., *MagpieTTS-LF*** — https://arxiv.org/abs/2606.18485 | Interspeech 2026 | Long-form TTS | **Prosodic Boundary Discontinuity**: ΔF0 (Hz), ΔEnergy (dB) in ±1000 ms windows at chunk boundaries, min-max normalized. Not human-validated, not language switches |
| Zuo et al., *Complex-Text Robustness for Low-Resource Multilingual TTS* — https://arxiv.org/abs/2609.11545 | arXiv Sep 2026 | Robustness benchmark incl. CS inputs | CER, LID accuracy, **duration abnormal rate** (utterance-level) |
| Méndez Kline & Zellou — https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2025.1565604/full | Frontiers CS 2025 | Perception study, es-en, Polly voices | CS sentences less intelligible than monolingual regardless of TTS type: the switch itself costs listeners |

**Zero-shot TTS families** (Seed-TTS, CosyVoice 2/3, F5-TTS, MaskGCT, Spark-TTS, Fish S2, XTTS, VALL-E X): none publishes a CS test set or switch-local metric. IndexTTS 2.5 mentions CS only as a prompt-conditioning nuisance and GRPO-samples on CS with WER+SpkSim rewards. CS3-Bench (arXiv 2510.07881) targets speech-to-speech LLMs, not TTS naturalness.

## 3.3 Hindi–English specific

| Work | What it is | Evaluation | Relevance |
|---|---|---|---|
| Dhoundiyal et al. 2023, *A Multilingual TTS Engine Hindi-English: Hinglish* — IEEE SMART 2023, DOI 10.1109/SMART59791.2023.10428607 | ⚠ **Body not accessible.** Abstract is motivational (528 M Hinglish users). Cannot confirm any phrase-break model | Unknown | The v0 plan's "phrase-break multi-task" description is **unverified**. Do not cite for a method until the PDF is read |
| Joshi & Garera (Flipkart), *Code-Mixed TTS under Low-Resource Constraints* — https://arxiv.org/abs/2312.01103 | SPECOM 2023 | Tacotron2+WaveGlow, transliterate English→Devanagari, monolingual Hi+En studio data, 3 h speaker adaptation | MOS 4.65, CMOS ≈ Google TTS, 50 raters, utterance-level | Strongest peer-reviewed Hinglish CS-TTS method paper. Read/studio data only |
| Anand et al. (AI4Bharat), *OOV performance of Indian TTS* — https://arxiv.org/abs/2407.13435 | Interspeech 2024 | Motivated by code-mixing; adds recordings of unseen bigrams | OOV intelligibility | |
| **IndicF5 / Phir Hera Fairy** — https://huggingface.co/ai4bharat/IndicF5 · https://arxiv.org/abs/2505.20693 | AI4Bharat 2025 | F5-TTS fine-tuned on 1,417 h IN11 (Rasa, IndicTTS, LIMMITS, IndicVoices-R) | Code-mix: 30 IndicVoices sentences, MUSHRA-intelligibility 76.7 | Base model. Own CS eval is intelligibility-only |
| Indic Parler-TTS / RASMALAI — https://arxiv.org/abs/2505.18609 | Interspeech 2025 | Parler-TTS, 1,806 h, 21 langs, Apache-2.0 | Native Speaker Score; no CS test | Fallback base; 3.40 on harrrshall set |
| Pawar et al., *Multilingual TTS with Accents & Emotions* — https://arxiv.org/abs/2506.16310 | arXiv 2025 | Parler-TTS + "dynamic accent code-switching" via RVQ | WER, "cultural correctness" MOS 4.2 | Independent, no code; treat cautiously |
| Praxy Voice — https://arxiv.org/abs/2604.25441 | arXiv Apr 2026 | Routes intra-sentential code-mix to IndicF5 with transliteration | LLM-WER 0.80→0.14–0.27 | Intelligibility only |
| **Anand et al., *Preferences of a Voice-First Nation*** — https://arxiv.org/html/2604.21481v2 | arXiv Apr/Jun 2026 | 120k+ pairwise, 1,915 raters, 7 systems, **4,164-sentence code-mixed Hinglish subset** | Utterance-level pairwise; Gemini 2.5 Pro TTS top; IndicF5 not top | Decisive for baseline choice: large Hinglish code-mix benchmark exists but is utterance-level |
| Sarvam Bulbul v3 — https://www.sarvam.ai/blogs/bulbul-v3 | Commercial, Feb 2026 | Built around "people switch languages mid-sentence"; code-mixing in CER robustness benchmark | No numbers, no paper, API only | Closed baseline for human eval |
| Veena (Maya Research) — https://huggingface.co/maya-research/Veena | 3B Llama-style, Apache-2.0 | Self-reported MOS 4.2 | No paper | |
| **tryorato/orato-tts-hindi-v1** — https://huggingface.co/tryorato/orato-tts-hindi-v1 | **IndicF5 fine-tuned on ~194 h Hindi/Hinglish call-domain (real + synthetic)** | CER 19.2→18.3, SpkSim 0.863→0.899; notes Latin-script English is "the weaker path" | No paper, no CS eval | Kills "first Hinglish IndicF5 fine-tune" claim |
| Saravananravi/indicf5-hinglish — https://huggingface.co/Saravananravi/indicf5-hinglish | IndicF5 fine-tuned on OpenSLR-104 read Hindi | none | Name "IndicF5-Hinglish" is taken |
| harrrshall/hinglish-tts — https://github.com/harrrshall/hinglish-tts | Zero-shot IndicF5 + IndicXlit + char-count duration patch | 4.70/5 intelligibility on 30 sentences (3-ASR consensus CER); Kokoro 3.90, Parler 3.40, unpatched IndicF5 2.13 | Explicitly no fine-tuning, no naturalness number, "flat delivery", nothing at the switch |
| Thomas et al. 2018 (above); Murthy SSW 2025 keynote on code-mixed Indic synthesis — https://www.isca-archive.org/ssw_2025/murthy25_ssw.html | | | IIT-M has worked on this for a decade |

**TTS-as-augmentation for Hinglish ASR** (none measure TTS quality; several measure ASR *at switch points*):
- Sharma et al., IIT-B + MSR, Interspeech 2020 — https://www.isca-archive.org/interspeech_2020/sharma20c_interspeech.pdf — Tacotron-2 CS synthesis, ~100 h synthetic, WER at switch points measured.
- Biswas et al., Oracle, Interspeech 2025 — https://www.isca-archive.org/interspeech_2025/biswas25_interspeech.pdf — Llama-3.3 text + Indic Parler-TTS; **Code-Switch Bigram Accuracy (CBA)** at switch points.
- Mitra et al., BEHE-CMDisfl, WILDRE @ LREC 2026 — https://aclanthology.org/2026.wildre-1.5/ — CS with disfluencies via Indic Parler-TTS.
- Hamed, Vu, Habash, CALCS 2025 — https://arxiv.org/abs/2503.23576 — synthetic CS data quality is task dependent.

## 3.4 Prosody at Hinglish switches (acoustic ground truth)

- **Rao, Pandya, Sabu, Kumar, Bondale (IIT-B), *Lexical and Prosodic Cues to Segmentation in Hindi-English CS Discourse*** — https://www.isca-archive.org/interspeech_2018/rao18_interspeech.html — Interspeech 2018. Embedded English is articulated more carefully, slower, with more vocal effort and higher pitch variation than surrounding Hindi. **This is the only acoustic description of natural Hinglish switches and nobody has used it as a TTS target or evaluation reference.**
- Torres Cacoullos 2020 (Frontiers) — bilinguals deliberately place switches in separate intonation units ("prosodic distancing"). Implication: some discontinuity at switches is *natural*.
- Pandey, Gogoi, Tang, *Forced alignment of code-mixed Hindi-English* — https://arxiv.org/abs/2607.25581 — MFA with code-mixed acoustic models reaches 4.15 ms boundary error vs ~38 ms monolingual. Tooling for precise switch-boundary measurement.
- No phrase-break / pause-prediction model trained on Hinglish text exists (all phrase-break work is monolingual).

## 3.5 The F5-TTS duration heuristic (engineering, not science)

Paper says "characters"; code uses UTF-8 **bytes** (`len(text.encode("utf-8"))` in `utils_infer.py`). Devanagari = 3 bytes/char, ASCII = 1, so mixed-script targets against a Devanagari reference under-allocate ~3× (truncation, 21/30 silent outputs in harrrshall's unpatched test). Fixes: character-count patch (harrrshall), transliterate everything (IndicXlit), explicit `fix_duration`, speaking-rate predictors (Cross-Lingual F5-TTS, https://arxiv.org/abs/2509.14579), DurFormer (https://arxiv.org/abs/2507.22612). No peer-reviewed analysis of the byte issue for Brahmic scripts exists; the harrrshall patch is whole-sentence, so **per-segment misallocation inside a mixed sentence is unaddressed** — a small, publishable side analysis.

## 3.6 Where we stand

| Claim in v0 plan | Status after survey |
|---|---|
| "Nobody has fine-tuned Hinglish TTS on real spontaneous CS speech" | **Partly false.** SEAME→CosyVoice2 (zh-en, 2025–26) is the same recipe; Orato fine-tuned IndicF5 on 194 h Hinglish call audio (no paper). Still true: no *academic, reproducible* fine-tune on an *open* spontaneous Hinglish corpus |
| "Nobody measures naturalness at the switch point" | **True for the acoustic-discontinuity formulation.** But LCG (2026) evaluates the embedded phrase locally, MagpieTTS-LF (2026) has an F0/energy boundary metric, Yeo (2026) has a frame-level acoustic CS index, SwitchLingua rates "switching naturalness" at utterance level. Reviewers will call SDS "join cost at switch points" unless within-utterance normalization + human validation + calibration to real switches are the headline |
| harrrshall/hinglish-tts is the strongest open baseline | **Not strictly.** Orato's fine-tune and the AI4Bharat 120k-rating benchmark (Gemini, Bulbul ahead of IndicF5) mean baseline selection must be defended |
| Dhoundiyal 2023 has a phrase-break multi-task model | **Unverified.** Body inaccessible; abstract is an application paper |
| HiACC is the best fine-tuning data | **True but small:** 3.22 h adult, phone-mic 16 kHz, license CC BY (Zenodo) vs CC BY-NC (paper) |

**Position to take:** the metric and its human-validated switch-window rating set are the primary contribution; the HiACC fine-tune is the case study that exercises it; the duration-allocation analysis is a secondary engineering finding. See 02_novelty_assessment.md and 08_research_plan_and_risks.md.
