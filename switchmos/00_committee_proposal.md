# SwitchMOS: Measuring Whether Mixed-Language Synthetic Speech Sounds Human

**Research proposal for a review committee** · Draft of 2026-09-30 · Author: Akshaj Tiwari

This document assumes no background in speech technology. Every technical term is explained the first time it appears, and there is a glossary at the end (§14).

---

## 1. Summary

Hundreds of millions of people in India speak in a mix of Hindi and English within a single sentence, for example *"मुझे office के लिए late हो गया"* ("I got late for office"). Computer voices, or **text-to-speech (TTS)** systems, are now used in voice assistants, customer-service calls, audiobooks, and accessibility tools. They increasingly speak this mixed language, but often sound unnatural at the exact moment the language changes.

Today there is no automatic way to measure this. The standard tools that estimate "how human does this voice sound" give one number for a whole recording. They were trained almost entirely on English, and they are known to be unreliable for Hindi and for modern voices.

We propose **SwitchMOS**, an automatic judge of speech naturalness that:

1. Gives **one overall score** for a recording, like existing tools.
2. Also gives **a score at every point where the language switches**, with a plain-language reason (e.g. "no natural slowdown before the English word; audible join").
3. Learns mainly from **real recordings of bilingual people** and from **automatically constructed before/after comparisons**, so it needs far fewer expensive human ratings than existing approaches.

We start with Hindi–English ("Hinglish"). If it works, we extend it to other Indian languages mixed with English, and later aim for a general tool that sits beside the current standard (UTMOS) in speech research.

---

## 2. Background for non-specialists

### 2.1 What is text-to-speech?
A TTS system takes written text and produces spoken audio. Modern systems are neural networks trained on many hours of recorded speech. They can imitate a voice from a few seconds of example audio ("voice cloning").

### 2.2 What is code-switching?
**Code-switching** is changing language within a conversation or a single sentence. The point where the language changes is a **switch point**. In Hinglish, Hindi is usually written in Devanagari script (मुझे) and English in Latin script (office), which makes switches easy to find in text.

### 2.3 How is voice quality measured today?
- **Listening tests.** People listen and rate each recording from 1 (bad) to 5 (excellent). The average is the **Mean Opinion Score (MOS)**, a practice inherited from telephone-quality testing in the 1990s. A variant asks listeners to compare two recordings and say which sounds better (a **pairwise preference**).
- **Automatic predictors.** Listening tests are slow and expensive, so researchers train neural networks to *predict* the MOS. The best known is **UTMOS** (2022), which won an international challenge (the VoiceMOS Challenge) and became a standard number reported in speech papers.

### 2.4 Why existing predictors fall short here
- They give **one number per recording**, so a problem lasting a quarter of a second at a switch gets averaged away.
- They were trained mostly on **English**. On Hindi, UTMOS agrees with human ratings only weakly (correlation 0.26 in one published study, where 1.0 would be perfect).
- On pairs of **modern** voices, UTMOS picks the one humans prefer only about 54% of the time, barely better than a coin toss.

---

## 3. The problem

Modern TTS usually gets the *words* right. What often sounds wrong is **how the voice moves from one language to the other**:
- an abrupt change in pitch or loudness;
- English words rushed or stretched unnaturally;
- a faint "glued-together" sound (a **seam**), as if two recordings were joined.

Companies advertise "smooth switching", but nobody can measure it. Researchers building these voices therefore can't tell whether a change actually improved the switches.

**A key scientific insight shapes our approach.** Studies of real bilingual speakers (Spanish–English, French–English, Greek–English, and Hindi–English) show that people do **not** switch perfectly smoothly. They tend to slow down slightly before a switch, and say the switched word a little longer and with more pitch movement. Listeners use these cues to follow the change. So the right target is not "no change at the switch" but **"the kind of change a real bilingual person makes"**.

---

## 4. Research perspective

### 4.1 Research questions
1. **RQ1:** Can an automatic judge identify *where* in a mixed-language recording the switching sounds unnatural, in agreement with human listeners?
2. **RQ2:** Does paying explicit attention to switch points make an automatic judge agree better with human preferences on mixed-language speech?
3. **RQ3:** Can most of the learning come from real bilingual recordings and automatically built comparisons, reducing the number of human ratings needed?
4. **RQ4:** Does a judge trained on some Indian languages work on an Indian language it has never seen?

