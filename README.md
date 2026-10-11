# FPS & Ping by Sagtary

A World of Tanks mod that shows FPS, ping and lag in battle and in replays, next to the game's own FPS/ping panel.

![The indicator in battle and in replays, normal and with Alt held](docs/hud.png)

## What it shows

The indicator is one line. Hold **Alt** (the game's extended info key, the same one that shows extra info on vehicle
markers) to add the graphs, 1% low and the lag history.

| Value | Meaning |
| --- | --- |
| `338fps` | Frames per second over the last second. The mod measures the time of every frame itself. |
| `237 1%` | 1% low (Alt only): the FPS of the slowest 1% of the time over the last 30 seconds. It shows stutters that the average hides. |
| `255replay` | Replays only: the FPS recorded in the replay, as the game's panel showed it in that battle. The first number is the FPS of the playback now. |
| `44ms` | Ping to the server, the same value as the game's panel. In a replay, the ping recorded in it. |
| ● lamp | The game's lag signal: green while server updates arrive, red while they stop. |

### Graphs (Alt)

Each graph has one point per second for the last 30 seconds, newest on the right.

- **FPS graph** is white.
- **Ping graph** is coloured by value, with the scale the game itself uses for server ping in the hangar:
  green 0–59 ms (good), yellow 60–119 ms (normal), red 120 ms and more (high).
- **Lag ticks**, before the lamp: one tick per second. Short and green means no lag in that second; tall and red means
  there was lag.

## Install

Copy `sagtary.fps_ping_<version>.wotmod` into the game's `mods\<game version>\` folder.

## Build

Build with Python 2.7, the game's Python version:

```text
C:\Python27\python.exe build.py            # build/<id>_<version>.wotmod
C:\Python27\python.exe build.py --install  # also copy it into the game's mods folder
```

The game folder is `D:\programs\World_of_Tanks_EU` unless the `WOT_DIR` environment variable says otherwise.
