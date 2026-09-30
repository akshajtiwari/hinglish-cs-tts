# SwitchMOS: A Better Automatic Judge of Whether Synthetic Speech Sounds Human

**Research proposal for a review committee** · Draft of 2026-09-30 (reframed) · Author: Akshaj Tiwari

This document assumes no background in speech technology. Every technical term is explained the first time it appears, and there is a glossary at the end (§14).

---

## 1. Summary

Computer voices, or **text-to-speech (TTS)** systems, now read news, answer customer-service calls, and power screen readers. Researchers and companies need a quick, cheap way to tell how *human* a voice sounds. The standard tool for that, **UTMOS** (2022), is an automatic judge trained to imitate human listeners.

But UTMOS was trained on older, mostly English voices, and it no longer keeps up:
- On today's clean commercial voices it agrees with human listeners only about 51–54% of the time when choosing the better of two recordings, close to a coin toss. Humans agree with each other about 76% of the time.
- It is weaker still on Indian languages and on speech that mixes languages in one sentence, which is how hundreds of millions of people speak (*"मुझे office के लिए late हो गया"*).

We propose **SwitchMOS**, a new automatic judge of **whole-recording naturalness** that:
1. **Beats UTMOS where it fails**: modern voices, Indian languages, and mixed-language speech. It stays competitive on the classic benchmarks where UTMOS is strong.
2. Learns from a **much broader mix of existing human-rated data** (English, Mandarin, Hindi, Tamil and 8 other Indian languages, including mixed-language recordings), using the design choices that published studies show matter most.
3. Adds one new ingredient: a **local-event component** that looks closely at moments where speech often goes wrong, starting with the points where the language switches. It feeds that evidence into the overall score and explains where a recording sounds unnatural.

---

## 2. Background for non-specialists

### 2.1 Text-to-speech
A TTS system turns written text into spoken audio. Modern systems are neural networks trained on many hours of speech and can imitate a voice from a few seconds of example ("voice cloning").

### 2.2 How voice quality is measured
- **Listening tests.** People rate recordings from 1 (bad) to 5 (excellent). The average is the **Mean Opinion Score (MOS)**. Alternatively, listeners hear two recordings and pick the better one (a **pairwise preference**).
- **Automatic judges (MOS predictors).** Listening tests are slow and costly, so neural networks are trained to predict human ratings. UTMOS won the 2022 VoiceMOS Challenge and became a standard number in speech papers. Newer judges exist (UTMOSv2, SpeechJudge), but no single one has replaced it.

### 2.3 Code-switching
**Code-switching** means changing language within a conversation or sentence. The moment the language changes is a **switch point**. Voices that handle each language well often stumble exactly there.

---

## 3. The problem

1. **Automatic judges don't track human judgment on modern voices.** A 2026 study measured how often judges pick the same recording as humans:

| Recordings | UTMOS | UTMOSv2 | Human-vs-human ceiling |
|---|---|---|---|
| Older research voices (BVCC) | 0.89 | 0.90 | 0.89 |
| Clean commercial voices | **0.51** | **0.53** | 0.76 |

2. **They fail outside English.** UTMOS scored below 0.35 correlation with humans on French voices; general judges reached about 0.29 on Indian languages.
3. **They average away brief problems.** A judge that gives one number for a whole recording barely notices a quarter-second glitch at a language switch, even though listeners do.
4. **Mixed-language speech has no dedicated measure.** Yet it's how hundreds of millions of people speak, and companies advertise "natural switching" without any way to check it.

**A scientific insight about switches.** Studies of real bilingual speakers show they do not switch perfectly smoothly. They slow down slightly before the switch and say the switched word a little longer, with more pitch movement. Listeners use these cues. So our switch component asks "does this switch sound like a real bilingual?", not "is it smooth?".

---

## 4. Research perspective

### 4.1 Thesis
How natural a recording sounds depends on **overall quality** *and* on **specific local moments** (language switches, glued-together joins, names, numbers). Today's judges fail for two reasons:
- they learned from narrow, old, mostly English data;
- they treat the recording as one undifferentiated block.

A better judge needs broader training data, better training methods, and the ability to look closely at local moments.