### 4.2 Hypotheses
- **H1:** Natural switches in real Hinglish speech show measurable patterns (slowing before, lengthening of the switched word, wider pitch range) compared with ordinary word boundaries.
- **H2:** Synthetic voices depart from these patterns in ways listeners notice.
- **H3:** A model trained on "same recording, only the switch changed" pairs learns switch-specific naturalness that general predictors miss.

### 4.3 What counts as success
Stated in advance, before any results are seen (§10). In short: the per-switch scores must agree with human listeners, and the full model must beat the same model *without* switch attention on mixed-language recordings.

---

## 5. Novelty: what exists and what is new

### 5.1 Closest existing work
| Work | What it does | What it lacks for our problem |
|---|---|---|
| UTMOS / UTMOSv2 (2022, 2024) | Predicts overall quality from audio | One score per clip; English-centric; unreliable on modern voices |
| SpeechJudge (2026) | Large (7-billion-parameter) judge trained on 99,000 human comparisons, including Mandarin–English mixed speech | No per-switch scores; not Indian languages; very large; discards "no preference" answers |
| SpeechArenaBench (2026) | 120,000+ human comparisons of TTS in 10 Indian languages | A dataset, not a judge; only a simple model over human ratings |
| DAMOS (2026) | Finds distorted regions, then scores the clip | Generic distortions, not language switches; small improvement |
| "Join cost" (1990s) | Measured discontinuity where recorded snippets were glued | Assumes less change is always better; abandoned with neural TTS |

### 5.2 What is new in our work (checked by literature search, Sept 2026)
1. **Scores for each language switch** inside a naturalness judge. Not found in any prior work.
2. **Training from "minimal pairs"**: the same real recording with only the switch regenerated, so any difference is due to the switch alone. No prior quality judge has been trained this way.
3. **First judge trained on SpeechArenaBench**, the Indian-language human-preference dataset.
4. **Using "no preference" answers** in training, which all prior work discards.
5. **Testing on unseen languages** (train on some Indian languages, test on another).
6. **Small and practical:** 25–100 times smaller than SpeechJudge, runnable by ordinary labs.

### 5.3 What we do *not* claim
- Not the first judge for mixed-language speech: SpeechJudge covers Mandarin–English.
- Not a replacement for UTMOS on ordinary single-language speech.
- Not a detector of whether speech is human or AI (§12).

### 5.4 Why this wasn't done earlier
Quality scoring came from telephony (one number per call). The old join-cost measures were dropped when neural voices removed explicit joins. Mixed-language TTS research spent years just making it work at all. The finding that real switches are "marked" sits in linguistics journals that speech engineers rarely read. And the enabling resources are new: the HiACC Hinglish corpus (2025), a multilingual alignment tool (MMS, 2023), and SpeechArenaBench (2026).

---

## 6. Value to society

### 6.1 Who benefits
- **Speakers of mixed languages.** Around 250 million Indians code-switch daily; worldwide, code-switching is the norm in many communities. Voices that sound natural to them improve access to services.
- **Accessibility.** Screen readers and reading aids for people with visual impairments or low literacy increasingly use TTS. Unnatural mixed speech is tiring and harder to understand; a published study found that listeners understand words just after a switch less well in synthetic speech.
- **Public services and small businesses.** Helplines, banking, healthcare reminders, and agricultural advisories in India use voice. A free, open measure lets smaller organisations check voice quality without costly listening tests.
- **Research.** A shared, open measure lets researchers compare systems fairly and track progress on a problem nobody can currently measure.
- **Better speech recognition.** Synthetic mixed speech is used to train speech-to-text systems. A quality filter keeps unnatural examples out of that training.

### 6.2 Risks and how we handle them
| Risk | Our position |
|---|---|
| More natural synthetic voices could make impersonation easier | We measure naturalness; we do not release a new voice generator. The tool's per-switch explanations are also useful for spotting imperfect synthetic speech. Voice-cloning safeguards remain the responsibility of TTS developers |
| Bias toward one variety of Hinglish (e.g. urban, educated speakers) | We document speaker demographics (age, gender) and state the limitation; later stages add more speakers and regions |
| Treating the score as absolute truth | Always reported alongside other measures and human tests; we publish its limits |
| Human raters' welfare and privacy | Informed consent, fair pay, no personal data kept |

---

