# -*- coding: utf-8 -*-
"""The texts, the graphs and the lag lamp, drawn with Flash (Scaleform) objects of the battle page."""
import logging

from gui.mods.sagtary_fps_ping.config import (FPS_GRAPH_COLOUR, GAP_GRAPH, GAP_LAMP, GAP_PART, GAP_TICKS,
                                         GAP_TICKS_LAMP, GRAPH_DOT, GRAPH_FILL_ALPHA, GRAPH_HEADROOM, GRAPH_LINE,
                                         GRAPH_OUTLINE, GRAPH_POINTS, GRAPH_SIZE, GRAPH_Y, LAG_COLOURS, LAMP_OUTLINE,
                                         LAMP_RADIUS, NUMBER_HTML, PING_ZONES, SEPARATOR_HTML, TEXT_SHADOW,
                                         TEXT_WIDTHS, TICK_HEIGHT, TICK_OUTLINE, TICK_WIDTH, UNIT_HTML,
                                         VIEW_POSITION)

_logger = logging.getLogger('sagtary.fps_ping')

# Flash class names of Vector.<int> and Vector.<Number> as the game's class factory finds them.
_VECTOR_INT = '__AS3__.vec::Vector$int'
_VECTOR_NUMBER = '__AS3__.vec::Vector$double'
# The empty space a Flash text field keeps around its text.
_GUTTER = 2
_DIGITS = u'0123456789'


def _fmtInt(value):
    return u'%.0f' % value if value is not None else u'-'


def _refill(vector, values):
    # Replaces the contents of a Flash vector in two calls.
    vector.length = 0
    vector.push(*values)


def _createText(factory, filters):
    text = factory.getObject('flash.text.TextField')
    text.selectable = False
    text.autoSize = 'left'
    if filters is not None:
        text.filters = filters
    return text


def _createShadow(factory):
    # Our own text shadow, a DropShadowFilter with the TEXT_SHADOW settings; None if it cannot be made.
    try:
        shadow = factory.getObject('flash.filters.DropShadowFilter')
        if shadow is None:
            return None
        (shadow.distance, shadow.angle, shadow.color, shadow.alpha, blur, shadow.strength,
         shadow.quality) = TEXT_SHADOW
        shadow.blurX = shadow.blurY = blur
        return shadow
    except Exception:
        _logger.exception('cannot create the text shadow, using the game panel one')
        return None


def _createVectors(factory):
    # Flash vectors for Graphics.drawPath: fill commands, line commands and the points; None if unavailable.
    try:
        vectors = (factory.getObject(_VECTOR_INT), factory.getObject(_VECTOR_INT), factory.getObject(_VECTOR_NUMBER))
    except Exception:
        _logger.exception('cannot create Flash vectors for drawPath')
        return None
    return vectors if all(vector is not None for vector in vectors) else None


def _zoneColour(value):
    colour = PING_ZONES[0][1]
    for start, zoneColour in PING_ZONES:
        if value >= start:
            colour = zoneColour
    return colour


class _TextWidths(object):
    # Widths of the pieces of a value text: each digit of NUMBER_HTML, each helper text of UNIT_HTML with its gap,
    # and SEPARATOR_HTML. Measured once, each on a new text field that is not shown: a text field keeps the
    # textWidth of its first text when the text changes. TEXT_WIDTHS if that fails.

    def __init__(self, factory):
        digit, units = TEXT_WIDTHS
        self._digits = dict.fromkeys(_DIGITS, digit)
        self._units = dict(units)
        try:
            digits = dict((char, self._measure(factory, NUMBER_HTML % (char * 10)) / 10.0) for char in _DIGITS)
            units = dict((unit, self._measure(factory, SEPARATOR_HTML if unit == u'/' else UNIT_HTML % unit))
                         for unit in self._units)
        except Exception:
            _logger.exception('cannot measure the text, using the default widths')
            return
        # All units of the same width means the measuring did not work.
        if (all(3.0 <= width <= 20.0 for width in digits.values()) and all(width > 0.0 for width in units.values())
                and len(set(units.values())) > 1):
            self._digits, self._units = digits, units
            _logger.info('text widths: digits %s, %s', ' '.join('%.1f' % digits[char] for char in _DIGITS),
                         ', '.join('%s %.1f' % (unit, width) for unit, width in sorted(units.items())))
        else:
            _logger.warning('text widths look wrong (digits %s, %s), using the defaults', digits, units)

    @staticmethod
    def _measure(factory, html):
        text = factory.getObject('flash.text.TextField')
        text.autoSize = 'left'
        text.htmlText = html
        return float(text.textWidth)

    def number(self, number):
        return sum(self._digits.get(char, self._digits[u'0']) for char in number)

    def unit(self, unit):
        return self._units[unit]


