# -*- coding: utf-8 -*-
"""The texts and the graphs, drawn with Flash (Scaleform) objects of the battle page."""
import logging

from gui.mods.pb_fps_ping.config import (ALT_FPS, ALT_PING, ALT_PING_X, DESYNC_HTML, FPS_LABEL_HTML, GRAPH_HEADROOM,
                                         GRAPH_LOOK, GRAPH_OUTLINE, GRAPH_POINTS, GRAPH_SIZE, GRAPH_Y,
                                         LINE_FPS_NUMBER_X, LINE_PING_NUMBER_X, LINE_PING_X, LOW_HTML, MS_HTML,
                                         NUMBER_HTML, PING_LABEL_HTML, TEXT_SHADOW, VIEW_POSITION)

_logger = logging.getLogger('pb.fps_ping')

# Flash class names of Vector.<int> and Vector.<Number> as the game's class factory finds them.
_VECTOR_INT = '__AS3__.vec::Vector$int'
_VECTOR_NUMBER = '__AS3__.vec::Vector$double'


def _fmtInt(value):
    return '%.0f' % value if value is not None else '-'


def _refill(vector, values):
    # Replaces the contents of a Flash vector in two calls.
    vector.length = 0
    vector.push(*values)


def _createText(factory, filters, html=None, x=0):
    text = factory.getObject('flash.text.TextField')
    text.selectable = False
    text.autoSize = 'left'
    text.x = x
    if filters is not None:
        text.filters = filters
    if html is not None:
        text.htmlText = html
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


class _Number(object):
    # A text field for a number and the text after it in the same field ("ms"); of fixed width if given, so what
    # follows does not move when the number gets longer. No positions depend on the text width: Python reads it wrong.
    # The text is set only when it changes.

    def __init__(self, factory, filters, html, x, width):
        self._html = html
        self.text = _createText(factory, filters, x=x)
        if width is not None:
            self.text.autoSize = 'none'
            self.text.width = width
            self.text.height = 22
        self._number = None

    def set(self, value, extra=''):
        number = (_fmtInt(value), extra)
        if number != self._number:
            self.text.htmlText = self._html % number[0] + extra
            self._number = number


class _Line(object):
    # Normal mode: one line, "fps 372    ping 74". The ping part is hidden while there is no ping.

    def __init__(self, factory, filters):
        self.sprite = factory.getObject('flash.display.Sprite')
        self.pingSprite = factory.getObject('flash.display.Sprite')
        self.fps = _Number(factory, filters, NUMBER_HTML, LINE_FPS_NUMBER_X, None)
        self.ping = _Number(factory, filters, NUMBER_HTML, LINE_PING_NUMBER_X, None)
        for child in (_createText(factory, filters, FPS_LABEL_HTML), self.fps.text, self.pingSprite):
            self.sprite.addChild(child)
        for child in (_createText(factory, filters, PING_LABEL_HTML, LINE_PING_X), self.ping.text):
            self.pingSprite.addChild(child)


class _Part(object):
    # Extended mode: the fps or ping part of the line, with the label, the graph and the number.

    def __init__(self, factory, filters, columns, labelHtml, numberHtml, numberWidth, look):
        # columns: (graph x, number x).
        self._look = look
        self.sprite = factory.getObject('flash.display.Sprite')
        self.number = _Number(factory, filters, numberHtml, columns[1], numberWidth)
        self._graph = factory.getObject('flash.display.Shape')
        self._graph.x, self._graph.y = columns[0], GRAPH_Y
        for child in (_createText(factory, filters, labelHtml), self._graph, self.number.text):
            self.sprite.addChild(child)
        # Flash vectors for Graphics.drawPath: fill commands, line commands and the points both use;
        # None if unavailable. The commands depend only on the number of points.
        self._paths = self._createPaths(factory)
        self._pathPoints = 0

    @property
    def drawPath(self):
        return self._paths is not None

    def drawGraph(self, points):
        graphics = self._graph.graphics
        width, height = GRAPH_SIZE
        graphics.clear()
        scale = max(points) * GRAPH_HEADROOM if len(points) >= 2 else 0.0
        if scale <= 0.0:
            return
        # Newest point at the right edge, one step per point.
        step = float(width) / (GRAPH_POINTS - 1)
        left = width - step * (len(points) - 1)
        coords = [(left + i * step, height * (1.0 - value / scale)) for i, value in enumerate(points)]
        if self._paths is not None:
            try:
                self._drawPaths(graphics, coords, height)
                return
            except Exception:
                _logger.exception('drawPath failed, drawing with lineTo')
                self._paths = None
                graphics.clear()
        self._drawLines(graphics, coords, height)

    @staticmethod
    def _createPaths(factory):
        try:
            paths = (factory.getObject(_VECTOR_INT), factory.getObject(_VECTOR_INT), factory.getObject(_VECTOR_NUMBER))
        except Exception:
            _logger.exception('cannot create Flash vectors for drawPath')
            return None
        return paths if all(vector is not None for vector in paths) else None

    def _drawPaths(self, graphics, coords, height):
        # Whole graph in a few calls: Graphics.drawPath takes all points at once (command 1 = moveTo, 2 = lineTo).
        # Fill and line share the points: bottom-left, the graph points, bottom-right. The line skips the bottom
        # corners with moveTo, so the fill edges are not outlined. The line's dark outline is the line drawn wider
        # first.
        line, fill, _ = self._look
        fillCommands, lineCommands, data = self._paths
        count = len(coords)
        if count != self._pathPoints:
            _refill(fillCommands, [1] + [2] * (count + 1))
            _refill(lineCommands, [1, 1] + [2] * (count - 1) + [1])
            self._pathPoints = count
        _refill(data, [coords[0][0], height] + [value for point in coords for value in point] + [coords[-1][0], height])
        graphics.beginFill(*fill)
        graphics.drawPath(fillCommands, data)
        graphics.endFill()
        for style in (GRAPH_OUTLINE, line):
            graphics.lineStyle(*style)
            graphics.drawPath(lineCommands, data)
        self._drawDot(graphics, coords[-1])

    def _drawLines(self, graphics, coords, height):
        # Fallback: one Flash call per point.
        line, fill, _ = self._look
        graphics.beginFill(*fill)
        graphics.moveTo(coords[0][0], height)
        for x, y in coords:
            graphics.lineTo(x, y)
        graphics.lineTo(coords[-1][0], height)
        graphics.endFill()
        for style in (GRAPH_OUTLINE, line):
            graphics.lineStyle(*style)
            graphics.moveTo(*coords[0])
            for x, y in coords[1:]:
                graphics.lineTo(x, y)
        self._drawDot(graphics, coords[-1])

    def _drawDot(self, graphics, point):
        colour, alpha, radius = self._look[2]
        graphics.lineStyle()
        graphics.beginFill(colour, alpha)
        graphics.drawCircle(point[0], point[1], radius)
        graphics.endFill()