## 7. Approach at a glance

```
            ┌──────────────────────────── A recording + its text ────────────────────────────┐
            │                                                                                  │
   1. Find where each word starts and ends          2. Turn the audio into features with a
      (forced alignment)                               pretrained multilingual speech model
            │                                                                                  │
   3. Mark every language switch                                                               │
            │                                                                                  │
   4. Measure each switch: pauses, speed,                                                      │
      pitch, loudness, "join" sound                                                            │
            │                                                                                  │
            ▼                                                                                  ▼
   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
   │ Switch expert   │   │ Whole-clip      │   │ Artefact expert │   5. Three specialist
   │ (each switch)   │   │ expert          │   │ (glitches)      │      sub-models ("experts")
   └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
            └──────────── 6. A "gate" decides how much to trust each ─────────┘
                                          │
                     Overall score  +  a score and reason for every switch
```

**Where the knowledge comes from:**
| Source | Teaches the model | Cost |
|---|---|---|
| Real bilingual recordings | What natural switches sound like | Free (existing public corpora) |
| Minimal pairs (same clip, only the switch regenerated) | What a bad switch sounds like, at the exact location | Computer time only |
| Human comparisons (SpeechArenaBench) | How people judge whole recordings | Already collected by others |
| Our small listening study | Whether per-switch scores match people | ~500 short clips, 5–8 listeners |

---

## 8. How we will build it: step by step, with every decision explained

Each step lists **what** we do, **why**, the **tools** and what they are for, the **decisions** made (with alternatives), the **output**, and a **gate**: a check that must pass before continuing.

### Step 0 — Settle key decisions (a few days)
| Decision | Choice | Why |
|---|---|---|
| Name | "SwitchMOS" (working) | Signals a MOS-style score with switch awareness. An earlier name, "Switch Discontinuity Score", wrongly implied less change is better |
| Lead claims | Per-switch scores + fewer human labels | Most likely to hold (§10.3); the overall-score gain is less certain |
| Loanwords ("office", "phone") | Count as switches but tag them; report with and without | Linguists debate whether everyday borrowed words are true switches |
| Fully romanised Hinglish ("mujhe office late…") | Out of scope for version 1 | Script can't reveal the language; needs an extra word-level language tool |

### Step 1 — Check the data (1 week)
**What.** Confirm the amount and meaning of the data we rely on.

| Data | What it is | Why we use it |
|---|---|---|
| **SpeechArenaBench** (AI4Bharat, MIT licence) | 120,000+ human "A vs B" judgments of 7 commercial TTS systems in 10 Indian languages. We counted **4,035 mixed-language Hindi comparisons** (2,493 sentences, 198 listeners) | The only large source of human judgments of Indian mixed-language TTS |
| **HiACC** (2025) | 5.2 hours of real Hinglish from 44 speakers, with each word labelled Hindi or English | Natural switches from real people; our reference for "natural" |
| **MUCS 2021** | ~95 h Hindi–English and ~53 h Bengali–English lecture speech | More natural switches; Bengali allows a second language |

**Decisions.**
- *Count mixed-language comparisons in the other nine languages*, because testing on unseen languages (RQ4) needs enough data in each (target ≥500).
- *Interpret unusual labels*: some SpeechArenaBench answers name two systems as preferred, and 677 Hindi answers are ties. We decide how to treat them before training.
- *Re-split HiACC by speaker.* We discovered HiACC's published train/test split puts the same 24 speakers in every part. We made our own split so that no speaker appears in more than one role:

| Role | Speakers | Used for |
|---|---|---|
| Reference | 6 (3 women, 3 men) | Defining "natural switch" and building minimal pairs |
| Test | 6 (3 women, 3 men) | The human study and test clips only |
| Fine-tune | 12 | An optional side experiment (§8, optional) |

*Why this matters:* if the same person's voice were used both to build the tool and to test it, the tool could look good simply by recognising that person.

**Gate:** enough mixed-language comparisons exist for the languages we plan to test.

### Step 1.5 — Check there is room for a switch-aware model (1 week, in parallel)
**What.** Train a plain model (no switch attention) on the human comparisons. Then ask: when it gets a mixed-language comparison wrong, do switch measurements explain the mistake?

**Why.** If a plain model already handles switches, building a switch expert adds little. This check costs one week and could save months.

