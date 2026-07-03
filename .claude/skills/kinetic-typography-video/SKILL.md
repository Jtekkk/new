---
name: kinetic-typography-video
description: Use when the user wants to turn an audio track plus synced lyrics into a kinetic typography music video — beat-synced, rhythm-driven word animations rendered to a legible 1080p or 4K 60fps MP4. Covers audio analysis, lyric alignment, typography and motion design, composition, and export.
---

# Kinetic Typography Video

Turn a song and its lyrics into a rhythm-driven kinetic-typography music video:
words that enter, pulse, cut, and flow in time with the beat, rendered to a
clean 1080p or 4K 60fps MP4 with the original audio.

The pipeline is data-driven — every animation is keyed off two machine-readable
files, so the result is reproducible and frame-accurate rather than hand-timed:

```
audio.wav ─▶ analyze_audio.py ─▶ beats.json  ┐
                                              ├─▶ compositor ─▶ frames ─▶ ffmpeg mux ─▶ final.mp4
lyrics.txt ─▶ forced aligner  ─▶ words.json  ┘                         (+ original audio)
```

## When to use

Use when the user asks for a lyric video, kinetic typography, animated lyrics,
or a beat-synced text music video, and provides (or points to) an audio track
and lyrics. If lyrics have no timestamps yet, step 2 generates them.

## Workflow

1. **Audio analysis.** Extract tempo, beats, downbeats, onsets (drum hits), and
   an energy envelope, and segment the song into sections:

   ```bash
   python3 scripts/analyze_audio.py song.wav --out beats.json
   ```

   These drive *when* things move (beats/downbeats), *how hard* (energy), and
   *where the structure changes* (verse/chorus/drop).

2. **Lyric alignment.** Produce word-level timestamps. Prefer WhisperX (word
   timings + confidence); `aeneas` or Montreal Forced Aligner also work. Output
   `words.json` as `[{word, start, end, emphasis}]`. Mark hooks and stressed
   syllables for emphasis. Schema and tool notes: `references/pipeline.md`.

3. **Typography design.** Pick a font family that matches the genre, set a size
   hierarchy (lead vocal large, backing smaller, ad-libs stylized), and plan a
   palette that shifts per section. Genre→font and palette tables live in
   `references/pipeline.md`.

4. **Animation choreography.** Map audio events to motion: entrances on
   downbeats, scale pulses on bass, rapid cuts on hi-hats, smooth flows on
   melody, shake/glitch on screams, gentle float/fade on soft vocals. The full
   event→technique catalog is in `references/pipeline.md`.

5. **Visual composition.** Add reactive backgrounds (particles/shapes driven by
   FFT bands), camera moves (zoom on climaxes, pan on verses, shake on drops),
   and secondary elements (progress bar, current-line highlight, visualizer).

6. **Export.** Render 1080p or 4K at 60fps, keep text legible even in fast
   sequences, then mux the original audio so sync is exact:

   ```bash
   ffmpeg -i frames_%05d.png -i song.wav -c:v libx264 -pix_fmt yuv420p \
     -r 60 -c:a aac -shortest final.mp4
   ```

## Rendering engines

- **Remotion** (React, Node) — recommended: frame-accurate, code-driven, reads
  `beats.json`/`words.json` directly, renders MP4. Good default here (Node is
  available).
- **HTML5 Canvas / WebGL + headless Chromium + ffmpeg** — no framework; capture
  frames from a timeline page. Chromium is preinstalled.
- **After Effects (ExtendScript/pybox)** — when the user already lives in AE.

Detailed setup, the JSON schemas, font/motion/palette tables, and export
presets are in `references/pipeline.md`.
