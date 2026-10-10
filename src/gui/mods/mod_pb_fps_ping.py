# -*- coding: utf-8 -*-
"""FPS & Ping by PB: battle FPS and ping indicator for World of Tanks."""
import logging
import time
from collections import deque

import BigWorld
import GUI
from gui.Scaleform.daapi.view.battle.shared.debug_panel import DebugPanel
from PlayerEvents import g_playerEvents

__version__ = '0.7.2'

_logger = logging.getLogger('pb.fps_ping')

# Same rate as the game's own debug panel (debug_ctrl.DebugController).
_UPDATE_INTERVAL = 0.2
# FPS is counted over the frames of the last _WINDOW seconds.
_WINDOW = 1.0
# Values go to game.log every N screen updates (once per second).
_LOG_EVERY = 5
# Text position in screen pixels from the top-left corner: just under the game's own FPS/ping panel.
_POSITION_PX = (4, 32)
# The game's own panel stays visible while the two are compared.
_HIDE_GAME_PANEL = False
# time.clock() is wall time only on Windows; elsewhere it is CPU time and runs slower than BigWorld.time().
# If it runs slower than this ratio, frames are timed by BigWorld.timeExact() (1 ms steps) instead.
_CLOCK_MIN_RATIO = 0.5
_CLOCK_CHECK_TIME = 1.0
# 1% low FPS: share of the window time, window length in whole seconds, and histogram bin width in seconds.
_LOW_SHARE = 0.01
_LOW_WINDOW = 30
_LOW_BIN = 0.00005
# FPS graph: one bar per _GRAPH_STEP seconds of frames, _GRAPH_BARS bars (30 s).
_GRAPH_STEP = 0.5
_GRAPH_BARS = 60
# Graph position and size in screen pixels: top-left corner under the text, width of one bar, height,
# and thickness of the line on top of the bars.
_GRAPH_POSITION_PX = (4, 70)
_GRAPH_BAR_PX = 2
_GRAPH_HEIGHT_PX = 30
_GRAPH_LINE_PX = 2
# The graph scale goes from 0 to the highest bar shown times this, so the line never touches the top.
_GRAPH_HEADROOM = 1.25
# Game font: Verdana 15 px, not bold, like the size of the game's own FPS/ping panel (default GUI.Text font is 20 px).
_FONT = 'verdana_small.font'
# Loading leaves long frames at the start of a battle; 1% low and the graph skip the first seconds.
_WARMUP = 3.0
# Plain white texture from the game, tinted by the component colour (r, g, b, a in 0..255).
_WHITE_TEXTURE = 'system/maps/col_white.dds'
_GRAPH_LINE_COLOUR = (244, 239, 232, 255)
_GRAPH_FILL_COLOUR = (244, 239, 232, 60)
_GRAPH_BACK_COLOUR = (0, 0, 0, 110)


class _LowFPS(object):
    # 1% low FPS over the last _LOW_WINDOW seconds, counted the way MSI Afterburner / RTSS do:
    # sort frames from the slowest, add up their times until the sum reaches _LOW_SHARE of the window time,
    # and take the FPS of the frame at that point.
    # Frames are not stored one by one: each second keeps a histogram {bin: [frames, time]} of frame times,
    # and the window total is the sum of the last _LOW_WINDOW second histograms.

    def __init__(self):
        self._seconds = deque()
        self._total = {}
        self._totalTime = 0.0
        self._secondEnd = None

    def reset(self):
        self._seconds.clear()
        self._total.clear()
        self._totalTime = 0.0
        self._secondEnd = None

    def add(self, now, frameTime):
        if self._secondEnd is None or now - self._secondEnd >= _LOW_WINDOW:
            self.reset()
            self._secondEnd = now + 1.0
            self._seconds.append({})
        while now >= self._secondEnd:
            self._secondEnd += 1.0
            self._seconds.append({})
            if len(self._seconds) > _LOW_WINDOW:
                self._drop(self._seconds.popleft())
        b = int(frameTime / _LOW_BIN)
        for histogram in (self._seconds[-1], self._total):
            entry = histogram.get(b)
            if entry is None:
                histogram[b] = [1, frameTime]
            else:
                entry[0] += 1
                entry[1] += frameTime
        self._totalTime += frameTime

    def fps(self):
        target = self._totalTime * _LOW_SHARE
        if target <= 0.0:
            return None
        summed = 0.0
        for b in sorted(self._total, reverse=True):
            frames, binTime = self._total[b]
            summed += binTime
            if summed >= target:
                return frames / binTime
        return None

    def _drop(self, histogram):
        for b, (frames, binTime) in histogram.iteritems():
            entry = self._total[b]
            entry[0] -= frames
            entry[1] -= binTime
            if entry[0] <= 0:
                del self._total[b]
        self._totalTime -= sum(binTime for _, binTime in histogram.itervalues())