class _Value(object):
    # A text field with one or more values, "367fps / 290 1% / 255replay": each value a number with small helper
    # text after it, values split by a "/". Knows the width of its text from _TextWidths; the text is set only when
    # it changes.

    def __init__(self, factory, filters, widths):
        self.text = _createText(factory, filters)
        self._widths = widths
        self._values = None
        self.width = 0.0
        self._x = None

    def set(self, values):
        # values: (number or None, helper text) pairs.
        values = tuple((_fmtInt(number), unit) for number, unit in values)
        if values == self._values:
            return
        self._values = values
        self.text.htmlText = SEPARATOR_HTML.join(NUMBER_HTML % number + UNIT_HTML % unit for number, unit in values)
        widths = self._widths
        self.width = (sum(widths.number(number) + widths.unit(unit) for number, unit in values) +
                      widths.unit(u'/') * (len(values) - 1))

    def place(self, x):
        # x of the text itself; the field starts a gutter before it.
        if x != self._x:
            self.text.x = x - _GUTTER
            self._x = x


class _Graph(object):
    # A line graph of the last GRAPH_POINTS values, newest at the right edge: fill under the line, a light dark
    # outline, the line, a dot on the newest point. One colour, or with zones each segment between two points, with
    # the fill under it, gets the zone colour of its higher end, so a spike is coloured down to the bottom. Segments
    # of one colour in a row are drawn as one run; all runs of one colour in one Graphics.drawPath call.

    def __init__(self, factory, colour=None, zones=False):
        self.shape = factory.getObject('flash.display.Shape')
        self.shape.y = GRAPH_Y
        self._colour = colour
        self._zones = zones
        self._paths = _createVectors(factory)

    @property
    def drawPath(self):
        return self._paths is not None

    def draw(self, points):
        graphics = self.shape.graphics
        width, height = GRAPH_SIZE
        graphics.clear()
        scale = max(points) * GRAPH_HEADROOM if len(points) >= 2 else 0.0
        if scale <= 0.0:
            return
        step = float(width) / (GRAPH_POINTS - 1)
        left = width - step * (len(points) - 1)
        coords = [(left + i * step, height * (1.0 - value / scale)) for i, value in enumerate(points)]
        # {colour: [(first point, last point) of each run]}
        runs = {}
        if self._zones:
            colours = [_zoneColour(max(points[i], points[i + 1])) for i in range(len(points) - 1)]
            start = 0
            for index in range(1, len(colours) + 1):
                if index == len(colours) or colours[index] != colours[start]:
                    runs.setdefault(colours[start], []).append((start, index))
                    start = index
            dot = _zoneColour(points[-1])
        else:
            runs[self._colour] = [(0, len(coords) - 1)]
            dot = self._colour
        # Each run as a polyline of its points, and as a polygon closed along the bottom for the fill.
        lines = dict((colour, [coords[first:last + 1] for first, last in spans]) for colour, spans in runs.items())
        fills = dict((colour, [[(coords[first][0], height)] + coords[first:last + 1] + [(coords[last][0], height)]
                               for first, last in spans]) for colour, spans in runs.items())
        if self._paths is not None:
            try:
                self._drawAll(graphics, coords, fills, lines, dot, self._drawShapesPath)
                return
            except Exception:
                _logger.exception('drawPath failed, drawing with lineTo')
                self._paths = None
                graphics.clear()
        self._drawAll(graphics, coords, fills, lines, dot, self._drawShapesLines)

    def _drawAll(self, graphics, coords, fills, lines, dot, drawShapes):
        for colour, shapes in fills.items():
            graphics.beginFill(colour, GRAPH_FILL_ALPHA)
            drawShapes(graphics, shapes)
            graphics.endFill()
        # The line's dark outline: the whole line drawn wider under the coloured runs.
        graphics.lineStyle(*GRAPH_OUTLINE)
        drawShapes(graphics, [coords])
        for colour, shapes in lines.items():
            graphics.lineStyle(GRAPH_LINE, colour, 1.0)
            drawShapes(graphics, shapes)
        graphics.lineStyle()
        graphics.beginFill(dot, 1.0)
        graphics.drawCircle(coords[-1][0], coords[-1][1], GRAPH_DOT)
        graphics.endFill()

    def _drawShapesPath(self, graphics, shapes):
        # All shapes in one call: Graphics.drawPath takes all points at once (command 1 = moveTo, 2 = lineTo).
        commands, _, data = self._paths
        _refill(commands, [command for shape in shapes for command in [1] + [2] * (len(shape) - 1)])
        _refill(data, [value for shape in shapes for point in shape for value in point])
        graphics.drawPath(commands, data)

    @staticmethod
    def _drawShapesLines(graphics, shapes):
        # Fallback: one Flash call per point.
        for shape in shapes:
            graphics.moveTo(*shape[0])
            for x, y in shape[1:]:
                graphics.lineTo(x, y)


