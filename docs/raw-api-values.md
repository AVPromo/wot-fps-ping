# Raw FPS, ping and network data from the WoT API

WoT EU client 2.4.0.2. What the BigWorld engine functions for FPS, ping and network return, and what each number
means. Also how the game's own FPS/ping panel uses them.

Sources:

- Diagnostic build 0.3.0 of the mod: a screenshot from a training battle (`10_hills`) and about 90 `probe` lines in
  `game.log`, one per second, on the way hangar → loading → battle.
- Diagnostic build 0.3.1: a second training battle (`08_ruinberg`), about 340 `probe` lines, with a ping of about
  100 ms and one artificial lag: the network was cut for a few seconds at about 11:29:00.
- Diagnostic builds 0.4.0 and 0.4.1: FPS only, variants of the current FPS and of the frame time side by side on the
  screen and in `game.log` once a second; training battles without an FPS limit, 200–470 FPS.
- A diagnostic build that wrote every frame of 90 s of battle: `getFPS()`, `time.clock()` and `BigWorld.timeExact()`.
- The lag probe of mod 0.24 (`lag_probe.py`): every frame of 157 s of a training battle written to a CSV, with the
  network cut 4 times, for 5, 10, 15 and 30 s.
- The decompiled Python and AS3 code of the client: where the game itself reads these values.

Confidence of each row:

- **log**: confirmed by values in `game.log` or the CSV over time;
- **code**: confirmed by how the game's code uses the value;
- **name**: inferred from the field name only, not checked.

The example values are from one moment of the first battle (`10_hills`, 11:14:22), unless said otherwise.

## `BigWorld.getFPS()`

A tuple of 4 numbers, for example `(333.333, 301.205, 125, 500)`.

| Item | Example | What it is | Confidence |
| --- | --- | --- | --- |
| `[0]` | 333.333 | FPS of the last frame. Always exactly 1000 / a whole number of milliseconds: 1000 (1 ms), 500 (2 ms), 333.333 (3 ms), 250 (4 ms), 62.5 (16 ms), 58.8235 (17 ms). The frame time is measured to 1 ms | log |
| `[1]` | 301.205 | Average FPS of the last 50 frames: `50 / (time of 50 frames in whole ms)`, updated every 0.5 s (details below). The game's panel shows it (`int()`) | log per frame, code |
| `[2]` | 125 | The worst frame, that is the minimum FPS. Never more than `[1]`. 125 = an 8 ms frame. Changes at other times than `[1]`; the window is not found | log |
| `[3]` | 500 | The best frame, that is the maximum FPS. Never less than `[1]`. On the loading screen with a 62.5 limit it was exactly 62.5. Changes together with `[2]` | log |

Before connecting it returns `(0, 0, 0, 0)`.

### How `getFPS()[1]` is computed

Checked by recording every frame of 90 s of battle (29 613 frames, 167 updates of `[1]`, about 300 FPS), with the
exact frame time from `time.clock()` and the `BigWorld.timeExact()` clock next to it.

- **Formula:** `[1] = 50 / T`, where `T` is the time of the last 50 frames in whole milliseconds. `50000 / [1]` is a
  whole number in all 167 updates: 304.878 = 50 frames / 164 ms. Confidence: log.
- **The window is exactly 50 frames.** It ends on the frame before the one in which Python reads the value. By
  `timeExact()` (1 ms steps) it matches to the millisecond in 128 updates of 167; the rest differ by 1 ms, because the
  clock is read at another moment of the frame. Windows of 49 and 51 frames never match. Confidence: log.
- **Update:** every 0.5 s by `BigWorld.time()` (median 0.502 s); now and then it skips one and keeps the value for
  1.0 s. Between updates the number does not change. Confidence: log.
- **`[2]` and `[3]`** change separately from `[1]` (391 times against 167, together 4 times). They match neither the
  minimum and maximum of `[0]` over the last N frames nor over the last N seconds. How they are computed is not found.

