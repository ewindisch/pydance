#!/usr/bin/env python
# This is a little utility program to find the BPM for a song.

# It works by printing out the total bpm that you've tapped in since you
# started.  This should let you average out bad values.

import getopt
import sys
import os
import time
import pygame, pygame.font, pygame.image, pygame.mixer
from pygame.locals import *

VERSION = "0.9"

def usage():
  print "findbpm " + VERSION + " - find the bpm of a song"
  print "Usage: " + sys.argv[0] + " songfile.ogg"
  print
  print """\
Press a key on time with the beat. An average BPM (for as long as you keep
tapping) will be calculated."""

def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "vh", ["help", "version"])
  except getopt.GetoptError:
    usage()
    sys.exit(2)
    
  if len(args) != 1:
    usage()
    sys.exit(2)
    
  pygame.init()
  screen = pygame.display.set_mode((400, 48), HWSURFACE|DOUBLEBUF)
  pygame.display.set_caption('Tap to find Start, BPM')
  screen.fill((0,0,0))
  font = pygame.font.Font(None, 48)
  text = font.render('Tap to find Start, BPM', 1, (250, 80, 80))
  textpos = text.get_rect()
  textpos.centerx = screen.get_rect().centerx
  textpos.centery = screen.get_rect().centery
  screen.blit(text, textpos)
  # show name
  pygame.display.flip()

  beats = -1
  starttime = 0
  timestr = ""
  
  pygame.mixer.music.load(args[0])
  pygame.mixer.music.play()
  beatstart = pygame.time.get_ticks()
  
  while 1:
    event = pygame.event.wait()

    if event.type == QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
      break

    elif event.type == KEYDOWN:
      beats += 1
      now = pygame.time.get_ticks()
      if beats == 0:
        starttime = now
        beatstart = starttime-beatstart
      else:
        screen.fill((0,0,0))
        timestr = '%0.6s' % (1000*60.0*beats/(now-starttime))
        beatstr = 'offset %s : bpm %s' % (beatstart, timestr)
        text = font.render(beatstr, 1, (250, 80, 80))
        textpos = text.get_rect()
        textpos.centerx = screen.get_rect().centerx
        textpos.centery = screen.get_rect().centery
        screen.blit(text, textpos)
        pygame.display.flip()

  if starttime:
    print "Started song", str(beatstart), "ms in"

  if beats > 0:
    print str(beats), 'beats over', str((now-starttime)/1000.0), 'seconds yields', timestr, 'BPM'

if __name__ == '__main__':
    main()
