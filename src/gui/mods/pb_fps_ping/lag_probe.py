# -*- coding: utf-8 -*-
"""Temporary diagnostics: BigWorld.statLagDetected() frame by frame, to find when the game's lag lamp turns red."""
import logging
import os

import BigWorld

from gui.mods.pb_fps_ping.config import LAG_PROBE_SECONDS

_logger = logging.getLogger('pb.fps_ping')

PATH = os.path.join(os.environ.get('TEMP') or '.', 'pb_fps_ping_lag.csv')
# Rows are written to disk this often, so a crash or a kick after a disconnect does not lose them.
_FLUSH_EVERY = 300


class LagProbe(object):
    # For the first LAG_PROBE_SECONDS of each battle writes one CSV row per frame to PATH (in the system temp folder,
    # not the game folder): our clock, the game's frame number, BigWorld.time(), BigWorld.serverTime(),
    # statLagDetected(), statPing() and LatencyInfo().value.

    def __init__(self):
        self._file = None
        self._end = None
        self._rows = 0

    def start(self, now):
        self.stop()
        if LAG_PROBE_SECONDS <= 0:
            return
        try:
            self._file = open(PATH, 'w')
            self._file.write('clock,frame,bw_time,server_time,lag,ping,lat0,lat1,lat2,lat3\n')
            self._end = now + LAG_PROBE_SECONDS
            self._rows = 0
            _logger.info('lag probe: writing %d s of frames to %s', LAG_PROBE_SECONDS, PATH)
        except Exception:
            _logger.exception('lag probe: cannot open %s', PATH)
            self._file = None

    def add(self, now, frame):
        if self._file is None:
            return
        if now >= self._end:
            self.stop()
            return
        try:
            latency = BigWorld.LatencyInfo().value
            self._file.write('%.7f,%d,%.6f,%.6f,%d,%.4f,%s,%.7f,%.7f,%.7f\n' % (
                now, frame, BigWorld.time(), BigWorld.serverTime(), 1 if BigWorld.statLagDetected() else 0,
                BigWorld.statPing(), latency[0], latency[1], latency[2], latency[3]))
            self._rows += 1
            if self._rows % _FLUSH_EVERY == 0:
                self._file.flush()
        except Exception:
            # The probe must never stop the frame timer.
            _logger.exception('lag probe failed, stopped')
            self.stop()

    def stop(self):
        if self._file is None:
            return
        try:
            self._file.close()
            _logger.info('lag probe: done, %d frames, %s', self._rows, PATH)
        except Exception:
            _logger.exception('lag probe: cannot close %s', PATH)
        self._file = None