Why `[1]` is an inexact FPS:

- **It counts a small part of the frames.** At 300 FPS, 50 frames take about 0.17 s, and the value is shown for 0.5 s:
  only the last third of each half-second gets into the number, the other two thirds of the frames are not counted. A
  freeze in the uncounted part does not get into the number at all.
- **A coarse clock.** A window of about 160 ms is measured to 1 ms, which is ±2 FPS at 300 FPS.
- **The window is in frames, not in time.** At 60 FPS the same 50 frames take 0.83 s, at 500 FPS 0.1 s: the higher
  the FPS, the shorter and noisier the window.

For comparison: the mod computes FPS as the number of frames in the last 1 s divided by their total time by
`time.clock()` (fractions of a millisecond), over all frames.

## `BigWorld.getBattleFPS()`

A tuple of 3 numbers, for example `(275.449, 402, 349.845)`. FPS statistics since the start of the battle.

| Item | Example | What it is | Confidence |
| --- | --- | --- | --- |
| `[0]` | 275.449 | The minimum FPS of the battle. Did not change after the battle started | log |
| `[1]` | 402 | The maximum FPS of the battle. Only grows | log |
| `[2]` | 349.845 | The average FPS of the battle | log |

Before the battle: `(3.40282e+38, 1.17549e-38, 0)`, the empty starting values: the minimum is the largest possible
float, the maximum the smallest positive float. Counting starts when the battle starts, after the countdown, when the
game calls `BigWorld.enableBattleStatisticCollector(True)`.

## `BigWorld.wg_getTimePerFrame()`

A number, for example `3.5708999633789062`. The frame time in milliseconds, with fractions.

- Close to `1000 / getFPS()[1]`, but not equal to it: with `getFPS()[1]` = 310.559 (3.22 ms) it was 3.0425. The
  averaging window is unknown. Confidence: log.
- While loading and during freezes: hundreds and thousands, 1247, 1510.4. Confidence: log.
- Not usable for the current FPS: `1000 / wg_getTimePerFrame()` jumps ±50% around the exact average over 1 s (197 at
  434, 469 at 368). Confidence: log.

## `BigWorld.wg_getFrameTimestamp()`

A whole number, for example `58089`. The frame number since the client started: a frame counter.

- Grows by the current FPS each second: in battle about 300 per second, with a 60 FPS limit about 60 per second
  (12806 → 13105 in 5 s). Confidence: log.
- Its growth over an interval divided by the growth of `BigWorld.time()` gives the exact average FPS of that interval.
  It matches the count of calls of a callback on every frame to ±0.5 FPS. Confidence: log.

## A callback on every frame: `BigWorld.callback(0.0, f)`

A callback with zero delay runs on the next engine tick. If it schedules itself again each time, the function is
called exactly once per frame: the number of calls in 1 s matches the growth of `wg_getFrameTimestamp()` to ±0.5 FPS
(321.0 and 321.4, 418.6 and 418.7). No frames are skipped. Confidence: log.

The time between two calls is the frame time. Its precision depends on the clock:

| Clock | Example over 1 s, ms | Precision | Confidence |
| --- | --- | --- | --- |
| `BigWorld.timeExact()` | last 3.00, range 1.00–5.00 | 1 ms: the frame time is always a whole number of ms ± 0.01 | log |
| `BigWorld.time()` | last 5.00, range 1.00–8.00 | 1 ms, like `timeExact()` | log |
| `time.clock()` (Python) | last 2.66, range 1.52–5.60 | fractions of a ms. In Python 2.7 on Windows it is `QueryPerformanceCounter` | log |

At 300–400 FPS a frame takes 2–4 ms, so a clock with 1 ms steps gives only 2, 3 or 4 ms. Only `time.clock()` is good
for the time of a single frame.

## `BigWorld.statPing()`

A number, for example `41.3992`. The ping in milliseconds; the game's panel shows it (`int()`).

