# 03 — The core engine: what runs every time

The core is a fixed pipeline plus a frozen **reference pack**. The pipeline code never changes between uses; the reference pack only changes with a new version number.

## 3.1 Frozen vs computed

| Frozen (built once, shipped in the reference pack) | Computed every call |
|---|---|
| Feature settings: window lengths, frame rate, pitch range, thresholds | Resampled audio |
| Group definitions: direction × position | Word timings from the aligner |
| Per-group mean vector and covariance of natural switch contrasts | Boundary list and types |
| Same for natural ordinary boundaries | Feature values per boundary |
| "Natural marking direction" vector per group | Contrasts against the clip's ordinary boundaries |
| Seam classifier weights | Distances, percentiles, seam probability |
| Percentile lookup tables (distance → percentile) | Aggregates and diagnosis |
| Aligner model version, uroman version | |

## 3.2 The pipeline, stage by stage

```
audio + transcript
   │
   ├─ 1. NORMALIZE     resample to 16 kHz, low-pass 8 kHz, loudness-normalize
   ├─ 2. TOKENIZE TEXT split words; tag language by script (or use given tags)
   ├─ 3. ROMANIZE      uroman copy of the transcript, for the aligner only
   ├─ 4. ALIGN         MMS forced alignment → start/end per word; confidence per word
   ├─ 5. BOUNDARIES    each adjacent pair → switch or ordinary; direction; position
   │                   (position = phrase boundary if pause ≥150 ms or punctuation, else mid-phrase)
   ├─ 6. FEATURES      pause, rate, lengthening, pitch jump/range/slope, loudness jump, spectral jump
   ├─ 7. CONTRAST      switch features minus the clip's ordinary-boundary features
   ├─ 8. SCORE         (uses the frozen reference pack)
   │      8a switch:   Mahalanobis distance to matching group → percentile; project on marking
   │                   direction → under / natural / over
   │      8b boundary: same for ordinary boundaries, absolute features
   │      8c seam:     logistic regression on jump features → probability
   ├─ 9. AGGREGATE     clip → system; bootstrap confidence intervals
   └─ 10. DIAGNOSE     plain-language explanation from the largest feature deviations
```

Stages 1–7 are measurement. Stage 8 is the only place the reference pack is used. Stage 10 is what makes SDS explainable.

## 3.3 Pseudocode

```python
def score_clip(audio, transcript, pack):
    wav   = normalize(audio, sr=16000, lowpass=8000)
    words = tokenize(transcript)                        # [(text, lang)]
    times = mms_align(wav, uroman(words))               # [(start, end, conf)]
    bnds  = make_boundaries(words, times)               # switch/ordinary, direction, position
    feats = [extract(wav, b) for b in bnds]             # dict per boundary
    ords  = [f for f, b in zip(feats, bnds) if b.type == "ordinary"]
    out = []
    for f, b in zip(feats, bnds):
        row = {"boundary": b, "features": f}
        row["seam_prob"] = pack.seam.predict(f.jumps)
        if b.type == "switch":
            c = contrast(f, ords)                        # z-score vs this clip's ordinary boundaries
            g = pack.groups[(b.direction, b.position)]
            d = mahalanobis(c, g.mean, g.cov)
            row["switch_pct"] = g.pct_table(d)
            row["marking"] = classify(project(c, g.marking_dir), g.band)
        else:
            g = pack.ordinary
            row["boundary_pct"] = g.pct_table(mahalanobis(f.absolute, g.mean, g.cov))
        row["diagnosis"] = explain(row, pack)
        out.append(row)
    return summarize(out)
```

## 3.4 Guarantees the core must keep

- **Deterministic:** same input, same output.
- **Invariant to** loudness scaling, input sample rate, leading/trailing silence.
- **Stable under** ±20 ms boundary jitter (the aligner's typical error).
- **Honest about failure:** low alignment confidence or missing pitch → the boundary is marked "not scored", never silently scored as zero.

## 3.5 Cost

CPU only. Alignment dominates: roughly a few clips per second on a laptop. A 300-clip system evaluation takes minutes.

## 3.6 SwitchMOS inference (update 2026-09-29)

SwitchMOS runs stages 1–7 above unchanged (normalize, text, romanize, align, boundaries, features, contrast), then passes the audio through a multilingual SSL encoder and the trained heads. Stage 8's frozen reference pack is still used, for the SDS diagnostics attached to each switch. Switch detection gains a word-level language-ID fallback for shared-script pairs. GPU optional; a CPU run is slower but works. Architecture: `13_switchmos.md` §13.5.
