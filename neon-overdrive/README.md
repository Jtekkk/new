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

Your top speed climbs continuously with distance ridden — from ~200 km/h at
the start to a screaming 405 km/h — and the difficulty climbs with it: spawn
rates keep tightening deep into the run, more bikers and drones gang up at
once, enemies fire faster and their bolts fly faster, laser-gate gaps narrow,
traffic gets armored, and the soundtrack's BPM rises with every wave.

## Tech

- Single-file HTML5 canvas, ~60 fps, no assets fetched — skyline, sun and
  billboards are pre-rendered to offscreen canvases at boot.
- Segment-based pseudo-3D road with procedural curves (layered sines),
  curve-following ground grid and roadside holo-billboards.
- Soundtrack: an embedded MP3 ("Flower Coffee People", base64-encoded so the
  game stays one file) played through Web Audio with live FFT beat detection —
  the ground grid, road edges and sun glow pulse to the track's actual bass
  hits, and playback rate ramps subtly as waves climb. If the track ever fails
  to play, the original procedural 138 BPM synth loop kicks in as a fallback.
  All SFX (lasers, explosions, klaxons, combo stingers, engine drone pitched
  by speed) remain fully synthesized — no other audio files.
- Juice: screenshake, hitstop, slow-mo death, chromatic glitch text, particle
  explosions, expanding shockwave rings, radial nitro speedlines, CRT scanline
  + vignette overlay.
