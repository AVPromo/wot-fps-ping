# -*- coding: utf-8 -*-
"""Battle loop: measures frames, reads ping, updates the view and writes both to game.log."""
import logging
from collections import deque

import BigWorld
from gui.shared import EVENT_BUS_SCOPE, g_eventBus
from gui.shared.events import GameEvent

from gui.mods.pb_fps_ping.config import GRAPH_EVERY, GRAPH_POINTS, LOG_EVERY, PING_NONE, UPDATE_INTERVAL
from gui.mods.pb_fps_ping.frame_timer import FrameTimer

_logger = logging.getLogger('pb.fps_ping')


def _fmt(value):
    return '%.1f' % value if value is not None else '-'


def _ping():
    # Ping in ms as the game's own panel shows it; None while there is none yet.
    ping = BigWorld.statPing()
    return ping if ping != PING_NONE else None


class Indicator(object):
    # Runs from the start to the end of a battle. Texts every UPDATE_INTERVAL; the graphs get a point and are redrawn
    # every GRAPH_EVERY updates, in the frame after the texts, so one frame does not get both. The graphs and 1% low
    # are shown while the game's extended info key is held (Alt by default, the same key that shows extra info on
    # vehicle markers).

    def __init__(self, view):
        self._view = view
        self._running = False
        self._callbackID = None
        self._graphCallbackID = None
        self._updates = 0
        self._frameTimer = FrameTimer()
        # FPS and ping shown at every GRAPH_EVERY update, newest last: the graph points.
        self._fpsPoints = deque(maxlen=GRAPH_POINTS)
        self._pingPoints = deque(maxlen=GRAPH_POINTS)

    def start(self):
        if self._running:
            return
        self._running = True
        self._updates = 0
        self._fpsPoints.clear()
        self._pingPoints.clear()
        self._view.setExtended(False)
        g_eventBus.addListener(GameEvent.SHOW_EXTENDED_INFO, self._onExtendedInfo, scope=EVENT_BUS_SCOPE.BATTLE)
        self._frameTimer.start()
        _logger.info('indicator started')
        self._update()

    def stop(self):
        self._frameTimer.stop()
        for name in ('_callbackID', '_graphCallbackID'):
            callbackID = getattr(self, name)
            if callbackID is not None:
                BigWorld.cancelCallback(callbackID)
                setattr(self, name, None)
        if self._running:
            self._running = False
            self._runView(self._view.hide)
            g_eventBus.removeListener(GameEvent.SHOW_EXTENDED_INFO, self._onExtendedInfo, scope=EVENT_BUS_SCOPE.BATTLE)
            _logger.info('indicator stopped')

    def _update(self):
        self._callbackID = None
        try:
            fps = self._frameTimer.fps()
            low = self._frameTimer.low.fps()
            ping = _ping()
            newPoint = self._updates % GRAPH_EVERY == 0
            if newPoint:
                if fps is not None:
                    self._fpsPoints.append(fps)
                if ping is not None:
                    self._pingPoints.append(ping)
            self._runView(self._view.update, fps, ping)
            if self._view.extended:
                self._runView(self._view.updateLow, low, self._frameTimer.desyncs)
                if newPoint:
                    self._scheduleGraphs()
            if self._updates % LOG_EVERY == 0:
                _logger.info('fps %s | 1%% low %s | desyncs %d | ping %s',
                             _fmt(fps), _fmt(low), self._frameTimer.desyncs, _fmt(ping))
            self._updates += 1
        except Exception:
            _logger.exception('update failed, indicator stopped')
            self.stop()
            return
        self._callbackID = BigWorld.callback(UPDATE_INTERVAL, self._update)

    def _onExtendedInfo(self, event):
        extended = bool(event.ctx.get('isDown'))
        if extended == self._view.extended:
            return
        self._runView(self._view.setExtended, extended)
        if extended:
            self._runView(self._view.updateLow, self._frameTimer.low.fps(), self._frameTimer.desyncs)
            self._scheduleGraphs()

    def _scheduleGraphs(self):
        if self._view.attached and self._graphCallbackID is None:
            self._graphCallbackID = BigWorld.callback(0.0, self._updateGraphs)

    def _updateGraphs(self):
        self._graphCallbackID = None
        self._runView(self._view.updateGraphs, self._fpsPoints, self._pingPoints)

    def _runView(self, update, *args):
        try:
            update(*args)
        except Exception:
            _logger.exception('view update failed, view removed')
            self._view.detach()
