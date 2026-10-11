# -*- coding: utf-8 -*-
"""Settings: timing, statistics windows, layout and look."""

# Same rate as the game's own debug panel (debug_ctrl.DebugController).
UPDATE_INTERVAL = 0.2
# FPS is counted over the frames of the last FPS_WINDOW seconds.
FPS_WINDOW = 1.0
# The game's own FPS/ping panel is hidden; the view takes its place.
HIDE_GAME_PANEL = True

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
# Layout in Flash pixels of the battle page (scaled with the game's interface scale), in place of the game's own
# FPS/ping panel at (0, 2). Container position: the text starts where the game's panel text did.
VIEW_POSITION = (9, 2)
# Normal mode: one line, "372fps    74ms ●"; in a replay "367fps / 255replay    45ms ●" (the measured FPS, then the
# one recorded in the replay). While the extended info key (Alt) is held, also one line:
# "<graph> 372fps / 261low    <graph> 74ms <lag ticks> ●"; in a replay "<graph> 367fps / 290low / 255replay ...".
# Gaps: between a graph and its number, between the fps and the ping parts, between the ping text and the lamp,
# between the ping text and the lag ticks, between the lag ticks and the lamp.
GAP_GRAPH = 7
GAP_PART = 16
GAP_LAMP = 12
GAP_TICKS = 7
GAP_TICKS_LAMP = 5
# Graphs and lag ticks: y and size; the lamp is centred on them.
GRAPH_Y = 3
GRAPH_SIZE = (64, 15)
# The graph scale goes from 0 to the highest point shown times this, so the line never touches the top.
GRAPH_HEADROOM = 1.1

# BigWorld.statPing() returns this while there is no ping yet (connecting, loading the battle).
PING_NONE = 999.0

# Look: the game's own panel font, all text pure white like the panel's label picture. Numbers 15 px, the helper
# text after a number ("fps", "low", "replay", "ms") 12 px on the same baseline, 2 px after it; the values of one
# part are split by a 12 px "/" with 5 px on both sides. The gaps are spaces of a smaller font size (half the size
# in px), so a size 4 space is 2 px.
NUMBER_HTML = u'<font face="$FieldFont" size="15" color="#FFFFFF">%s</font>'
UNIT_HTML = u'<font face="$FieldFont" size="4"> </font><font face="$FieldFont" size="12" color="#FFFFFF">%s</font>'
SEPARATOR_HTML = (u'<font face="$FieldFont" size="10"> </font>'
                  u'<font face="$FieldFont" size="12" color="#FFFFFF">/</font>'
                  u'<font face="$FieldFont" size="10"> </font>')
# Text widths: Python cannot read the width of a shown text field reliably, so the width of each digit, helper text
# and separator is measured once when the view is created, and these are used if that fails: digit, then the texts.
TEXT_WIDTHS = (8.0, {u'fps': 18.0, u'low': 20.0, u'replay': 36.0, u'ms': 17.0, u'/': 14.0})
# Text shadow, a DropShadowFilter like the game's own panel text has (read from the game in 2.4), but a little
# darker: strength 0.8 instead of 0.6. Distance, angle, colour, alpha, blur, strength, quality.
TEXT_SHADOW = (1.0, 90.0, 0x000000, 1.0, 4.0, 0.8, 2)

# Graph look: line thickness, fill alpha under the line, radius of the dot on the newest point, and a light dark
# outline of the line (the same line drawn wider under it: thickness, colour, alpha).
GRAPH_LINE = 1.3
GRAPH_FILL_ALPHA = 0.3
GRAPH_DOT = 1.8
GRAPH_OUTLINE = (3.0, 0x000000, 0.35)
# The FPS graph is white.
FPS_GRAPH_COLOUR = 0xFFFFFF
# The ping graph is coloured by value, by the scale the game itself uses for the ping of the servers in the hangar
# (predefined_hosts.py: up to 59 ms good, up to 119 normal, then high): (from ms, colour). Each segment of the
# graph and the fill under it get the colour of its higher end.
PING_ZONES = ((0, 0x3CCF4E), (60, 0xFFD23F), (120, 0xEF3B2D))

# Lag: the lamp is green while the server's updates come, red while they do not (BigWorld.statLagDetected(), the
# game panel's lamp): radius and outline (thickness, colour, alpha).
LAG_COLOURS = (0x3CCF4E, 0xEF3B2D)
LAMP_RADIUS = 4.0
LAMP_OUTLINE = (1.5, 0x000000, 0.7)
# Lag ticks, one per graph point (red if there was lag in that second): tick width, height without lag (with lag the
# full graph height), and the dark outline under each tick (width, colour, alpha).
TICK_WIDTH = 1.0
TICK_HEIGHT = 5.0
TICK_OUTLINE = (1.6, 0x000000, 0.45)
