# -*- coding: utf-8 -*-
"""Frame times: a callback on every frame, current FPS and 1% low."""
import logging
import time
from collections import deque

import BigWorld

from gui.mods.pb_fps_ping.config import CLOCK_CHECK_TIME, CLOCK_MIN_RATIO, FPS_WINDOW
from gui.mods.pb_fps_ping.low_fps import LowFPS

_logger = logging.getLogger('pb.fps_ping')


class FrameTimer(object):
    # Runs once per frame: a zero-delay callback that schedules itself again.
    # The time between two calls is one frame. Keeps the frame times of the last FPS_WINDOW seconds.

    def __init__(self):
        self._callbackID = None
        self._clock = time.clock
        self._clockName = 'time.clock()'
        # (clock time, BigWorld.time()) at the start, until the clock is checked.
        self._clockCheck = None
        self._lastTime = None
        # The game's frame number at the previous call, and how many calls since the start were not exactly one
        # frame after the previous one (twice in one frame, or frames skipped). Measured times are wrong then.
        self._lastFrame = None
        self.desyncs = 0
        # (end time, frame time) in seconds, and the sum of their frame times.
        self._frames = deque()
        self._framesTime = 0.0
        self.low = LowFPS()

    def start(self):
        self.stop()
        self._clockCheck = (self._clock(), BigWorld.time())
        self._lastFrame = None
        self.desyncs = 0
        self._resetFrames()
        self._tick()

    def stop(self):
        if self._callbackID is not None:
            BigWorld.cancelCallback(self._callbackID)
            self._callbackID = None

    def fps(self):
        if not self._frames or self._framesTime <= 0.0:
            return None
        return len(self._frames) / self._framesTime

    def _resetFrames(self):
        self._lastTime = None
        self._frames.clear()
        self._framesTime = 0.0
        self.low.reset()

    def _tick(self):
        self._callbackID = None
        try:
            self._checkStep(BigWorld.wg_getFrameTimestamp())
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

    def _checkStep(self, frame):
        if self._lastFrame is not None and frame - self._lastFrame != 1:
            self.desyncs += 1
            if self.desyncs == 1:
                _logger.warning('frame callback out of step with the game frames: frame number %d after %d',
                                frame, self._lastFrame)
        self._lastFrame = frame

    def _addFrame(self, now, frameTime):
        self._frames.append((now, frameTime))
        self._framesTime += frameTime
        self.low.add(now, frameTime)
        # Keep only frames that ended within the last FPS_WINDOW seconds.
        while now - self._frames[0][0] >= FPS_WINDOW:
            self._framesTime -= self._frames.popleft()[1]

    def _checkClock(self, now):
        clockStart, engineStart = self._clockCheck
        engineElapsed = BigWorld.time() - engineStart
        if engineElapsed < CLOCK_CHECK_TIME:
            return
        self._clockCheck = None
        ratio = (now - clockStart) / engineElapsed
        if ratio >= CLOCK_MIN_RATIO:
            _logger.info('clock %s ok, ratio to BigWorld.time() %.3f', self._clockName, ratio)
            return
        _logger.warning('clock %s runs at %.3f of BigWorld.time(), using BigWorld.timeExact()', self._clockName, ratio)
        self._clock = BigWorld.timeExact
        self._clockName = 'BigWorld.timeExact()'
        self._resetFrames()
