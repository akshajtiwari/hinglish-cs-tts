# 14 — SwitchMOS architecture options (survey-backed, 2026-09-29)

Supersedes the single-model sketch in 13 §13.5, which is now "v0". The goal is not to copy UTMOS but to take its lessons forward: learn what natural switches are from real bilingual speech and synthetic minimal pairs, and use human labels mainly to calibrate and test.

## 14.1 What actually made UTMOS / UTMOSv2 work (from their ablations)

| Component | Effect | Take it? |
|---|---|---|
| Frame-level scores averaged to a clip score | Beat pooled training | Yes, but see 14.3: frame scores from a full-context encoder are not truly local |
| Contrastive / ranking loss | Works even without MSE | Yes, as Bradley–Terry on preference pairs |
| Listener / domain embedding | **Largest single effect in UTMOS** (OOD SRCC 0.871 → 0.825 without) | Yes: rater, system-set, and language-pair embeddings |
| Multi-stage training (train branches → freeze → fuse → fine-tune) | **Largest effect in UTMOSv2** (0.613 → 0.482 without stages 1–2) | Yes |
| Diverse modern-TTS training data | Crucial in both | Yes: SpeechArenaBench's commercial systems |
| Spectrogram CNN branch (UTMOSv2) | Better absolute MOS; SSL better at ranking | Optional artefact expert |
| Multi-level stacking (UTMOS, 4 stages, 48+ weak learners) | Mostly lowers MSE; SRCC +0.006 | **No** |
| Phoneme encoder | Hurt on large data, helped only on low-data OOD | No |

Existing predictors fail on modern and code-switched speech: UTMOS reaches **53.7%** pairwise agreement on SpeechJudge-Eval (near chance) and 60.8% on VMC'23 pairs; LCG (2026) reports UTMOS penalizing code-switched transitions that humans rate fine.

## 14.2 Evidence that changes the plan

1. **A label-free prosody likelihood alone is weak.** TTScore-pro (2509.20485), the closest published "prosody likelihood" metric, gets utterance SRCC **0.04–0.05** on SOMOS and 0.33 on BVCC. So a switch-prosody model trained only on natural speech should be a *feature*, not the headline metric.
2. **Generic localization adds little.** DAMOS (2608.21176) fuses a generic distortion localizer into a MOS model and gains only 0.878 → 0.885 SRCC; its biggest effect is learned SSL layer weighting. Localization pays off only if it captures what global models miss, here switch-boundary prosody and accent transitions.
3. **Frame scores are not local by default.** Kuhlmann 2025: in a full-context SSL encoder a local defect shifts every frame's score. Chunked encoding fixes locality but hurts out-of-domain accuracy. So per-switch scores need switch-anchored windows or local supervision.
4. **No quality predictor has been trained on edited minimal pairs.** Speech-editing TTS (F5 `speech_edit.py`, VoiceCraft) regenerates only a span, conditioned on context. But the whole clip is re-vocoded, so the fair comparison is *vocoded original vs vocoded edited*.
5. **Bradley–Terry beats MSE** for scalar preference models (MOS-RMBench: 80.0% vs 75.8%). **Every prior work drops ties;** a tie-aware BT (Davidson) uses SpeechArenaBench's 677 Hindi ties.
6. **Active learning for MOS** helps from the second round on; uncertainty sampling beats diversity sampling (Miniconi et al., Interspeech 2025).

## 14.3 Three options

All share: a frozen or lightly fine-tuned multilingual SSL encoder (mHuBERT-147 or XLS-R) with learned layer weights; MMS + uroman word alignment; switch detection by script (word-level LID where English appears in native script); evaluation on SpeechArenaBench code-mixed pairs with held-out systems and held-out languages.

### A. SwitchLM — label-free switch-prosody likelihood
- **What:** a small Transformer over word-level prosody tokens (F0 statistics, duration, energy, pause, pooled SSL accent features), conditioned on words, language tags, and left context. Per-switch score = surprisal of the words around the switch.
- **Trained on:** natural code-switched speech only (MUCS Hi–En ~95 h, MUCS Bn–En ~53 h, CS-YODAS Hindi 21 h (NC), HiACC 5 h, mined IndicVoices/Vaani).
- **Labels:** a few hundred pairs, for calibration only.
- **Compute:** 20–50M parameters, features precomputed; easy on one A16.
- **New:** label-free, per-switch by construction, language-independent.
- **Risk:** likely weak alone (TTScore-pro evidence); lecture/YouTube speech differs from studio TTS.

### B. SwitchMoE — gated ensemble with switch-anchored experts
- **Experts:** (1) global SSL expert with frame head and late pooling; (2) **local switch expert** on ±0.5–1 s windows around each switch, fed SSL window features + SwitchLM surprisal + boundary features (pitch reset, rate jump, pause, spectral and speaker-embedding jump); (3) optional spectrogram CNN artefact expert.
- **Gate:** conditioned on switch density, language pair, and domain. Clip score = gated mix of experts plus a soft-min over switch scores (a single bad switch can dominate perception).
- **Training:** UTMOSv2-style stages: experts → freeze → gate → joint fine-tune. Bradley–Terry with Davidson ties; the six SpeechArenaBench axes as auxiliary targets; gate diversity regularizer.
- **Labels:** all 4,035 Hindi code-mixed pairs (plus other languages), plus ~500–1,000 actively selected per-switch AB labels.
- **Compute:** fits 4×A16 with DDP, SSL features precomputed.
- **New:** switch-anchored experts and switch-conditioned gating; 30–300M parameters vs SpeechJudge's 7B.
- **Risk:** only 7 commercial systems, so the gate may learn system identity (mitigate with system-held-out CV); gains may be small like DAMOS unless the local expert gets real switch supervision.

