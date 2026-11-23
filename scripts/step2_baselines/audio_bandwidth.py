"""Effective bandwidth of every SAB vote clip: the frequency below which 99% of the clip's spectral energy lies.

Listeners hear each clip at its own sample rate (Sonic 3 is 44.1 kHz, the others 24 kHz), while all four judges
resample to 16 kHz and so never see energy above 8 kHz. This measures how much each system has up there.
Method: 2048-sample Hann frames with hop 1024 at the clip's own rate, power spectra summed over the frames whose
energy is within 35 dB of the loudest frame (as in collect_failure_evidence.measure), then the 99% point of the
cumulative sum. Also saved: the share of energy above 8 kHz.

Run (server, tmux):
  PYTHONPATH=src ~/projects/baselines-venv/bin/python scripts/step2_baselines/audio_bandwidth.py \\
      --votes ~/projects/hinglish-cs-tts/datasets/_exam/votes_speecharena.csv \\
      --out ~/projects/hinglish-cs-tts/analysis/step2/cues/audio_bandwidth.csv
"""
import argparse
import csv
from pathlib import Path

import numpy

from switchmos import files
from switchmos.audio import load_audio


def bandwidth(wav, sr, frame=2048, hop=1024):
    """(frequency in Hz below which 99% of the energy lies, share of energy above 8 kHz)."""
    if len(wav) < frame:
        wav = numpy.pad(wav, (0, frame - len(wav)))
    window = numpy.hanning(frame)
    spectra = []
    energies = []
    for start in range(0, len(wav) - frame + 1, hop):
        piece = wav[start:start + frame]
        spectra.append(numpy.abs(numpy.fft.rfft(piece * window)) ** 2)
        energies.append(float(numpy.sqrt(numpy.mean(piece ** 2))))
    energies = numpy.array(energies)
    keep = energies > energies.max() * 10 ** (-35 / 20)
    power = numpy.array(spectra)[keep].sum(axis=0)
    freqs = numpy.fft.rfftfreq(frame, 1 / sr)
    cumulative = numpy.cumsum(power) / power.sum()
    edge = float(freqs[numpy.searchsorted(cumulative, 0.99)])
    above_8k = float(power[freqs > 8000].sum() / power.sum())
    return edge, above_8k


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--votes", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    paths = set()
    with open(args.votes) as f:
        for row in csv.DictReader(f):
            if row["audio_status"] == "ok":
                paths.add(row["path_a"])
                paths.add(row["path_b"])
    lines = ["path,bandwidth_hz,energy_above_8k"]
    for path in sorted(paths):
        wav, sr = load_audio(path)
        edge, above_8k = bandwidth(wav, sr)
        lines.append(f"{path},{edge:.1f},{above_8k:.6f}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    files.save_text(args.out, "\n".join(lines) + "\n")
    print(f"{len(paths)} clips -> {args.out}")


if __name__ == "__main__":
    main()
