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
SOURCE_DIR = os.path.join(ROOT, 'src', 'gui', 'mods')
# The entry module the game loads; it holds __version__.
SOURCE = os.path.join(SOURCE_DIR, MOD_SCRIPT + '.py')
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


def source_files():
    # Every .py under src/gui/mods as a path relative to it with '/' separators, sorted.
    found = []
    for directory, _, names in os.walk(SOURCE_DIR):
        for name in names:
            if name.endswith('.py'):
                found.append(os.path.relpath(os.path.join(directory, name), SOURCE_DIR).replace(os.sep, '/'))
    return sorted(found)


def compile_scripts(tmp_dir):
    # {relative .pyc path: bytecode}.
    compiled = {}
    for relative in source_files():
        pyc = os.path.join(tmp_dir, relative.replace('/', '_') + 'c')
        # dfile keeps the local source path out of tracebacks in game.log.
        py_compile.compile(os.path.join(SOURCE_DIR, relative), cfile=pyc, dfile='gui/mods/' + relative, doraise=True)
        with open(pyc, 'rb') as f:
            compiled[relative + 'c'] = f.read()
    return compiled


def write_package(path, version, compiled):
    meta = META_XML.format(id=MOD_ID, version=version, name=escape(MOD_NAME), description=escape(MOD_DESCRIPTION))
    # The game expects an uncompressed zip with explicit directory entries.
    directories = set()
    for relative in compiled:
        parts = (PACKAGE_SCRIPT_DIR + relative).split('/')[:-1]
        directories.update('/'.join(parts[:i]) + '/' for i in range(1, len(parts) + 1))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_STORED) as z:
        z.writestr('meta.xml', meta)
        for directory in sorted(directories):
            z.writestr(directory, '')
        for relative in sorted(compiled):
            z.writestr(PACKAGE_SCRIPT_DIR + relative, compiled[relative])


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
        compiled = compile_scripts(tmp_dir)
    finally:
        shutil.rmtree(tmp_dir)

    if not os.path.isdir(BUILD_DIR):
        os.makedirs(BUILD_DIR)
    package = os.path.join(BUILD_DIR, '%s_%s.wotmod' % (MOD_ID, version))
    write_package(package, version, compiled)
    print('build   ' + package)

    if '--install' in sys.argv[1:]:
        install(package)


if __name__ == '__main__':
    main()
