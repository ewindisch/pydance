#! /usr/bin/env python
# pydance - dancing game written in Python

import pygame
from constants import *

from ui import ui
from pad import pad

import fontfx, menudriver, fileparsers, audio, colors
from courses import CRSFile

import os, sys, error, util, getopt

os.chdir(pydance_path)

def SetDisplayMode(mainconfig):
  try:
    flags = HWSURFACE | DOUBLEBUF
    if mainconfig["vesacompat"]: flags = 0
    elif mainconfig["fullscreen"]: flags |= FULLSCREEN
    screen = pygame.display.set_mode([640, 480], flags, 16)
  except:
    print "E: Can't get a 16 bit display!" 
    sys.exit()
  return screen

def load_files(screen, files, type, Ctr, args):
  # Remove duplicates
  screen.fill(colors.BLACK)
  pct = 0
  inc = 100.0 / len(files)
  files = list(dict(map(None, files, [])).keys())
  objects = []
  message = "Found %d %s. Loading..." % (len(files), type)
  pbar = fontfx.TextProgress(FONTS[60], message, colors.WHITE, colors.BLACK)
  r = pbar.render(0).get_rect()
  r.center = (320, 240)
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
    except Exception, message:
      print "E: Unknown error loading", f
      print "E:", message
      print "E: Please contact the developers (pydance-devel@icculus.org)."
      print
    pct += inc
    img = pbar.render(pct)
    pygame.display.update(screen.blit(img, r))

  return objects


def main():
  print "pydance", VERSION, "<pydance-discuss@icculus.org> - irc.freenode.net/#pyddr"

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
    print "Searching", dir
    song_list.extend(util.find(dir, ['*.step', '*.dance', '*.dwi',
                                     '*.sm', '*/song.*']))
  for dir in mainconfig["coursedir"].split(os.pathsep):
    print "Searching", dir
    course_list.extend(util.find(dir, ['*.crs']))

  screen = SetDisplayMode(mainconfig)
  
  pygame.display.set_caption('pydance ' + VERSION)
  pygame.mouse.set_visible(0)

  audio.load(os.path.join(sound_path, "menu.ogg"))
  audio.play(4, 0.0)

  songs = load_files(screen, song_list, "songs",
                     fileparsers.SongItem, (False,))

  song_dict = {}
  for song in songs:
    mix = song.info["mix"].lower()
    title = song.info["title"].lower()
    if song.info["subtitle"]: title += song.info["subtitle"].lower()
    if not song_dict.has_key(mix): song_dict[mix] = {}
    song_dict[mix][title] = song

  courses = load_files(screen, course_list, "courses", CRSFile, (song_dict,))

  song_list = None
  course_list = None
  ui.empty()

  if len(songs) < 1:
    error.ErrorMessage(screen,
                      ("You don't have any songs or step files. Check out",
                       "http://icculus.org/pyddr/get.php",
                       "and download some free ones."
                       " ", " ", " ",
                       "If you already have some, make sure they're in",
                       mainconfig["songdir"]))
    print "You don't have any songs. http://icculus.org/pyddr/get.php."
    sys.exit(1)

  menudriver.do(screen, (songs, courses, screen))
  audio.stop()
  pygame.display.quit()
  mainconfig.write(os.path.join(rc_path, "pydance.cfg"))
  if mainconfig["saveinput"]:
    pad.write(os.path.join(rc_path, "input.cfg"))

if __name__ == '__main__': main()
