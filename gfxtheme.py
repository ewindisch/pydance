# GFXTheme and associated classes.
# These handle loading the various graphics themes for pyDDR.

import dircache

from constants import *
from spritelib import *

class GFXTheme:
  def themes(cls):
    theme_list = []
    for path in search_paths:
      checkpath = os.path.join(path, "themes", "gfx")
      if os.path.isdir(checkpath):
        for name in dircache.listdir(checkpath):
          if os.path.isfile(os.path.join(checkpath, name, "arr_c_d_0.png")):
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
    self.xanim = Xanim(self.path)

  def __repr__(self):
    return ('<GFXTheme name=%r>' % self.name)

class ArrowSet: 
  def __init__ (self, path, prefix='arr', imgtype='png', separator='_'):
    # left, up, right, down
    arrows = {'l': 12, 'd': 12+76, 'u': 12+2*76, 'r': 12+3*76}
    for dir,left in arrows.items():
      for cnum in range(4):
        if cnum == 3:
          casdf = 1
        else:
          casdf = cnum
        arrows[dir+repr(cnum)] = Arrow(self,dir,path,prefix,imgtype,separator,left,casdf)
    # allow access by instance.l or instance.arrows['l']
    for n in arrows.keys(): self.__dict__[n] = arrows[n] 
    self.arrows = arrows
  def __getitem__ (self,item):
    # allow access by instance['l']
    return getattr(self,item)

class Arrow:
  def __init__ (self, parent, dir, path, prefix, imgtype, separator,left=0,color=0):
      # reference to ArrowSet
      self.parent=parent
      # direction (short) i.e. 'l'
      self.dir = dir
      # normal, pulse, stepped on, pulse & stepped on, colored, offbeat colored
      states = {'c':None} #, 'p':None, 's':None, 'b':None, 'n':None, 'o':None}
      for state in states.keys():
        fn = os.path.join(path, separator.join([prefix,state,dir,repr(color)]) + '.' + imgtype)
        states[state] = SimpleSprite(fn)
        states[state].rect.left = left
      # allow access by instance.n or instance.states['n']
      for n in states.keys(): self.__dict__[n] = states[n]

class BarSet:
  def __init__ (self, path, suffix='bar', imgtype='png'):
    bars = {'red':None, 'org':None, 'yel':None, 'grn':None}
    for color in bars.keys():
      fn = os.path.join(path, ''.join([color,suffix,'.',imgtype]))
      bars[color] = SimpleSprite(fn,zindex=BARSZINDEX)
    self.bars = bars
    for n in bars.keys(): self.__dict__[n] = bars[n]

class Xanim(SimpleAnim):
  def __init__ (self, path, prefix='x_out', separator='-', imgtype='png', frameNumbers=None, files=None):
    SimpleAnim.__init__(self,path,prefix,separator,imgtype,frameNumbers,files,zindex=XANIMZINDEX)

