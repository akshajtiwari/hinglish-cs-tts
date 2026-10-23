"""Step 3 pilot, part 3: train a small scoring head on the cached features of one encoder and check it on validation.

The model (only this small head is trained; the encoder stays frozen):
  learned weights over the encoder layers -> weighted sum of each layer's (mean, std) -> 2-layer network -> one score.
  Rating clips also get a per-dataset scale and offset, because MOS (1-5) and MUSHRA page z-scores use different scales.
Losses, with equal weight: mean squared error on the rating clips (BVCC, SOMOS, MANGO) and the Bradley-Terry loss on
the SpeechJudge pairs (the chance that clip A beats clip B is sigmoid(score A - score B)).
Model selection (owner decision 2026-10-22, docs/plan/20_evaluation_spec.md): after every epoch, the plain average of
SpeechJudge val accuracy, BVCC val SRCC, SOMOS val SRCC and MANGO val SRCC; the best epoch is kept.
Only train and val data are read. Test splits and SpeechArenaBench are never read here.
Writes <out>/best_head.pt, <out>/history.json, <out>/summary.json and a run manifest in <out>/runs/.

Run (server):
  PYTHONPATH=src ~/projects/baselines-venv/bin/python scripts/step3_pilot/train_pilot.py \
      --data ~/projects/hinglish-cs-tts/datasets/_train --encoder xlsr --seed 0 \
      --out ~/projects/hinglish-cs-tts/analysis/step3/pilot_xlsr_seed0 --device cuda:0
"""
import argparse
from pathlib import Path

import numpy
import pandas as pd
import torch
import torch.nn.functional as F

from switchmos import files
from switchmos import pilot
from switchmos import run_log
from switchmos.eval import metrics

EPOCHS = 20
BATCH_SIZE = 64
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4
HIDDEN = 256
RATING_DATASETS = ["bvcc", "somos", "mango"]


class PilotHead(torch.nn.Module):
    """Learned layer weights, a small network, and a scale and offset per rating dataset."""

    def __init__(self, n_layers, n_features):
        super().__init__()
        self.layer_logits = torch.nn.Parameter(torch.zeros(n_layers))
        self.network = torch.nn.Sequential(
            torch.nn.Linear(n_features, HIDDEN),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.1),
            torch.nn.Linear(HIDDEN, 1),
        )
        self.scale = torch.nn.Parameter(torch.ones(len(RATING_DATASETS)))
        self.offset = torch.nn.Parameter(torch.zeros(len(RATING_DATASETS)))

    def score(self, features):
        """One naturalness score per clip. features: clips x layers x features."""
        weights = torch.softmax(self.layer_logits, dim=0)
        pooled = (features * weights[None, :, None]).sum(dim=1)
        return self.network(pooled)[:, 0]

    def rating(self, features, dataset_ids):
        """The score moved onto the scale of each clip's own rating dataset."""
        return self.score(features) * self.scale[dataset_ids] + self.offset[dataset_ids]


def load_features(folder):
    """All cached parts of one encoder: (list of clip keys, array clips x layers x features in float16)."""
    keys = []
    arrays = []
    for part_path in sorted(Path(folder).glob("part_*.npz")):
        data = numpy.load(part_path)
        if len(data["keys"]) == 0:
            continue
        keys.extend(data["keys"].tolist())
        arrays.append(data["stats"])
    return keys, numpy.concatenate(arrays)


def feature_normaliser(stats, train_rows):
    """Mean and standard deviation of every (layer, feature) over the training clips, computed in chunks."""
    total = numpy.zeros(stats.shape[1:], dtype="float64")
    total_squares = numpy.zeros(stats.shape[1:], dtype="float64")
    for start in range(0, len(train_rows), 5000):
        chunk = stats[train_rows[start:start + 5000]].astype("float64")
        total += chunk.sum(axis=0)
        total_squares += (chunk ** 2).sum(axis=0)
    mean = total / len(train_rows)
    std = numpy.sqrt(numpy.maximum(total_squares / len(train_rows) - mean ** 2, 1e-10))
    return mean.astype("float32"), std.astype("float32")


