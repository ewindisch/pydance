# GFXTheme and associated classes.
# These handle loading the various graphics themes for pyDDR.

import dircache, os

from constants import *
from spritelib import *

class GFXTheme:
  def themes(cls, imgtype = "png"):
    theme_list = []
    for path in search_paths:
      checkpath = os.path.join(path, "themes", "gfx")
      if os.path.isdir(checkpath):
        for name in dircache.listdir(checkpath):
          if os.path.isfile(os.path.join(checkpath, name,
                                         "arr_c_d_0." + imgtype)):
            theme_list.append(name)
    return theme_list

  themes = classmethod(themes)

  def __init__(self, name):
    self.name = name
    self.path = None
    for path in search_paths:
      if os.path.isdir(os.path.join(path, "themes", "gfx", name)):
        self.path = os.path.join(path, "themes", "gfx", name)
    if self.path == None:
      print "Error: Cannot load graphics theme '%s'." % name
      sys.exit(1)

    self.load()

  def load(self):
    self.arrows = ArrowSet(self.path)
    self.bars = BarSet(self.path)

  def toparrows(self, bpm, ypos, playernum):
    arrs = {}
    arrfx = {}
    for d in DIRECTIONS:
      arrs[d] = TopArrow(bpm, d, ypos, playernum, self.path)
      arrfx[d] = ArrowFX(bpm, d, ypos, playernum, self.path)
    return arrs, arrfx

  def __repr__(self):
    return ('<GFXTheme name=%r>' % self.name)

class ArrowSet: 
  def __init__ (self, path, imgtype='png'):
    arrows = {"l": 12, "d": 12+76, "u": 12+2*76, "r": 12+3*76}
    for dir,left in arrows.items():
      for cnum in range(4):
        if cnum == 3:
          color = 1
        else:
          color = cnum
        arrows[dir+repr(cnum)] = ScrollingArrow(path, dir, str(color),
                                                imgtype, left)
    # allow access by instance.l or instance.arrows['l']
    for n in arrows: self.__dict__[n] = arrows[n] 
    self.arrows = arrows
  def __getitem__ (self,item):
    # allow access by instance['l']
    return getattr(self,item)

class TopArrow(pygame.sprite.Sprite):

  def __init__ (self, bpm, direction, ypos, playernum, path):
    pygame.sprite.Sprite.__init__(self)        #call Sprite initializer
    self.presstime = -1
    self.tick = toRealTime(bpm, 1);
    self.frame = 0
    self.oldframe = -1
    self.state = 'n'
    self.filepref = 'arr_'
    self.adder = 0
    self.direction = direction
    self.topimg = []
    self.playernum = playernum
    self.ypos = ypos

    for i in range(8):
      if i < 4:        ftemp = 'n_'
      else:            ftemp = 's_'
      fn = os.path.join(path,
                        'arr_'+ftemp+self.direction+'_'+repr(i)+'.png')
      self.topimg.append(pygame.image.load(fn))
      self.topimg[i].set_colorkey(self.topimg[i].get_at((0,0)),RLEACCEL)

      self.image = self.topimg[0]
      self.rect = self.image.get_rect()
      self.rect.top = self.ypos
      if self.direction == 'l':        self.rect.left = 12
      if self.direction == 'd':        self.rect.left = 88
      if self.direction == 'u':        self.rect.left = 164
      if self.direction == 'r':        self.rect.left = 240

      self.rect.left += (320*self.playernum)

  def stepped(self, modifier, time):
    if modifier:    self.adder = 4
    else:           self.adder = 0
    self.presstime = time

  def update(self,time):
    if time > (self.presstime+0.2):        self.adder = 0

    self.keyf = int(time / (self.tick / 2)) % 8
    if self.keyf > 3:        self.keyf = 3
    self.frame = self.adder + self.keyf

    if self.frame != self.oldframe:
      self.image = self.topimg[self.frame]
      self.oldframe = self.frame

