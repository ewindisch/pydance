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
from constants import *

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

class TextZoomer:
  def __init__(self, text, font, size, fore, back):
    self.tempsurface = pygame.surface.Surface(size)
    self.back = back
    self.fore = fore
    self.size = size
    self.font = font

    self.reset()
    self.zoomtext = text
    self.textrendered = 0

  def reset(self):
    self.mrangle = 0
    self.textrendered = 0

  def iterate(self):
    self.mrangle += 2

    zoomsurface = pygame.transform.scale(self.tempsurface,
                                         (self.size[0] + 16,
                                          self.size[1] + 16))
    zoomsurface = pygame.transform.rotate(self.tempsurface,self.mrangle)
    zoomsurface.set_alpha(120)
    zsrect = zoomsurface.get_rect()
    zsrect.center = (self.size[0] / 2, self.size[1] / 2)
    self.tempsurface.fill(self.back)
    self.tempsurface.blit(zoomsurface, zsrect)
    text = self.font.render(self.zoomtext,1, self.fore)
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
        self.text.set_colorkey(1, RLEACCEL)
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
        base.set_colorkey(0, RLEACCEL)
        img.blit(base, (0, 0))
        img.blit(base, (2, 0))
        img.blit(base, (0, 2))
        img.blit(base, (2, 2))
        base.set_colorkey(0, RLEACCEL)
        base.set_palette_at(1, self.notcolor)
        img.blit(base, (1, 1))
        img.set_colorkey(self.notcolor, RLEACCEL)
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
        surf.set_colorkey(self.notcolor, RLEACCEL)
        return surf

class zztext(pygame.sprite.Sprite):
    def __init__(self, text, x, y):
      pygame.sprite.Sprite.__init__(self)
      self.cent = (x, y)
      self.zoom = 0
      self.baseimage = pygame.surface.Surface((320,24))
      self.rect = self.baseimage.get_rect()
      self.rect.center = self.cent

      for i in (0, 1, 2, 3, 4, 5, 6, 7, 8, 15):
        font = pygame.font.Font(None, 9+i)
        gtext = font.render(text, 1, (i * 16,) * 3)
        textpos = gtext.get_rect()
        textpos.center = (160, 12)
        self.baseimage.blit(gtext, textpos)

      self.baseimage.set_colorkey(self.baseimage.get_at((0, 0)), RLEACCEL)
      self.image = self.baseimage

    def zin(self):
      self.zoom = 1
      self.zdir = 1
      
    def zout(self):
      self.zoom = 31
      self.zdir = -1
      
    def update(self):
      if 32 > self.zoom > 0:
        self.image = pygame.transform.rotozoom(self.baseimage, 0,
                                               self.zoom/32.0)
        self.rect = self.image.get_rect()
        self.rect.center = self.cent
        self.zoom += self.zdir
      else:
        self.zdir = 0
