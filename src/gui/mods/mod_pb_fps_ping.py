# -*- coding: utf-8 -*-
"""FPS & Ping by PB: battle FPS and ping indicator for World of Tanks.

Entry point loaded by the game; the code is in the gui.mods.pb_fps_ping package.
"""
import logging

from gui.Scaleform.daapi.view.battle.shared.debug_panel import DebugPanel
from PlayerEvents import g_playerEvents

from gui.mods.pb_fps_ping.config import HIDE_GAME_PANEL
from gui.mods.pb_fps_ping.flash_view import FlashView
from gui.mods.pb_fps_ping.indicator import Indicator

__version__ = '0.12.2'

_logger = logging.getLogger('pb.fps_ping')

_view = FlashView()
_indicator = Indicator(_view)
_originalPopulate = DebugPanel._populate
_originalDispose = DebugPanel._dispose


def _populate(self):
    # The game's own FPS/ping panel is created with the battle page; the view goes next to it.
    _originalPopulate(self)
    if HIDE_GAME_PANEL:
        try:
            self.flashObject.visible = False
        except Exception:
            _logger.exception('cannot hide the game debug panel')
    try:
        _view.attach(self)
    except Exception:
        _logger.exception('cannot create the view')
        _view.detach()


def _dispose(self):
    _view.detach()
    _originalDispose(self)


def init():
    # Called by gui.mods after all mods are imported.
    DebugPanel._populate = _populate
    DebugPanel._dispose = _dispose
    g_playerEvents.onAvatarReady += _indicator.start
    g_playerEvents.onAvatarBecomeNonPlayer += _indicator.stop
    _logger.info('init v%s', __version__)


def fini():
    # Called by gui.mods when the client shuts down.
    DebugPanel._populate = _originalPopulate
    DebugPanel._dispose = _originalDispose
    g_playerEvents.onAvatarReady -= _indicator.start
    g_playerEvents.onAvatarBecomeNonPlayer -= _indicator.stop
    _indicator.stop()
    _view.detach()
    _logger.info('fini')