class ArrowFX(pygame.sprite.Sprite):
  def __init__ (self, bpm, direction, ypos, playernum, path):
    pygame.sprite.Sprite.__init__(self)        #call Sprite initializer
    self.presstime = -1000000
    self.tick = toRealTime(bpm, 1);
    self.centery = ypos + 32
    self.centerx = {'l':44, 'd':120, 'u':196, 'r':272}[direction]
    self.playernum = playernum
    
    fn = os.path.join(path, 'arr_n_' + direction + '_3.png')
    self.baseimg = pygame.image.load(fn).convert(16)
    self.tintimg = pygame.Surface(self.baseimg.get_size(), 0, 16)

    self.blackbox = pygame.surface.Surface((64,64))
    self.blackbox.set_colorkey(0)
    self.image = self.blackbox
    self.rect = self.image.get_rect()
    self.displaying = 1
    self.direction = 1
    self.holdtype = 0

    style = mainconfig['explodestyle']
    self.rotating, self.scaling = {3:(1,1), 2:(0,1), 1:(1,0), 0:(0,0)}[style]
    
  def holding(self, yesorno):
    self.holdtype = yesorno
  
  def stepped(self, time, tinttype):
    self.presstime = time
    self.tintimg = pygame.Surface(self.baseimg.get_size(), 0, 16)
    self.tintimg.blit(self.baseimg, (0,0))
    tinter = pygame.surface.Surface((64,64))
    if tinttype == 'MARVELOUS':
      tinter.fill((255,255,255))
    elif tinttype == 'PERFECT':
      tinter.fill((255,255,0))
    elif tinttype == 'GREAT':
      tinter.fill((0,255,0))
    tinter.set_alpha(127)
    self.tintimg.blit(tinter,(0,0))
    self.tintimg.set_colorkey(self.tintimg.get_at((0,0)))
    self.tintimg = self.tintimg.convert() #_alpha() #rotozoom wants _alpha 
    if self.direction == 1: self.direction = -1
    else: self.direction = 1

  def update(self, time, combo):
    steptimediff = time - self.presstime
    if (steptimediff < 0.2) or self.holdtype:
      self.displaying = 1
      self.image = self.tintimg
      if self.scaling:
        if self.holdtype:
          scale = 1.54
        else:
          scale = 1.0 + (steptimediff * 4.0) * (1.0+(combo/256.0))
        newsize = [int(x*scale) for x in self.image.get_size()]
        self.image = pygame.transform.scale(self.image, newsize)
      if self.rotating:
        angle = steptimediff * 230.0 * self.direction
        self.image = pygame.transform.rotate(self.image, angle)
      if self.holdtype == 0:
        tr = 224-int(1024.0*steptimediff)
      else:
        tr = 112
      self.image.set_alpha(tr)
            
    if self.displaying:
      if steptimediff > 0.2 and (self.holdtype == 0):
        self.image = self.blackbox
        self.displaying = 0
      self.rect = self.image.get_rect()
      self.rect.center = self.centerx, self.centery

      self.rect.left += (320*self.playernum)

class ScrollingArrow:
  def __init__ (self, path, dir, color, imgtype, left):
    self.dir = dir
    states = {}
    for state in ("c",):
      filename = os.path.join(path,
                              "_".join(("arr", state, dir, color))+"."+imgtype)
      states[state] = SimpleSprite(filename)
      states[state].rect.left = left
    # allow access by instance.n or instance.states['n']
    for n in states: self.__dict__[n] = states[n]

class BarSet:
  def __init__ (self, path, imgtype='png'):
    bars = {'red': None, 'org':None, 'yel':None, 'grn':None}
    for color in bars:
      fn = os.path.join(path, ''.join((color,"bar",'.',imgtype)))
      bars[color] = SimpleSprite(fn, zindex=BARSZINDEX)
    self.bars = bars
    for n in bars: self.__dict__[n] = bars[n]
