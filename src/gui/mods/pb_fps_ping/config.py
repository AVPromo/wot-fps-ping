# -*- coding: utf-8 -*-
"""Settings: timing, statistics windows, layout and look."""

# Same rate as the game's own debug panel (debug_ctrl.DebugController).
UPDATE_INTERVAL = 0.2
# FPS is counted over the frames of the last FPS_WINDOW seconds.
FPS_WINDOW = 1.0
# FPS, 1% low and ping go to game.log every N screen updates (once per second).
LOG_EVERY = 5
# The game's own panel stays visible while the two are compared.
HIDE_GAME_PANEL = False

# time.clock() is wall time only on Windows; elsewhere it is CPU time and runs slower than BigWorld.time().
# If it runs slower than this ratio after CLOCK_CHECK_TIME seconds, frames are timed by BigWorld.timeExact()
# (1 ms steps) instead.
CLOCK_MIN_RATIO = 0.5
CLOCK_CHECK_TIME = 1.0

# 1% low FPS: share of the window time, window length in whole seconds, and histogram bin width in seconds.
LOW_SHARE = 0.01
LOW_WINDOW = 30
LOW_BIN = 0.00005

# Graphs: once per GRAPH_INTERVAL a point with the shown value, redrawn at the same time;
# GRAPH_SECONDS of points, newest on the right.
GRAPH_INTERVAL = 1.0
GRAPH_SECONDS = 30
GRAPH_EVERY = int(round(GRAPH_INTERVAL / UPDATE_INTERVAL))
GRAPH_POINTS = int(round(GRAPH_SECONDS / GRAPH_INTERVAL))

# Layout in Flash pixels of the battle page (scaled with the game's interface scale), next to the game's own
# FPS/ping panel at (0, 2). Container position.
VIEW_POSITION = (6, 30)
# Normal mode: one line, "fps 393   ping 261 ms". The "fps" label is at x 0; the fps number at (x, width) in a field
# of fixed width, so the ping part does not move when it gets longer; x of the "ping" label and of "261 ms".
LINE_FPS_NUMBER = (28, 38)
LINE_PING_X = 74
LINE_PING_NUMBER_X = 110
# While the extended info key (Alt) is held: two rows with the same columns, "fps <graph> 330   1% low 261" and
# "ping <graph> 261 ms" PING_ROW_Y below it. Inside a row the label is at x 0, the number at NUMBER_X in a field of
# fixed width (fps row, ping row) so what follows does not move when it gets longer; the graph position and size,
# and the 1% low text x.
PING_ROW_Y = 20
NUMBER_X = 120
ROW_NUMBER_WIDTH = (38, 60)
GRAPH_POSITION = (36, 3)
GRAPH_SIZE = (80, 15)
LOW_TEXT_X = 164
# The graph scale goes from 0 to the highest point shown times this, so the line never touches the top.
GRAPH_HEADROOM = 1.1

# BigWorld.statPing() returns this while there is no ping yet (connecting, loading the battle).
PING_NONE = 999.0

# Look: the game's own panel font, size and colour; in extended mode the ping number and graph in light blue.
LINE_PING_NUMBER_HTML = '<font face="$FieldFont" size="15" color="#F4EFE8">%s ms</font>'
FPS_LABEL_HTML = '<font face="$FieldFont" size="15" color="#F4EFE8">fps</font>'
FPS_NUMBER_HTML = '<font face="$FieldFont" size="15" color="#F4EFE8">%s</font>'
PING_LABEL_HTML = '<font face="$FieldFont" size="15" color="#F4EFE8">ping</font>'
PING_NUMBER_HTML = ('<font face="$FieldFont" size="15" color="#8FD3FF">%s</font>'
                    '<font face="$FieldFont" size="15" color="#F4EFE8"> ms</font>')
LOW_HTML = '<font face="$FieldFont" size="15" color="#F4EFE8">1%% low %s</font>'
# Added after 1% low once the frame callback has been out of step with the game's frames at least once this battle.
DESYNC_HTML = '<font face="$FieldFont" size="15" color="#FF9A4F">   desync %d</font>'
# Graph look: line (thickness, colour, alpha), fill under the line (colour, alpha), dot on the newest point
# (colour, alpha, radius).
FPS_GRAPH = ((1.3, 0xF4EFE8, 1.0), (0xF4EFE8, 0.25), (0xF4EFE8, 1.0, 1.8))
PING_GRAPH = ((1.3, 0x8FD3FF, 1.0), (0x8FD3FF, 0.25), (0x8FD3FF, 1.0, 1.8))