- Computed from `LatencyInfo().value[3]`: `statPing = (value[3] − 0.05) × 1000`. In the log it matches to the last
  digit: 0.0913992 → 41.3992. The game's lag report in `Avatar.py` subtracts the same 0.05 s (half a server tick of
  0.1 s). Confidence: log, code.
- `999.0`: no data: connecting, loading the battle. Confidence: log.
- `1.0`: the lower limit: if `value[3]` is less than 0.05 s, the ping is clamped to 1. Confidence: log.
- Not updated every frame: one value holds for 1–4 seconds. Confidence: log.
- During lag it does not grow but freezes: from 11:29:00 to 11:29:15 it held 106.417, with no new measurements.
  Confidence: log.

## `BigWorld.statLagDetected()`

`True` or `False`: the "lag now" flag. The game's panel picks its lag icon by it. Confidence: code.

It means "no updates from the server", not "high ping": with a steady ping of 100–150 ms it stayed `False`.
Confidence: log.

Timing, from the lag probe (network cut 4 times in one battle):

| Cut | Flag `True` | What the data shows |
| --- | --- | --- |
| 5 s | 50.3 → 56.4 s (6.1 s) | — |
| 10 s | 70.5 → 83.5 s (13.0 s) | last packet from the server (a ping measurement) at 70.085 s, `True` at 70.469 s, 0.38 s later |
| 15 s | 91.2 → 107.4 s (16.2 s) | first packet after the network came back at 107.186 s, `False` 0.22 s later |
| 30 s | from 119.4 s until the disconnect | 37 s after the flag turned `True` the game closed the connection |

- **The flag reacts almost at once:** at most 0.4 s after the last packet, and it clears 0.2–0.4 s after the first
  packet. Confidence: log.
- **It stays `True` longer than the cut itself** (6.1 s for a 5 s cut, 13 s for a 10 s cut): after the network is
  back, the adapter needs time to reconnect. Confidence: log.
- **After about 37 s without a connection the game leaves the battle:** `Disconnecting due to dead channel` in
  `game.log`. Confidence: log.
- **The exact threshold is not found.** It is computed in the C++ engine: in Python the avatar only calls
  `filter.enableLagDetection(True)` on its movement filter (`BigWorld.AvatarFilter`), so the lag is probably detected
  by missing position updates from the server. Packets are visible in the probe only by ping measurements, which are
  rare, so the threshold could not be measured to 0.1 s.

An earlier estimate of "about 6 s" was wrong: it was measured by the freeze of `statPing()`, which keeps one value for
several seconds even without lag.

## `BigWorld.LatencyInfo().value`

A tuple of 4 numbers, for example `(1, 0.0913992, 0.248558, 0.0913992)`. `LatencyInfo` is a C++ class of the BigWorld
engine. Each read of `.value` gives the current data. It has no other attributes than `value`; `__doc__` is `None`,
and the client has no documentation for it.

| Item | Example | Hangar | Battle | What it is | Confidence |
| --- | --- | --- | --- | --- | --- |
| `[0]` | 1 | 0 before connecting, then 1 | 1 | There is a connection to the server | log |
| `[1]` | 0.0913992 | 0 | always equal to `[3]` (both battles) | Empty in the hangar, a copy of `[3]` in battle. Possibly the delay to the battle server | log; meaning is a guess |
| `[2]` | 0.248558 | equal to `[3]` | changes rarely: in the second battle 0.145915 held for about 100 seconds, then became 0.176034 | Looks like an average delay over a long period, about 100 seconds: 0.145915 is close to the average of `[3]` over that time | log; meaning is a guess |
| `[3]` | 0.0913992 | delay | delay | Round-trip delay to the server, in seconds. `statPing()` is computed from it. The game uses it to predict shots (`ChargeShotComponent`, `LowChargeShotController`, `BustleFeedController`), for the shot wait timeout (`Avatar`: `value[3] × 0.5`) and for the turret desync tolerance (`VehicleGunRotator`) | log, code |