**Decision:** compare sentences of similar length, because mixed-language sentences are also longer and harder, which would otherwise confuse the comparison.

**Gate:** switch measurements explain a meaningful share of the plain model's errors. If not, we drop the overall-score claim and lead with per-switch scores.

### Step 2 — Check that minimal pairs are feasible (1 week)
**What.** Take a real Hinglish recording, regenerate *only* the switch region with a TTS model, and compare.

**Tools and why.**
- **IndicF5** (AI4Bharat): an open TTS model for 11 Indian languages that can regenerate part of a recording while keeping the rest ("infilling"). Chosen because it's open, Indian-language, and supports this editing mode.
- **A vocoder** turns the model's internal spectrogram into sound. Editing passes the *whole* recording through it, so we also pass the untouched original through the same vocoder. Otherwise the model would learn to spot "was processed", not "sounds unnatural".

**Decisions.**
- Measure time per edit on our GPUs (the A16 is a slow card; §9).
- **20-pair listening check:** do edited switches actually sound worse? If regenerated switches sound just as good, the pairs would teach nothing.

**Gate:** editing works and edits sound worse. Otherwise we fall back to simple audio edits (joining, pitch jumps, wrong durations), which are clearly worse by construction.

### Step 3 — Find and measure switches (2 weeks)
**What and why, sub-step by sub-step.**

| Sub-step | Tool / method | What it's for | Why this choice |
|---|---|---|---|
| Standardise audio | Resample to **16 kHz** (16,000 samples per second) and remove sound above **8 kHz** | Make all recordings comparable | HiACC was recorded at 16 kHz, which holds sound only up to 8 kHz. Synthetic voices go up to 12 kHz; without matching, the tool would detect "synthetic" from bandwidth alone |
| Equalise loudness | Scale to the same average level | Prevent quiet recordings looking like loudness jumps | — |
| Label each word's language | Script: Devanagari = Hindi, Latin = English | Find switches | Free and accurate for HiACC and SpeechArenaBench text |
| Find word timings | **uroman** (converts any script to Latin letters) + **MMS forced aligner** (Meta; given audio and its text, finds when each word is spoken) | Know *when* each switch happens | Handles 1,100+ languages without a pronunciation dictionary |
| Check timing accuracy | Hand-mark 20 switches in **Praat** (standard phonetics software) | Aligner must be accurate to ≤25 ms | Measurements are taken in ~100 ms windows; larger errors would blur them |
| Measure each boundary | Pause length; speaking speed before vs after; how stretched the switched word is; pitch jump and range (two pitch trackers must agree, to avoid errors); loudness jump; spectral "join" distance | Describe what happens at the switch | Each corresponds to a pattern reported in bilingual-speech research, or to the classic join-cost measure of seams |
| Compare with the rest of the sentence | Subtract the same measurements at ordinary word boundaries | Remove differences due to speaker, microphone, speaking style | Otherwise a naturally slow speaker would look "unnatural" everywhere |

**Gate (H1):** in real Hinglish, switches differ from ordinary boundaries in the predicted ways (at least two of: slowing before, lengthening, wider pitch). If not, the switch expert uses only learned features, not these hand-designed ones.

### Step 4 — Pre-compute (1 week)
**What.** Run the heavy processing once and save the results: word timings, switch measurements, and features from the pretrained speech model.

**Pretrained speech model (encoder).** A neural network pretrained on thousands of hours of unlabelled speech that turns audio into numerical features. We use a **multilingual** one (mHuBERT-147 or XLS-R), because the English-trained ones (e.g. WavLM) are weaker on Indian languages. We compare candidates in a small pilot.

**Why pre-compute:** our GPUs are slow; doing this once instead of every training round saves days.

### Step 5 — Build training pairs (1–2 weeks)
| Pair type | How | Teaches |
|---|---|---|
| Regenerated switch | Real clip vs same clip with the switch regenerated (both through the same vocoder) | What an unnatural switch sounds like, exactly where it is |
| Spliced | Two real segments glued at the switch | Seams |
| Flattened | Natural slowdown and pitch movement removed | "Robotic" switches |
| Exaggerated | Long pause or pitch jump inserted | Overdone switches |
| **Non-switch edit (control)** | Regenerate a non-switch word; the model must *not* prefer either version | Prevents the model from simply detecting "was edited" |

**Sources:** the 6 reference speakers and MUCS, never the 6 test speakers.

