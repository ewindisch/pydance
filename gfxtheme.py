# GFXTheme and associated classes.
# These handle loading the various graphics themes for pydance.

import dircache, os, games

from constants import *
from util import toRealTime

class GFXTheme(object):
  def themes(cls):
    theme_list = []
    for path in search_paths:
      checkpath = os.path.join(path, "themes", "gfx")
      if os.path.isdir(checkpath):
        for name in dircache.listdir(checkpath):
          if os.path.isfile(os.path.join(checkpath, name, "is-theme")):
            theme_list.append(name)
    return theme_list

  themes = classmethod(themes)

  def __init__(self, name, pid, game):
    self.name = name
    self.game = game
    self.path = None
    self.pid = pid
    size = "%dx%d" % (game.width, game.width)
    for path in search_paths:
      if os.path.isdir(os.path.join(path, "themes", "gfx", name)):
        self.path = os.path.join(path, "themes", "gfx", name)
    if self.path == None:
      print "Error: Cannot load graphics theme '%s'." % name
      sys.exit(1)

    self.fullpath = os.path.join(self.path, size)

  def arrows(self, pid):
    return ArrowSet(self.fullpath, self.game, pid)

  def toparrows(self, bpm, ypos, pid):
    arrs = {}
    arrfx = {}
    for d in self.game.dirs:
      arrs[d] = TopArrow(bpm, d, ypos, pid, self.fullpath, self.game)
      arrfx[d] = ArrowFX(bpm, d, ypos, pid, self.fullpath, self.game)
    return arrs, arrfx

  def __repr__(self):
    return ('<GFXTheme name=%r>' % self.name)

class ArrowSet(object):
  def __init__ (self, path, game, pid):
    arrows = {}
    for dir in game.dirs:
      left = game.left_off(pid) + game.width * game.dirs.index(dir) + pid * game.player_offset
      for cnum in range(4):
        if cnum == 3: color = 1
        else: color = cnum
        arrows[dir+repr(cnum)] = ScrollingArrow(path, dir, str(color), left)
    # allow access by instance.l or instance.arrows['l']
    for n in arrows: self.__dict__[n] = arrows[n] 
    self.arrows = arrows
  def __getitem__ (self,item):
    # allow access by instance['l']
    return getattr(self,item)

class TopArrow(pygame.sprite.Sprite):

  def __init__ (self, bpm, direction, ypos, pid, path, game):
    pygame.sprite.Sprite.__init__(self)
    self.presstime = -1
    self.tick = toRealTime(bpm, 1);
    self.frame = 0
    self.oldframe = -1
    self.state = 'n'
    self.filepref = 'arr_'
    self.adder = 0
    self.direction = direction
    self.topimg = []
    self.ypos = ypos

    for i in range(8):
      if i < 4:        ftemp = 'n_'
      else:            ftemp = 's_'
      fn = os.path.join(path,
                        'arr_'+ftemp+self.direction+'_'+repr(i)+'.png')
      self.topimg.append(pygame.image.load(fn).convert())
      self.topimg[i].set_colorkey(self.topimg[i].get_at((0, 0)), RLEACCEL)

      self.image = self.topimg[0]
      self.rect = self.image.get_rect()
      self.rect.top = self.ypos
      self.rect.left = game.left_off(pid) + (game.dirs.index(direction) *
                                             game.width)
      self.rect.left += game.player_offset * pid

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
  def __init__ (self, bpm, direction, ypos, pid, path, game):
    pygame.sprite.Sprite.__init__(self)
    self.presstime = -1000000
    self.tick = toRealTime(bpm, 1);
    self.centery = ypos + game.width / 2
    self.centerx = (game.left_off(pid) +
                    game.dirs.index(direction) * game.width + game.width / 2)
    self.pid = pid
    
    fn = os.path.join(path, 'arr_n_' + direction + '_3.png')
    self.baseimg = pygame.image.load(fn).convert(16)
    self.tintimg = pygame.Surface(self.baseimg.get_size())

    self.blackbox = pygame.surface.Surface([game.width] * 2)
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
    tinter = pygame.surface.Surface(self.baseimg.get_size())
    if tinttype == 'MARVELOUS':
      tinter.fill((255,255,255))
    elif tinttype == 'PERFECT':
      tinter.fill((255,255,0))
    elif tinttype == 'GREAT':
      tinter.fill((0,255,0))
    tinter.set_alpha(127)
    self.tintimg.blit(tinter,(0,0))
    self.tintimg.set_colorkey(self.tintimg.get_at((0,0)))
    self.tintimg = self.tintimg.convert()
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
        newsize = [max(0, int(x*scale)) for x in self.image.get_size()]
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

      self.rect.left += (320 * self.pid)

class ScrollingArrow(object):
  def __init__ (self, path, dir, color, left):
    self.dir = dir
    self.left = left
    fn = "_".join(["arr", "c", dir, color]) + ".png"
    if not os.path.exists(os.path.join(path, fn)):
      fn = "_".join(["arr", "c", dir, "0"]) + ".png"
    self.image = pygame.image.load(os.path.join(path, fn)).convert()
    self.image.set_colorkey(self.image.get_at([0, 0]), RLEACCEL)
