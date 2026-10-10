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
# FPS/ping panel at (0, 2). Container position: the text starts at the same x as the game's panel text.
VIEW_POSITION = (9, 30)
# Normal mode: one line, "fps 372    ping 74"; 7 px between a label and its number, parts split by 4 spaces. The
# "fps" label is at x 0, the fps number at LINE_FPS_NUMBER_X; the "ping" label and the ping number at fixed x, 4
# spaces after a 3-digit fps (the width of a text field read from Python is not reliable).
LINE_FPS_NUMBER_X = 22
LINE_PING_X = 57
LINE_PING_NUMBER_X = 86
# While the extended info key (Alt) is held, also one line: "fps <graph> 372    1% low 261    ping <graph> 74 ms",
# same gaps. Each part has its label at x 0 and (graph x, number x); 1% low is in the fps number's text field, the
# ping part at ALT_PING_X, 4 spaces after a 3-digit fps and 1% low. Graph y and size.
ALT_FPS = (22, 110)
ALT_PING = (29, 117)
ALT_PING_X = 222
GRAPH_Y = 3
GRAPH_SIZE = (80, 15)
# The graph scale goes from 0 to the highest point shown times this, so the line never touches the top.
GRAPH_HEADROOM = 1.1

# BigWorld.statPing() returns this while there is no ping yet (connecting, loading the battle).
PING_NONE = 999.0

# Look: the game's own panel font; the numbers and the labels ("fps", "1% low", "ping", "ms") pure white, like the
# panel's label picture; the graphs in saturated orange, which stands out against the sky.
# Text shadow, a DropShadowFilter like the game's own panel text has (read from the game in 2.4), but a little
# darker: strength 0.8 instead of 0.6. Distance, angle, colour, alpha, blur, strength, quality.
TEXT_SHADOW = (1.0, 90.0, 0x000000, 1.0, 4.0, 0.8, 2)
# Labels.
LABEL_HTML = u'<font face="$FieldFont" size="15" color="#FFFFFF">%s</font>'
FPS_LABEL_HTML = LABEL_HTML % u'fps'
PING_LABEL_HTML = LABEL_HTML % u'ping'
NUMBER_HTML = u'<font face="$FieldFont" size="15" color="#FFFFFF">%s</font>'
# "ms" right after the ping number in extended mode, in the same text field. The space is of a smaller font size, so
# the gap is 4 px as in the game's panel and not 6.
MS_HTML = u'<font face="$FieldFont" size="8"> </font>' + LABEL_HTML % u'ms'
# 1% low in extended mode, after the fps number in the same text field: "    1% low 261" (%% for the later
# formatting).
LOW_HTML = LABEL_HTML % u'    1%% low ' + NUMBER_HTML
# Added at the end of the extended line once the frame callback has been out of step with the game's frames at
# least once this battle.
DESYNC_HTML = '<font face="$FieldFont" size="15" color="#FF5A4F">   desync %d</font>'
# Graph look: line (thickness, colour, alpha), fill under the line (colour, alpha), dot on the newest point
# (colour, alpha, radius).
GRAPH_LOOK = ((1.3, 0xFF8A1F, 1.0), (0xFF8A1F, 0.3), (0xFF8A1F, 1.0, 1.8))
# Light dark outline of the graph line, the same line drawn wider under it: thickness, colour, alpha.
GRAPH_OUTLINE = (3.0, 0x000000, 0.35)
