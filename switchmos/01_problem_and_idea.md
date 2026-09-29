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

## Why not just a switch-only score?

A clip can be natural at the switch and robotic everywhere else. The headline number covers the whole clip; switch scores explain it and catch what whole-clip models miss.

## Why not just copy UTMOS?

Its own ablations show its famous multi-level stacking barely helped (+0.006 correlation). What helped was rater/domain information, staged training, and modern training data. We keep those, and add what UTMOS lacks: attention to where the language changes, and supervision that doesn't depend on thousands of human ratings.

## Deliverables

- SwitchMOS model + code, released.
- A small human-rated set of switch clips, released.
- A paper (target: Interspeech).
- Optional case study: IndicF5 fine-tuned on real Hinglish, scored by SwitchMOS.
