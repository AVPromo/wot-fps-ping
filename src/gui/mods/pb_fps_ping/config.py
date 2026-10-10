# -*- coding: utf-8 -*-
"""Settings: timing, statistics windows, layout and look."""

# Same rate as the game's own debug panel (debug_ctrl.DebugController).
UPDATE_INTERVAL = 0.2
# FPS is counted over the frames of the last FPS_WINDOW seconds.
FPS_WINDOW = 1.0
# FPS and 1% low go to game.log every N screen updates (once per second).
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

# FPS graph: once per GRAPH_INTERVAL a point with the shown FPS value (the last second), redrawn at the same time;
# GRAPH_SECONDS of points, newest on the right.
GRAPH_INTERVAL = 1.0
GRAPH_SECONDS = 30
GRAPH_EVERY = int(round(GRAPH_INTERVAL / UPDATE_INTERVAL))
GRAPH_POINTS = int(round(GRAPH_SECONDS / GRAPH_INTERVAL))

# Layout in Flash pixels of the battle page (scaled with the game's interface scale), next to the game's own
# FPS/ping panel at (0, 2). One row: "fps 330", and while the extended info key (Alt) is held
# "fps <graph> 330   1% low 261". Container position; inside it the "fps" label is at x 0, the number at
# NUMBER_X (normal, extended) with a fixed width so what follows does not move when it gets longer, the graph
# position and size, and the 1% low text x.
VIEW_POSITION = (6, 30)
NUMBER_X = (28, 112)
NUMBER_WIDTH = 38
GRAPH_POSITION = (28, 3)
GRAPH_SIZE = (80, 15)
LOW_TEXT_X = 156
# The graph scale goes from 0 to the highest point shown times this, so the line never touches the top.
GRAPH_HEADROOM = 1.1

# Look: the game's own panel font, size and colour.
LABEL_HTML = '<font face="$FieldFont" size="15" color="#F4EFE8">fps</font>'
NUMBER_HTML = '<font face="$FieldFont" size="15" color="#F4EFE8">%s</font>'
LOW_HTML = '<font face="$FieldFont" size="15" color="#F4EFE8">1%% low %s</font>'
# Line: thickness, colour, alpha. Fill under the line: colour, alpha. Dot on the newest point: colour, alpha, radius.
GRAPH_LINE = (1.3, 0xF4EFE8, 1.0)
GRAPH_FILL = (0xF4EFE8, 0.25)
GRAPH_DOT = (0xF4EFE8, 1.0, 1.8)
