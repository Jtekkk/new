# Kinetic typography pipeline — reference

Depth behind `SKILL.md`. Read when you need concrete tool commands, the JSON
schemas the compositor consumes, or the design decision tables.

## 1. Audio analysis (`scripts/analyze_audio.py`)

Built on [librosa](https://librosa.org). Install: `pip install librosa soundfile`.

```bash
python3 scripts/analyze_audio.py song.wav --out beats.json --downbeat-meter 4
```

`beats.json` schema:

```json
{
  "duration": 213.4,
  "bpm": 128.0,
  "beats":      [0.47, 0.94, 1.41, ...],        // every beat, seconds
  "downbeats":  [0.47, 2.35, 4.22, ...],         // bar starts (meter-derived)
  "onsets":     [0.47, 0.61, 0.94, ...],         // percussive hits
  "energy":     [{"t": 0.0, "rms": 0.02}, ...],  // loudness envelope
  "sections":   [{"start": 0.0, "end": 24.1, "label": "A"}, ...]
}
```

- **beats / bpm** → the master grid; snap entrances and cuts to these.
- **downbeats** → strongest entrances (new line on each bar or phrase).
- **onsets** → micro-timing for rapid cuts and per-hit accents.
- **energy** → animation intensity and background reactivity; local maxima are
  candidate drops/climaxes.
- **sections** → recurrence-matrix labels (A/B/C…); map to verse/chorus/bridge
  by position and energy, and switch palette/typography on section change.

## 2. Lyric alignment → `words.json`

Word-level timing is what makes text land on the vocal. Options, best first:

| tool | gives you | notes |
|------|-----------|-------|
| [WhisperX](https://github.com/m-bain/whisperX) | word timings + confidence | best default; ASR + forced alignment |
| [aeneas](https://github.com/readbeyond/aeneas) | word/line timings from known text | fast when you already have exact lyrics |
| Montreal Forced Aligner | phoneme + word timings | most precise; heavier setup |

Target schema:

```json
[
  {"word": "run", "start": 12.41, "end": 12.63, "line": 4, "emphasis": 1.0},
  {"word": "away", "start": 12.63, "end": 13.10, "line": 4, "emphasis": 0.6}
]
```

Set `emphasis` (0–1) higher on hooks, stressed syllables, and held notes — the
choreography scales motion by it.

## 3. Typography — genre → font

| genre / mood | font direction | examples |
|--------------|----------------|----------|
| EDM / hyperpop | bold geometric / grotesque sans | Montserrat Black, Druk, Space Grotesk |
| hip-hop / trap | heavy display, condensed | Anton, Archivo Black, Bebas Neue |
| rock / metal | grunge, distressed, condensed | Oswald, Teko, custom brush |
| ballad / R&B | elegant serif / high-contrast | Playfair Display, Cormorant |
| indie / lo-fi | humanist sans / mono | Inter, IBM Plex, JetBrains Mono |
| ambient / cinematic | light serif, wide tracking | EB Garamond, Cinzel |

Hierarchy: lead vocal 100%, backing 55–70% and lower-contrast, ad-libs stylized
(outline, italic, offset). Keep line length short; one hook word can fill frame.

## 4. Animation choreography — audio event → technique

| trigger | motion | feel |
|---------|--------|------|
| downbeat / bar start | entrance: slide, typewriter, mask-reveal | establishes the line |
| kick / bass | scale pulse, weight punch | grounds the rhythm |
| hi-hat / fast onsets | rapid cuts, word-swap, jitter | energy, urgency |
| sustained melody | smooth ease, drift, tracking-open | lyricism |
| build → drop | accelerate then explode/implode on the drop | payoff |
| scream / high energy | shake, glitch, RGB-split, chromatic aberration | aggression |
| soft / breathy vocal | float, fade, slow blur | intimacy |
| section change | palette + font-weight shift, transition wipe | structure |

Ease with rhythm, not linear time: cubic-bezier eases whose duration is a
fraction of the beat period (e.g. 1/4 or 1/2 beat) read as "on the grid."

## 5. Composition

- **Backgrounds**: particle systems / shapes whose count, size, or displacement
  is driven by FFT band energy (`librosa.stft` → low/mid/high bands). Keep
  contrast high enough that text stays legible (see export legibility rules).
- **Camera**: subtle continuous drift on verses; push-in on climaxes; quick
  shake (few-frame position noise) on drops; cut camera on section changes.
- **Secondary elements**: thin progress bar on the beat grid, current-line
  highlight, a small spectrum visualizer, thematic glyphs tied to the lyric.

## 6. Export & legibility

- Container/codec: `libx264` (`yuv420p`) for compatibility, or `libx265` /
  ProRes for masters. 60fps. 1080p (1920×1080) or 4K (3840×2160).
- Always mux the **original** audio, not a re-encode of a re-encode:

  ```bash
  ffmpeg -framerate 60 -i frames_%05d.png -i song.wav \
    -c:v libx264 -pix_fmt yuv420p -crf 16 -c:a aac -b:a 320k -shortest final.mp4
  ```

- Legibility rules that survive fast sequences: minimum on-screen dwell ~3
  frames per word at 60fps; maintain ≥ 4.5:1 contrast against the background
  behind the glyphs (add a scrim/blur if a busy background drops below it);
  avoid sub-24px type at 1080p.

## Data flow recap

`analyze_audio.py` and the aligner are independent and can run in parallel; the
compositor is the only stage that needs both. Cache `beats.json` / `words.json`
so re-renders (font/color/motion tweaks) skip re-analysis entirely.
