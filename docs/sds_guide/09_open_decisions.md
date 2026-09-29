# 09 — Crucial decisions not yet made

Each item: the question, why it matters, the options, a recommendation, and when it must be decided.

## Decide in Phase 0

### D1. What counts as a "switch"? (loanwords)
- **Why:** "office", "school", "phone", "late" are used daily in Hindi. Linguists call these *borrowings*, not switches. Script-based tagging counts every Latin word as a switch. If most "switches" are really borrowings, the reference mixes two phenomena.
- **Options:** (a) script = language, count all; (b) exclude a list of frequent loanwords; (c) count all, but tag loanwords and analyse separately.
- **Recommendation:** (c). Build a small loanword list (most frequent single-word English insertions in HiACC); report results with and without them.

### D2. Romanized Hinglish input
- **Why:** much real Hinglish text is all-Latin ("mujhe office late ho gaya"). Script can't tell the language.
- **Options:** require Devanagari+Latin input; add a word-level language-ID model; require user tags.
- **Recommendation:** v1 requires mixed-script transcripts or user tags. Word-level LID is v2.

### D3. The name
- **Why:** "Switch *Discontinuity* Score" implies smaller discontinuity is better, which is the opposite of the core finding.
- **Options:** keep SDS; rename, e.g. "Switch Naturalness Score (SNS)" or "Code-Switch Prosody Score".
- **Recommendation:** rename before anything is public. Decide in Phase 0.

### D4. The paper's primary claim
- **Recommendation:** "A switch-localized metric calibrated to real Hinglish switches agrees with bilingual listeners significantly better than join cost." Not "universal". Portability shown as a secondary demonstration only.

### D5. Speaker re-split
- **Status:** proposed in 04 §4.1. Needs your sign-off.

### D16. Paper framing: switch metric vs switch-aware predictor
- **Why:** a switch-only score is niche; users want one whole-clip number. SpeechArenaBench (MIT, 16,694 Hindi pairs with audio) makes a learned whole-clip predictor feasible.
- **Options:** (a) SDS metric paper as planned; (b) switch-aware predictor with SDS as its switch branch; (c) both, SDS first as a short paper.
- **Recommendation:** (b), pending two checks: a full novelty search on code-switched MOS prediction, and a count of code-mixed Hindi pairs in SpeechArenaBench. See `../11_switch_aware_predictor.md`.

## Decide by Phase 3

### D6. How is "phrase boundary" detected?
- **Why:** switches at phrase boundaries legitimately have pauses and pitch resets; the reference is split by position.
- **Options:** pause ≥ 150 ms; punctuation in transcript; a prosodic boundary detector.
- **Recommendation:** pause ≥ 150 ms OR punctuation, for v1. Check agreement with hand labels on 50 boundaries.

### D7. Single-word insertions vs multi-word islands
- **Why:** "मुझे office के लिए" (one English word) and "मैंने कहा that it is a festival of light" (a long English stretch) behave differently.
- **Recommendation:** record island length; if the pilot shows a large difference, make it a grouping variable.

### D8. Is the reference big enough?
- **Why:** ~970 REF switches across 6 speakers, split into groups, with ~10 features.
- **Recommendation:** default to 2 groups (direction only) unless each of 4 groups has ≥100 switches. Add IIT-B or cross-fitting if T1 fails.

### D9. Which phonetic effects count for the B3 gate?
- **Recommendation:** pre-register: pre-switch rate ratio < 1, lengthening > 1, pitch range ratio > 1, energy of embedded English > 0 dB. Pass if ≥2 hold with p < 0.05 across speakers.

## Decide by Phase 6

### D10. Test sentences
- HiACC TEST transcripts (spoken-style) + COMI-LINGUA (broader vocabulary). Check every character is in each system's vocabulary; verbalize numbers.

### D11. Reference voice clip for TTS
- One 5–10 s clip per TEST speaker, fixed across systems. Choose clips with no switch inside, so the reference itself doesn't leak switch behaviour.

### D12. Closed systems (Bulbul, Gemini)
- Check terms of service allow benchmarking. Include in the human study only.

### D13. Script policy for TTS input
- Devanagari+Latin as HiACC (IndicF5 vocab covers both). Same policy for every system that accepts it; document exceptions.

## Decide by Phase 7

### D14. Raters: who, how many, pay, ethics
- 5–8 bilinguals; fair hourly pay; consent form; check whether your institution needs ethics approval.

### D15. Rating scale wording
- Pilot two wordings ("How natural is the language change?" vs "Does the change of language sound like a real person?") on the pilot and keep the one with higher α.

## Already decided

| Decision | Choice | Where |
|---|---|---|
| Score structure | three parts + in-range rate | 02 |
| Scale | percentile of natural | 02 |
| Training data for SDS | natural REF speech only | 01, 04 |
| Human ratings role | test only | 01 |
| Pass bar | beat join cost by Steiger p < 0.05 | 05 |
| Bandwidth | 16 kHz, 8 kHz low-pass | 03 |
| Aligner | MMS + uroman | 03 |
