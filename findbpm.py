#!/usr/bin/env python

"""
This is a little utility program to find the BPM for a song.

It works by printing out the total bpm that you've tapped in since you
started.  This should let you average out bad values.
"""

import sys
import os
import pygame, pygame.font, pygame.image, pygame.mixer
from pygame.locals import *

def main():
    if len(sys.argv) != 2:
	raise "supply a music file as the only argument"
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

    pygame.mixer.music.load(sys.argv[1])
    pygame.mixer.music.play()
    beatstart = pygame.time.get_ticks()

    while 1:
	event = pygame.event.wait()

	if event.type == QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
	    break

	if event.type == KEYDOWN:
	    beats = beats + 1
	    now = pygame.time.get_ticks()
	    if beats == 0:
		starttime = now
		beatstart = starttime-beatstart
	    else:
		screen.fill((0,0,0))
		timestr = '%0.6s' % (1000*60.0*beats/(now-starttime))
		beatstr = '%s : %s' % (beatstart, timestr)
		text = font.render(beatstr, 1, (250, 80, 80))
		textpos = text.get_rect()
		textpos.centerx = screen.get_rect().centerx
		textpos.centery = screen.get_rect().centery
		screen.blit(text, textpos)
		pygame.display.flip()

    if starttime:
	print '*** Started song', beatstart, 'ms in'
    if beats > 0:
	print '***', beats, 'beats over', (now-starttime)/1000.0 ,'seconds yields', timestr, 'BPM'

if __name__ == '__main__':
    main()