class _LagTicks(object):
    # One tick per graph point, newest at the right edge: short and green without lag in that second, full height
    # and red with lag. Each tick has a dark outline under it.

    def __init__(self, factory):
        self.shape = factory.getObject('flash.display.Shape')
        self.shape.y = GRAPH_Y
        self._paths = _createVectors(factory)

    def draw(self, points):
        graphics = self.shape.graphics
        graphics.clear()
        if not points:
            return
        width, height = GRAPH_SIZE
        step = float(width) / GRAPH_POINTS
        outlineWidth, outlineColour, outlineAlpha = TICK_OUTLINE
        outlines, ticks = [], ([], [])
        for index, lag in enumerate(points):
            x = width - step * (len(points) - index)
            tickHeight = height if lag else TICK_HEIGHT
            outlines.append((x, height - tickHeight - 0.5, outlineWidth, tickHeight + 0.5))
            ticks[1 if lag else 0].append((x + (outlineWidth - TICK_WIDTH) / 2.0, height - tickHeight, TICK_WIDTH,
                                           tickHeight))
        for rects, colour, alpha in ((outlines, outlineColour, outlineAlpha), (ticks[0], LAG_COLOURS[0], 1.0),
                                     (ticks[1], LAG_COLOURS[1], 1.0)):
            if rects:
                self._fillRects(graphics, rects, colour, alpha)

    def _fillRects(self, graphics, rects, colour, alpha):
        graphics.beginFill(colour, alpha)
        if self._paths is not None:
            try:
                # Each rectangle: moveTo and four lineTo.
                commands, _, data = self._paths
                _refill(commands, [1, 2, 2, 2, 2] * len(rects))
                _refill(data, [value for x, y, w, h in rects
                               for value in (x, y, x + w, y, x + w, y + h, x, y + h, x, y)])
                graphics.drawPath(commands, data)
                graphics.endFill()
                return
            except Exception:
                _logger.exception('drawPath failed for the lag ticks, drawing with drawRect')
                self._paths = None
        for rect in rects:
            graphics.drawRect(*rect)
        graphics.endFill()


class _Lamp(object):
    # The lag lamp, a circle with a dark outline, green or red. Redrawn only when the state changes.

    def __init__(self, factory):
        self.shape = factory.getObject('flash.display.Shape')
        self.shape.y = GRAPH_Y + GRAPH_SIZE[1] / 2.0
        self._lag = None
        self._x = None

    def set(self, lag):
        if lag == self._lag:
            return
        self._lag = lag
        graphics = self.shape.graphics
        graphics.clear()
        graphics.lineStyle(*LAMP_OUTLINE)
        graphics.beginFill(LAG_COLOURS[1 if lag else 0], 1.0)
        graphics.drawCircle(0, 0, LAMP_RADIUS)
        graphics.endFill()

    def place(self, x):
        # x of the lamp's left edge.
        if x != self._x:
            self.shape.x = x + LAMP_RADIUS
            self._x = x


