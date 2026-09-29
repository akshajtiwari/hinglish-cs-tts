# 01 — Problem and idea

## The problem

- Hinglish is everyday speech for roughly 250 million people. Voice assistants, call centres, and dubbing all need TTS that speaks it naturally.
- Modern TTS gets the words right. What still sounds robotic is often the **moment of switching**: a flat or abrupt change, rushed English words, a pitch jump no person would make, a faint "glued together" seam.
- We can't measure that automatically:
  - Human listening tests (MOS) are slow and costly.
  - Automatic MOS predictors score the whole clip, trained mostly on English. UTMOS agrees with humans only 53.7% of the time on modern TTS pairs, and reportedly penalizes code-switched transitions that humans find fine.
  - Industry (Sarvam, Gnani, Gradium) markets "smooth switching" with no way to measure it.

## The key insight

Real bilinguals **don't** switch smoothly. They slow down before the switch, and say the switched word longer and with more pitch movement. Listeners use these cues. So the target isn't "no discontinuity"; it's "the discontinuity a real bilingual would produce".

## What we build

**SwitchMOS**, a naturalness predictor that:
1. Outputs **one whole-clip score** (like any MOS predictor) **plus a score per language switch**, with a plain-language reason ("no slowdown before 'office'; seam likely").
2. Works for **any code-switched language pair** in principle, and is tested on pairs it never trained on.
3. Learns mostly from **real bilingual speech** and **automatically built minimal pairs** (the same clip with only the switch regenerated), using human ratings mainly to calibrate and test.

## Scope, honestly

- **v1 is Hinglish-first.** Natural reference speech, human study, and most minimal pairs are Hindi–English.
- **Designed to generalize to Indic–English pairs**, tested by leave-one-language-out on SpeechArenaBench. "Any two languages" is not claimed.
- **Not handled in v1:** fully romanized Hinglish ("mujhe office ke liye late ho gaya") without word-level language tags.
- **Relationship to UTMOS:** same family (neural predictor on a self-supervised encoder), reusing its proven ideas, but a switch-aware specialist, trained on preferences and minimal pairs, with per-switch output. Not a new general-purpose UTMOS, and not aiming to win the VoiceMOS 2022 leaderboard.

## Long-term vision: three stages

| Stage | Scope | Data | Outcome |
|---|---|---|---|
| **1. Hinglish** (current) | Hindi–English | HiACC, MUCS, SpeechArenaBench Hindi, our human study | Validated SwitchMOS for Hinglish (paper 1) |
| **2. Indic–English** | SpeechArenaBench's 10 languages | SpeechArenaBench, MUCS Bengali–English | Leave-one-language-out; the Indic standard |
| **3. Universal** | Any code-switched pair, then other local events | Spanish–English (Bangor Miami), Mandarin–English (ASCEND, SpeechJudge), more to collect | A **local naturalness score used beside UTMOS**: UTMOS says how natural overall, SwitchMOS says where it isn't |

**Hypothesized universal core** (to be tested, not assumed):
- **Seams:** a glued join sounds wrong in any language. Most likely universal.
- **Switch marking:** slowing before and lengthening at the switch appear in Spanish–, French–, Greek–English and Hinglish studies; strength varies by speaker and direction. Probably universal with per-pair calibration.
- **Pitch patterns:** differ for tone languages (e.g. Mandarin). Pair-specific.

**Beyond switches:** the same pipeline (align → locate events → score → train on minimal pairs) applies to other local trouble spots: names, numbers, emphasized words, joins between generated chunks in long-form TTS. That generalization is what could make a local score a routine companion to UTMOS.

**Order matters:** stage 2 only after stage 1's per-switch scores match human judgments; stage 3 only after leave-one-language-out works in stage 2.

## Why not just a switch-only score?

A clip can be natural at the switch and robotic everywhere else. The headline number covers the whole clip; switch scores explain it and catch what whole-clip models miss.

## Why not just copy UTMOS?

Its own ablations show its famous multi-level stacking barely helped (+0.006 correlation). What helped was rater/domain information, staged training, and modern training data. We keep those, and add what UTMOS lacks: attention to where the language changes, and supervision that doesn't depend on thousands of human ratings.

## Deliverables

- SwitchMOS model + code, released.
- A small human-rated set of switch clips, released.
- A paper (target: Interspeech).
- Optional case study: IndicF5 fine-tuned on real Hinglish, scored by SwitchMOS.
