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
        arrows[dir+repr(cnum)] = Arrow(path, dir, str(color), imgtype, left)
    # allow access by instance.l or instance.arrows['l']
    for n in arrows: self.__dict__[n] = arrows[n] 
    self.arrows = arrows
  def __getitem__ (self,item):
    # allow access by instance['l']
    return getattr(self,item)

class Arrow:
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
