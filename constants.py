# This file *cannot* be imported until pyddr.init() is called.
# It needs to have pygame.event (and therefore display, too) ready.

# Event types.
E_PASS,E_QUIT,E_FULLSCREEN,E_SCREENSHOT,E_PGUP,E_PGDN,E_SELECT,E_MARK,E_UP,E_DOWN,E_LEFT,E_RIGHT,E_START,E_CREATE,E_UNSELECT,E_CLEAR,E_UNMARK = range(17)

# Z index constants
DEFAULTZINDEX,PADZINDEX,ARROWZINDEX,XANIMZINDEX,BARSZINDEX = range(5)

import sys, os, config, pygame

# Detect the name of the OS - MacOS X is not really UNIX.
osname = None
if os.name == "nt": osname = "win32"
elif os.name == "posix":
  if os.path.islink("/System/Library/CoreServices/WindowServer"):
    osname = "macosx"
  elif os.environ.has_key("HOME"):
    osname = "posix"
else:
  print "Your platform is not supported by pyDDR. We're going to call it"
  print "POSIX, and then just let it crash."

if osname == 'posix': # We need to force stereo in many cases.
  try: pygame.mixer.pre_init(44100,-16,2)
  except: pygame.mixer.pre_init()

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
  rc_path = os.path.join(os.environ["HOME"], ".pyddr")
elif osname == "macosx":
  rc_path = os.path.join(os.environ["HOME"], "Library", "Preferences", "pyDDR")
elif osname == "win32":
  rc_path = "."

if not os.path.isdir(rc_path): os.mkdir(rc_path)

search_paths = (pyddr_path, rc_path)

# Set up the configuration file
mainconfig = config.Config({ # Wow we have a lot of options
  "gfxtheme": "classic", "djtheme": "none", "songdir": ".",
  "stickycombo": 1,  "lowestcombo": 4,  "totaljudgings": 1,  "stickyjudge": 1,
  "lyriccolor": "cyan",  "transcolor": "aqua",
  "mixerclock": 1, "onboardaudio": 0, "masteroffset": 0,
  "reversescroll": 0, "scrollspeed": 1,
  "explodestyle": 3, "arrowspin": 0, "arrowscale" : 1,
  "vesacompat": 0, "fullscreen": 0,
  "sortmode": 0,
  "previewmusic": 1,
  "showbackground": 1, "bgbrightness": 127,
  "gratuitous": 1,
  "sudden": 0, "hidden": 0, "little": 0, "assist": 0, "badknees": 0,
  "arrowcolors": 4, "fpsdisplay": 1, "showlyrics": 1,
  "showcombo": 1, "showtoparrows": 1,
  "autofail": 1,
  "grading": 1,
  "keyboard": "qwerty",
  "strobe": 0
  })

if osname == "posix":
  mainconfig.load("/etc/pyddr.cfg", True)
elif osname == "macosx":
  mainconfig.load("/Library/Preferences/pyDDR/pyddr.cfg")

mainconfig.load("pyddr.cfg")
mainconfig.load(os.path.join(rc_path, "pyddr.cfg"))

import input

event = input.EventManager()

# Fonts
FONTS = {}
for s in (192, 60, 48, 40, 32, 28, 26, 20, 16, 14):
  FONTS[s] = pygame.font.Font(None, s)
