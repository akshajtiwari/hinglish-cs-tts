# 14 — State of the art and available human-labelled data (surveyed 2026-09-30)

Evidence behind the reframed plan. Numbers were checked against the cited papers; items marked ⚠ could not be verified on a primary source.

## 14.1 How far the field has moved past UTMOS

| Model | Type | Reported result | Source |
|---|---|---|---|
| UTMOS (2022) | SSL strong learners + weak learners, stacked | BVCC utt SRCC 0.897, sys 0.936 | arXiv 2204.02152 |
| UTMOSv2 (2024) | wav2vec2 + spectrogram CNN fusion, multi-stage, multi-dataset | VMC'24 T1 sys SRCC 0.919 vs UTMOS 0.615 (25% zoom) | 2409.09305 |
| APG-MOS | Auditory branch + HuBERT-RVQ + w2v2, ranking + regression | BVCC sys SRCC 0.936 vs UTMOS 0.925 | 2504.20447 |
| DistilMOS | Layer-wise self-distillation | BVCC 0.889 / 0.936; zero-shot SOMOS utt 0.387 vs SSL-MOS 0.188 | 2601.13700 |
| SpeechJudge-BTRM / GRM | Qwen2.5-Omni-7B; Bradley–Terry / generative | SpeechJudge-Eval pairwise: UTMOS 53.7%, DNSMOS 57.9%, Gemini-2.5-Flash 69.1%, **BTRM 72.7%, GRM 77.2%** | 2511.07931 |
| MOS-RMBench models | Scalar / generative reward models | Scalar BT 80.0%; UTMOS 68.2%; pairs with ΔMOS ≤ 0.5 have >40% error | 2510.00743 |
| PrefSQA | Dual SSL, uncertainty-aware BT | SOMOS-NM pairwise 74.7% | 2606.19597 |
| Auto-ATT | Qwen2-Audio LoRA, Chinese human-likeness | Trap-item F1 0.92 vs UTMOSv2 0.14 | 2505.11200 |
| Conversational Naturalness Predictor | Whisper-large-v3 encoder | ConvTTS PCC 0.48 vs **UTMOSv2 −0.19** | 2603.01467 |

**VoiceMOS Challenge winners:**
- 2023: T05 on French Blizzard, 0.91, trained only on non-BVCC multilingual data; UTMOS scored below 0.35.
- 2024: kNN retrieval (T06) and UTMOSv2 (T05).
- 2026: large ensembles with listener modelling; emotional TTS QMOS SRCC 0.785.

## 14.2 Where every current predictor fails

"Limits of reference-free metrics" (2609.13150), pairwise accuracy:

| Corpus | UTMOS | UTMOSv2 | SCOREQ | Longest-clip heuristic | Human ceiling |
|---|---|---|---|---|---|
| BVCC (old systems) | 0.892 | 0.899 | 0.909 | 0.517 | 0.887 |
| TTS-HP (clean commercial TTS) | **0.510** | **0.528** | **0.502** | 0.524 | 0.764 |

