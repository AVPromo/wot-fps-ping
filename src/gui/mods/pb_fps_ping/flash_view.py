# -*- coding: utf-8 -*-
"""The text and the graph, drawn with Flash (Scaleform) objects of the battle page."""
import logging

from gui.mods.pb_fps_ping.config import (GRAPH_DOT, GRAPH_FILL, GRAPH_HEADROOM, GRAPH_LINE, GRAPH_POINTS,
                                         GRAPH_POSITION, GRAPH_SIZE, LABEL_HTML, LOW_HTML, LOW_TEXT_X, NUMBER_HTML,
                                         NUMBER_WIDTH, NUMBER_X, VIEW_POSITION)

_logger = logging.getLogger('pb.fps_ping')

# Flash class names of Vector.<int> and Vector.<Number> as the game's class factory finds them.
_VECTOR_INT = '__AS3__.vec::Vector$int'
_VECTOR_NUMBER = '__AS3__.vec::Vector$double'


def _fmtInt(fps):
    return '%.0f' % fps if fps is not None else '-'


def _refill(vector, values):
    # Replaces the contents of a Flash vector in two calls.
    vector.length = 0
    vector.push(*values)


class FlashView(object):
    # One row of Flash objects on the battle page, next to the game's own FPS/ping panel: "fps" and the number,
    # and in extended mode (while Alt is held) the graph between them and the 1% low text after the number.
    # The whole row is hidden until there is an FPS value to show, and again when the battle loop stops.
    # Python cannot construct Flash objects itself; the game's class factory (App.utils.classFactory) does it.

    def __init__(self):
        self._container = None
        self._labelText = None
        self._numberText = None
        self._graph = None
        self._lowText = None
        self._extended = False
        self._shown = False
        # Flash vectors for Graphics.drawPath: fill commands, line commands and the points both use;
        # None if unavailable. The commands depend only on the number of points.
        self._paths = None
        self._pathPoints = 0

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
        container.visible = False
        self._shown = False
        try:
            # Same drop shadow as the game's panel text.
            filters = flashObject.fpsTF.filters
        except Exception:
            _logger.exception('cannot read the text filters of the game panel')
            filters = None
        labelText = self._createText(factory, filters)
        labelText.htmlText = LABEL_HTML
        numberText = self._createText(factory, filters)
        numberText.autoSize = 'none'
        numberText.width = NUMBER_WIDTH
        numberText.height = 22
        graph = factory.getObject('flash.display.Shape')
        graph.x, graph.y = GRAPH_POSITION
        lowText = self._createText(factory, filters)
        lowText.x = LOW_TEXT_X
        for child in (labelText, numberText, graph, lowText):
            container.addChild(child)
        flashObject.parent.addChild(container)
        self._container, self._labelText, self._numberText = container, labelText, numberText
        self._graph, self._lowText = graph, lowText
        self.setExtended(False)
        self._paths = self._createPaths(factory)
        self._pathPoints = 0
        _logger.info('view created, drawPath vectors %s', 'ready' if self._paths else 'unavailable')

    def detach(self):
        container = self._container
        if container is None:
            return
        self._container = self._labelText = self._numberText = self._graph = self._lowText = self._paths = None
        self._extended = False
        self._shown = False
        try:
            parent = container.parent
            if parent is not None:
                parent.removeChild(container)
        except Exception:
            _logger.exception('cannot remove the view')

    def setExtended(self, extended):
        self._extended = extended
        if self._container is None:
            return
        self._numberText.x = NUMBER_X[1 if extended else 0]
        self._graph.visible = extended
        self._lowText.visible = extended

    def updateFps(self, fps):
        if self._container is None:
            return
        if fps is None:
            self.hide()
            return
        self._numberText.htmlText = NUMBER_HTML % _fmtInt(fps)
        if not self._shown:
            self._container.visible = self._shown = True

    def hide(self):
        if self._container is not None and self._shown:
            self._container.visible = self._shown = False

    def updateLow(self, low):
        if self._container is None or not self._extended:
            return
        self._lowText.htmlText = LOW_HTML % _fmtInt(low)

    def updateGraph(self, points):
        if self._container is None or not self._extended:
            return
        graphics = self._graph.graphics
        width, height = GRAPH_SIZE
        graphics.clear()
        scale = max(points) * GRAPH_HEADROOM if len(points) >= 2 else 0.0
        if scale <= 0.0:
            return
        # Newest point at the right edge, one step per point.
        step = float(width) / (GRAPH_POINTS - 1)
        left = width - step * (len(points) - 1)
        coords = [(left + i * step, height * (1.0 - fps / scale)) for i, fps in enumerate(points)]
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
    def _createText(factory, filters):
        text = factory.getObject('flash.text.TextField')
        text.selectable = False
        text.autoSize = 'left'
        if filters is not None:
            text.filters = filters
        return text

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
        # corners with moveTo, so the fill edges are not outlined.
        fillCommands, lineCommands, data = self._paths
        count = len(coords)
        if count != self._pathPoints:
            _refill(fillCommands, [1] + [2] * (count + 1))
            _refill(lineCommands, [1, 1] + [2] * (count - 1) + [1])
            self._pathPoints = count
        _refill(data, [coords[0][0], height] + [value for point in coords for value in point] + [coords[-1][0], height])
        graphics.beginFill(*GRAPH_FILL)
        graphics.drawPath(fillCommands, data)
        graphics.endFill()
        graphics.lineStyle(*GRAPH_LINE)
        graphics.drawPath(lineCommands, data)
        self._drawDot(graphics, coords[-1])

    def _drawLines(self, graphics, coords, height):
        # Fallback: one Flash call per point.
        graphics.beginFill(*GRAPH_FILL)
        graphics.moveTo(coords[0][0], height)
        for x, y in coords:
            graphics.lineTo(x, y)
        graphics.lineTo(coords[-1][0], height)
        graphics.endFill()
        graphics.lineStyle(*GRAPH_LINE)
        graphics.moveTo(*coords[0])
        for x, y in coords[1:]:
            graphics.lineTo(x, y)
        self._drawDot(graphics, coords[-1])

    @staticmethod
    def _drawDot(graphics, point):
        colour, alpha, radius = GRAPH_DOT
        graphics.lineStyle()
        graphics.beginFill(colour, alpha)
        graphics.drawCircle(point[0], point[1], radius)
        graphics.endFill()
