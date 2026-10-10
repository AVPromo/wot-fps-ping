# -*- coding: utf-8 -*-
"""1% low FPS over a sliding window."""
from collections import deque

from gui.mods.pb_fps_ping.config import LOW_BIN, LOW_SHARE, LOW_WINDOW


class LowFPS(object):
    # 1% low FPS over the last LOW_WINDOW seconds, counted the way MSI Afterburner / RTSS do:
    # sort frames from the slowest, add up their times until the sum reaches LOW_SHARE of the window time,
    # and take the FPS of the frame at that point.
    # Frames are not stored one by one: each second keeps a histogram {bin: [frames, time]} of frame times,
    # and the window total is the sum of the last LOW_WINDOW second histograms.

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
        if self._secondEnd is None or now - self._secondEnd >= LOW_WINDOW:
            self.reset()
            self._secondEnd = now + 1.0
            self._seconds.append({})
        while now >= self._secondEnd:
            self._secondEnd += 1.0
            self._seconds.append({})
            if len(self._seconds) > LOW_WINDOW:
                self._drop(self._seconds.popleft())
        b = int(frameTime / LOW_BIN)
        for histogram in (self._seconds[-1], self._total):
            entry = histogram.get(b)
            if entry is None:
                histogram[b] = [1, frameTime]
            else:
                entry[0] += 1
                entry[1] += frameTime
        self._totalTime += frameTime

    def fps(self):
        target = self._totalTime * LOW_SHARE
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