- Other failures: UTMOSv2 at 0.118 system correlation on modern zero-shot TTS (2603.24430); UTMOS below 0.35 on French (VMC'23); off-the-shelf SSL-MOS at 0.285 utterance SRCC on Indic LIMMITS (IndicMOS).
- Reward hacking: optimizing a TTS against a single predictor collapsed held-out UTMOS from 4.51 to 1.23. A composite reward held.

**The open gap:** modern, clean, non-English, and code-switched speech.

## 14.3 What drives gains (from ablations)

| Lever | Effect |
|---|---|
| Training-data diversity / multi-dataset | **Largest** (UTMOSv2; MOS-Bench; VMC'23 0.91 vs <0.35) |
| Multi-stage training | Large (UTMOSv2 sys SRCC 0.919 → 0.710 without it) |
| Pairwise / Bradley–Terry objective | Large on clean TTS (MOS-RMBench 80% vs regression 76%) |
| Fine-tuned audio-LLM judge | Moderate (+4.5 over BTRM); expensive |
| Listener / domain conditioning | Moderate (UTMOS OOD 0.871 → 0.825 without) |
| SSL + spectrogram fusion | Moderate (spectrogram best absolute, SSL best ranking) |
| Retrieval / kNN | Moderate (VMC'24 winner) |
| Ensembling / stacking | Small |
| Backbone choice | Small in-domain; matters out of domain |
| Phoneme / text conditioning | Small or negative |

## 14.4 Human-labelled datasets

| Dataset | Languages | Size | Label | TTS era | License | Code-switched |
|---|---|---|---|---|---|---|
| BVCC (VMC'22) | en | ~7k clips ⚠, 187 systems | MOS | ≤2020 | Blizzard parts non-commercial | No |
| SOMOS | en | 20k clips, 375k ratings | MOS | 2020 | CC-BY-NC-SA | No |
| Blizzard 2008–2025 | en, zh, fr, **Indic 2014/15**, … | varies | MOS, MUSHRA | old → 2025 zero-shot | Non-commercial, request from CSTR | No |
| **SpeechJudge-Data** | zh, en, **zh–en mixed** | 99K pairs, 211 GB | Preference with strength | Modern zero-shot | CC-BY-NC, auto-gated | **Yes** |
| **SpeechArenaBench** | 10 Indic | 120K+ comparisons, 651 GB | Pairwise + 6 axes | Modern commercial | MIT (HF) vs CC-BY (paper) ⚠ | **Yes (78%)** |
| **MANGO** | hi, ta, en | 255k ratings | MUSHRA | 2022–23 | CC-BY | No |
| CodecMOS-Accent | en, 10 accents | 4,000 clips | Naturalness, similarity, accent | Modern zero-shot | Release ⚠ | No |
| VMC'26 emotional | en | ~18k | QMOS, EMOS | Recent | ⚠ | No |
| LIMMITS 23/24 | Indic | 2.4k / 4.4k clips, ~1 rating each | MOS | 2023–24 | Not public ⚠ | No |
| SingMOS-Pro | zh, ja singing | 8k | MOS | mixed | CC-BY | No |
| QualiSpeech | en | 15k | 7 dimensions + text | mixed | CC-BY-NC-SA ⚠ | No |
| SQuId | 65 locales | >1M ratings | MOS | — | Proprietary | — |

**Gaps:**
- No public absolute-MOS dataset with code-switched speech.
- Hindi–English code-switched human labels exist only as SpeechArenaBench pairs.
- SpeechArenaBench audio comes from commercial APIs; their terms of service may limit training use. Check before release.

## 14.5 What "beating UTMOS" must mean in 2026

1. Report the classic suite: BVCC utt/sys, SOMOS, VMC'23, VMC'24 T1, BC2019.
2. Report pairwise accuracy on SpeechJudge-Eval (targets 72.7% / 77.2%) and MOS-RMBench (>80%), next to the human ceiling.
3. Beat the longest-clip heuristic on clean commercial TTS.
4. Ablate the data mixture first; it is the biggest lever.
5. Use a Bradley–Terry objective; report pairs with small differences separately.
6. Fuse SSL and spectrogram branches; ablate each.
7. Use listener and domain conditioning.
8. Evaluate on non-English data and held-out languages.
9. Include out-of-domain probes (conversational, emotional, long-form).
10. Test robustness as a reward.
11. Release code and checkpoints; use public splits (MOS-Bench / SHEET).

## 14.6 Sources

UTMOS 2204.02152 · UTMOSv2 2409.09305 · APG-MOS 2504.20447 · DistilMOS 2601.13700 · Distill-MOS 2502.05356 · SAMOS 2411.11232 · SpeechJudge 2511.07931 · MOS-RMBench 2510.00743 · PrefSQA 2606.19597 · AudioJudge 2507.12705 · Auto-ATT 2505.11200 · Conversational predictor 2603.01467 · Limits of reference-free metrics 2609.13150 · I2D 2603.24430 · VMC'23 2310.02640 · VMC'24 2409.07001 · VMC'26 2609.13792 · MOS-Bench 2411.03715 · IndicMOS (Interspeech 2024) · SQuId 2210.06324 · CodecMOS-Accent 2603.14328 · MANGO https://huggingface.co/datasets/ai4bharat/MANGO · SpeechArenaBench https://huggingface.co/datasets/ai4bharat/SpeechArenaBench · SpeechJudge-Data https://huggingface.co/datasets/RMSnow/SpeechJudge-Data · SOMOS https://zenodo.org/records/7378801 · VMC'22 data https://zenodo.org/records/10691660 · Blizzard https://www.cstr.ed.ac.uk/projects/blizzard/data.html