class _FrameTimer(object):
    # Runs once per frame: a zero-delay callback that schedules itself again.
    # Keeps the frame times of the last _WINDOW seconds.

    def __init__(self):
        self._callbackID = None
        self._clock = time.clock
        self._clockName = 'time.clock()'
        self._clockCheck = None
        self._lastTime = None
        self._lastFrame = None
        # (end time, frame time) in seconds, and the sum of their frame times.
        self._frames = deque()
        self._framesTime = 0.0
        # Callback calls by frame number step: 1 = once per frame, 0 = twice in one frame, 2+ = frames skipped.
        self.stepOne = self.stepZero = self.stepMore = 0
        self.low = _LowFPS()
        # FPS of each finished _GRAPH_STEP, newest last; frames and time of the step being filled.
        self.points = deque(maxlen=_GRAPH_BARS)
        self._pointFrames = 0
        self._pointTime = 0.0
        self._warmupEnd = None

    @property
    def clockName(self):
        return self._clockName

    def start(self):
        self.stop()
        self._lastTime = None
        self._lastFrame = None
        self._frames.clear()
        self._framesTime = 0.0
        self.low.reset()
        self._resetPoints()
        self.stepOne = self.stepZero = self.stepMore = 0
        self._clockCheck = (self._clock(), BigWorld.time())
        self._warmupEnd = self._clock() + _WARMUP
        self._tick()

    def stop(self):
        if self._callbackID is not None:
            BigWorld.cancelCallback(self._callbackID)
            self._callbackID = None

    def fps(self):
        if not self._frames or self._framesTime <= 0.0:
            return None
        return len(self._frames) / self._framesTime

    def _tick(self):
        self._callbackID = None
        try:
            self._countStep(BigWorld.wg_getFrameTimestamp())
            now = self._clock()
            if self._lastTime is not None:
                self._addFrame(now, now - self._lastTime)
            self._lastTime = now
            if self._clockCheck is not None:
                self._checkClock(now)
        except Exception:
            _logger.exception('frame timer failed, stopped')
            return
        self._callbackID = BigWorld.callback(0.0, self._tick)

    def _countStep(self, frame):
        if self._lastFrame is not None:
            step = frame - self._lastFrame
            if step == 1:
                self.stepOne += 1
            elif step == 0:
                self.stepZero += 1
            else:
                self.stepMore += 1
        self._lastFrame = frame

    def _addFrame(self, now, frameTime):
        self._frames.append((now, frameTime))
        self._framesTime += frameTime
        if now >= self._warmupEnd:
            self.low.add(now, frameTime)
            self._pointFrames += 1
            self._pointTime += frameTime
            if self._pointTime >= _GRAPH_STEP:
                self.points.append(self._pointFrames / self._pointTime)
                self._pointFrames = 0
                self._pointTime = 0.0
        # Keep only frames that ended within the last _WINDOW seconds.
        while now - self._frames[0][0] >= _WINDOW:
            self._framesTime -= self._frames.popleft()[1]

    def _checkClock(self, now):
        clockStart, engineStart = self._clockCheck
        engineElapsed = BigWorld.time() - engineStart
        if engineElapsed < _CLOCK_CHECK_TIME:
            return
        self._clockCheck = None
        ratio = (now - clockStart) / engineElapsed
        if ratio >= _CLOCK_MIN_RATIO:
            _logger.info('clock %s ok, ratio to BigWorld.time() %.3f', self._clockName, ratio)
            return
        _logger.warning('clock %s runs at %.3f of BigWorld.time(), using BigWorld.timeExact()', self._clockName, ratio)
        self._clock = BigWorld.timeExact
        self._clockName = 'BigWorld.timeExact()'
        self._warmupEnd = self._clock() + _WARMUP
        self._lastTime = None
        self._frames.clear()
        self._framesTime = 0.0
        self.low.reset()
        self._resetPoints()

    def _resetPoints(self):
        self.points.clear()
        self._pointFrames = 0
        self._pointTime = 0.0


def _clipPosition(pixels):
    # GUI.Text position is in clip space: x and y from -1 to 1, (-1, 1) is the top-left corner.
    width, height = GUI.screenResolution()
    return -1.0 + 2.0 * pixels[0] / width, 1.0 - 2.0 * pixels[1] / height, 0