## `BigWorld.serverTime()`

A number, for example `94441.97`. The server time in seconds.

- `-1.0` before connecting, `0.0` at the moment of connecting. Confidence: log.
- The hangar and the battle count differently (about 4 685 against about 94 402): they are different servers.
  Confidence: log.

## `BigWorld.stime`

The same number as `serverTime()`, a second name for the server time. The values match in all log lines.
Confidence: log.

## `BigWorld.time()`

A number, for example `99.29`. The client time in seconds since the game started. Confidence: log.

## `BigWorld.server`

A string: the address of the server the client is connected to, as `host:port`, for example
`u'login2.p4.worldoftanks.eu:20016'`. Confidence: log.

## `BigWorld.getMemoryInfoKB()`

A dictionary, values in kilobytes. Meanings from the key names; the sizes are plausible: `dedicatedMemTotal` =
12 229 632 KB ≈ 11.7 GB matches the video memory in the telemetry (`gpuMemory` = 11 943 MB). Confidence: name, checked
against the sizes.

| Key | Example, KB | What it is |
| --- | --- | --- |
| `systemMemUsed` | 3 636 680 | RAM used by the client (≈ 3.5 GB) |
| `systemMemReserved` | 0 | Reserved RAM |
| `dedicatedMemTotal` | 12 229 632 | Video memory, total |
| `dedicatedMemCommitted` | 3 131 864 | Video memory used by the client (≈ 3 GB) |
| `sharedMemTotal` | 32 614 383 | Shared (system) memory available to the video card |
| `sharedMemCommitted` | 44 808 | Shared memory used by the video card |
| `virtualAddressSpaceTotal` | 137 438 953 344 | Virtual address space of the process, total |
| `virtualAddressSpaceUsage` | 26 059 472 | Virtual address space, used |

## `BigWorld.memUsed()`

A whole number, for example `7368428`. Hardly changes during a battle. Unit and meaning unknown: if it is kilobytes,
that is ≈ 7 GB, twice as much as `systemMemUsed`. Confidence: log; meaning not found.

## `BigWorld.Latency`

Not a data source but a class of an engine GUI component: attributes `textureName`, `position`, `size`, `colour`,
`visible` and others, like any BigWorld interface element. No delay fields, `__doc__` is `None`. Confidence: log
(`dir()`).

## Replay data: `BattleReplay.g_replayCtrl`

Only while a replay plays (`isPlaying`). From the recording, not from the current network. While a battle is recorded,
the game's panel controller writes `getFPS()[1]`, `statPing()` and `statLagDetected()` into the replay every 0.2 s
(`setFpsPingLag`). Confidence: code.

| Field | What it is |
| --- | --- |
| `fps` | FPS recorded in the replay: `getFPS()[1]` of the recorded battle. 0 if the replay has none |
| `ping` | Ping recorded in the replay |
| `isLaggingNow` | Lag flag recorded in the replay |

While a replay plays, `statPing()` stays at `999.0`: there is no connection. Confidence: log.

## The game's own FPS/ping panel

Code: `gui/battle_control/controllers/debug_ctrl.py`, `gui/Scaleform/daapi/view/battle/shared/debug_panel.py`,
`DebugPanel.as`; layout from `debugPanel.swf` and `battlePage.swf` in `res/packages`. Coordinates are in the Flash
pixels of the battle interface. The battle page stage is 1024×800; the game scales the whole Flash interface at once.

What it reads, every 0.2 s (`_UPDATE_INTERVAL`):

| | In battle | In a replay |
| --- | --- | --- |
| FPS | `int(getFPS()[1])` | `getFPS()[1]` of the playback, without `int()` |
| Recorded FPS | — | `int(replayCtrl.fps)`; if more than 0 the FPS text is `recorded(current)`, for example `60(347)` |
| Ping | `int(statPing())` | `replayCtrl.ping`, without `int()` |
| Lag | `statLagDetected()` | `replayCtrl.isLaggingNow` |

