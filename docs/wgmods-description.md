# FPS, Ping and Lag

Exact FPS, 1% low, ping and lag in one line, with 30-second graphs on Alt. Works in replays.

- exact FPS, counted from every frame;
- ping and a lag lamp;
- on **Alt**: 30-second graphs of FPS and ping, 1% low FPS and lag history;
- in replays: the FPS, ping and lag recorded in the replay.

![FPS, Ping and Lag in battle and in replays, normal and with Alt held](cover.png)

## Installation

![Installation: copy the file into the game version folder in mods](install-guide.png)

1. Download `sagtary.fps_ping_<version>.wotmod`.
2. Copy it into `mods/<game version>` in the game folder, where `WorldOfTanks.exe` is. Replace the old version if
   asked.
3. Check that the file is in the folder shown in the picture.
4. Start a battle: FPS, ping and lag are in the top left corner.

## Found a bug? Have an idea?

> [Create an issue on GitHub](https://github.com/pavel-bolhovitin/wot-fps-ping/issues/new) or just write in the
> comments here.

## What it shows

### FPS

- **Current FPS**, for example `338fps`: frames per second over the last second, measured from the time of every
  frame.
- **FPS graph** (Alt): FPS history for the last 30 seconds, newest on the right.
- **1% low** (Alt), for example `237low`: the FPS of the slowest 1% of the time over the last 30 seconds. Shows
  stutters that the average FPS hides.
- **Replay FPS** (replays only), for example `255replay`: the FPS the game showed when the battle was recorded.

### Ping

- **Current ping**, for example `44ms`: the same value as the game's panel. In a replay, the ping recorded in it.
- **Ping graph** (Alt): ping history for the last 30 seconds, coloured with the game's own scale for server ping:
  green up to 59 ms, yellow 60–119 ms, red 120 ms and more.

### Lag

- **Lag lamp**: green while updates from the server arrive, red when they stop. This is the game's own lag signal;
  high ping alone does not make it red.
- **Lag ticks** (Alt): one tick per second for the last 30 seconds. Tall and red means there was lag in that second.

## FAQ

**1. Why is the FPS different from the game's panel?**

The game's panel shows the average of the last 50 frames, updated every 0.5 s. At 300 FPS that is only about the
last third of each half-second, so a short freeze can be missed. This mod counts every frame of the last second.

**2. Why does the ping not change while the lamp is red?**

During lag no new ping measurements arrive, so the game keeps the last value. The lamp is the sign that the ping on
the screen is out of date.

**3. What does 1% low mean?**

Sort the last 30 seconds of frames from the slowest, take the slowest 1% of the time, and look at the FPS there.
`379fps / 237low` means the game mostly runs at 379 FPS but drops to about 237 in short moments.

## Source code

Source code is on GitHub: <https://github.com/pavel-bolhovitin/wot-fps-ping>

## Changelog

### Version 1.0.0

First release.
