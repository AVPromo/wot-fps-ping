# -*- coding: utf-8 -*-
"""Battle loop: measures frames, reads ping, updates the view and writes both to game.log."""
import logging
from collections import deque

import BattleReplay
import BigWorld
from gui.shared import EVENT_BUS_SCOPE, g_eventBus
from gui.shared.events import GameEvent

from gui.mods.pb_fps_ping.config import GRAPH_EVERY, GRAPH_POINTS, LOG_EVERY, PING_NONE, UPDATE_INTERVAL
from gui.mods.pb_fps_ping.frame_timer import FrameTimer

_logger = logging.getLogger('pb.fps_ping')


def _fmt(value):
    return '%.1f' % value if value is not None else '-'


def _replay():
    # The replay controller while a replay plays, else None.
    replayCtrl = BattleReplay.g_replayCtrl
    return replayCtrl if replayCtrl is not None and replayCtrl.isPlaying else None


def _ping(replay):
    # Ping in ms as the game's own panel shows it; None while there is none yet. While a replay plays there is no
    # connection (statPing() stays at PING_NONE), so the ping recorded in the replay is shown, as the panel does.
    ping = replay.ping if replay is not None else BigWorld.statPing()
    return ping if ping is not None and ping != PING_NONE else None


def _lag(replay):
    # Whether the server's updates do not come now, as the game panel's lamp shows; in a replay as recorded in it.
    return bool(replay.isLaggingNow if replay is not None else BigWorld.statLagDetected())


class Indicator(object):
    # Runs from the start to the end of a battle. Texts and the lag lamp every UPDATE_INTERVAL; the graphs get a point
    # and are redrawn every GRAPH_EVERY updates, in the frame after the texts, so one frame does not get both. The
    # graphs, the lag ticks and 1% low are shown while the game's extended info key is held (Alt by default, the same
    # key that shows extra info on vehicle markers).

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
        # Whether there was lag at any update since the last point, and the lag of each point.
        self._lagSincePoint = False
        self._lagPoints = deque(maxlen=GRAPH_POINTS)

    def start(self):
        if self._running:
            return
        self._running = True
        self._updates = 0
        self._fpsPoints.clear()
        self._pingPoints.clear()
        self._lagPoints.clear()
        self._lagSincePoint = False
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
            replay = _replay()
            ping = _ping(replay)
            lag = _lag(replay)
            self._lagSincePoint = self._lagSincePoint or lag
            # A replay also shows the FPS of the battle as recorded in it: the game panel's counter
            # (BigWorld.getFPS()[1]) in whole numbers every 0.2 s. The FPS, its graph and 1% low are measured for the
            # playback.
            replayFps = replay.fps if replay is not None and replay.fps > 0 else None
            newPoint = self._updates % GRAPH_EVERY == 0
            if newPoint:
                if fps is not None:
                    self._fpsPoints.append(fps)
                if ping is not None:
                    self._pingPoints.append(ping)
                    self._lagPoints.append(self._lagSincePoint)
                self._lagSincePoint = False
            self._runView(self._view.update, fps, low, ping, lag, self._frameTimer.desyncs, replayFps)
            if self._view.extended and newPoint:
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
            self._scheduleGraphs()

    def _scheduleGraphs(self):
        if self._view.attached and self._graphCallbackID is None:
            self._graphCallbackID = BigWorld.callback(0.0, self._updateGraphs)

    def _updateGraphs(self):
        self._graphCallbackID = None
        self._runView(self._view.updateGraphs, self._fpsPoints, self._pingPoints, self._lagPoints)

    def _runView(self, update, *args):
        try:
            update(*args)
        except Exception:
            _logger.exception('view update failed, view removed')
            self._view.detach()
