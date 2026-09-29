# 07 — Using SDS after it's built

## 7.1 What a user runs

Command line:
```bash
sds score --audio out/*.wav --transcripts out/transcripts.tsv --pack hinglish-v1 --out results.jsonl
sds compare results_sysA.jsonl results_sysB.jsonl      # paired comparison with CIs
```

Python:
```python
from sds import Scorer
s = Scorer(pack="hinglish-v1")
r = s.score("utt_0042.wav", "मुझे office के लिए late हो गया")
print(r.in_range_rate, r.sds_switch, r.diagnosis)
```

Backend: exactly the core engine in 03, with the frozen pack. Nothing is trained at use time.

## 7.2 Typical uses

| Use | How |
|---|---|
| **Compare TTS systems** | Same sentences, same reference voice, every system. Report in-range rate and the three parts with CIs, next to CER and speaker similarity |
| **Pick a fine-tune checkpoint** | Score each saved checkpoint on a fixed dev sentence set; choose best in-range rate subject to CER not worsening |
| **Debug a system** | Read the diagnosis counts: mostly "under" means flat switches; high seam means splicing artifacts |
| **Filter synthetic training data** | Before using synthetic Hinglish for ASR training, drop clips with high seam probability or low in-range rate |
| **Track progress over time** | Same pack version, same sentence set, every release |

## 7.3 Rules for fair use

- Only compare numbers computed with the **same pack version**.
- Hold sentences, reference voice, and text normalization fixed across systems.
- Report SDS **alongside** CER, speaker similarity, and some human or MOS measure.
- Don't compare a system's SDS on one sentence set with another system's on a different set.
- Don't use SDS as a training reward without checking for gaming (e.g. a model learning to insert pauses).

## 7.4 Using it for another language pair

The engine is language-independent; the reference pack isn't.
1. Collect natural code-switched speech for the pair, with transcripts.
2. Provide per-word language tags if both languages use the same script (e.g. Spanish–English).
3. Run the building steps in 04 to create a new pack, e.g. `zh-en-v1`.
4. The seam part transfers as-is; the switch part must be re-validated with listeners of that pair.
