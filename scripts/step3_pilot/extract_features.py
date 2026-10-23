"""Step 3 pilot, part 2: encode every clip with one frozen speech encoder and save per-layer statistics.

For each clip: load the audio (mono, 16 kHz, at most 30 seconds), run the encoder, and for every hidden layer keep the
mean and the standard deviation over time. The encoder itself is never trained.
Saved in parts of 1,000 clips (float16):
  <out>/part_00000.npz    keys (clip keys) and stats (clips x layers x 2*hidden size)
  <out>/errors.csv        clips that could not be read or encoded
  <out>/clips_used.csv    the clip list of the first run; a later run refuses a different list
A part that already exists is skipped, so the job can be stopped and started again (the server shuts down every evening).
Several copies may run at the same time on the same --out folder: each claims a free part (claim_00000 files).

Run (server):
  PYTHONPATH=src ~/projects/baselines-venv/bin/python scripts/step3_pilot/extract_features.py --encoder xlsr \
      --clips ~/projects/hinglish-cs-tts/datasets/_train/clips.csv \
      --out ~/projects/hinglish-cs-tts/datasets/_train/features/xlsr --device cuda:0
"""
import argparse
import csv
import time
from pathlib import Path

import numpy
import pandas as pd
import torch

from switchmos import files
from switchmos.audio import load_audio

# the three multilingual encoders compared in the pilot (owner decision 2026-10-22)
ENCODERS = {
    "xlsr": "facebook/wav2vec2-xls-r-300m",
    "mhubert": "utter-project/mHuBERT-147",
    "w2vbert": "facebook/w2v-bert-2.0",
}
SAMPLE_RATE = 16000
# shortcut: clips are cut at 30 s to bound memory; only a few SpeechJudge clips are longer, revisit if that changes
MAX_SECONDS = 30
PART_SIZE = 1000


def load_encoder(name, device):
    """The feature extractor (audio to model input) and the frozen encoder."""
    from transformers import AutoFeatureExtractor
    from transformers import AutoModel
    model_id = ENCODERS[name]
    extractor = AutoFeatureExtractor.from_pretrained(model_id)
    model = AutoModel.from_pretrained(model_id).to(device).eval()
    return extractor, model


def layer_statistics(extractor, model, wav, device):
    """Mean and standard deviation over time of every hidden layer: an array of layers x (2 * hidden size)."""
    inputs = extractor(wav, sampling_rate=SAMPLE_RATE, return_tensors="pt")
    model_inputs = {}
    for name in inputs:
        model_inputs[name] = inputs[name].to(device)
    with torch.no_grad():
        outputs = model(**model_inputs, output_hidden_states=True)
    layers = torch.stack(outputs.hidden_states)[:, 0]      # layers x time x hidden
    mean = layers.mean(dim=1)
    std = layers.std(dim=1)
    return torch.cat([mean, std], dim=1).float().cpu().numpy().astype("float16")


def check_clip_list(clips, out):
    """Save the clip list on the first run; stop if a later run gets a different list (the parts would not match)."""
    used = out / "clips_used.csv"
    if not used.exists():
        clips[["key", "path"]].to_csv(used, index=False)
        return
    previous = pd.read_csv(used)
    if list(previous["key"]) != list(clips["key"]):
        raise SystemExit(f"{used} holds a different clip list; use a new --out folder")


def main():
    parser = argparse.ArgumentParser(description="Cache per-layer statistics of one frozen encoder.")
    parser.add_argument("--encoder", required=True, choices=list(ENCODERS))
    parser.add_argument("--clips", required=True, help="clips.csv from prepare_training_data.py")
    parser.add_argument("--out", required=True)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    clips = pd.read_csv(args.clips)
    check_clip_list(clips, out)
    device = args.device
    if device.startswith("cuda") and not torch.cuda.is_available():
        device = "cpu"
    extractor, model = load_encoder(args.encoder, device)
    n_parts = (len(clips) + PART_SIZE - 1) // PART_SIZE
    print(f"{args.encoder}: {len(clips)} clips in {n_parts} parts, device {device}", flush=True)

    error_path = out / "errors.csv"
    new_error_file = not error_path.exists()
    start_time = time.time()
    with open(error_path, "a", newline="") as error_file:
        errors = csv.writer(error_file)
        if new_error_file:
            errors.writerow(["key", "error"])
        # several copies can run at once (on GPUs and on the CPU): each claims the next unfinished part,
        # so faster copies simply do more parts; a copy stops when no part is left to claim
        while True:
            worked = False
            for part_number in range(n_parts):
                part_path = out / f"part_{part_number:05d}.npz"
                if part_path.exists():
                    continue
                claim_path = out / f"claim_{part_number:05d}"
                if not files.claim(claim_path):
                    continue
                if part_path.exists():          # another copy finished it between the two checks
                    claim_path.unlink(missing_ok=True)
                    continue
                part = clips.iloc[part_number * PART_SIZE:(part_number + 1) * PART_SIZE]
                keys = []
                stats = []
                for key, path in zip(part["key"], part["path"]):
                    try:
                        wav, sr = load_audio(path, target_sr=SAMPLE_RATE)
                        wav = wav[:MAX_SECONDS * SAMPLE_RATE]
                        stats.append(layer_statistics(extractor, model, wav, device))
                        keys.append(key)
                    except Exception as error:
                        errors.writerow([key, f"{type(error).__name__}: {str(error)[:200]}"])
                        error_file.flush()
                if len(stats) == 0:
                    stats_array = numpy.zeros((0, 1, 1), dtype="float16")      # every clip of this part failed
                else:
                    stats_array = numpy.stack(stats)
                # the temporary name must not match part_*.npz, or a reader could pick up a half-written file
                tmp = out / f"unfinished_part_{part_number:05d}.npz"
                with open(tmp, "wb") as f:
                    numpy.savez(f, keys=numpy.array(keys), stats=stats_array)
                tmp.replace(part_path)
                minutes = (time.time() - start_time) / 60
                print(f"  part {part_number + 1}/{n_parts} saved ({len(keys)} clips), {minutes:.1f} min so far", flush=True)
                claim_path.unlink(missing_ok=True)
                worked = True
            if not worked:
                break
    print(f"{args.encoder}: done", flush=True)


if __name__ == "__main__":
    main()