class FlashView(object):
    # Flash objects on the battle page, next to the game's own FPS/ping panel. Normal mode: one line, fps and ping.
    # Extended mode (while Alt is held): also one line, fps and ping each with its graph before the number,
    # and 1% low after the fps number; "desync N" at the end. Each part is hidden while its value is
    # missing.
    # Python cannot construct Flash objects itself; the game's class factory (App.utils.classFactory) does it.

    def __init__(self):
        self._container = None
        self._line = None
        self._fpsPart = None
        self._pingPart = None
        self._extended = False
        self._fps = None
        self._ping = None
        # Shown after the ping in extended mode.
        self._desync = ''
        # Shown after the fps number in extended mode: "    1% low 261".
        self._low = ''
        # Visibility of (line, its ping part, extended fps part, extended ping part) as last set.
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
        line = _Line(factory, filters)
        fpsPart = _Part(factory, filters, ALT_FPS, FPS_LABEL_HTML, NUMBER_HTML, None, GRAPH_LOOK)
        pingPart = _Part(factory, filters, ALT_PING, PING_LABEL_HTML, NUMBER_HTML + MS_HTML, None,
                         GRAPH_LOOK)
        pingPart.sprite.x = ALT_PING_X
        for child in (line.sprite, fpsPart.sprite, pingPart.sprite):
            child.visible = False
            container.addChild(child)
        flashObject.parent.addChild(container)
        self._container, self._line, self._fpsPart, self._pingPart = container, line, fpsPart, pingPart
        self._visible = (False, True, False, False)
        _logger.info('view created, drawPath vectors %s',
                     'ready' if fpsPart.drawPath and pingPart.drawPath else 'unavailable')

    def detach(self):
        container = self._container
        if container is None:
            return
        self._container = self._line = self._fpsPart = self._pingPart = self._visible = None
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

    def update(self, fps, low, ping, desyncs):
        self._fps, self._ping = fps, ping
        self._low = LOW_HTML % _fmtInt(low)
        self._desync = DESYNC_HTML % desyncs if desyncs else ''
        self._show()

    def hide(self):
        self.update(None, None, None, 0)

    def updateGraphs(self, fpsPoints, pingPoints):
        if self._container is None or not self._extended:
            return
        self._fpsPart.drawGraph(fpsPoints)
        self._pingPart.drawGraph(pingPoints)

    def _show(self):
        # Sets the numbers of the current mode and shows only the parts with a value.
        if self._container is None:
            return
        fps, ping, extended = self._fps, self._ping, self._extended
        if extended:
            if fps is not None:
                self._fpsPart.number.set(fps, self._low)
            if ping is not None:
                self._pingPart.number.set(ping, self._desync)
        elif fps is not None:
            self._line.fps.set(fps)
            if ping is not None:
                self._line.ping.set(ping)
        visible = (not extended and fps is not None, ping is not None,
                   extended and fps is not None, extended and ping is not None)
        if visible != self._visible:
            for sprite, shown, wasShown in zip((self._line.sprite, self._line.pingSprite, self._fpsPart.sprite,
                                                self._pingPart.sprite), visible, self._visible):
                if shown != wasShown:
                    sprite.visible = shown
            self._visible = visible
