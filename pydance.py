#!/usr/bin/env python
# pydance - a dancing game written in Python

import os
import sys
import util
import getopt
import pygame
import colors
import records
import menudriver

from fileparsers import SongItem
from courses import CRSFile
from pygame.mixer import music
from fontfx import TextProgress
from error import ErrorMessage
from pad import pad

from constants import *

def set_display_mode(mainconfig):
  try:
    flags = HWSURFACE | DOUBLEBUF
    if mainconfig["vesacompat"]: flags = 0
    elif mainconfig["fullscreen"]: flags |= FULLSCREEN
    screen = pygame.display.set_mode([640, 480], flags, 16)
  except:
    print "E: Can't get a 16 bit display!" 
    sys.exit(3)
  return screen

def load_files(screen, files, type, Ctr, args):
  if len(files) == 0: return []

  screen.fill(colors.BLACK)
  pct = 0
  inc = 100.0 / len(files)
  # Remove duplicates
  files = list(dict(map(None, files, [])).keys())
  objects = []
  message = "Found %d %s. Loading..." % (len(files), type)
  pbar = TextProgress(FONTS[60], message, colors.WHITE, colors.BLACK)
  r = pbar.render(0).get_rect()
  r.center = [320, 240]
  for f in files:
    try: objects.append(Ctr(*((f,) + args)))
    except RuntimeWarning, message:
      print "W:", f
      print "W:", message
      print
    except RuntimeError, message:
      print "E", f
      print "E:", message
      print
    except None:#Exception, message:
      print "E: Unknown error loading", f
      print "E:", message
      print "E: Please contact the developers (pyddr-devel@icculus.org)."
      print
    pct += inc
    img = pbar.render(pct)
    pygame.display.update(screen.blit(img, r))

  return objects


def main():
  print "pydance", VERSION, "<pyddr-discuss@icculus.org> - irc.freenode.net/#pyddr"

  if mainconfig["usepsyco"]:
    try:
      import psyco
      print "Psyco optimizing compiler found. Using psyco.full()."
      psyco.full()
    except ImportError: print "Psyco optimizing compiler not found."

  # FIXME Debug mode needs to be added again. Or some command line options.

  song_list = []
  course_list = []
  for dir in mainconfig["songdir"].split(os.pathsep):
    print "Searching for songs in", dir
    song_list.extend(util.find(dir, ['*.step', '*.dance', '*.dwi',
                                     '*.sm', '*/song.*']))
  for dir in mainconfig["coursedir"].split(os.pathsep):
    print "Searching for courses in", dir
    course_list.extend(util.find(dir, ['*.crs']))

  screen = set_display_mode(mainconfig)
  
  pygame.display.set_caption("pydance " + VERSION)
  pygame.mouse.set_visible(0)

  music.load(os.path.join(sound_path, "menu.ogg"))
  music.play(4, 0.0)

  songs = load_files(screen, song_list, "songs", SongItem, (False,))

  song_dict = {}
  for song in songs:
    mix = song.info["mix"].lower()
    title = song.info["title"].lower()
    if song.info["subtitle"]: title += song.info["subtitle"].lower()
    if not song_dict.has_key(mix): song_dict[mix] = {}
    song_dict[mix][title] = song

  courses = load_files(screen, course_list, "courses", CRSFile, (song_dict,))

  # Let the GC clean these up if it needs to.
  song_list = None
  course_list = None

  pad.empty()

  if len(songs) < 1:
    ErrorMessage(screen,
                 ("You don't have any songs or step files. Check out",
                  "http://icculus.org/pyddr/get.php",
                  "and download some free ones."
                  " ", " ", " ",
                  "If you already have some, make sure they're in",
                  mainconfig["songdir"]))
    print "You don't have any songs. Check http://icculus.org/pyddr/get.php."
    sys.exit(1)

  menudriver.do(screen, (songs, courses, screen))
  music.stop()
  pygame.quit()
  mainconfig.write(os.path.join(rc_path, "pydance.cfg"))
  if mainconfig["saveinput"]: pad.write(os.path.join(rc_path, "input.cfg"))
  records.write()

if __name__ == '__main__': main()
