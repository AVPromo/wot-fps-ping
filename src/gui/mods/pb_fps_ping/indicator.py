# -*- coding: utf-8 -*-
"""Battle loop: measures frames, updates the view and writes FPS to game.log."""
import logging
from collections import deque

import BigWorld
from gui.shared import EVENT_BUS_SCOPE, g_eventBus
from gui.shared.events import GameEvent

from gui.mods.pb_fps_ping.config import GRAPH_EVERY, GRAPH_POINTS, LOG_EVERY, UPDATE_INTERVAL
from gui.mods.pb_fps_ping.frame_timer import FrameTimer

_logger = logging.getLogger('pb.fps_ping')


def _fmtFPS(fps):
    return '%.1f' % fps if fps is not None else '-'


class Indicator(object):
    # Runs from the start to the end of a battle. Texts every UPDATE_INTERVAL; the graph gets a point and is redrawn
    # every GRAPH_EVERY updates, in the frame after the texts, so one frame does not get both. The graph and 1% low are shown while the game's extended info key is held
    # (Alt by default, the same key that shows extra info on vehicle markers).

    def __init__(self, view):
        self._view = view
        self._running = False
        self._callbackID = None
        self._graphCallbackID = None
        self._updates = 0
        self._frameTimer = FrameTimer()
        # FPS shown at every update, newest last: the graph points.
        self._points = deque(maxlen=GRAPH_POINTS)

    def start(self):
        if self._running:
            return
        self._running = True
        self._updates = 0
        self._points.clear()
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
            newPoint = self._updates % GRAPH_EVERY == 0 and fps is not None
            if newPoint:
                self._points.append(fps)
            self._runView(self._view.updateFps, fps)
            if self._view.extended:
                self._runView(self._view.updateLow, low)
                if newPoint:
                    self._scheduleGraph()
            if self._updates % LOG_EVERY == 0:
                _logger.info('fps %s | 1%% low %s', _fmtFPS(fps), _fmtFPS(low))
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
            self._runView(self._view.updateLow, self._frameTimer.low.fps())
            self._scheduleGraph()

    def _scheduleGraph(self):
        if self._view.attached and self._graphCallbackID is None:
            self._graphCallbackID = BigWorld.callback(0.0, self._updateGraph)

    def _updateGraph(self):
        self._graphCallbackID = None
        self._runView(self._view.updateGraph, self._points)

    def _runView(self, update, *args):
        try:
            update(*args)
        except Exception:
            _logger.exception('view update failed, view removed')
            self._view.detach()
