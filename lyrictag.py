#!/usr/bin/env python

"""
This sucker is a much hacked version of mu's findbpm.py to tag lyrics in a 
text file.
"""

import sys
import os
import pygame, pygame.font, pygame.image, pygame.mixer
from pygame.locals import *

def main():
  if len(sys.argv) != 3:
    print "lyrictag syntax:    ./lyrictag.py songfile txtfile"
    print "  SONGFILE denotes an MP3, OGG, WAV, MID, etc. to play."
    print "  TXTFILE denotes a text file to read in lyrics from."
    print "  Both should be path qualified if necessary."
    print "  Make sure the text file has no blank lines between text."
    print
    print "Usage:"
    print "A screen will appear with the current lyric centered on the screen."
    print "Press enter on the lyric when it should be displayed. The list will"
    print "auto-advance. When the song is over or you press ESC, the program"
    print "will quit and you can paste the text in the newly created text file"
    print "into your step file before the line that contains 'SINGLE'"
    print
    print "That's it!"
  else:
    pygame.init()
    screen = pygame.display.set_mode((640, 480), HWSURFACE|DOUBLEBUF)
    pygame.display.set_caption('lyric tagger')
    screen.fill((0,0,0))

    txtfile = open(sys.argv[2],"r") #but for reading
    print "Opened ",sys.argv[2], " to read lyrics from."

    lyricfile = open(sys.argv[2]+".lyric","w") #but for writing
    print "Opened ",sys.argv[2]+".lyric", " for writing step lyric data to."
    lyricfile.write("LYRICS\n")

    currentline = 0
    totallines = 0
    lyrictext = []
    fileline = '-'
    while fileline != '':
      fileline = txtfile.readline()
      if fileline != '':
        totallines += 1
        lyrictext.append(fileline)
    lyrictext.append('[END OF FILE]\n')
 
    pygame.mixer.music.load(sys.argv[1])
    pygame.mixer.music.play()
    beatstart = pygame.time.get_ticks()

    font = pygame.font.Font(None, 48)
    while 1:
	event = pygame.event.poll()
        
        screen.fill((0,0,0))
        for j in range(11):
          i = j - 5 
          c = i + currentline
          if c >= 0 and c <= totallines:
            if j == 5:
              text = font.render(lyrictext[c][:-1], 1, (224, 224, 224))
            else:
              text = font.render(lyrictext[c][:-1], 1, (160, 160, 160))
            textpos = text.get_rect()
            textpos.centerx = screen.get_rect().centerx
            textpos.centery = 20 + (48*j)
            screen.blit(text, textpos)
        # show name
        pygame.display.flip()

	if event.type == QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
	    break

        if not pygame.mixer.music.get_busy():
          break

	if event.type == KEYDOWN:
	    now = pygame.time.get_ticks()/1000.0
            if currentline < totallines:
              lyricfile.write("atsec "+repr(now)+"\n")
              lyricfile.write("lyric "+lyrictext[currentline])
              currentline += 1

    lyricfile.write("end\n")
    print "song ended."

if __name__ == '__main__':
    main()
