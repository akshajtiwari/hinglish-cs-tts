# 06 — Base Models and Fine-Tuning Feasibility

Verified 2026-09-23 from model cards, HF API, GitHub, arXiv. ⚠ = could not verify.

## 6.1 IndicF5 (primary base)

Sources: https://huggingface.co/ai4bharat/IndicF5 · https://github.com/ai4bharat/IndicF5 · paper "Phir Hera Fairy" https://arxiv.org/abs/2505.20693 · upstream https://github.com/SWivid/F5-TTS

| Item | Value |
|---|---|
| Architecture | F5-TTS: flow matching, DiT backbone, ConvNeXt text encoder, Vocos 24 kHz mel vocoder. Config F5TTS_Base: dim 1024, depth 22, 16 heads, 100-mel / hop 256 / 24 kHz. ~336 M params (card says "0.4B"; safetensors 1.4 GB fp32) |
| Init | English F5-TTS checkpoint (~100 K h, Emilia, **CC BY-NC**) then adapted on Indic data only ("EN→IN" recipe) |
| Training data | 1,417 h "IN11": Rasa + IndicTTS + LIMMITS + IndicVoices-R + Google crowdsourced TTS; 11 languages; Hindi hours not broken out |
| Compute (base) | 32×H100, up to 150 K steps, AdamW lr 5e-5, 30,000 frames/GPU |
| Tokenizer | Character-level custom `vocab.txt`, 685 chars covering IN11 scripts. **Latin coverage ⚠ unverified** (gated, HTTP 401). Indirect evidence (Orato card: "Latin English is the weaker path"; harrrshall needs IndicXlit to reach 4.7/5) says Latin is at best under-trained |
| License | HF metadata `mit`; paper says CC BY 4.0; unanswered license discussion (#3). Conservative reading: non-commercial-tainted via the Emilia-trained init. Academic use fine either way |
| Gated | Yes, auto-approval on accepting terms |
| Fine-tuning code | Full F5-TTS training stack ships in repo: `f5_tts/train/train.py`, `finetune_cli.py`, `finetune_gradio.py`, `datasets/prepare_csv_wavs.py`. README documents inference only; discussion #42 asks for a fine-tune example. Use upstream SWivid recipe: CSV `audio_file|text`, `tokenizer=custom`, `tokenizer_path=vocab.txt`, init from IndicF5 `model.safetensors` |
| Inference | Python 3.10, `AutoModel.from_pretrained(..., trust_remote_code=True)`, reference audio + transcript → 24 kHz. Community quality complaints (#41, #35); transformers-5 fix (#33) |
| Own code-mix eval | 30 curated IndicVoices sentences, MUSHRA-intelligibility 76.7 |

**Public IndicF5 fine-tunes to learn from**
- **Orato** https://huggingface.co/tryorato/orato-tts-hindi-v1 — 194 h Hindi/Hinglish call-domain, 3 epochs, lr 1e-5, 19,200 frames/GPU, 1×H100, 10,659 updates, **fp32 because bf16 NaN'd**. CER 19.2→18.3, SpkSim 0.863→0.899.
- **SPRINGLab F5-Hindi-24KHz** https://huggingface.co/SPRINGLab/F5-Hindi-24KHz — Small config 151 M, IndicTTS+IndicVoices-R Hindi, 8×A100-40GB ~1 week, CC BY 4.0.
- Saravananravi/indicf5-hinglish — OpenSLR-104 read Hindi, no metrics (name collision: avoid calling ours "IndicF5-Hinglish").

**Community fine-tuning data points (upstream F5-TTS)**
- 40 h Greek + 20 h English → good results in ~half a day on one RTX 4090; lr 1e-5–7.5e-5; ~1,618 frames/GPU on 24 GB (discussion #57).
- 10–60 min per speaker on a 12 GB laptop GPU "improved output quality significantly" (discussion #769).
- LoRA (PEFT) rank 16 ≈ 0.9 % trainable params, 6 MB adapters, runs on 3090 Ti: https://github.com/instavar/f5-tts-lora-finetuning
- `use_ema=True` can hurt early fine-tunes (train README).

## 6.2 The duration-allocation bug (must be handled before any experiment)

`src/f5_tts/infer/utils_infer.py`:
```
ref_text_len = len(ref_text.encode("utf-8"))
gen_text_len = len(gen_text.encode("utf-8"))
duration = ref_audio_len + int(ref_audio_len / ref_text_len * gen_text_len / local_speed)
```
Output length ∝ UTF-8 **bytes**. Devanagari = 3 bytes/char, ASCII = 1. A Devanagari reference with a Roman/mixed target under-allocates ~3× (truncation; harrrshall: 21/30 unpatched outputs silent). Chunking (`max_chars`) and the `<10 bytes → speed 0.3` fallback inherit the bug.

Fix ladder:
1. Count non-whitespace characters (harrrshall patch) — global only.
2. Transliterate all English to Devanagari (IndicXlit, Apache-2.0; needs Python ≤3.11 for fairseq).
3. Pass `fix_duration` from a per-token duration model fitted on HiACC word alignments (adult sec/word ≈ 0.39).
4. Train with an explicit duration predictor (EraX viF5TTS fork `--use_duration_predictor`, F5-TTS issue #993).
5. Speaking-rate predictor from the prompt audio (Cross-Lingual F5-TTS, https://arxiv.org/abs/2509.14579).

**Paper side-result:** per-segment (not whole-sentence) misallocation inside a mixed sentence is unstudied. Measure it: switched-word duration ratio vs natural, as a function of script policy. It feeds directly into the SDS duration term.

## 6.3 Script policy for English tokens (experimental variable)

| Policy | Pros | Cons |
|---|---|---|
| A. Devanagari via IndicXlit + override table | Matches IndicF5 training; 4.7/5 intelligibility shown | Loses English-specific phonology; loanword table does not generalize (n=30 vocab) |
| B. Keep Latin | Preserves identity of English words | Vocab coverage ⚠; Orato says "weaker path" |
| C. Extend vocab with Latin + fine-tune | Principled | New embeddings randomly initialised; needs more data |

Run A and B on HiACC; C only if B is clearly broken. HiACC transcripts are already A/B-ready (Devanagari Hindi + Latin English with token LID).

## 6.4 Compute budget

| Setting | Estimate |
|---|---|
| Data | HiACC adult 3.22 h ≈ 11.6 K s; + ~3 h clean Hindi mix |
| Full fine-tune | ~57 updates/epoch at 19,200 frames/GPU; 100–300 epochs ≈ 6–17 K updates ≈ **4–15 h on one A100/H100**, or 1–2 days on a 24 GB 3090/4090 at ~2 K frames/GPU |
| LoRA r=16 | fits 12–16 GB; hours, not days |
| Sweeps + ablations (LR, LoRA vs full, script policy, mix ratio, adult+child) | **50–100 GPU-hours total** |
| Inference for eval | negligible |
| Precision | fp32 (Orato: bf16 NaN'd) |

No multi-node needed. A single rented A100 for ~2 weeks of intermittent use covers everything.

## 6.5 Recipe (v1)

1. Prepare HiACC adult: manual transcript re-check; MMS_FA alignment; drop bottom-10 % alignment-score segments; resample 16→24 kHz; write `audio_file|text` CSV under both script policies.
2. Mix 1:1 with Rasa Hindi or IndicVoices-R Hindi (CC BY, gated) to protect acoustic quality.
3. Init from IndicF5; lr 1e-5; fp32; `use_ema=False` initially; LoRA r=16 first, full fine-tune second.
4. Track: validation loss, CER (Whisper-large-v3 + IndicConformer), SpkSim (ECAPA), **monolingual Hindi/English retention** on IndicTTS/IndicVoices test sets, SDS on HiACC test switches.
5. Checkpoint selection by SDS-prosody on validation, not by loss.

## 6.6 Alternative bases

| Model | Hindi | Open weights | License | Fine-tune code | Params | Verdict |
|---|---|---|---|---|---|---|
| **IndicF5** | yes | gated-auto | MIT (card) / CC BY (paper), NC-tainted init | yes (F5-TTS stack) | 336 M | **Primary**: only Indic-pretrained, small, full training stack, reference-conditioned |
| Indic Parler-TTS | yes (107 h Hindi) | gated-auto | Apache-2.0 | yes | 0.9 B | Clean-license fallback; 3.40 on harrrshall set; description-prompted |
| Orpheus-TTS 3B Hindi (Canopy) | yes | gated-auto | Apache-2.0 | yes (`finetune/`) | 3 B | Clean-license fallback; heavier |
| Veena (Maya Research) | Hi/En, code-mixed claimed | yes | Apache-2.0 | LoRA example | 3 B | 4 fixed voices, no cloning, proprietary data |
| Rumik-OSS-1 (2026) | 22 Indic + En, code-switch demoed | yes | CC BY-NC + AUP | not yet | 3 B | Research-only; watch |
| Kokoro-82M | 4 Hindi voices, grade C | yes | Apache-2.0 | no | 82 M | Baseline only (3.90 on harrrshall set) |
| XTTS-v2 | yes | yes | Coqui non-commercial | yes (archived) | ~460 M | Engine behind CS-FLEURS; accented |
| Chatterbox Multilingual | yes | yes | MIT | **no** | ~0.5 B | Zero-shot baseline only |
| VibeVoice Hindi community | via finetunes | yes | MIT | fork | 1.5 B / 7 B | Unvetted |
| CosyVoice 2/3, Fish S1, Spark, IndexTTS-2, Kyutai, Dia | **no Hindi** | — | — | — | — | Not usable |
| Sarvam Bulbul v3, Gemini 2.5 Pro TTS | yes | **API only** | commercial | — | — | Closed baselines for human eval |

## 6.7 Risks specific to fine-tuning

- **Quality regression:** SEAME→CosyVoice2 lowered UTMOS at 10 h. Expect the same; report it honestly with the monolingual retention numbers. Mitigate: clean-Hindi mixing, LoRA, low LR, early stopping on SDS.
- **16 kHz → 24 kHz mismatch:** upsampled data has no energy above 8 kHz; model may learn a band-limited "spontaneous" style. Check spectral rolloff of outputs; consider bandwidth extension (e.g., AudioSR) on training data as an ablation.
- **Transcript noise:** Whisper-seeded transcripts; prune by alignment score, manual pass.
- **License:** resolve HiACC CC BY vs CC BY-NC by email; IndicF5's NC-tainted lineage blocks nothing academic but blocks a commercial demo.
- **Name collision:** do not call the model "IndicF5-Hinglish".
