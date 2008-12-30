# Define and precompute font themes.

import pygame
from ConfigParser import *
import os, dircache
from constants import *

# Find the appropriate font size to fit string into max_width pixels,
# that's at most max_size, and at least 6.
def max_size(font, string, max_width, max_size):
  for size in range(max_size, 0, -1):
    f = pygame.font.Font(font, size)
    if f.size(string)[0] < max_width: return f
  return pygame.font.Font(font, 6)

class FontTheme:
  _themes = {}
  _FIXED_SIZE=['help', 'songlist', 'loadingscreen',
               'menu', 'menusub1', 'menusub2','menutop','bannerdispbpm',
               'gamelist','gamedsc','optlist','optdsc','optsel','optseldsc',
               'crslist','crsdisp','crsdispsmall','errormessage',
               'lifebar','scoredisp','lyrics','fps','timedisp','padconfmsg',
               'padconfplr','padconfinput','padconfdirs',
               'judgingdisp','judgingholddisp',
               'songinfoscrctdn','songinfoscrplr','songinfoscropts',
               'gradescreen','gradescrcont',
'endlessplr','endlessselby','endlesssel','diffbox',
               'credits']
  _VAR_SIZE=['bannerdisptitle','bannerdispartist','bannerdispsubtitle',
             'sortmode','gameseltitle','gameselselected',
             'crsseltitle','crsselcrstitle','songinfoscrsel','songinfoscrnext']
  _SCALE_SIZE=['titleartist','combo']

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

    cls._current=title

    for purpose in cls._FIXED_SIZE:
      fontfn,fontsize=cls._themes[title].fonts[purpose]
      cls.__dict__[purpose]=pygame.font.Font(fontfn,fontsize)
    for purpose in cls._SCALE_SIZE:
      cls.__dict__[purpose] = cls._themes[title].fonts[purpose]
  set=classmethod(set)

  def font(cls, purpose, string='', max_width=None, size=None):
    if purpose in cls._FIXED_SIZE:
      return cls.__dict__[purpose]
    elif purpose in cls._VAR_SIZE:
      if max_width is not None:
        fontfn, maxsize = cls._themes[cls._current].fonts[purpose]
        return max_size(fontfn, string, max_width, maxsize)
      elif size is not None: 
        fontfn = cls._themes[cls._current].fonts[purpose][0]
        return pygame.font.Font(fontfn, size)
      else:
        return cls._themes[cls._current].fonts[purpose][0]
    elif purpose in cls._SCALE_SIZE:
      return cls._themes[cls._current].fonts[purpose]
    else: raise Exception("Requested font purpose not found.")
  font=classmethod(font)

  def __init__(self,path):
    fontconf = ConfigParser()
    fontconf.read(path)
    
    self.fonts = {}

    self.title = fontconf.get('global', 'title')

    if fontconf.has_option('global','font'): 
      defFont = os.path.join(os.path.dirname(path),fontconf.get('global','font'))
    else:
      defFont = None

    for purpose in FontTheme._FIXED_SIZE + FontTheme._VAR_SIZE + FontTheme._SCALE_SIZE:
      if fontconf.has_option(purpose,'font'):
        fontfn = os.path.join(os.path.dirname(path),fontconf.get(purpose,'font'))
      else:
        fontfn = defFont
      fontsize = fontconf.getint(purpose,'size')
      self.fonts[purpose]=(fontfn,fontsize)


FontTheme.load_themes()
FontTheme.set(mainconfig['fonttheme'])
