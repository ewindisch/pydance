# Event types.
E_PASS,E_QUIT,E_FULLSCREEN,E_SCREENSHOT,E_PGUP,E_PGDN,E_SELECT,E_MARK,E_UP,E_DOWN,E_LEFT,E_RIGHT,E_START,E_CREATE,E_UNSELECT,E_CLEAR,E_UNMARK, E_CENTER = range(18)

E_SORT = E_SCREENSHOT

E_UPLEFT, E_UPRIGHT, E_DOWNLEFT, E_DOWNRIGHT = E_UNMARK, E_PGUP, E_MARK, E_PGDN

DIRECTIONS = ['l', 'd', 'u', 'r']

VERSION = "0.8.0"

import sys, os, config, pygame
import games

# Detect the name of the OS - MacOS X is not really UNIX.
osname = None
if os.name == "nt": osname = "win32"
elif os.name == "posix":
  if os.path.islink("/System/Library/CoreServices/WindowServer"):
    osname = "macosx"
  elif os.environ.has_key("HOME"):
    osname = "posix"
else:
  print "Your platform is not supported by pydance. We're going to call it"
  print "POSIX, and then just let it crash."

# SDL_mixer is the bane of my existance.
if osname == 'posix': # We need to force stereo in many cases.
  try: pygame.mixer.pre_init(44100, -16, 2)
  except: pass

# K_* constants, mostly
from pygame.locals import *

# Find out our real directory - resolve symlinks, etc
pyddr_path = sys.argv[0]
if osname == "posix":
  pyddr_path = os.path.split(os.path.realpath(pyddr_path))[0]
else: pyddr_path = os.path.split(os.path.abspath(pyddr_path))[0]
sys.path.append(pyddr_path)

# Set up some bindings for common directories
image_path = os.path.join(pyddr_path, "images")
sound_path = os.path.join(pyddr_path, "sound")

# Set a binding for our savable resource directory
rc_path = None
if osname == "posix":
  old_rc_path = os.path.join(os.environ["HOME"], ".pyddr")
  rc_path = os.path.join(os.environ["HOME"], ".pydance")
elif osname == "macosx":
  old_rc_path = os.path.join(os.environ["HOME"], "Library",
                             "Preferences", "pyDDR")
  rc_path = os.path.join(os.environ["HOME"], "Library",
                             "Preferences", "pydance")
elif osname == "win32":
  old_rc_path = rc_path = "."

if os.path.isdir(old_rc_path) and not os.path.isdir(rc_path):
  os.rename(old_rc_path, rc_path)

if os.path.exists(os.path.join(rc_path, "pyddr.cfg")):
  os.rename(os.path.join(rc_path, "pyddr.cfg"), os.path.join(rc_path, "pydance.cfg"))

if not os.path.isdir(rc_path): os.mkdir(rc_path)

search_paths = (pyddr_path, rc_path, old_rc_path)
#if pyddr_path != "." and rc_path != ".":
#  search_paths += (".",)

if not sys.stdout.isatty():
  sys.stdout = open(os.path.join(rc_path, "pydance.log"), "w")
  sys.stderr = sys.stdout

# Set up the configuration file
default_conf = { # Wow we have a lot of options
  "djtheme": "none", "songdir": ".",
  "stickycombo": 1,  "lowestcombo": 4, "stickyjudge": 1,
  "lyriccolor": "cyan/aqua",
  "onboardaudio": 0, "masteroffset": 0,
  "explodestyle": 3, "vesacompat": 0, "fullscreen": 0,
  "sortmode": 0,
  "folders": 1,
  "previewmusic": 1,
  "showbackground": 1, "bgbrightness": 127,
  "gratuitous": 1,
  "assist": 0,
  "fpsdisplay": 1, "showlyrics": 1,
  "showcombo": 1,
  "autofail": 1,
  "grading": 1,
  "keyboard": "qwerty",
  "ingamehelp": 1,
  "strobe": 0,
  "usemad": 1, "usepsyco": 1,
  }

for dummy, game in games.GAMES.items():
  default_conf["%s-theme" % game.theme] = "default"

mainconfig = config.Config(default_conf)

player_config = {"spin": 0,
                 "accel": 0,
                 "transform": 0,
                 "scale": 1,
                 "speed": 1.0,
                 "sudden": 0,
                 "hidden": 0,
                 "size": 0,
                 "dark": 0,
                 "jumps": 0,
                 "holds": 1,
                 "colortype": 4,
                 "scrollstyle": 0 }

game_config = {"battle": 0,
               "diff": 1,
               "lifebar": 0,
               "onilives": 3,
               }

if osname == "posix":
  mainconfig.load("/etc/pyddr.cfg", True)
  mainconfig.load("/etc/pydance.cfg", True)
elif osname == "macosx":
  mainconfig.load("/Library/Preferences/pyDDR/pyddr.cfg", True)
  mainconfig.load("/Library/Preferences/pydance/pydance.cfg", True)

mainconfig.load("pyddr.cfg")
mainconfig.load("pydance.cfg")
mainconfig.load(os.path.join(old_rc_path, "pyddr.cfg"))
mainconfig.load(os.path.join(rc_path, "pydance.cfg"))
mainconfig["sortmode"] %= 4

pygame.init()

import input

event = input.EventManager()

# Fonts
FONTS = {}
for s in (192, 60, 48, 40, 36, 32, 28, 26, 20, 16, 14):
  FONTS[s] = pygame.font.Font(None, s)
