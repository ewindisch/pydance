# Constants used in the game and some simple initialization routines
# This file should be kept as small as possible, probably. (But I seem
# to be failing at doing that.)

import sys
import os
import locale
VERSION = "1.0.3"

try: locale.setlocale(locale.LC_ALL, '')
except locale.Error: pass

# Detect the name of the OS - Mac OS X is not really UNIX.
osname = None
if os.name == "nt": osname = "win32"
elif os.name == "posix":
  if os.path.islink("/System/Library/CoreServices/WindowServer"):
    osname = "macosx"
  elif "HOME" in os.environ:
    osname = "posix"
else:
  raise SystemExit(
    "Your platform is not supported by pydance. In particular, it\n" +
    "doesn't seem to be Win32, Mac OS X, or a Unix that sets $HOME.")

# SDL_mixer is the bane of my existance.
if osname == 'posix': # We need to force stereo in many cases.
  try: pygame.mixer.pre_init(44100, -16, 2)
  except: pass

# Find out our real directory - resolve symlinks, etc
pydance_path = sys.argv[0]
if osname == "posix":
  pydance_path = os.path.split(os.path.realpath(pydance_path))[0]
else: pydance_path = os.path.split(os.path.abspath(pydance_path))[0]
sys.path.insert(0, pydance_path)

if os.path.exists(os.path.join(pydance_path, "pydance.zip")):
  sys.path.insert(0, os.path.join(pydance_path, "pydance.zip"))

# Set up some names for commonly referenced directories
image_path = os.path.join(pydance_path, "images")
sound_path = os.path.join(pydance_path, "sound")

# Set a name for our savable resource directory
rc_path = None
if osname == "posix":
  rc_path = os.path.join(os.environ["HOME"], ".pydance")
elif osname == "macosx":
  rc_path = os.path.join(os.environ["HOME"], "Library",
                             "Preferences", "pydance")
elif osname == "win32": rc_path = "."

if not os.path.isdir(rc_path): os.mkdir(rc_path)

search_paths = (pydance_path, rc_path)

if not sys.stdout.isatty():
  sys.stdout = file(os.path.join(rc_path, "pydance.log"), "w")
  sys.stderr = sys.stdout

import pygame
import games
import config
import colors

from pygame.locals import *

# Set up the configuration file
default_conf = {
  "djtheme": "djenzay",
  "songdir": os.pathsep.join([os.path.join(rc_path, "songs"),
                              os.path.join(pydance_path, "songs")]),
  "coursedir": os.pathsep.join([os.path.join(rc_path, "courses"),
                                os.path.join(pydance_path, "courses")]),
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
  "animation": 1,
  "grading": 1,
  "saveinput": 1,
  "strobe": 0,
  "usepsyco": 1,
  "autogen": 1,
  "centerconfirm": 1,
  "songinfoscreen": 1,

  # Player config
  "spin": 0,
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
  "scrollstyle": 0,

  # Game options
  "battle": 0,
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

for game in games.GAMES.values():
  default_conf["%s-theme" % game.theme] = game.theme_default

mainconfig = config.Config(default_conf)

if osname == "posix":
  mainconfig.load("/etc/pydance.cfg", True)
elif osname == "macosx":
  mainconfig.load("/Library/Preferences/pydance/pydance.cfg", True)

mainconfig.load("pydance.cfg")
mainconfig.load(os.path.join(rc_path, "pydance.cfg"))
mainconfig["sortmode"] %= 4

player_config = dict([(k, mainconfig[k]) for k in
                      ["spin", "accel", "transform", "scale", "speed",
                       "fade", "size", "dark", "jumps", "holds", "colortype",
                       "scrollstyle"]])

game_config = dict([(k, mainconfig[k]) for k in
                    ["battle", "scoring", "combo", "grade", "judge",
                     "judgescale", "life", "secret", "lifebar", "onilives"]])


# The list of options that are safe to change between songs on a
# playlist
# Each tuple has the following entries:
# 0. Option "key", like the one used in the options.OPTIONS dictionary
# 1. A dictionary of option values that require special displaying:
#    the key is the value of the option and the value is a string that
#    should be shown on the song info screen if that option is
#    selected.  If there is no key for a particular option, the string
#    that is displayed for that value in the option menu is used.
#    E.g. for the "jumps" option, value 0 will map to "No Jumps" while
#    value 2 is not in the dictionary so will display "Wide".

changeable_between = [('speed', {}),
                      ('transform', {}),
                      ('size', {}),
                      ('fade', {}),
                      ('accel', {}),
                      ('scale', {}),
                      ('scrollstyle', {}),
                      ('jumps', {0:"No Jumps"}),
                      ('spin', {1:"Spin"}),
                      ('colortype', {}),
                      ('dark', {1:"Dark"}),
                      ('holds', {0:"No Holds"})
                      ]


pygame.init()

# Fonts
FONTS = {}
for s in (192, 60, 48, 40, 36, 32, 28, 26, 24, 20, 18, 16, 14):
  FONTS[s] = pygame.font.Font(None, s)

# The different colors pydance uses for difficulties in the UI.
DIFF_COLORS = { "BEGINNER": colors.color["white"],
                "LIGHT": colors.color["orange"],
                "EASY": colors.color["orange"],
                "BASIC": colors.color["orange"],
                "STANDARD": colors.color["red"],
                "STANDER": colors.color["red"], # Shit you not, 3 people.
                "TRICK": colors.color["red"],
                "MEDIUM": colors.color["red"],
                "DOUBLE": colors.color["red"],
                "ANOTHER": colors.color["red"],
                "PARA": colors.color["blue"],
                "NORMAL": colors.color["red"],
                "MANIAC": colors.color["green"],
                "HARD": colors.color["green"],
                "HEAVY": colors.color["green"],
                "HARDCORE": colors.color["purple"],
                "SMANIAC": colors.color["purple"],
                "S-MANIAC": colors.color["purple"], # Very common typo
                "CHALLENGE": colors.color["purple"],
                "CRAZY": colors.color["purple"],
                "EXPERT": colors.color["purple"]
                }
