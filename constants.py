# This file *cannot* be imported until pyddr.init() is called.
# It needs to have pygame.event (and therefore display, too) ready.

# Event types.
E_PASS,E_QUIT,E_FULLSCREEN,E_SCREENSHOT,E_PGUP,E_PGDN,E_SELECT,E_MARK,E_UP,E_DOWN,E_LEFT,E_RIGHT,E_START = range(13)

# Z index constants
DEFAULTZINDEX,PADZINDEX,ARROWZINDEX,XANIMZINDEX,BARSZINDEX = range(5)

# Colors!
BLACK=(0,0,0)
WHITE=(255,255,255)

# K_* constants, mostly
from pygame.locals import *

import sys, os, config

# Detect the name of the OS - MacOS X is not really UNIX.
osname = None
if os.name == "nt": osname = "nt"
elif os.name == "posix":
  if os.path.islink("/System/Library/CoreServices/WindowServer"):
    osname = "macosx"
  elif os.environ.has_key("HOME"):
    osname = "posix"
else:
  print "Your platform is not supported by pyDDR. We're going to call it"#'
  print "POSIX, and then just let it crash."

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
elif osname == "nt":
  rc_path = "."

if not os.path.isdir(rc_path): os.mkdir(rc_path)

search_paths = (pyddr_path, rc_path)

lyric_colors = (('cyan', (0, 244, 244)),
                ('aqua', (0, 244, 122)),
                ('yellow', (244, 244, 122)),
                ('white', (244, 244, 244)),
                ('black', (0, 0, 0)),
                ('red', (244, 122, 122)),
                ('purple', (244, 122, 244)),
                ('orange', (244, 170, 0)))
# The above, as a hash
color_hash = {}
for color in lyric_colors: color_hash[color[0]] = color[1]

# Set up the configuration file
mainconfig = config.Config({ # Wow we have a lot of options
  "gfxtheme": "classic", "djtheme": "none", "songdir": ".",
  "stickycombo": 1,  "lowestcombo": 4,  "totaljudgings": 1,  "stickyjudge": 1,
  "lyriccolor": "cyan",  "transcolor": "aqua",
  "mixerclock": 1, "onboardaudio": 0, "masteroffset": 0,
  "reversescrolls": 0, "scrollspeed": 1,
  "explodestyle": 3, "arrowspin": 0, "arrowscale" : 1,
  "vesacompat": 0, "fullscreen": 0,
  "sortmode": 0, "sortpersist": 1,
  "previewmusic": 1,
  "showbackground": 1, "bgbrightness": 127,
  "sudden": 0, "hidden": 0, "little": 0, "assist": 0, "badknees": 0,
  "arrowcolors": 4, "fpsdisplay": 1, "showlyrics": 1,
  "showcombo": 1, "showtoparrows": 1,
  "killsongonfail": 0,
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