### C. SwitchEdit — contrastive training on edited minimal pairs
- **What:** take natural code-switched clips; regenerate only a switch window with speech-editing TTS (IndicF5/F5 infilling) or DSP perturbations (wrong duration, pitch reset, accent-mismatched re-render); pass both original and edited through the **same vocoder**. Train a Siamese scorer: natural > edited-at-switch.
- **Controls against shortcut learning:** edit a *non-switch* word and train "no preference" against the resynthesized original, so the model can't just detect "was edited"; include resynthesis-only originals.
- **Labels:** synthetic pairs are free; a ~200-pair human AB check that edited-at-switch really sounds worse; SpeechArenaBench for calibration and testing.
- **Compute:** generation is the bottleneck (~50k edits ≈ days across 4 A16s at reduced sampling steps; not yet benchmarked); training is light.
- **New:** no prior quality predictor trained on edited minimal pairs; directly supervises locality and switch specificity; any language pair with an editing TTS.
- **Risk:** the model may learn regeneration artefacts rather than naturalness; regenerated spans may not actually sound worse; IndicF5 editing and Latin-token behaviour unverified.

## 14.4 Recommendation

**Build B as the model, with C as its main source of local supervision and A as one of its input features.**

Why this combination:
- C fixes B's weakest point: per-switch scores would otherwise have no supervision at all.
- A is cheap and gives a label-free, interpretable switch signal, but the evidence says it can't carry the metric alone.
- Human labels are used where they add the most: calibrating the clip score (SpeechArenaBench), and a small, actively selected per-switch test.

What the paper would claim, differentiated from SpeechJudge / UTMOS / DAMOS:
1. **Locality:** explicit per-switch scores, validated on edited pairs with known locations and on human switch judgments.
2. **Label efficiency:** most supervision from natural speech and synthetic minimal pairs; a curve of accuracy vs number of human pairs.
3. **Language independence:** leave-one-language-out across Indic–English pairs, plus zero-shot on another pair.
4. **Tie-aware preference training.**
5. **Size:** 25–100× smaller than SpeechJudge's 7B judge.

Not claimed: first code-switched predictor (SpeechJudge covers Mandarin–English).

## 14.5 Baselines to report

UTMOS, UTMOSv2, SpeechJudge-GRM (7B, 4-bit on one A16, untested), TTSDS2 (system level), duration-only, the same model without the switch expert, SDS alone.

## 14.6 Data for the label-free parts

| Corpus | Pair | Hours | License |
|---|---|---|---|
| MUCS 2021 (OpenSLR 104) | Hi–En, **Bn–En** | ~95, ~53 | CC BY-SA 4.0 |
| HiACC | Hi–En | 5.2 | CC BY 4.0 (Zenodo) / BY-NC (paper) |
| CS-YODAS | Hindi 21 h context (6.3 h CS) + 6 others | 313 total | CC BY-NC 4.0 |
| ASCEND | Cantonese/Mandarin–En | 10.6 | CC BY-SA 4.0 |
| Bangor Miami | Es–En | ~35 | GPL-3.0 (TalkBank) |
| IndicVoices / Vaani | many Indic | large; CS not labelled | CC BY 4.0, gated |

MUCS writes some English in Devanagari, so it needs a word-level language tagger. IndicLID is sentence-level and unsuitable; use mBERT/MuRIL fine-tuned on FIRE 2013 + COMI-LINGUA (~95–96 F1). Note: COMI-LINGUA's often-quoted 94.90 for aya is its NER score; its LID F1 is 87.15 (best: LLaMA-3.1-8B, 94.75).

## 14.7 Open questions (added to 09 as D21–D22)

- Does IndicF5's CFM support `speech_edit.py`-style infilling, and how does it handle Latin tokens?
- How many switch events are in MUCS Hi–En and Bn–En?
- Can SpeechJudge-GRM run in 4-bit on one 16 GB A16?

## 14.8 Key sources

UTMOS 2204.02152 · UTMOSv2 2409.09305 · SpeechJudge 2511.07931 · DAMOS 2608.21176 · Kuhlmann 2508.10374 · Vioni 2211.00342 · TTScore 2509.20485 · SpeechLMScore 2212.04559 · TTSDS2 2506.19441 · MOS-RMBench 2510.00743 · PrefSQA 2606.19597 · MoE MOS 2507.06116 · BAM 2407.21611 · CS-YODAS 2606.11514 · COMI-LINGUA 2503.21670 · GLUECoS 2004.12376 · MUCS 2104.00235 · Miniconi et al., Interspeech 2025 (active learning for MOS).
