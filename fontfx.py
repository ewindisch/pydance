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
    self.tempsurface = pygame.surface.Surface((640,64))
    self.r = random.randint(64, r)
    self.g = random.randint(64, g)
    self.b = random.randint(64, b)
    self.cycles_left = 0

    self.reset()
    self.zoomtext = text
    self.textrendered = 0

  def reset(self):
    self.mrangle = 0
    self.textrendered = 0
    self.cycles_left = 0

  def iterate(self):
    if self.cycles_left == 0:
      self.cycles_left = random.randint(20, 50)
      self.colortochange = random.randint(0,3)
      self.colordiff = random.randint(-2, 2)

    if self.colortochange == 0:
      if self.r == 64 or self.r == 128: self.colordiff *= -1
      self.r += self.colordiff
      self.r = min(128, max(self.r, 64))
    elif self.colortochange == 1:
      if self.g == 64 or self.g == 128: self.colordiff *= -1
      self.g += self.colordiff
      self.g = min(128, max(self.g, 64))
    elif self.colortochange == 2:
      if self.b == 64 or self.b == 128: self.colordiff *= -1
      self.b += self.colordiff
      self.b = min(128, max(self.b, 64))

    opposite = (127 + self.r, 127 + self.g, 127 + self.b)

    self.mrangle += 2
    self.cycles_left -= 1

    zoomsurface = pygame.transform.scale(self.tempsurface,(656,72))
    zoomsurface = pygame.transform.rotate(self.tempsurface,self.mrangle)
    zoomsurface.set_alpha(120)
    zsrect = zoomsurface.get_rect()
    zsrect.centerx = 320
    zsrect.centery = 32
    self.tempsurface.fill(opposite)
    self.tempsurface.blit(zoomsurface, zsrect)
    text = self.zf.render(self.zoomtext,1,(self.r,self.g,self.b))
    trect = text.get_rect()
    self.tempsurface.blit(text, (320-(trect.size[0]/2),
                                      32-(trect.size[1]/2)))

# From the PCR (http://www.pygame.org/pcr/progress_text/index.php),
# by Pete Shinners.
class TextProgress:
    def __init__(self, font, message, color, bgcolor):
        self.font = font
        self.message = message
        self.color = color
        self.bgcolor = bgcolor
        self.offcolor = [c^40 for c in color]
        self.notcolor = [c^0xFF for c in color]
        self.text = font.render(message, 0, (255,0,0), self.notcolor)
        self.text.set_colorkey(1)
        self.outline = self.textHollow(font, message, color)
        self.bar = pygame.Surface(self.text.get_size())
        self.bar.fill(self.offcolor)
        width, height = self.text.get_size()
        stripe = Rect(0, height/2, width, height/4)
        self.bar.fill(color, stripe)
        self.ratio = width / 100.0

    def textHollow(self, font, message, fontcolor):
        base = font.render(message, 0, fontcolor, self.notcolor)
        size = base.get_width() + 2, base.get_height() + 2
        img = pygame.Surface(size, 16)
        img.fill(self.notcolor)
        base.set_colorkey(0)
        img.blit(base, (0, 0))
        img.blit(base, (2, 0))
        img.blit(base, (0, 2))
        img.blit(base, (2, 2))
        base.set_colorkey(0)
        base.set_palette_at(1, self.notcolor)
        img.blit(base, (1, 1))
        img.set_colorkey(self.notcolor)
        return img

    def render(self, percent=50):
        surf = pygame.Surface(self.text.get_size())
        if percent < 100:
            surf.fill(self.bgcolor)
            surf.blit(self.bar, (0,0), (0, 0, percent*self.ratio, 100))
        else:
            surf.fill(self.color)
        surf.blit(self.text, (0,0))
        surf.blit(self.outline, (-1,-1))
        surf.set_colorkey(self.notcolor)
        return surf
