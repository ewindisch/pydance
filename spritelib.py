# Contains various sprite extension classes pydance uses.

#FIXME - needs documentation (and cleanups?)
# and probably generalization so we can use these elsewhere in the code

import pygame, glob, colors
from constants import *

class SimpleSprite(pygame.sprite.Sprite):
  def __init__ (self, file):
    pygame.sprite.Sprite.__init__(self)
    image = pygame.image.load(file).convert()
    image.set_colorkey(image.get_at((0,0)))
    self.fn = file
    self.image = image
    self.rect = image.get_rect()

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

  def __getattr__(self,attr):
    return getattr(self.image,attr)
    
  def __repr__(self):
    return '<Sprite fn=%r rect=%r>'%(self.fn,self.rect)

class BlankSprite(SimpleSprite):
  def __init__ (self, res, fill=colors.BLACK):
    pygame.sprite.Sprite.__init__(self)
    image = pygame.Surface(res)
    if fill is not None: image.fill(fill)
    self.image = image
    self.rect = image.get_rect()

  def __repr__(self):
    return '<Sprite rect=%r>'%(self.rect)

class CloneSprite(BlankSprite):
  def __init__ (self, spr):
    pygame.sprite.Sprite.__init__(self)
    self.image = spr.convert()
    try:
      self.rect = Rect(spr.rect)
    except:
      self.rect = spr.get_rect()

class TransformSprite(BlankSprite):
  _rotozoom = pygame.transform.rotozoom
  _rotate = pygame.transform.rotate
  _flip = pygame.transform.flip
  _scale = pygame.transform.scale
  def __init__ (self, spr, scale=None, size=None,hflip=0,vflip=0,angle=None,filter=None):
    pygame.sprite.Sprite.__init__(self)
    image = None
    try:
      image = spr.image
    except:
      image = spr
    if scale and not size:      size = map(lambda n,scale=scale: scale*n, spr.rect.size)
    if angle and size:          image = self._rotozoom(image,angle,zoom)
    elif angle:                 image = self._rotate(image,angle)
    elif size:                  image = self._scale(image,size)
    if hflip or vflip:          image = self._flip(image,hflip,vflip)
    self.image = image
    self.rect = self.image.get_rect()

class TextSprite(BlankSprite):
  def __init__(self, font=None, size=32, text='', color=colors.WHITE, bold=None, italic=None, underline=None, antialias=1, bkgcolor=None):
    pygame.sprite.Sprite.__init__(self)
    surf = None
    font = pygame.font.Font(font, size)
    if bold:      font.set_bold(bold)
    if italic:    font.set_italic(italic)
    if underline: font.set_underline(underline)
    if bkgcolor:
      surf = font.render(text,antialias,color,bkgcolor)
      surf.set_colorkey(bkgcolor)
    else:
      surf = font.render(text,antialias,color)
    self.image = surf
    self.rect = surf.get_rect()

# acts like a subclass of Sprite
class SimpleAnim:
  def __init__ (self, path, prefix, separator, imgtype='png', frameNumbers=None, files=None):
    frames = []
    if files is None:
      if frameNumbers is None:
        files=glob.glob(os.path.join(path,separator.join([prefix,'*.'+imgtype])))
      else:
        files=[]
        for i in frameNumbers: 
          files.append(os.path.join(path,separator.join([prefix,"%d.%s"%(i,imgtype)])))
    self.frames=map(lambda fn,SimpleSprite=SimpleSprite: SimpleSprite(fn), files)
    self.curframe = 0

  def update(self):
    """swap the groups of old sprite into new sprite"""
    oldspr = self.curframe
    frames = self.frames
    curframe = oldspr+1
    if curframe>=len(frames): curframe=0
    # degenerate case, a 1 frame animation
    if oldspr == curframe: return
    frames[curframe].rect = frames[oldspr].rect
    # only one frames is the "sprite" at any given time
    for n in frames[oldspr].groups: frames[curframe].add(n)
    frames[oldspr].kill()
    self.curframe = curframe

  def __getattr__(self,attr):
    """pretend we are a Sprite by overloading getattr with frames[curframe]"""
    return getattr(self.frames[self.curframe],attr)

#  def __setattr__(self,attr,val):
#    if attr=='rect': setattr(self.frames[self.curframe],attr,val)
#    else: self.__dict__[attr]=val 

class BGimage(pygame.sprite.Sprite):
  def __init__ (self, filename):
    pygame.sprite.Sprite.__init__(self)
    self.image = pygame.transform.scale(pygame.image.load(filename),(640,480)).convert()
    self.image.set_alpha(mainconfig['bgbrightness'], RLEACCEL)
    self.rect = self.image.get_rect()
    self.rect.top = 0
    self.rect.left = 0