def _clipSize(pixels):
    width, height = GUI.screenResolution()
    return 2.0 * pixels[0] / width, 2.0 * pixels[1] / height


def _plainRect(colour, horizontalAnchor, verticalAnchor):
    rect = GUI.Simple(_WHITE_TEXTURE)
    rect.colour = colour
    rect.materialFX = GUI.Simple.eMaterialFX.BLEND
    rect.horizontalAnchor = horizontalAnchor
    rect.verticalAnchor = verticalAnchor
    GUI.addRoot(rect)
    return rect


class _Graph(object):
    # FPS graph, newest on the right: a line at each bar's value over a faint filled bar.
    # Scale is from 0 to the highest bar shown times _GRAPH_HEADROOM.

    def __init__(self):
        self._back = None
        self._fills = []
        self._lines = []

    def start(self):
        if self._back is not None:
            return
        self._back = _plainRect(_GRAPH_BACK_COLOUR, GUI.Simple.eHAnchor.LEFT, GUI.Simple.eVAnchor.TOP)
        self._fills = [_plainRect(_GRAPH_FILL_COLOUR, GUI.Simple.eHAnchor.LEFT, GUI.Simple.eVAnchor.BOTTOM)
                       for _ in range(_GRAPH_BARS)]
        self._lines = [_plainRect(_GRAPH_LINE_COLOUR, GUI.Simple.eHAnchor.LEFT, GUI.Simple.eVAnchor.BOTTOM)
                       for _ in range(_GRAPH_BARS)]

    def stop(self):
        for component in [self._back] + self._fills + self._lines:
            if component is not None:
                GUI.delRoot(component)
        self._back = None
        self._fills = []
        self._lines = []

    def update(self, points):
        if self._back is None:
            return
        left, top = _GRAPH_POSITION_PX
        self._back.position = _clipPosition((left, top))
        self._back.size = _clipSize((_GRAPH_BARS * _GRAPH_BAR_PX, _GRAPH_HEIGHT_PX))
        bottom = top + _GRAPH_HEIGHT_PX
        scale = max(points) * _GRAPH_HEADROOM if points else 0.0
        empty = _GRAPH_BARS - len(points)
        for i in range(_GRAPH_BARS):
            fill, line = self._fills[i], self._lines[i]
            shown = i >= empty and scale > 0.0
            fill.visible = line.visible = shown
            if not shown:
                continue
            x = left + i * _GRAPH_BAR_PX
            height = max(int(round(_GRAPH_HEIGHT_PX * points[i - empty] / scale)), _GRAPH_LINE_PX)
            fill.position = _clipPosition((x, bottom))
            fill.size = _clipSize((_GRAPH_BAR_PX, height))
            line.position = _clipPosition((x, bottom - height + _GRAPH_LINE_PX))
            line.size = _clipSize((_GRAPH_BAR_PX, _GRAPH_LINE_PX))


class _ColourProbe(object):
    # Temporary: squares under the graph, each set to red in a different way, to find which way of setting
    # a GUI.Simple colour works in the game. Their attributes go to game.log.

    def __init__(self):
        self._squares = []

    def start(self):
        if self._squares:
            return
        import Math
        red = (255, 0, 0, 255)
        variants = (
            ('white ints blend', _WHITE_TEXTURE, red, 'BLEND', False),
            ('white floats blend', _WHITE_TEXTURE, (255.0, 0.0, 0.0, 255.0), 'BLEND', False),
            ('white Vector4 blend', _WHITE_TEXTURE, Math.Vector4(255.0, 0.0, 0.0, 255.0), 'BLEND', False),
            ('no texture ints blend', '', red, 'BLEND', False),
            ('white ints solid', _WHITE_TEXTURE, red, 'SOLID', False),
            ('white ints no materialFX', _WHITE_TEXTURE, red, None, False),
            ('white ints after addRoot', _WHITE_TEXTURE, red, 'BLEND', True),
            ('black texture, no colour', 'system/maps/col_black.dds', None, None, False),
        )
        _logger.info('probe eMaterialFX: %s', [n for n in dir(GUI.Simple.eMaterialFX) if not n.startswith('_')])
        for i, (label, texture, colour, materialFX, afterAddRoot) in enumerate(variants):
            try:
                square = GUI.Simple(texture)
                square.horizontalAnchor = GUI.Simple.eHAnchor.LEFT
                square.verticalAnchor = GUI.Simple.eVAnchor.TOP
                if materialFX is not None and hasattr(GUI.Simple.eMaterialFX, materialFX):
                    square.materialFX = getattr(GUI.Simple.eMaterialFX, materialFX)
                if colour is not None and not afterAddRoot:
                    square.colour = colour
                GUI.addRoot(square)
                if colour is not None and afterAddRoot:
                    square.colour = colour
                left, top = _GRAPH_POSITION_PX
                square.position = _clipPosition((left + i * 16, top + _GRAPH_HEIGHT_PX + 6))
                square.size = _clipSize((14, 14))
                self._squares.append(square)
                _logger.info('probe square %d %s: colour=%r materialFX=%r textureName=%r size=%r widthMode=%r',
                             i, label, square.colour, square.materialFX, square.textureName, square.size,
                             getattr(square, 'widthMode', None))
            except Exception:
                _logger.exception('probe square %d %s failed', i, label)

    def stop(self):
        for square in self._squares:
            GUI.delRoot(square)
        self._squares = []


