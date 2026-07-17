# NEON//OVERDRIVE 🏍️⚡

A fast, loud, neon-soaked cyberpunk motorbike blaster in a single HTML file.
No build, no dependencies — just open `index.html` in a browser and ride.

![genre](https://img.shields.io/badge/genre-synthwave%20moto%20blaster-ff2d95)

## Play

Open `neon-overdrive/index.html` (double-click, or serve the repo and visit the path).

| Input | Action |
| --- | --- |
| `◄ ►` / `A D` | Steer |
| `SPACE` / `X` / `J` | Fire blasters |
| `SHIFT` | Nitro (ram bikers & drones for NITRO KILLs) |
| `P` / `Esc` | Pause |
| `M` | Mute |
| Touch | Drag to steer (auto-fire), second finger = nitro |

## The loop

Endless pseudo-3D highway (OutRun-style projection) through a synthwave city.
Blast rival bikers, attack drones, hover-traffic and mines; dodge what you
can't kill — near misses feed your nitro. Kills chain into a combo multiplier
(RAMPAGE → CARNAGE → UNSTOPPABLE). Waves escalate every ~17 seconds and
periodically deploy a HUNTER gunship mini-boss that drops a blaster upgrade.
Pickups: `W` weapon level (up to quad-fire), `N` nitro, `HP` hull, `SH` shield.
Best score persists in `localStorage`.

## Tech

- Single-file HTML5 canvas, ~60 fps, no assets fetched — skyline, sun and
  billboards are pre-rendered to offscreen canvases at boot.
- Segment-based pseudo-3D road with procedural curves (layered sines),
  curve-following ground grid and roadside holo-billboards.
- Procedural audio via Web Audio: 138 BPM synth bass/kick/hat loop that gains
  an arp lead as waves rise, plus engine drone pitched by speed and synthesized
  laser/explosion/pickup SFX. No audio files.
- Juice: screenshake, hitstop, slow-mo death, chromatic glitch text, particle
  explosions, expanding shockwave rings, radial nitro speedlines, CRT scanline
  + vignette overlay.