### 4.2 Research questions
| # | Question | Role |
|---|---|---|
| **RQ1** | Can a judge trained on a broad mix of existing human ratings beat UTMOS and UTMOSv2 on modern, Indian-language, and mixed-language speech, while staying competitive on classic benchmarks? | **Main question** |
| RQ2 | Does looking closely at language switches improve the overall score on mixed-language speech, without hurting single-language speech? | Tests our new component |
| RQ3 | Can automatically built "before/after" recordings replace expensive human ratings for teaching the model about local problems? | Cost / label efficiency |
| RQ4 | Does the judge work on languages and voices it has never seen? | Generalization |

### 4.3 Hypotheses
- **H1:** Training data diversity and preference-based training close most of the gap on modern and Indian-language speech.
- **H2:** On mixed-language recordings, switch-level evidence adds information the overall-quality components miss.
- **H3:** Real Hinglish switches show measurable patterns (slowing, lengthening, pitch range), and synthetic voices depart from them in ways listeners notice.

### 4.4 What counts as success
Fixed in advance (§10): beat UTMOSv2 on modern, Indian-language, and mixed-language tests; stay close to it on classic tests; and show the switch component adds a significant gain on mixed-language speech.

---

## 5. Novelty

### 5.1 Existing work
| Work | What it does | Limitation |
|---|---|---|
| UTMOS (2022) | Standard automatic judge | Old English data; near chance on modern voices |
| UTMOSv2 (2024) | Adds an image-like spectrogram view, more data | Still English-centric; near chance on commercial voices |
| SpeechJudge (2026) | 7-billion-parameter judge, 99,000 human comparisons, includes Mandarin–English mixed speech | Very large; no Indian languages; one score per clip; discards "no preference" answers |
| IndicMOS (2024) | Judge for 7 Indian languages | Small, older data; no mixed-language speech |
| SpeechArenaBench (2026) | 120,000+ human comparisons in 10 Indian languages | A dataset; no audio-based judge trained on it |
| DAMOS (2026) | Finds distorted regions, then scores | Generic distortions; small improvement |

### 5.2 What is new
1. **A broad multilingual training mix for a naturalness judge:** absolute ratings and comparisons across English, Mandarin, 10 Indian languages, and mixed-language speech. No published judge combines these.
2. **First judge trained on SpeechArenaBench.**
3. **A local-event component** that scores language switches inside a naturalness judge. Not found in prior work.
4. **Training the local component with "before/after" recordings**: the same real recording with only one moment regenerated. No quality judge has been trained this way.
5. **Using "no preference" answers** in training, which prior work discards.
6. **Practical size:** 10–25 times smaller than SpeechJudge.

### 5.3 Not claimed
- Not the first judge for mixed-language speech (SpeechJudge covers Mandarin–English).
- Not a detector of human-vs-AI speech (§12).
- Not necessarily better than UTMOS on old English benchmarks; there we aim to stay close.

---

## 6. Value to society

- **Better voices for mixed-language speakers.** A reliable judge lets developers improve voices for the ~250 million Indians who code-switch daily, and for mixed-language communities worldwide.
- **Accessibility.** Screen readers and reading aids for people with visual impairments or low literacy increasingly use TTS; more natural voices are less tiring and easier to understand.
- **Public services.** Helplines, banking, healthcare reminders, and farm advisories in India use voice. An open judge lets small organisations check quality without costly listening tests.
- **Research.** A judge that works on modern and multilingual voices restores a trustworthy shared measure, and its explanations show developers *where* to improve.
- **Safer training of voices.** Judges are now used as automatic rewards when training TTS; a judge that can be "fooled" leads to worse voices. We test for this.

**Risks and responses**
| Risk | Response |
|---|---|
| Better voices could aid impersonation | We release a judge, not a voice generator; safeguards belong to TTS developers |
| Bias toward some speakers or dialects | Document the data; report results per language; widen coverage in later stages |
| Over-trusting a single number | Always report alongside human tests and other measures; publish limits |
| Rater welfare | Consent, fair pay, no personal data |

---

## 7. Approach at a glance

```
                        A recording (+ its text, language)
                                      │
      ┌───────────────────────────────┼───────────────────────────────┐
      ▼                               ▼                               ▼
 Semantic view                  Acoustic view                  Local-event view (new)
 (pretrained multilingual       (spectrogram "image"           find switch points; measure
  speech model)                  of the sound)                  pauses, speed, pitch, joins
      │                               │                               │
      └────────────── combined, informed by dataset / listener / language tags ──┘
                                      │
                 Overall naturalness score  +  where it sounds unnatural, and why
```

