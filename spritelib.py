# Contains various sprite extension classes pydance uses.

#FIXME - needs documentation (and cleanups?)
# and probably generalization so we can use these elsewhere in the code

import pygame, glob, colors
from constants import *

class SimpleSprite(pygame.sprite.Sprite):
  def __init__ (self, file=None,spr = None, res = None, fill = colors.BLACK ):
    pygame.sprite.Sprite.__init__(self)
    if file:
      image = pygame.image.load(file).convert()
      image.set_colorkey(image.get_at((0,0)))
      self.fn = file
      rect = image.get_rect()
    elif spr:
      try:
        image = spr.image.convert()
        rect = Rect(spr.rect)
      except:
        image = spr.convert()
        rect = image.get_rect()
    elif res:
      image = pygame.Surface(res)
      if fill is not None: image.fill(fill)
      rect = image.get_rect()
    self.image = image
    self.rect = rect
  		
  def draw(self,surf,pos=None,rect=None):
    if rect and pos:
      return surf.blit(self.image,pos,rect)
    elif pos:
      return surf.blit(self.image,pos)
    elif rect:
      return surf.blit(self.image,(0,0),rect)
    else:
      return surf.blit(self.image,self.rect)

  def update(self):
    pass
    
  def __repr__(self):
    return '<Sprite rect=%r>'%(self.fn,self.rect)