def batch_tensor(stats, rows, mean, std, device):
    """The normalised features of some clips as a float32 tensor."""
    x = (stats[rows].astype("float32") - mean) / std
    return torch.from_numpy(x).to(device)


def score_rows(model, stats, rows, mean, std, device):
    """The model's score for every row (no training), as a list of floats."""
    model.eval()
    scores = []
    with torch.no_grad():
        for start in range(0, len(rows), 256):
            batch = batch_tensor(stats, rows[start:start + 256], mean, std, device)
            scores.extend(model.score(batch).cpu().tolist())
    return scores


def validation_metrics(model, stats, mean, std, device, val_pairs, val_ratings, row_of_key):
    """SpeechJudge val accuracy and the val SRCC of each rating dataset, plus the selection score."""
    results = {}
    rows_a = numpy.array([row_of_key[key] for key in val_pairs["key_a"]])
    rows_b = numpy.array([row_of_key[key] for key in val_pairs["key_b"]])
    scores_a = score_rows(model, stats, rows_a, mean, std, device)
    scores_b = score_rows(model, stats, rows_b, mean, std, device)
    results["speechjudge_val_accuracy"] = metrics.pairwise_accuracy(scores_a, scores_b, list(val_pairs["label"]))
    for dataset in ["bvcc", "somos"]:
        part = val_ratings[val_ratings["dataset"] == dataset]
        rows = numpy.array([row_of_key[key] for key in part["key"]])
        results[f"{dataset}_val_srcc"] = metrics.spearman(score_rows(model, stats, rows, mean, std, device), list(part["target"]))
    # MANGO: SRCC inside each language, then the average over the languages in val
    mango = val_ratings[val_ratings["dataset"] == "mango"]
    per_language = []
    for lang in sorted(mango["lang"].unique()):
        part = mango[mango["lang"] == lang]
        rows = numpy.array([row_of_key[key] for key in part["key"]])
        value = metrics.spearman(score_rows(model, stats, rows, mean, std, device), list(part["target"]))
        results[f"mango_{lang}_val_srcc"] = value
        per_language.append(value)
    if len(per_language) == 0:
        results["mango_val_srcc"] = float("nan")
    else:
        results["mango_val_srcc"] = sum(per_language) / len(per_language)
    results["selection"] = pilot.selection_score(results)
    return results


def save_checkpoint(path, model, mean, std, encoder, epoch):
    """Save the head and the feature normaliser atomically."""
    tmp = path.with_name(path.name + ".tmp")
    torch.save({"model": model.state_dict(), "mean": mean, "std": std, "encoder": encoder, "epoch": epoch,
                "rating_datasets": RATING_DATASETS}, tmp)
    tmp.replace(path)


