# -*- coding: utf-8 -*-
"""FPS & Ping by PB: battle FPS and ping indicator for World of Tanks."""
import logging
import re

import BattleReplay
import BigWorld
import GUI
from gui.Scaleform.daapi.view.battle.shared.debug_panel import DebugPanel
from PlayerEvents import g_playerEvents

__version__ = '0.2.0'

_logger = logging.getLogger('pb.fps_ping')

# Same rate as the game's own debug panel (debug_ctrl.DebugController).
_UPDATE_INTERVAL = 0.2
# GUI.Text position in clip space: x and y from -1 to 1, (-1, 1) is the top-left corner.
_POSITION = (-0.99, 0.99, 0)
# BigWorld names worth logging once, to find extra network stats (e.g. packet loss).
_PROBE_NAME = re.compile('stat|ping|latency|packet|loss|net|fps|lag|bandwidth', re.I)

# Raw game API values shown on screen, as (label, getter). No values are derived.
_SOURCES = (
    ('BigWorld.getFPS()', BigWorld.getFPS),
    ('BigWorld.statPing()', BigWorld.statPing),
    ('BigWorld.statLagDetected()', BigWorld.statLagDetected),
    ('BigWorld.LatencyInfo().value', lambda: tuple(BigWorld.LatencyInfo().value)),
)
_REPLAY_SOURCES = (
    ('replay.fps', lambda: BattleReplay.g_replayCtrl.fps),
    ('replay.ping', lambda: BattleReplay.g_replayCtrl.ping),
    ('replay.isLaggingNow', lambda: BattleReplay.g_replayCtrl.isLaggingNow),
)


def _fmt(value):
    if isinstance(value, float):
        return '%.3f' % value
    if isinstance(value, tuple):
        return ' | '.join(_fmt(v) for v in value)
    return str(value)


def _read(getter):
    try:
        return _fmt(getter())
    except Exception as e:
        return 'error: %r' % e


def _logProbe():
    names = sorted(name for name in dir(BigWorld) if _PROBE_NAME.search(name))
    _logger.info('probe BigWorld names: %s', ', '.join(names))


class _Indicator(object):

    def __init__(self):
        self._text = None
        self._callbackID = None

    def start(self):
        if self._text is not None:
            return
        text = GUI.Text('')
        text.multiline = True
        text.horizontalAnchor = GUI.Simple.eHAnchor.LEFT
        text.verticalAnchor = GUI.Simple.eVAnchor.TOP
        text.position = _POSITION
        GUI.addRoot(text)
        self._text = text
        _logger.info('indicator started')
        _logProbe()
        self._update()

    def stop(self):
        if self._callbackID is not None:
            BigWorld.cancelCallback(self._callbackID)
            self._callbackID = None
        if self._text is not None:
            GUI.delRoot(self._text)
            self._text = None
            _logger.info('indicator stopped')

    def _update(self):
        self._callbackID = None
        try:
            sources = _SOURCES
            if BattleReplay.g_replayCtrl.isPlaying:
                sources += _REPLAY_SOURCES
            self._text.text = '\n'.join('%s = %s' % (label, _read(getter)) for label, getter in sources)
        except Exception:
            _logger.exception('update failed, indicator stopped')
            self.stop()
            return
        self._callbackID = BigWorld.callback(_UPDATE_INTERVAL, self._update)


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
