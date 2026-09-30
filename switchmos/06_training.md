# 06 — Training

## 6.1 Training data mix (research-only model)

| Dataset | Label | Why |
|---|---|---|
| SOMOS | Absolute MOS (375k ratings) | Scale and calibration; UTMOSv2 found it among the most useful |
| BVCC + sarulab zoomed | Absolute MOS | Classic benchmark domain; zoomed set covers high-quality systems |
| **SpeechJudge-Data** | 99K modern pairs with strength; **zh–en mixed slice** | Modern zero-shot TTS; code-switched |
| **MANGO** | Hindi / Tamil MUSHRA | Indic absolute scores (normalize per MUSHRA page) |
| ~~SpeechArenaBench~~ | — | **Not used for training** (vendor terms; `03_datasets.md` §3.6b). Tier A+B pairs are the held-out test set. Tier B training only as an optional, legally cleared ablation |
| **Blizzard 2014/2015 Indic** | Absolute MOS, six Indic languages | Indic absolute ratings from open research systems (old; non-commercial research, request via CSTR) |
| CodecMOS-Accent (if released) | Naturalness, modern zero-shot, accents | Modern English variety |
| VMC'26 emotional (optional) | QMOS | Expressive range |
| Blizzard (optional) | MOS incl. Indic 2014/15 | Extra languages; older systems |

Local-event supervision (no human labels): natural code-switched speech (HiACC reference speakers, MUCS Hi–En / Bn–En) and minimal pairs (§6.3).

## 6.2 Stages (multi-stage training was UTMOSv2's biggest factor)

| Stage | Trains | Data | Loss |
|---|---|---|---|
| 0 | — | Cache SSL features, spectrograms, alignments, switch features | — |
| 1 | Semantic and acoustic branches separately | Absolute MOS sets + pairwise sets | Clipped MSE + Bradley–Terry (Davidson ties) |
| 2 | Local-event branch | Minimal pairs, controls; SwitchLM on natural code-switched speech | Ranking (natural > edited), no-preference on non-switch edits, control classes |
| 3 | Fusion, conditioning, heads (branches frozen) | Full mix | All heads |
| 4 | Everything, low learning rate | Full mix | All heads, weighted |

## 6.3 Minimal pairs for the local-event branch

1. Take a natural code-switched clip.
2. Regenerate only a switch window (IndicF5 / F5 infilling) or apply a DSP change (wrong duration, pitch reset, splice).
3. Pass both original and edited through the same vocoder, so the model learns "unnatural", not "was vocoded".
4. Negative control: edit a non-switch word; the model must not prefer either version.
5. Check on ~20–200 pairs that edits really sound worse.

## 6.4 Splits

Hold out whole TTS systems, whole languages, raters, and sentences. HiACC by speaker role (`../model/configs/hiacc_speaker_split.json`). Use public MOS-Bench / SHEET splits for classic sets.

## 6.5 Data-mix ablations first

Data diversity is the biggest lever in the literature, so the first experiments vary the mix: English-only → + SpeechJudge → + MANGO → + SpeechArenaBench → + local-event branch.

## 6.6 Compute on 4×A16

- Cache encoder features once (SpeechArenaBench 651 GB and SpeechJudge 211 GB of audio fit the 4.6 TB disk).
- Train on cached features with DDP and mixed precision; fine-tune only top encoder layers.
- Minimal-pair generation is the other large cost (days at reduced sampling steps; to be benchmarked).
