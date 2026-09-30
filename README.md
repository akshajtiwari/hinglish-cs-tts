# Hinglish Code-Switched TTS

Research project on Hindi-English code-switched text-to-speech, started 2026-09-23.

**Working title:** *Natural Switches Are Not Seamless: A Switch-Localized, Human-Calibrated Metric for Code-Switched TTS, with a Hinglish Case Study.*

**Start here: [`switchmos/`](switchmos/README.md)**, a self-contained description of the current project.

**Current direction (2026-09-30): SwitchMOS**, a whole-clip naturalness predictor that beats UTMOS where it fails (modern, Indian-language, and code-switched speech), trained on a broad mix of existing human ratings, with a built-in local-event branch that scores language switches. Spec: [`docs/sds_guide/13_switchmos.md`](docs/sds_guide/13_switchmos.md).

**Original problem in one line:** Hinglish TTS gets the words right but sounds wrong at the exact moment it switches between Hindi and English, and nobody measures that moment. We build a score that checks whether a switch sounds like a real bilingual speaker, then use it to test what training on real Hinglish conversation fixes and what it costs.

All research documents are in [`docs/`](docs/README.md).
