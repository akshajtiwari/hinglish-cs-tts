# 13 — Study plan for SwitchMOS

What to learn, in order. Detailed resources and verified video links for most topics are in `../docs/09_study_guide.md`; below adds what's specific to SwitchMOS.

| # | Topic | Why | Depth | Start with |
|---|---|---|---|---|
| 1 | Speech signals (spectrograms, pitch, energy) | Switch features | Do | Velardo's audio-for-ML playlist; speech.zone Speech Processing |
| 2 | Code-switching phonetics | Why switches are "marked" | Know | Rao et al. 2018 (Hinglish); Fricke et al. 2016; Olson 2016 |
| 3 | Forced alignment (CTC, MMS, uroman) | Finding switches | Do | torchaudio multilingual alignment tutorial; Chodroff's MFA workshop |
| 4 | Self-supervised speech encoders | Backbone | Know | wav2vec 2.0 and HuBERT papers; mHuBERT-147 model card |
| 5 | **MOS prediction** | The field we're extending | **Own** | UTMOS (2204.02152) and UTMOSv2 (2409.09305), especially their ablations |
| 6 | **Preference learning** | Training signal | **Own** | Bradley–Terry basics; MOS-RMBench (2510.00743); SpeechJudge (2511.07931) |
| 7 | Localized quality | Switch expert design | Know | DAMOS (2608.21176); Kuhlmann frame-level MOS (2508.10374) |
| 8 | **Speech editing TTS** | Minimal pairs | Do | F5-TTS `speech_edit.py`; Voicebox paper; VoiceCraft |
| 9 | Mixture of experts / gating | Combining experts | Know | MoE MOS (2507.06116); any MoE intro |
| 10 | Label-free quality | SwitchLM | Know | SpeechLMScore (2212.04559); TTScore (2509.20485); TTSDS2 (2506.19441) |
| 11 | Active learning | Human study | Know | Miniconi et al., Interspeech 2025 |
| 12 | Evaluation statistics | Proving it works | Own | Bootstrap CIs, Spearman/Kendall, Krippendorff's α, paired tests (StatQuest videos) |
| 13 | PyTorch + DDP + mixed precision | Training on 4×A16 | Do | PyTorch DDP tutorial; HF Accelerate docs |

**Suggested order:** 1 → 3 → 5 → 6 → 4 → 8 → 7 → 9 → 12 → 2 → 10 → 11 → 13 (as needed).

**Checkpoint per topic:** run one small thing. Align a HiACC clip; score a clip with UTMOS; fit Bradley–Terry on 100 SpeechArenaBench pairs; edit one word with F5 and listen.
