#!/usr/bin/env python
# pydance - a dancing game written in Python

import os
import sys
import util
import games
import dance
from getopt import getopt
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

def print_help():
  print
  print "Usage: %s [options]" % sys.argv[0]
  print " -h, --help         display this help text and exit"
  print " -v, --version      display the version and exit"
  print " -f, --filename     load and play a step file"
  print " -m, --mode         the mode to play the file in (default SINGLE)"
  print " -d, --difficulty   the difficult to play the file (default BASIC)"
  sys.exit()

def print_version(): sys.exit()

def play_and_quit(fn, mode, difficulty):
  print "Entering debug (play-and-quit) mode."
  screen = set_display_mode(mainconfig)  
  pygame.display.set_caption("pydance " + VERSION)
  pygame.mouse.set_visible(0)
  pc = games.GAMES[mode].players
  dance.play(screen, [(fn, [difficulty] * pc)],
             [player_config] * pc, game_config, mode)
  sys.exit()

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
    except Exception, message:
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

  mode = "SINGLE"
  difficulty = "BASIC"
  test_file = None
  for opt, arg in getopt(sys.argv[1:],
                         "hvf:d:m:", ["help", "version", "filename=",
                                      "difficulty=", "mode="])[0]:
    if opt in ["-h", "--help"]: print_help()
    elif opt in ["-v", "--version"]: print_version()
    elif opt in ["-f", "--filename"]: test_file = arg
    elif opt in ["-m", "--mode"]: mode = arg
    elif opt in ["-d", "--difficulty"]: difficulty = arg

  if test_file: play_and_quit(test_file, mode, difficulty)

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
  record_dict = {}
  for song in songs:
    mix = song.info["mix"].lower()
    title = song.info["title"].lower()
    if song.info["subtitle"]: title += song.info["subtitle"].lower()
    if not song_dict.has_key(mix): song_dict[mix] = {}
    song_dict[mix][title] = song
    record_dict[song.info["recordkey"]] = song

  courses = load_files(screen, course_list, "courses", CRSFile,
                       (song_dict, record_dict))

  records.verify(record_dict)
  # Let the GC clean these up if it needs to.
  song_list = None
  course_list = None
  record_dict = None
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
