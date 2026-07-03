#!/usr/bin/env python3
"""analyze_audio — step 1 of the kinetic-typography pipeline.

Extracts the rhythm/energy/structure features the compositor keys animations off
and writes them as ``beats.json``:

    tempo (bpm), beats, downbeats, percussive onsets, a loudness envelope, and
    approximate song sections.

Usage:
    python3 analyze_audio.py song.wav --out beats.json [--downbeat-meter 4]
                                      [--hop 512] [--energy-hz 10] [--sr 22050]

librosa does the DSP; it is imported lazily so ``--help`` and argument parsing
work without it. Install the runtime deps with:  pip install librosa soundfile
"""

from __future__ import annotations

import argparse
import json
import sys


def _round_list(xs, nd=3):
    return [round(float(x), nd) for x in xs]


def analyze(path, sr=None, hop=512, meter=4, energy_hz=10):
    """Return the beats.json dict for an audio file. Imports librosa lazily."""
    try:
        import numpy as np
        import librosa
    except ImportError as e:  # pragma: no cover - depends on runtime env
        raise SystemExit(
            f"missing dependency: {e.name}. Install with: pip install librosa soundfile"
        )

    y, sr = librosa.load(path, sr=sr, mono=True)
    if y.size == 0:
        raise SystemExit(f"error: {path} decoded to empty audio")
    duration = float(librosa.get_duration(y=y, sr=sr))

    # --- tempo + beats -----------------------------------------------------
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    tempo, beat_frames = librosa.beat.beat_track(
        onset_envelope=onset_env, sr=sr, hop_length=hop)
    bpm = round(float(np.atleast_1d(tempo)[0]), 2)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop)

    # --- downbeats: pick the beat phase with the most onset strength -------
    downbeat_times = []
    if len(beat_frames) >= meter:
        safe = beat_frames[beat_frames < len(onset_env)]
        strength = onset_env[safe]
        best_phase, best_sum = 0, -1.0
        for phase in range(meter):
            s = float(strength[phase::meter].sum())
            if s > best_sum:
                best_sum, best_phase = s, phase
        downbeat_times = beat_times[best_phase::meter]

    # --- percussive onsets (drum hits) -------------------------------------
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr, hop_length=hop, backtrack=True)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop)

    # --- loudness envelope, resampled to energy_hz -------------------------
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    rms_t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    step = 1.0 / energy_hz
    grid = np.arange(0.0, duration, step)
    rms_grid = np.interp(grid, rms_t, rms)
    peak = float(rms_grid.max()) or 1.0
    energy = [{"t": round(float(t), 3), "rms": round(float(v) / peak, 4)}
              for t, v in zip(grid, rms_grid)]

    # --- approximate sections via chroma self-similarity -------------------
    sections = _sections(y, sr, hop, duration, np, librosa)

    return {
        "duration": round(duration, 3),
        "bpm": bpm,
        "beats": _round_list(beat_times),
        "downbeats": _round_list(downbeat_times),
        "onsets": _round_list(onset_times),
        "energy": energy,
        "sections": sections,
    }


def _sections(y, sr, hop, duration, np, librosa):
    """Coarse A/B/C section labels from chroma similarity (approximate)."""
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    except Exception:
        return []
    T = chroma.shape[1]
    if T < 4:
        return [{"start": 0.0, "end": round(duration, 3), "label": "A"}]
    k = max(2, min(12, int(round(duration / 20.0))))
    bounds = sorted(set([0] + list(librosa.segment.agglomerative(chroma, k)) + [T]))
    ranges = [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)
              if bounds[i + 1] > bounds[i]]

    def cos(a, b):
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        return float(a @ b / (na * nb)) if na and nb else 0.0

    centroids, out = [], []
    next_label = 0
    for a, b in ranges:
        feat = chroma[:, a:b].mean(axis=1)
        label, best = None, 0.88
        for lab, c in centroids:
            s = cos(feat, c)
            if s >= best:
                best, label = s, lab
        if label is None:
            label = chr(ord("A") + next_label) if next_label < 26 else f"S{next_label}"
            next_label += 1
            centroids.append((label, feat))
        t0 = float(librosa.frames_to_time(a, sr=sr, hop_length=hop))
        t1 = float(librosa.frames_to_time(b, sr=sr, hop_length=hop))
        out.append({"start": round(t0, 3), "end": round(min(t1, duration), 3),
                    "label": label})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Extract beats/energy/sections to beats.json")
    ap.add_argument("audio", help="input audio file (wav/mp3/flac/…)")
    ap.add_argument("--out", default="beats.json", help="output JSON path")
    ap.add_argument("--sr", type=int, default=None, help="resample rate (default: native)")
    ap.add_argument("--hop", type=int, default=512, help="hop length in samples")
    ap.add_argument("--downbeat-meter", type=int, default=4, dest="meter",
                    help="beats per bar for the downbeat heuristic")
    ap.add_argument("--energy-hz", type=float, default=10.0, dest="energy_hz",
                    help="samples per second for the loudness envelope")
    args = ap.parse_args(argv)

    data = analyze(args.audio, sr=args.sr, hop=args.hop, meter=args.meter,
                   energy_hz=args.energy_hz)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")

    print(f"{args.audio}: {data['bpm']} bpm, {len(data['beats'])} beats, "
          f"{len(data['downbeats'])} downbeats, {len(data['onsets'])} onsets, "
          f"{len(data['sections'])} sections → {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