class FlashView(object):
    # Flash objects on the battle page, next to the game's own FPS/ping panel, in one line.
    # Normal mode: "372fps    74ms ●". Extended mode (while Alt is held): each part with its graph before it, 1% low
    # after the fps, the lag ticks before the lamp: "<graph> 372fps / 261 1%    <graph> 74ms <ticks> ●". In a replay the fps part also shows the FPS recorded in the replay: "367fps / 255replay".
    # The ping part and the lamp are hidden while there is no ping, everything while there is no FPS.
    # Python cannot construct Flash objects itself; the game's class factory (App.utils.classFactory) does it.

    def __init__(self):
        self._container = None
        self._extended = False
        self._fps = None
        self._low = None
        self._replayFps = None
        self._ping = None
        self._lag = False
        # Visibility of each child as last set.
        self._visible = None

    @property
    def attached(self):
        return self._container is not None

    @property
    def extended(self):
        return self._extended

    def attach(self, panel):
        self.detach()
        flashObject = panel.flashObject
        factory = flashObject.root.utils.classFactory
        container = factory.getObject('flash.display.Sprite')
        container.x, container.y = VIEW_POSITION
        container.mouseEnabled = False
        container.mouseChildren = False
        shadow = _createShadow(factory)
        if shadow is not None:
            filters = [shadow]
        else:
            try:
                # The drop shadow of the game's panel text (a Flash array comes to Python as a list).
                filters = flashObject.fpsTF.filters
            except Exception:
                _logger.exception('cannot read the text filters of the game panel')
                filters = None
        widths = _TextWidths(factory)
        self._fpsGraph = _Graph(factory, colour=FPS_GRAPH_COLOUR)
        self._fpsText = _Value(factory, filters, widths)
        self._pingGraph = _Graph(factory, zones=True)
        self._pingText = _Value(factory, filters, widths)
        self._lagTicks = _LagTicks(factory)
        self._lamp = _Lamp(factory)
        # x of the children placed by _place, as last set.
        self._x = {}
        self._children = (self._fpsGraph.shape, self._fpsText.text, self._pingGraph.shape, self._pingText.text,
                          self._lagTicks.shape, self._lamp.shape)
        for child in self._children:
            child.visible = False
            container.addChild(child)
        flashObject.parent.addChild(container)
        self._container = container
        self._visible = (False,) * len(self._children)
        _logger.info('view created, drawPath vectors %s',
                     'ready' if self._fpsGraph.drawPath and self._pingGraph.drawPath else 'unavailable')

    def detach(self):
        container = self._container
        if container is None:
            return
        self._container = self._visible = None
        self._extended = False
        try:
            parent = container.parent
            if parent is not None:
                parent.removeChild(container)
        except Exception:
            _logger.exception('cannot remove the view')

    def setExtended(self, extended):
        self._extended = extended
        self._show()

    def update(self, fps, low, ping, lag, replayFps=None):
        self._fps, self._low, self._ping, self._lag, self._replayFps = fps, low, ping, lag, replayFps
        self._show()

    def hide(self):
        self.update(None, None, None, False)

    def updateGraphs(self, fpsPoints, pingPoints, lagPoints):
        if self._container is None or not self._extended:
            return
        self._fpsGraph.draw(fpsPoints)
        self._pingGraph.draw(pingPoints)
        self._lagTicks.draw(lagPoints)

    def _show(self):
        # Sets the texts of the current mode, lays the line out from the left and shows only the parts with a value.
        if self._container is None:
            return
        extended, hasFps, hasPing = self._extended, self._fps is not None, self._ping is not None
        x = 0.0
        if hasFps:
            values = [(self._fps, u'fps')]
            if extended and self._low is not None:
                values.append((self._low, u'1%'))
            if self._replayFps is not None:
                values.append((self._replayFps, u'replay'))
            self._fpsText.set(values)
            if extended:
                x += GRAPH_SIZE[0] + GAP_GRAPH
            self._fpsText.place(x)
            x += self._fpsText.width + GAP_PART
        if hasFps and hasPing:
            if extended:
                self._place(self._pingGraph.shape, x)
                x += GRAPH_SIZE[0] + GAP_GRAPH
            self._pingText.set([(self._ping, u'ms')])
            self._pingText.place(x)
            x += self._pingText.width
            if extended:
                x += GAP_TICKS
                self._place(self._lagTicks.shape, x)
                x += GRAPH_SIZE[0] + GAP_TICKS_LAMP
            else:
                x += GAP_LAMP
            self._lamp.set(self._lag)
            self._lamp.place(x)
        withPing = hasFps and hasPing
        visible = (extended and hasFps, hasFps, extended and withPing, withPing, extended and withPing, withPing)
        if visible != self._visible:
            for child, shown, wasShown in zip(self._children, visible, self._visible):
                if shown != wasShown:
                    child.visible = shown
            self._visible = visible

    def _place(self, child, x):
        # Sets child.x only when it changes.
        if self._x.get(id(child)) != x:
            child.x = x
            self._x[id(child)] = x
