# FontFX, by Brendan Becker  ( http://clickass.org/ )
# use this anywhere you want, just give me a little credit =]
#
# Implement with:
# import fontfx
# [....]
#  asdf = fontfx.effect("text",size,effect_amt,(rectsizex,rectsizey),(r,g,b))
#  asdfpos = asdf.get_rect()
#  asdfpos.centerx = screen.get_rect().centerx
#  asdfpos.top = 16
#  screen.blit(asdf,asdfpos)

import pygame, pygame.font
from pygame.locals import *

# SINKBLUR - sinking "motion blur" effect (middle is brightest)
def sinkblur(textstring, textsize, amount, displaysize, trgb=(255,255,255)):
  displaysurface = pygame.Surface(displaysize)
  displayrect = displaysurface.get_rect()
  if amount*2 > textsize:
    amount = textsize / 2
  for i in xrange(amount):
    font = pygame.font.Font(None, textsize-(i*2))
    camt = amount-i
    r = trgb[0]/camt
    g = trgb[1]/camt
    b = trgb[2]/camt
    if r < 0:  r = 0
    if g < 0:  g = 0
    if b < 0:  b = 0
    text = font.render(textstring, 1, (r,g,b) )
    textrect = text.get_rect()
    displaysurface.blit(text, (displayrect.centerx-textrect.centerx,displayrect.centerx-textrect.centerx) )
  return displaysurface

# EMBFADE - does a 3d emboss-like effect
def embfade(textstring, textsize, amount, displaysize, trgb=(255,255,255)):
  displaysurface = pygame.Surface(displaysize)
  font = pygame.font.Font(None, textsize)
  for i in xrange(amount):
    camt = i + 1
    r = trgb[0]/camt
    g = trgb[1]/camt
    b = trgb[2]/camt
    if r < 0:  r = 0
    if g < 0:  g = 0
    if b < 0:  b = 0
    text = font.render(textstring, 1, (r,g,b) )
    displaysurface.blit(text, (0+i,0+i))
  return displaysurface

# SHADEFADE - does a 3d dropshadow-like effect
def shadefade(textstring, textsize, amount, displaysize, trgb=(255,255,255)):
  displaysurface = pygame.Surface(displaysize)
  font = pygame.font.Font(None, textsize)
  for i in xrange(amount):
    camt = amount-i
    r = trgb[0]/camt
    g = trgb[1]/camt
    b = trgb[2]/camt
    if r < 0:  r = 0
    if g < 0:  g = 0
    if b < 0:  b = 0
    text = font.render(textstring, 1, (r,g,b) )
    displaysurface.blit(text, (camt,camt))
  return displaysurface

