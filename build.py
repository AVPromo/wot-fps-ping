# -*- coding: utf-8 -*-
"""Build the .wotmod package (and optionally install it into the game).

Run with the game's Python version (2.7):
    C:\\Python27\\python.exe build.py            -> build/<id>_<version>.wotmod
    C:\\Python27\\python.exe build.py --install  -> also copy into the game mods folder
"""
import glob
import os
import py_compile
import re
import shutil
import sys
import tempfile
import zipfile
from xml.sax.saxutils import escape

MOD_ID = 'pavel-bolhovitin.fps_ping'
MOD_NAME = 'FPS & Ping by PB'
MOD_DESCRIPTION = 'Battle FPS and ping indicator.'
MOD_SCRIPT = 'mod_pb_fps_ping'

GAME_DIR = os.environ.get('WOT_DIR', r'D:\programs\World_of_Tanks_EU')
GAME_VERSION = '2.4.0.2'

ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(ROOT, 'src', 'gui', 'mods', MOD_SCRIPT + '.py')
BUILD_DIR = os.path.join(ROOT, 'build')
PACKAGE_SCRIPT_DIR = 'res/scripts/client/gui/mods/'

META_XML = """<root>
  <id>{id}</id>
  <version>{version}</version>
  <name>{name}</name>
  <description>{description}</description>
</root>
"""


def read_version():
    with open(SOURCE) as f:
        match = re.search(r"^__version__ = '([^']+)'", f.read(), re.M)
    if not match:
        sys.exit('__version__ not found in ' + SOURCE)
    return match.group(1)


def compile_script(tmp_dir):
    pyc = os.path.join(tmp_dir, MOD_SCRIPT + '.pyc')
    # dfile keeps the local source path out of tracebacks in game.log.
    py_compile.compile(SOURCE, cfile=pyc, dfile='gui/mods/' + MOD_SCRIPT + '.py', doraise=True)
    with open(pyc, 'rb') as f:
        return f.read()


def write_package(path, version, pyc_data):
    meta = META_XML.format(id=MOD_ID, version=version, name=escape(MOD_NAME), description=escape(MOD_DESCRIPTION))
    # The game expects an uncompressed zip with explicit directory entries.
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_STORED) as z:
        z.writestr('meta.xml', meta)
        parts = PACKAGE_SCRIPT_DIR.rstrip('/').split('/')
        for i in range(1, len(parts) + 1):
            z.writestr('/'.join(parts[:i]) + '/', '')
        z.writestr(PACKAGE_SCRIPT_DIR + MOD_SCRIPT + '.pyc', pyc_data)


def install(package):
    mods_dir = os.path.join(GAME_DIR, 'mods', GAME_VERSION)
    if not os.path.isdir(mods_dir):
        sys.exit('mods folder not found: ' + mods_dir)
    for old in glob.glob(os.path.join(mods_dir, MOD_ID + '_*.wotmod')):
        print('remove  ' + old)
        os.remove(old)
    shutil.copy2(package, mods_dir)
    print('install ' + os.path.join(mods_dir, os.path.basename(package)))


def main():
    if sys.version_info[:2] != (2, 7):
        sys.exit('Run with Python 2.7 (the game bytecode version), got ' + sys.version.split()[0])

    version = read_version()
    tmp_dir = tempfile.mkdtemp()
    try:
        pyc_data = compile_script(tmp_dir)
    finally:
        shutil.rmtree(tmp_dir)

    if not os.path.isdir(BUILD_DIR):
        os.makedirs(BUILD_DIR)
    package = os.path.join(BUILD_DIR, '%s_%s.wotmod' % (MOD_ID, version))
    write_package(package, version, pyc_data)
    print('build   ' + package)

    if '--install' in sys.argv[1:]:
        install(package)


if __name__ == '__main__':
    main()
