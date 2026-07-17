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
Blast rival bikers, attack drones, kamikaze razor saws, hover-traffic and
mines; thread the gap in laser gates or shoot them open; dodge what you can't
kill — near misses feed your nitro. Kills chain into a combo multiplier
(RAMPAGE → CARNAGE → UNSTOPPABLE).

Kills, near misses and threaded gates charge the gold **OVERDRIVE** meter —
when it fills you go invincible for 6 seconds with double score and max
blasters. Waves escalate every ~17 seconds, periodically deploy a HUNTER
gunship mini-boss, and every 5th wave summons the **WARLORD**: an armored
gun-fortress — destroy its three turrets to expose the reactor core.

Every 3 waves the world shifts zone: **Sunset Strip → Datastream → Cryo
Sector**, each recoloring the sky, sun, grid and road. Pickups: `W` weapon
level (up to quad-fire), `M` +8 homing missiles, `N` nitro, `HP` hull,
`SH` shield. Best score persists in `localStorage`.

## Tech

- Single-file HTML5 canvas, ~60 fps, no assets fetched — skyline, sun and
  billboards are pre-rendered to offscreen canvases at boot.
- Segment-based pseudo-3D road with procedural curves (layered sines),
  curve-following ground grid and roadside holo-billboards.
- Procedural audio via Web Audio: 138 BPM synth bass/kick/hat loop that gains
  an arp lead as waves rise, plus engine drone pitched by speed and synthesized
  laser/explosion/pickup SFX. No audio files. The ground grid, road edges and
  sun glow all pulse in sync with the kick drum.
- Juice: screenshake, hitstop, slow-mo death, chromatic glitch text, particle
  explosions, expanding shockwave rings, radial nitro speedlines, CRT scanline
  + vignette overlay.