Layout and look:

- **Where:** the top left corner, at x=0, y=2 of the battle page (the same for random battles, ranked, Frontline and
  Stronghold).
- **Shift:** the panel's code moves it on x: −23 if the FPS text is at most 4 characters (a normal battle), 0 if
  longer (a replay, `60(347)`), so the text does not go past the screen edge.
- **Labels:** `fps`, `ping:`, `ms` are not text but one picture of 106×17 px at 0, 0 of the panel, pure white.
- **Values:** two text fields, `fpsTF` at x=2, y=2 and `pingTF` at x=88, y=2. Each 59×27 px, font `$FieldFont` 15 px,
  colour `#F4EFE8`, right-aligned, HTML text.
- **Text shadow:** a `DropShadowFilter`: distance 1, angle 90, colour `#000000`, alpha 1, blur 4, strength ≈ 0.6
  (0.59765625), quality 2. Read from the text fields in the game.
- **Lag icon:** two pictures of 16×16 px at the same point x=168, y=5, one of them shown: a small green dot in a dark
  circle without lag, a red one with lag.

## The game's server ping scale

The game colours the ping of the servers in the hangar and on the login screen by three levels
(`predefined_hosts.py`, `PING_STATUSES`). The ping icon has 3, 2 or 1 bars; only the high level has a colour-blind
variant. Confidence: code.

| Level | Ping, ms |
| --- | --- |
| `LOW` (good) | up to 59 |
| `NORM` | 60–119 |
| `HIGH` | 120 and more |

The mod colours its ping graph by this scale.

## `BigWorld.wg_getClientStatistics()`

A dictionary of the telemetry the client sends to Wargaming after a battle (`helpers/statistics.py`:
`wg_reportSessionData`, `wg_reportSystemData`). The values accumulate over the battle.

Collection starts only when the battle starts (after the countdown). Before that, all performance and network fields
are 0 and `invalidStats` is 32; when the battle starts `invalidStats` becomes 0. The telemetry measures FPS every 0.5
seconds. Confidence: log (entries every 10 s).

> **Privacy.** Some fields identify the computer: `cat_hw_id` (a hardware ID), the models of the CPU, video card and
> disks, the device maker. Their values are not given in this document. Do not show these fields on stream and do not
> publish them in logs.

### Performance

| Key | Example | What it is | Confidence |
| --- | --- | --- | --- |
| `fpsMin` | 332 | The minimum FPS of the battle among half-second measurements. That is why it is higher than `getBattleFPS()[0]` (275.449), which uses shorter measurements | log |
| `fpsMax` | 402 | The maximum FPS of the battle | log |
| `fpsAvg` | 350 | The average FPS of the battle | log |
| `fpsDeviation` | 29 | FPS spread over the battle | name |
| `fps_0_5` … `fps_161_180`, `fps_gt_180` | `fps_gt_180=30` | FPS histogram: how many half-second measurements fell into each range. 2 measurements a second: 6 after 3 s of battle, 26 after 13 s | log |
| `fps_gt_40` | 30 | How many measurements were above 40 FPS. A general counter that overlaps the narrow ranges above 40 | log |
| `cpu_utilization` | 82.70 | CPU load, % | name |
| `gpu_utilization` | 95.05 | GPU load, % | name |
| `cpu_utilization_low_fps`, `gpu_utilization_low_fps` | 81.53, 99.47 | The same, at moments of low FPS | name |
| `vertical_sync` | True | Vertical sync is on | name |
| `loadingTime` | 4 | Battle loading time. Appears right after the map loads; by its size, seconds | log; the unit is a guess |
| `activeTime` | 15127 | Time since the battle started, in milliseconds: 3116 after 3 s, 13126 after 13 s | log |
| `gameSessionDuration` | 15 | Time since the battle started, in seconds: 3, then 13 | log |
| `invalidStats` | 0 | Invalid statistics flag: 32 before the battle starts, 0 in battle, 2 at the very end of the second battle | log; meaning of 32 and 2 not found |