**Where the knowledge comes from**
| Source | Teaches | Cost |
|---|---|---|
| Existing human ratings (SOMOS, BVCC, SpeechJudge, MANGO, SpeechArenaBench) | How people judge whole recordings, across languages and voice generations | Already collected by others |
| Real bilingual recordings (HiACC, MUCS) | What natural switches sound like | Free |
| "Before/after" recordings | What a bad local moment sounds like, exactly where it is | Computer time |
| A small listening study of our own | Whether the switch explanations match people | ~500 short clips, 5–8 listeners |

---

## 8. Steps, with every decision explained

### Step 1 — Gather and harmonize human-rated data (2 weeks)
| Dataset | Content | Why |
|---|---|---|
| SOMOS | 20,000 English clips, 375,000 ratings | Large; teaches the 1–5 scale |
| BVCC (+ "zoomed" version) | Classic English benchmark | Lets us compare with UTMOS directly |
| SpeechJudge-Data | 99,000 comparisons of modern voices, incl. Mandarin–English mixed | Modern voices; mixed-language speech |
| MANGO | Hindi and Tamil ratings (MUSHRA, a 0–100 comparative scale) | Indian-language absolute ratings |
| SpeechArenaBench | 120,000+ comparisons, 10 Indian languages, 78% mixed-language sentences, 6 detailed quality ratings | Modern Indian-language and mixed speech |

**Decisions**
- **Research-only licence.** Several key datasets forbid commercial use, so the released judge is for research. This allows the strongest data mix.
- **Common format.** Every item is stored as recording, system, listener, dataset, and label type, so absolute scores and comparisons can train together.
- **Hold out whole voices, languages, listeners, and sentences** for testing, so results show real generalization, not memorization.
- **Resolve the commercial voices' terms of service first (blocker).** SpeechArenaBench recordings come from company products; several vendors (e.g. Sarvam, ElevenLabs) forbid using their outputs to train or even test machine-learning systems. We will ask the dataset's authors, get a legal read, and if needed train on open-model data (SpeechJudge, MANGO, our own ratings of open voices) and use SpeechArenaBench for testing only.

### Step 2 — Measure the current judges (1–2 weeks)
Run UTMOS, UTMOSv2, DNSMOS, and SpeechJudge on every test set. **Why:** this gives the exact numbers to beat and shows *where* each fails before we build anything. **Gate:** reproduce UTMOS's published score on BVCC (≈0.897), proving our test setup is correct.

### Step 3 — Build the overall judge (3–4 weeks)
| Choice | Decision | Why |
|---|---|---|
| Pretrained speech model | Multilingual (w2v-BERT 2.0, mHuBERT-147, or XLS-R), picked by a small trial | English-only models transfer poorly to Indian languages |
| Which internal layers | Learn a weighted mix | Different layers carry quality vs intelligibility; the biggest single effect in a 2026 study |
| Spectrogram view | Add a small image-style network | UTMOSv2 showed it improves absolute scores; combining both views beats either |
| Dataset and listener tags | Include | Different datasets use different scales; listener information was UTMOS's largest single gain |
| Learning from comparisons | Bradley–Terry method, with Davidson's extension for ties | Better than predicting numbers directly on comparison data; uses "no preference" answers |
| Training order | Train parts separately, freeze, combine, then fine-tune gently | The largest factor in UTMOSv2's success |
| First experiments | Vary the data mix | Data diversity is the biggest lever in the literature |

**Gate:** beats UTMOSv2 on a development split of modern and Indian-language comparisons.

### Step 4 — Add the local-event component (3–4 weeks)
| Sub-step | Method | Why |
|---|---|---|
| Standardize audio | 16 kHz, remove sound above 8 kHz | Real Hinglish recordings are 16 kHz; matching prevents "synthetic" being detected from bandwidth |
| Find word timings | uroman (writes any script in Latin letters) + MMS aligner (finds when each word is spoken) | Works for 1,100+ languages without a dictionary |
| Mark switches | Devanagari = Hindi, Latin = English | Free and accurate for our data |
| Measure each switch | Pause, speed before/after, word lengthening, pitch jump and range, loudness jump, "join" sound | Each matches a pattern in bilingual-speech research or a classic join measure |
| Check real switches | Do real Hinglish switches show the predicted patterns? | If not, rely on learned features only |
| Build "before/after" pairs | Regenerate only a switch with IndicF5; pass both versions through the same audio converter; also edit non-switch words as a control | Teaches the component exactly where problems are, without human labels, and prevents it learning "was edited" |
| Check pairs | Listen to 20 pairs: do edits sound worse? | If not, use simple edits that are worse by construction |
| Integrate | Feed switch scores into the overall judge; let one bad switch pull the score down | Listeners notice one bad moment |