### Step 6 — Train the model (3–4 weeks)

**Components and their purpose.**
| Component | Purpose | Why |
|---|---|---|
| **SwitchLM** (small model trained only on real mixed speech) | Estimates how *surprising* each switch is compared with real speech | Needs no human labels. Published evidence shows such signals are weak alone, so we use it as one input, not the final score |
| **Switch expert** | Scores each switch from a ±0.5–1 s window | Looks only at the switch region, so problems elsewhere don't leak in |
| **Whole-clip expert** | Scores the overall recording | Captures voice quality, expressiveness, everything besides switches |
| **Artefact expert** (optional) | Looks for glitches in the spectrogram image | A lesson from UTMOSv2, whose image-based branch helped predict absolute quality |
| **Gate** | Decides how much each expert counts for this recording | A recording with many switches should lean on the switch expert; one with none should not |
| **"Worst switch" pooling** | Lets a single bad switch lower the overall score | Listeners notice one bad moment more than an average suggests |
| **Listener, language and dataset tags** | Tell the model who rated, which language pair, which dataset | UTMOS's own analysis found this the single most helpful idea |

**Training order** (training parts separately, then together, was the biggest factor in UTMOSv2's success):
1. SwitchLM on real mixed speech.
2. Switch expert on the pairs from Step 5.
3. Whole-clip and artefact experts on human comparisons.
4. Gate only, with the experts fixed.
5. Everything together, gently.

**How the model learns from comparisons.** We use the **Bradley–Terry** method: for each human "A is better than B", the model is adjusted so A's score exceeds B's. A published comparison found this works better than predicting 1–5 numbers directly. We add **Davidson's extension**, which also learns from "no preference" answers; all prior work throws these away.

**Data splits.** We keep entire TTS systems, languages, listeners, and sentences out of training, so tests measure genuine generalisation, not memory.

### Step 7 — Human listening study (2 weeks)
**Why needed:** no existing dataset rates individual switches, so without it we couldn't show our per-switch scores mean anything to people.

| Item | Plan | Why |
|---|---|---|
| Listeners | 5–8 fluent Hindi–English bilinguals, headphones, screened, paid, consenting | Native judgment of switches |
| Clips | ~500 short excerpts centred on a switch (~1.5 s), full sentence available | Focus attention on the switch |
| Which clips | Chosen where the model is *least sure*, in two or more rounds (**active learning**) | Gets more information per rating; published work shows gains from the second round |
| Tasks | Rate switch naturalness 1–5; mark where it sounds wrong; identify the word after the switch in background noise | Opinion, location, and an objective comprehension measure |
| Pilot first | 50 clips, 3 listeners; listener agreement must reach a set minimum (Krippendorff's α ≥ 0.5) | If people don't agree with each other, no tool can agree with them |

### Step 8 — Evaluate (1–2 weeks)
See §10.

### Step 9 — Release and publish (2 weeks)
- Release the model, code, and rated clips openly, installable in one command, so others can use and check it.
- Write the paper for **Interspeech**, the main international speech conference.

### Optional, in parallel — a Hinglish voice experiment
Fine-tune IndicF5 on real Hinglish conversation (the 12 "fine-tune" speakers) and check with SwitchMOS whether switching improves. This provides an extra voice to test and a practical use case. Server environment and scripts are prepared; training starts only after code review.

---

## 9. Resources and timeline

**Computing.** One server with 4 NVIDIA A16 GPUs (16 GB memory each), 480 GB RAM, 32 CPU cores, 4.6 TB disk. Each A16 is roughly one-sixth the speed of a common research GPU (RTX 3090), which is why we pre-compute features and keep the model small. The main time cost is generating edited pairs, estimated at a few days.

**People.** One researcher; 5–8 paid bilingual listeners for about two weeks.

**Timeline (part-time):**
| Weeks | Steps |
|---|---|
| 1–2 | 0, 1, 1.5, 2 (the cheap checks that decide the design) |
| 3–5 | 3, 4 |
| 6–7 | 5 |
| 8–11 | 6 |
| 12–13 | 7 |
| 14–15 | 8 |
| 16–17 | 9 |

**Total:** about 14–18 weeks.

---

## 10. How success will be judged

### 10.1 Tests
| Test | Question |
|---|---|
| With vs without switch expert | Does paying attention to switches improve agreement with humans on mixed-language recordings, without hurting single-language ones? |
| Unseen TTS systems | Does it work on voices it never trained on? |
| Unseen languages | Train on nine Indian languages, test on the tenth |
| Locating edits | Do per-switch scores point to the regenerated switches in held-out pairs? |
| Matching listeners | Do per-switch scores agree with the human switch ratings? |
| Label efficiency | How accuracy grows as we use 10%, 25%, … 100% of human comparisons |
| Robustness | Stable when volume, recording format, or word timings shift slightly |
| Standard benchmarks | A "no harm" check on the VoiceMOS 2022/2023 and SOMOS datasets. **We expect to trail UTMOS here** and say so in advance, because those datasets contain no language switches |

**Comparisons:** UTMOS, UTMOSv2, SpeechJudge, the same model without the switch expert, a trivial "longer recording wins" rule (length is a known source of false success), and the hand-designed switch measurements alone.

### 10.2 Pass criteria (fixed in advance)
- The switch expert improves agreement on mixed-language comparisons from unseen systems, confirmed statistically (paired bootstrap, p < 0.05), with no loss on single-language ones.
- Per-switch scores locate edited switches well (AUC ≥ 0.8, where 0.5 is chance and 1.0 perfect) and correlate positively and significantly with human switch ratings.

### 10.3 Honest expectations
| Claim | Expected strength |
|---|---|
| Beats UTMOS on Hindi mixed speech | High, but mainly because we train on the right data |
| Per-switch scores locate problems | Fairly high |
| Needs fewer human labels | Fairly high |
| Per-switch scores match listeners | Moderate |
| Switch expert improves the overall score | Uncertain; a similar published idea gained little |
| Works on unseen languages | Unknown until data is counted |

If the overall-score improvement doesn't appear, that is itself a publishable finding ("listeners' overall judgments do not hinge on switches"), and the per-switch tool, the minimal-pair method, and the rated dataset remain contributions.

---

## 11. Risks and fallbacks

| Risk | Fallback |
|---|---|
| Model learns *which company* made the voice rather than quality (only 7 systems in the data) | Test on systems held out of training; add our own voices as extra tests |
| Model learns to spot editing instead of unnaturalness | Same vocoder on both versions; "non-switch edit" controls; listening check |
| Regenerated switches don't sound worse | Use simple audio edits that are worse by construction |
| Real switches show no measurable pattern (H1 fails) | Switch expert relies on learned features only |
| Few mixed-language comparisons in some languages | Test only languages with enough data |
| Someone publishes first (the dataset is public) | Move quickly; the per-switch method and minimal pairs remain distinct |
| Licence limits on some speech corpora (non-commercial) | Keep them out of the released model's training, or release it for research use only |

---

## 12. Out of scope, and what each item means

| Out of scope | What it means | Why excluded |
|---|---|---|
| **Detecting AI vs human speech** ("deepfake detection") | Deciding whether a real person or a computer produced a recording | A different research field. A synthetic voice can sound fully natural; we measure naturalness, not origin |
| **Building a new TTS system** | Creating a new voice generator | We measure voices. The optional IndicF5 experiment adapts an existing model only as a test case |
| **Fully romanised Hinglish** ("mujhe office ke liye late ho gaya") | Hindi typed in English letters | Script can no longer reveal the language; needs a separate word-level language identifier (planned for version 2) |
| **Speech recognition** (speech → text) | Converting audio to text | Different task; used only as a helper and a downstream application |
| **Replacing UTMOS for single-language speech** | Becoming the general-purpose quality score | UTMOS remains appropriate there; we complement it |
| **Audio quality problems unrelated to speech** (background noise, microphones) | Recording-condition issues | Covered by existing tools (e.g. DNSMOS) |
| **Absolute 1–5 scores** as the main output | Predicting the exact MOS number | We learn from comparisons, which rank well; calibration to 1–5 is optional |
| **Languages beyond Indian languages + English** in this project | e.g. Spanish–English, Mandarin–English | Planned for a later stage once the approach is proven (§13) |
| **Emotion, speaker identity, pronunciation accuracy** | Other aspects of speech quality | Measured by other tools; reported alongside ours |
| **Children's speech** | HiACC includes children | Different acoustics; kept for later robustness checks |

---

## 13. Beyond this project

1. **Stage 1 (this proposal): Hinglish.** A validated tool and paper.
2. **Stage 2: Indian languages mixed with English.** All 10 languages in SpeechArenaBench; the unseen-language test.
3. **Stage 3: Universal.** Other language pairs (Spanish–English, Mandarin–English), and other local trouble spots in synthetic speech: names, numbers, emphasised words, joins between chunks in long recordings.

The long-term aim: UTMOS reports **how natural** a recording is overall; SwitchMOS reports **where** it isn't.

---

## 14. Glossary

| Term | Meaning |
|---|---|
| **Text-to-speech (TTS)** | Software that turns written text into spoken audio |
| **Code-switching** | Changing language within a conversation or sentence |
| **Switch point** | The place in a sentence where the language changes |
| **Hinglish** | Hindi and English mixed in everyday speech |
| **Devanagari / Latin script** | The writing systems for Hindi / English |
| **MOS (Mean Opinion Score)** | The average of listeners' 1–5 ratings |
| **Pairwise preference** | A listener hears two recordings and picks the better one (or says "no preference") |
| **UTMOS** | A widely used automatic predictor of MOS (2022) |
| **SpeechJudge** | A large automatic judge trained on human comparisons, including Mandarin–English mixed speech (2026) |
| **SpeechArenaBench** | A public collection of 120,000+ human comparisons of TTS in 10 Indian languages |
| **HiACC** | A public corpus of real Hinglish speech with each word labelled by language |
| **MUCS** | Public Hindi–English and Bengali–English speech from a 2021 challenge |
| **Neural network / model** | A computer program that learns patterns from examples |
| **Training / testing** | Learning from examples / checking on examples not seen during learning |
| **Encoder (pretrained speech model)** | A neural network that turns audio into numerical features, pretrained on large amounts of unlabelled speech |
| **Forced alignment** | Finding when each word in a known text is spoken in the audio |
| **MMS / uroman** | Meta's multilingual forced aligner / a tool that writes any script in Latin letters |
| **Sampling rate (16 kHz)** | How many times per second sound is measured; limits the highest pitch recorded |
| **Pitch (F0)** | How high or low the voice is |
| **Seam** | An audible join, as if two recordings were glued together |
| **Vocoder** | The part of a TTS system that turns an internal representation into sound |
| **Minimal pair** | Two versions of a recording that differ only in one small part |
| **Infilling** | Regenerating one part of a recording while keeping the rest |
| **Expert / gate** | A specialised sub-model / a component deciding how much each expert counts |
| **Bradley–Terry** | A method for learning scores from "A is better than B" judgments |
| **Davidson's extension** | A variant that also learns from "no preference" answers |
| **Active learning** | Choosing which examples humans should label, to learn the most per label |
| **Correlation** | How closely two sets of numbers rise and fall together (1 = perfectly, 0 = unrelated) |
| **AUC** | How well a score separates two groups (0.5 = chance, 1 = perfect) |
| **Krippendorff's α** | How much human raters agree with each other |
| **Bootstrap / p-value** | Statistical tools to check that a result isn't due to chance |
| **GPU** | A processor specialised for the arithmetic of neural networks |
| **Interspeech** | The main international conference on speech research |

---

## 15. Key references

- Saeki et al., *UTMOS*, VoiceMOS Challenge 2022 (arXiv 2204.02152); Baba et al., *UTMOSv2* (arXiv 2409.09305).
- Zhang et al., *SpeechJudge*, ICLR 2026 (arXiv 2511.07931).
- Anand et al., *Preferences of a Voice-First Nation* / SpeechArenaBench, Interspeech 2026 (arXiv 2604.21481).
- Singh, Singh & Kadyan, *HiACC*, Data in Brief 2025 (doi 10.1016/j.dib.2025.111886).
- Li et al., *DAMOS* (arXiv 2608.21176); Kuhlmann et al., frame-level quality prediction, Interspeech 2025 (arXiv 2508.10374).
- MOS-RMBench (arXiv 2510.00743) — Bradley–Terry vs regression for quality judges.
- Rao et al., prosodic cues in Hindi–English code-switched discourse, Interspeech 2018; Fricke, Kroll & Dussias 2016; Olson 2016 — natural switch patterns.
- Hunt & Black 1996 — join cost in concatenative synthesis.
- Pratap et al., MMS (arXiv 2305.13516) — multilingual forced alignment.