def main():
    parser = argparse.ArgumentParser(description="Train the pilot head on one encoder's cached features.")
    parser.add_argument("--data", required=True, help="the _train folder from prepare_training_data.py")
    parser.add_argument("--encoder", required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", required=True)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    data = Path(args.data).expanduser()
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    device = args.device
    if device.startswith("cuda") and not torch.cuda.is_available():
        device = "cpu"

    config = {"encoder": args.encoder, "epochs": EPOCHS, "batch_size": BATCH_SIZE, "learning_rate": LEARNING_RATE,
              "weight_decay": WEIGHT_DECAY, "hidden": HIDDEN, "device": device}
    run_dir = run_log.start_run(f"pilot_{args.encoder}", config, args.seed, root=out / "runs")
    rng = numpy.random.default_rng(args.seed)

    keys, stats = load_features(data / "features" / args.encoder)
    row_of_key = {}
    for row, key in enumerate(keys):
        row_of_key[key] = row
    ratings = pd.read_csv(data / "ratings.csv")
    pairs = pd.read_csv(data / "pairs.csv")
    # clips whose features failed are left out (they are listed in the encoder's errors.csv)
    ratings = ratings[ratings["key"].isin(row_of_key)]
    pairs = pairs[pairs["key_a"].isin(row_of_key) & pairs["key_b"].isin(row_of_key)]
    train_ratings = ratings[ratings["split"] == "train"]
    val_ratings = ratings[ratings["split"] == "val"]
    train_pairs = pairs[pairs["split"] == "train"]
    val_pairs = pairs[pairs["split"] == "val"]
    print(f"{len(keys)} clips with features; train: {len(train_ratings)} rated clips, {len(train_pairs)} pairs; "
          f"val: {len(val_ratings)} rated clips, {len(val_pairs)} pairs; device {device}", flush=True)

    rating_rows = numpy.array([row_of_key[key] for key in train_ratings["key"]])
    dataset_ids = torch.tensor([RATING_DATASETS.index(name) for name in train_ratings["dataset"]], device=device)
    rating_targets = torch.tensor(list(train_ratings["target"]), dtype=torch.float32, device=device)
    pair_rows_a = numpy.array([row_of_key[key] for key in train_pairs["key_a"]])
    pair_rows_b = numpy.array([row_of_key[key] for key in train_pairs["key_b"]])
    a_won = torch.tensor([1.0 if label == "A" else 0.0 for label in train_pairs["label"]], device=device)

    train_clip_rows = numpy.unique(numpy.concatenate([rating_rows, pair_rows_a, pair_rows_b]))
    mean, std = feature_normaliser(stats, train_clip_rows)
    model = PilotHead(stats.shape[1], stats.shape[2]).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)

    history = []
    best = None
    for epoch in range(1, EPOCHS + 1):
        model.train()
        pair_order = rng.permutation(len(pair_rows_a))
        rating_order = rng.permutation(len(rating_rows))
        rating_position = 0
        total_pair_loss = 0.0
        total_rating_loss = 0.0
        n_steps = len(pair_order) // BATCH_SIZE
        for step in range(n_steps):
            pair_batch = pair_order[step * BATCH_SIZE:(step + 1) * BATCH_SIZE]
            # the rating clips are fewer than the pairs, so their order is reshuffled whenever it runs out
            if rating_position + BATCH_SIZE > len(rating_order):
                rating_order = rng.permutation(len(rating_rows))
                rating_position = 0
            rating_batch = rating_order[rating_position:rating_position + BATCH_SIZE]
            rating_position += BATCH_SIZE

            score_a = model.score(batch_tensor(stats, pair_rows_a[pair_batch], mean, std, device))
            score_b = model.score(batch_tensor(stats, pair_rows_b[pair_batch], mean, std, device))
            pair_loss = F.binary_cross_entropy_with_logits(score_a - score_b, a_won[pair_batch])
            predicted = model.rating(batch_tensor(stats, rating_rows[rating_batch], mean, std, device),
                                     dataset_ids[rating_batch])
            rating_loss = F.mse_loss(predicted, rating_targets[rating_batch])
            loss = pair_loss + rating_loss
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_pair_loss += pair_loss.item()
            total_rating_loss += rating_loss.item()

        val = validation_metrics(model, stats, mean, std, device, val_pairs, val_ratings, row_of_key)
        val["epoch"] = epoch
        val["train_pair_loss"] = total_pair_loss / n_steps
        val["train_rating_loss"] = total_rating_loss / n_steps
        history.append(val)
        files.save_json(out / "history.json", history)
        print(f"epoch {epoch}: selection {val['selection']:.4f} (SpeechJudge {val['speechjudge_val_accuracy']:.4f}, "
              f"BVCC {val['bvcc_val_srcc']:.4f}, SOMOS {val['somos_val_srcc']:.4f}, MANGO {val['mango_val_srcc']:.4f})",
              flush=True)
        if val["selection"] is not None and (best is None or val["selection"] > best["selection"]):
            best = val
            save_checkpoint(out / "best_head.pt", model, mean, std, args.encoder, epoch)

    if best is None:
        raise SystemExit("no epoch had a complete selection score; see history.json")
    weights = torch.softmax(model.layer_logits, dim=0).detach().cpu().tolist()
    summary = {"encoder": args.encoder, "seed": args.seed, "best_epoch": best["epoch"], "best": best,
               "layer_weights_last_epoch": weights}
    files.save_json(out / "summary.json", summary)
    run_log.finish_run(run_dir, metrics=best, outputs=[str(out / "best_head.pt"), str(out / "summary.json")])
    print(f"best epoch {best['epoch']}: selection {best['selection']:.4f}", flush=True)


if __name__ == "__main__":
    main()
