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

  # Remove duplicates
  song_list = list(dict(map(None, song_list, [])).keys())
  course_list = list(dict(map(None, course_list, [])).keys())

  screen = SetDisplayMode(mainconfig)
  
  pygame.display.set_caption('pydance ' + VERSION)
  pygame.mouse.set_visible(0)

  audio.load(os.path.join(sound_path, "menu.ogg"))
  audio.play(4, 0.0)

  total = len(song_list)
  parsed = 0.0
  songs = []

  pbar = fontfx.TextProgress(FONTS[60], "Found " + str(total) +
                             " songs. Loading...", colors.WHITE, colors.BLACK)
  r = pbar.render(0).get_rect()
  r.center = (320, 240)
  for f in song_list:
    try: songs.append(fileparsers.SongItem(f, False))
    except RuntimeWarning, message:
      print "W:", message
    except RuntimeError, message:
      print "E:", message
    except Exception, message:
      print "E: Unknown error loading", f
      print "E:", message
      print "E: Please contact the developers (pydance-devel@icculus.org)."
    img = pbar.render(parsed / total)
    pygame.display.update(screen.blit(img, r))
    parsed += 100.0

  screen.fill(colors.BLACK)
  pygame.display.update()
  total = len(course_list)
  parsed = 0.0
  courses = []
  pbar = fontfx.TextProgress(FONTS[60], "Found " + str(total) +
                             " courses. Loading...", colors.WHITE,colors.BLACK)
  r = pbar.render(0).get_rect()
  r.center = (320, 240)
  for f in course_list:
    try: courses.append(CRSFile(f, songs))
    except RuntimeWarning, message:
      print "W:", message
    except RuntimeError, message:
      print "E: Error loading", f
      print "E:", message
    except Exception, message:
      print "E: Unknown error loading", f
      print "E:", message
      print "E: Please contact the developers (pydance-devel@icculus.org)."
    img = pbar.render(parsed / total)
    pygame.display.update(screen.blit(img, r))
    parsed += 100.0
        
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
