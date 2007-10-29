# Define and precompute font themes.

import pygame
from ConfigParser import *
import os, dircache
from constants import *

class FontTheme:
  _themes = {}
  _FONT_PURPOSES=['help', 'songlist', 'loadingscreen',
                  'menu', 'menusub1', 'menusub2']

  def load_themes(cls):
    for path in search_paths:
      fontdir = os.path.join(path, 'themes', 'font')
      if os.path.exists(fontdir) and os.path.isdir(fontdir):
        for fontcfg in dircache.listdir(fontdir):
          if fontcfg.endswith('.cfg'):
            theme=FontTheme(os.path.join(fontdir,fontcfg))
            cls._themes[theme.title]=theme
  load_themes=classmethod(load_themes)

  def themes(cls):
    if cls._themes=={}: cls.load_themes()
    return cls._themes.keys()
  themes=classmethod(themes)

  def set(cls,title):
    if cls._themes=={}: cls.load_themes()
    for purpose in cls._FONT_PURPOSES:
      fontfn,fontsize=cls._themes[title].fonts[purpose]
      cls.__dict__[purpose]=pygame.font.Font(fontfn,fontsize)
  set=classmethod(set)

  def __init__(self,path):
    fontconf = ConfigParser()
    fontconf.read(path)
    
    self.fonts = {}

    self.title = fontconf.get('global', 'title')

    if fontconf.has_option('global','font'): 
      defFont = os.path.join(os.path.dirname(path),fontconf.get('global','font'))
    else:
      defFont = None

    for purpose in FontTheme._FONT_PURPOSES:
      if fontconf.has_option(purpose,'font'):
        fontfn = os.path.join(os.path.dirname(path),fontconf.get(purpose,'font'))
      else:
        fontfn = defFont
      fontsize = fontconf.getint(purpose,'size')
      self.fonts[purpose]=(fontfn,fontsize)


FontTheme.load_themes()
FontTheme.set(mainconfig['fonttheme'])