**Gate (RQ2):** the component improves the overall score on mixed-language test comparisons. If not, it stays as an explanation tool only.

### Step 5 — Small listening study (2 weeks)
**Why:** no dataset rates individual switches, so without this we can't show the explanations match people.
- 5–8 paid, consenting Hindi–English bilinguals; about 500 short clips centred on switches.
- Clips are chosen where the model is least sure (**active learning**).
- A 50-clip pilot must show listeners agree with each other (Krippendorff's α ≥ 0.5).

### Step 6 — Full evaluation, release, paper (3 weeks)
Run every test (§10). Release the judge, code, test splits, and ratings openly. Write the paper for Interspeech.

---

## 9. Resources and timeline

**Computing:** one server with 4 NVIDIA A16 GPUs (16 GB each), 480 GB RAM, 32 CPU cores, 4.6 TB disk. Each A16 is roughly one-sixth the speed of a common research GPU, so we compute features once and store them, and keep the new parts of the model small.

**People:** one researcher; 5–8 paid bilingual listeners for about two weeks.

**Timeline:** about 19 weeks to the Interspeech 2027 deadline (papers due Feb 9, 2027), with a pre-agreed cut-list if steps slip (`10_roadmap.md`).
| Weeks | Steps |
|---|---|
| 1–2 | 1 (data) |
| 3–4 | 2 (current judges) |
| 5–8 | 3 (overall judge) |
| 7–11 | 4 (local-event component, overlapping) |
| 12–13 | 5 (listening study) |
| 14–17 | 6 (evaluation, release, paper) |

---

## 10. How success will be judged

### 10.1 Tests
| Group | What | Role |
|---|---|---|
| Modern voices | Comparisons from SpeechJudge, MOS-RMBench, and clean commercial voices | **Main** |
| Indian languages | SpeechArenaBench (held-out voices and languages), MANGO | **Main** |
| Mixed-language | Mixed-language subsets of SpeechArenaBench and SpeechJudge | **Main** |
| Classic benchmarks | BVCC, SOMOS, VoiceMOS 2023/2024, Mandarin Blizzard 2019 | "No harm" |
| Switch explanations | Before/after pairs with known locations; our listening study | Validates the explanations |
| Other speech | Conversational, emotional, long recordings | Generalization |
| Robustness | Volume, format, timing shifts; training a voice against the judge to see if it can be fooled | Safe to use |

**Compared against:** UTMOS, UTMOSv2, DNSMOS, SpeechJudge, a trivial "longer recording wins" rule, our judge without the switch component, and our judge trained only on UTMOS's data (to separate the effect of data from design).

### 10.2 Pass criteria (fixed in advance)
1. Beat UTMOSv2 on modern, Indian-language, and mixed-language tests (statistically confirmed).
2. Within a small margin of UTMOSv2 on classic tests.
3. The switch component gives a significant gain on mixed-language tests, with no loss elsewhere.
4. Match SpeechJudge's smaller model (72.7%) on its own test, at a fraction of the size.

### 10.3 Honest expectations
| Claim | Expectation |
|---|---|
| Beats UTMOS/UTMOSv2 on Indian and mixed-language speech | High, partly thanks to training data; a data-only comparison shows how much |
| Beats them on modern voices | Fairly high |
| Competitive on classic benchmarks | Fairly high |
| Switch component improves the overall score | Uncertain; similar published ideas gained little |
| Matches SpeechJudge | Uncertain |

If the switch component doesn't raise the overall score, the main result (a better judge for modern and multilingual speech) stands, and the switch explanations remain a useful diagnostic.

---

## 11. Risks and fallbacks

| Risk | Fallback |
|---|---|
| Different rating scales clash in training | Dataset tags with per-dataset offsets; stage-wise training |
| Model learns *which company* made a voice | Test on voices held out of training |
| Only 7 commercial voices in SpeechArenaBench | Combine with SpeechJudge and MANGO voices; add our own test voices |
| Judge can be "fooled" when used as a training reward | Explicit test; recommend combining with other measures |
| Before/after pairs teach "was edited" | Same audio converter on both; non-switch edit controls; listening check |
| Terms of service of commercial voices forbid training (or testing) on their outputs | Resolve before training (ask dataset authors, legal read); fall back to open-model training data and evaluation-only use |
| Someone publishes first | Move quickly; our combination (multilingual mix + local component) stays distinct |

---

## 12. Out of scope, and what each item means

| Out of scope | Meaning | Why |
|---|---|---|
| Human-vs-AI detection | Deciding whether a person or a computer spoke | Different field; a synthetic voice can sound fully natural |
| Building a new TTS system | Creating a voice generator | We judge voices; an optional side experiment only adapts an existing one |
| Fully romanised Hinglish | Hindi typed in English letters ("mujhe office late…") | Script no longer reveals the language; needs an extra tool (later version) |
| Recording-quality assessment | Background noise, microphones | Existing tools (DNSMOS) cover it |
| Beating UTMOS on old English benchmarks | Winning where UTMOS is already strong | Not our aim; we stay competitive there |
| Commercial licence | Use in paid products | Key training data is non-commercial |
| Emotion, speaker identity, pronunciation accuracy | Other aspects of speech | Other tools; reported alongside |
| Children's speech | Young speakers | Different acoustics; later |

---

## 13. Beyond this project
1. **Stage 1 (this proposal):** a better whole-recording judge, strongest on Hindi–English and Indian languages.
2. **Stage 2:** all 10 Indian languages mixed with English; testing on unseen languages.
3. **Stage 3:** more language pairs and more local moments (names, numbers, joins in long recordings), aiming for a judge reported beside UTMOS in speech research.

---

## 14. Glossary

| Term | Meaning |
|---|---|
| Text-to-speech (TTS) | Software that turns text into spoken audio |
| MOS | Average of listeners' 1–5 ratings |
| Pairwise preference | Listener picks the better of two recordings (or "no preference") |
| MOS predictor / automatic judge | Neural network trained to predict human ratings |
| UTMOS / UTMOSv2 | Widely used automatic judges (2022 / 2024) |
| SpeechJudge | Large (7B) automatic judge trained on human comparisons (2026) |
| SpeechArenaBench | 120,000+ human comparisons of voices in 10 Indian languages |
| SOMOS, BVCC, MANGO | Public datasets of human ratings (English; English; Hindi/Tamil) |
| MUSHRA | A listening-test format scoring 0–100 against reference recordings |
| Code-switching / switch point | Changing language / where it changes |
| Pretrained speech model (encoder) | Network that turns audio into numerical features, trained on unlabelled speech |
| Spectrogram | A picture of sound: frequency over time |
| Forced alignment (MMS, uroman) | Finding when each word is spoken / tools that do it for any script |
| Local event | A brief moment that can sound wrong: a switch, a join, a name |
| Before/after pair (minimal pair) | Two versions of a recording differing in one small part |
| Bradley–Terry (+ Davidson) | Method for learning scores from comparisons (including ties) |
| Active learning | Choosing which clips humans rate, to learn most per rating |
| Correlation / pairwise accuracy | How well the judge's scores / choices match humans |
| Krippendorff's α | How much raters agree with each other |
| GPU | Processor for neural-network arithmetic |
| Interspeech | The main international speech-research conference |

---

## 15. Key references
- UTMOS (arXiv 2204.02152); UTMOSv2 (2409.09305); SpeechJudge (2511.07931); MOS-RMBench (2510.00743).
- "Limits of reference-free speech quality metrics" (2609.13150); VoiceMOS Challenges 2023/2024/2026 (2310.02640, 2409.07001, 2609.13792).
- IndicMOS (Interspeech 2024); SpeechArenaBench / Preferences of a Voice-First Nation (2604.21481); MANGO (AI4Bharat).
- DAMOS (2608.21176); frame-level quality prediction (2508.10374).
- HiACC (Data in Brief 2025); MMS (2305.13516); Rao et al. 2018; Fricke et al. 2016; Olson 2016.
- Full survey tables: `02_related_work_and_novelty.md` and `03_datasets.md`; pre-implementation checklist: `12_pre_implementation_checklist.md`.
