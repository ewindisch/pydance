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
import random
from pygame.locals import *

# SINKBLUR - sinking "motion blur" effect (middle is brightest)
def sinkblur(textstring, textsize, amount, displaysize, trgb=(255,255,255)):
  displaysurface = pygame.Surface(displaysize)
  displayrect = displaysurface.get_rect()
  if amount*2 > textsize:
    amount = textsize / 2
  for i in range(amount):
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
  for i in range(amount):
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
  for i in range(amount):
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

# Zoom and rotate text randomly
class TextZoomer:
  def __init__(self,text,r,g,b):
    self.zf = pygame.font.Font(None,60)
    self.zoomsurface = pygame.surface.Surface((640,64))
    self.tempsurface = pygame.surface.Surface((640,64))
    self.r = r
    self.g = g
    self.b = b

    self.zoomtext = text
    self.reset()

  def changetext(self,text):
    if text:
      self.zoomtext = text
      self.textrendered = 0

  def reset(self):
    self.mrangle = 0
    self.textrendered = 0

  def iterate(self):
    colortochange = random.randint(0,333) % 4
    colordiff = (random.random()*8) - 4
    if colortochange == 0:
      if 255 > (self.r + colordiff) > 0:
        self.r += colordiff
    if colortochange == 1:
      if 255 > (self.g + colordiff) > 0:
        self.g += colordiff
    if colortochange == 2:
      if 255 > (self.b + colordiff) > 0:
        self.b += colordiff

    self.mrangle += 1

    self.zoomsurface = pygame.transform.scale(self.tempsurface,(656,72))
    self.zoomsurface = pygame.transform.rotate(self.zoomsurface,self.mrangle)
    self.zoomsurface.set_alpha(48)
    zsrect = self.zoomsurface.get_rect()
    zsrect.centerx = 320
    zsrect.centery = 32
    self.tempsurface.blit(self.zoomsurface,zsrect)
    self.textrendered = 0
    if not self.textrendered:
      self.text = self.zf.render(self.zoomtext,1,(self.r,self.g,self.b))
      self.trect = self.text.get_rect()
      self.textrendered = 1
    self.tempsurface.blit(self.text,(320-(self.trect.size[0]/2),32-(self.trect.size[1]/2)))