### Network

| Key | Example | What it is | Confidence |
| --- | --- | --- | --- |
| `ping` | 40 | Average ping of the battle, ms, a whole number. In the second battle it held at 100–102, while `statPing()` changed from 70 to 120 | log |
| `lag` | 3 | Share of the battle time with lag, in percent, a whole number. In the second battle, after a lag of about 3 seconds, it was 9 at second 31 of the battle, then 6, 5, 4, 4, 3, 3, 3: it falls while the battle goes on without new lag | log |
| `ping_lt_50` | 0.6085 | Share of the battle time with a ping below 50 ms (here 61 %). The five shares add up to exactly 1.0 | log |
| `ping_51_100` | 0.3800 | Share of the time with a ping of 51–100 ms | name |
| `ping_101_150` | 0.0036 | Share of the time with a ping of 101–150 ms | name |
| `ping_151_400` | 0.0079 | Share of the time with a ping of 151–400 ms | name |
| `ping_gt_400` | 0.0 | Share of the time with a ping above 400 ms | name |

### Memory

By their sizes, the values are in megabytes. Confidence: name. `ramPeak` only grows in the log: the peak since the
client started.

| Key | What it is |
| --- | --- |
| `ramTotal`, `ramAvailable`, `ramPeak` | RAM: total, free, peak use |
| `pageFileTotal`, `pageFileAvailable`, `pageFilePeak` | Page file: total, free, peak |
| `virtTotal`, `virtAvailable`, `virtPeak` | Virtual memory of the process: total, free, peak |
| `memoryCritical` | There was a critical lack of memory |

### Battle and camera

| Key | Example | What it is | Confidence |
| --- | --- | --- | --- |
| `spaceName` | `u'10_hills'` | Internal name of the current space: empty → `login` → `hangar_v…` → the battle map | log |
| `spaceID` | 9 | Space number in the client | name |
| `cameraPos` | `(157.676, 33.4286, -301.518)` | Camera position on the map | name |
| `cameraDir` | `(-0.472114, 0.660947, 1.88763e-08)` | Camera direction | name |

### System and hardware

Values are not given. Confidence: name.

| Key | What it is |
| --- | --- |
| `cat_hw_id` | Hardware ID of the computer. **Identifies the PC** |
| `cpuName`, `cpuVendor`, `cpuFamily`, `cpuCores`, `cpuFreq` | CPU: model (**identifies**), maker, family, cores, frequency |
| `gpuVendor`, `gpuFamily`, `gpuMemory`, `gpuDriverVersion`, `multiGPU` | Video card: maker, family, memory, driver version, several GPUs |
| `systemHddName`, `gameHddName` | Models of the system disk and of the game disk. **Identifies** |
| `workstationVendor`, `isLaptop` | Device maker (**identifies**), laptop or not |
| `os`, `osBit`, `clientBit`, `reason32bit` | OS version, bitness of the OS and of the client |
| `graphicsAPIID`, `graphicsEngine`, `graphicsSettings` | Graphics API, render engine, encoded graphics settings |
| `hasMods` | Mods are installed |
| `crashed` | The client crashed last time |

## Not checked yet

- `getFPS()[2]` and `[3]`: how they are computed.
- `statLagDetected()`: the exact threshold, to 0.1 s.
- `LatencyInfo().value[2]`: the "average delay over about 100 seconds" guess needs a longer battle with a ping that
  changes a lot.
- `memUsed()`: the unit.
- `invalidStats`: what 32 and 2 mean.
- `ping_151_400` and `ping_gt_400`: a ping above 150 ms did not hold in the tests.

Besides, `dir(BigWorld)` has 752 names. Not called yet on this topic:

- `getScaleformMemory`, `getGenericMemory`, `getHeapMemory`, `getStreamingMemory` and other `get…Memory`: memory by
  subsystem;
- `WGPinger`: ping of the servers; the game uses it to pick a server on the login screen.
