# Event types.
E_PASS,E_QUIT,E_FULLSCREEN,E_SCREENSHOT,E_UPRIGHT,E_DOWNRIGHT,E_SELECT,E_DOWNLEFT,E_UP,E_DOWN,E_LEFT,E_RIGHT,E_START,E_CREATE,E_UNSELECT,E_CLEAR,E_UPLEFT, E_CENTER = range(18)

E_SORT = E_SCREENSHOT

E_UNMARK, E_PGUP, E_MARK, E_PGDN = E_UPLEFT, E_UPRIGHT, E_DOWNLEFT, E_DOWNRIGHT

VERSION = "0.8.1"

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
pydance_path = sys.argv[0]
if osname == "posix":
  pydance_path = os.path.split(os.path.realpath(pydance_path))[0]
else: pydance_path = os.path.split(os.path.abspath(pydance_path))[0]
sys.path.append(pydance_path)

# Set up some bindings for common directories
image_path = os.path.join(pydance_path, "images")
sound_path = os.path.join(pydance_path, "sound")

# Set a binding for our savable resource directory
rc_path = None
if osname == "posix":
  rc_path = os.path.join(os.environ["HOME"], ".pydance")
elif osname == "macosx":
  rc_path = os.path.join(os.environ["HOME"], "Library",
                             "Preferences", "pydance")
elif osname == "win32": rc_path = "."

if not os.path.isdir(rc_path): os.mkdir(rc_path)

search_paths = (pydance_path, rc_path)
#if pydance_path != "." and rc_path != ".":
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
  "strobe": 0,
  "usemad": 1, "usepsyco": 1,
  "autogen": 1,
  }

for game in games.GAMES.values():
  default_conf["%s-theme" % game.theme] = game.theme_default

mainconfig = config.Config(default_conf)

player_config = {"spin": 0,
                 "accel": 0,
                 "transform": 0,
                 "scale": 1,
                 "speed": 1.0,
                 "fade": 0,
                 "size": 0,
                 "dark": 0,
                 "jumps": 1,
                 "holds": 1,
                 "colortype": 4,
                 "scrollstyle": 0 }

game_config = {"battle": 0,
               "scoring": 0,
               "combo": 0,
               "grade": 0,
               "judge": 0,
               "judgescale": 1.0,
               "life": 1.0,
               "secret": 1,
               "lifebar": 0,
               "onilives": 3,
               }

if osname == "posix":
  mainconfig.load("/etc/pydance.cfg", True)
elif osname == "macosx":
  mainconfig.load("/Library/Preferences/pydance/pydance.cfg", True)

mainconfig.load("pydance.cfg")
mainconfig.load(os.path.join(rc_path, "pydance.cfg"))
mainconfig["sortmode"] %= 4

pygame.init()

# Fonts
FONTS = {}
for s in (192, 60, 48, 40, 36, 32, 28, 26, 24, 20, 16, 14):
  FONTS[s] = pygame.font.Font(None, s)