def _fmtFPS(fps):
    return '%.1f' % fps if fps is not None else '-'


def _fmtInt(fps):
    return '%.0f' % fps if fps is not None else '-'


class _Indicator(object):

    def __init__(self):
        self._text = None
        self._callbackID = None
        self._updates = 0
        self._frameTimer = _FrameTimer()
        self._graph = _Graph()
        self._colourProbe = _ColourProbe()
        # (BigWorld.time(), frame number) at the previous log line: reference FPS by the game's frame counter.
        self._counterStart = None

    def start(self):
        if self._text is not None:
            return
        text = GUI.Text('')
        text.multiline = True
        text.font = _FONT
        text.horizontalAnchor = GUI.Simple.eHAnchor.LEFT
        text.verticalAnchor = GUI.Simple.eVAnchor.TOP
        GUI.addRoot(text)
        self._text = text
        self._updates = 0
        self._counterStart = None
        self._graph.start()
        self._colourProbe.start()
        self._frameTimer.start()
        _logger.info('indicator started')
        self._update()

    def stop(self):
        self._frameTimer.stop()
        if self._callbackID is not None:
            BigWorld.cancelCallback(self._callbackID)
            self._callbackID = None
        self._graph.stop()
        self._colourProbe.stop()
        if self._text is not None:
            GUI.delRoot(self._text)
            self._text = None
            _logger.info('indicator stopped')

    def _update(self):
        self._callbackID = None
        try:
            fps = self._frameTimer.fps()
            low = self._frameTimer.low.fps()
            self._text.position = _clipPosition(_POSITION_PX)
            self._text.text = 'FPS %s\n1%% low %s' % (_fmtInt(fps), _fmtInt(low))
            self._graph.update(self._frameTimer.points)
            if self._updates % _LOG_EVERY == 0:
                self._log(fps, low)
            self._updates += 1
        except Exception:
            _logger.exception('update failed, indicator stopped')
            self.stop()
            return
        self._callbackID = BigWorld.callback(_UPDATE_INTERVAL, self._update)

    def _log(self, fps, low):
        now, frame = BigWorld.time(), BigWorld.wg_getFrameTimestamp()
        counterFPS = None
        if self._counterStart is not None and now > self._counterStart[0]:
            counterFPS = (frame - self._counterStart[1]) / (now - self._counterStart[0])
        self._counterStart = (now, frame)
        timer = self._frameTimer
        _logger.info('fps %s | counter %s | getFPS()[1] %.1f | 1%% low %s | frame steps 1: %d, 0: %d, 2+: %d | clock %s',
                     _fmtFPS(fps), _fmtFPS(counterFPS), BigWorld.getFPS()[1], _fmtFPS(low),
                     timer.stepOne, timer.stepZero, timer.stepMore, timer.clockName)


_indicator = _Indicator()
_originalPopulate = DebugPanel._populate


def _hiddenPopulate(self):
    # Hide the game's own FPS/ping panel; this mod shows its own text instead.
    _originalPopulate(self)
    try:
        self.flashObject.visible = False
    except Exception:
        _logger.exception('cannot hide the game debug panel')


def init():
    # Called by gui.mods after all mods are imported.
    if _HIDE_GAME_PANEL:
        DebugPanel._populate = _hiddenPopulate
    g_playerEvents.onAvatarReady += _indicator.start
    g_playerEvents.onAvatarBecomeNonPlayer += _indicator.stop
    _logger.info('init v%s', __version__)


def fini():
    # Called by gui.mods when the client shuts down.
    DebugPanel._populate = _originalPopulate
    g_playerEvents.onAvatarReady -= _indicator.start
    g_playerEvents.onAvatarBecomeNonPlayer -= _indicator.stop
    _indicator.stop()
    _logger.info('fini')
