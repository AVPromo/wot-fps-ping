# -*- coding: utf-8 -*-
"""FPS & Ping by PB: battle FPS and ping indicator for World of Tanks."""
import logging

__version__ = '0.1.0'

_logger = logging.getLogger('pb.fps_ping')


def init():
    # Called by gui.mods after all mods are imported.
    _logger.info('init v%s', __version__)


def fini():
    _logger.info('fini')
