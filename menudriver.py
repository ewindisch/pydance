# Code to construct pydance's menus

import pygame, menus, os, sys, copy, colors, games

from constants import *
from announcer import Announcer
from gfxtheme import ThemeFile
from songselect import SongSelect
from endless import Endless

# A simple on/off setting, 1 or 0
def get_onoff(name):
  if mainconfig[name]: return None, "on"
  else: return None, "off"

def switch_onoff(name):
  mainconfig[name] ^= 1
  return get_onoff(name)

def on_onoff(name):
  mainconfig[name] = 1
  return get_onoff(name)

def off_onoff(name):
  mainconfig[name] = 0
  return get_onoff(name)

# A simple on/off setting, 0 or 1
def get_offon(name):
  if mainconfig[name]: return None, "off"
  else: return None, "on"

def switch_offon(name):
  mainconfig[name] ^= 1
  return get_offon(name)

def on_offon(name):
  mainconfig[name] = 0
  return get_offon(name)

def off_offon(name):
  mainconfig[name] = 1
  return get_offon(name)

# Rotate through a list of option strings
def get_rotate(name, list):
  return None, mainconfig[name]

def switch_rotate(name, list):
  try:
    new_i = (list.index(mainconfig[name]) + 1) % len(list)
    mainconfig[name] = list[new_i]
  except ValueError: mainconfig[name] = list[0]
  return get_rotate(name, list)

def switch_rotate_back(name, list):
  try:
    new_i = (list.index(mainconfig[name]) - 1) % len(list)
    mainconfig[name] = list[new_i]
  except ValueError: mainconfig[name] = list[-1]
  return get_rotate(name, list)

# Rotate through a list of option strings, but use the index as the value.
def get_rotate_index(name, list):
  return None, list[mainconfig[name]]

def switch_rotate_index(name, list):
  mainconfig[name] = (mainconfig[name] + 1) % len(list)
  return get_rotate_index(name, list)

def switch_rotate_index_back(name, list):
  mainconfig[name] = (mainconfig[name] - 1) % len(list)
  return get_rotate_index(name, list)

def fullscreen_toggle(dummy):
  mainconfig["fullscreen"] ^= 1
  pygame.display.toggle_fullscreen()
  return None, None

def get_tuple(name, list):
  for item in list:
    if item[0] == mainconfig[name]:
      return None, item[1]
  return None, "custom: " + str(mainconfig[name])

def switch_tuple(name, list):
  next = False
  orig = mainconfig[name]
  for item in list:
    if next:
      mainconfig[name] = item[0]
      next = False
      break
    elif item[0] == mainconfig[name]:
      next = True
  if next: mainconfig[name] = list[0][0]
  elif mainconfig[name] == orig: mainconfig[name] = list[0][0]  
  return get_tuple(name, list)

def switch_tuple_back(name, list):
  list = copy.copy(list)
  list.reverse()
  return switch_tuple(name, list)

# Wrap an object constructor
def wrap_ctr(Obj, args):
  Obj(*args)
  return None, None

def do(screen, songdata):

  onoff_opt = { E_START: switch_onoff, E_CREATE: get_onoff,
                 E_LEFT: off_onoff, E_RIGHT: on_onoff }
  offon_opt = { E_START: switch_offon, E_CREATE: get_offon,
                 E_LEFT: off_offon, E_RIGHT: on_offon }
  rotate_opt = { E_START: switch_rotate,
                 E_LEFT: switch_rotate_back,
                 E_RIGHT: switch_rotate,
                 E_CREATE: get_rotate }
  rotate_index_opt = { E_START: switch_rotate_index,
                       E_LEFT: switch_rotate_index_back,
                       E_RIGHT: switch_rotate_index,
                       E_CREATE: get_rotate_index }
  tuple_opt = { E_START: switch_tuple,
                E_LEFT: switch_tuple_back,
                E_RIGHT: switch_tuple,
                E_CREATE: get_tuple }

  # FIXME We need to present these in a logical order.
  # Ideally, we need to not have one preference for each game, but each
  # game type.
  themes = [[name.title(), rotate_opt, ("%s-theme" % name,
                                        ThemeFile.list_themes(name))] for
            name in games.GAMES]
  themes = tuple(themes) # Python sucks Python sucks Python sucks

  m = (("Play Game",
        ["Single", {E_START: wrap_ctr}, (SongSelect, songdata + ("SINGLE",))],
        ["Versus", {E_START: wrap_ctr}, (SongSelect, songdata + ("VERSUS",))],
        ["Couple", {E_START: wrap_ctr}, (SongSelect, songdata + ("COUPLE",))],
        ["Double", {E_START: wrap_ctr}, (SongSelect, songdata + ("DOUBLE",))],
        ["5 Panel", {E_START: wrap_ctr}, (SongSelect, songdata + ("5PANEL",))],
        ["5 Versus", {E_START: wrap_ctr}, (SongSelect, songdata + ("5VERSUS",))],
        ["5 Couple", {E_START: wrap_ctr}, (SongSelect, songdata + ("5COUPLE",))],
        ["5 Double", {E_START: wrap_ctr}, (SongSelect, songdata + ("5DOUBLE",))],
        ["6 Panel", {E_START: wrap_ctr}, (SongSelect, songdata + ("6PANEL",))],
        ["8 Panel", {E_START: wrap_ctr}, (SongSelect, songdata + ("8PANEL",))],
        ["Endless", {E_START: wrap_ctr}, (Endless, songdata + ("SINGLE",))],
        ["Back", None, None]
        ),
       ("Game Options",
        ["Autofail", onoff_opt, ("autofail",)],
        ["Assist Mode", onoff_opt, ("assist",)],
        ["Announcer", rotate_opt, ('djtheme', Announcer.themes())],
        ("Themes ...",) +  themes,
        ["Back", None, None]
        ),
       ("Graphic Options",
        ["Arrow Effects", rotate_index_opt,
         ('explodestyle', ('none', 'rotate', 'scale', 'rotate & scale'))],
        ["Backgrounds", onoff_opt, ('showbackground',)],
        ["Brightness", tuple_opt, ('bgbrightness',
                                   [(32, 'very dark'),
                                    (64, 'dark'),
                                    (127, 'normal'),
                                    (192, 'bright'),
                                    (255, 'very bright')])],
        ["Lyrics", onoff_opt, ("showlyrics",)],
        ["Lyrics Color", rotate_opt, ("lyriccolor",
                                     ["pink/purple", "purple/cyan",
                                      "cyan/aqua", "aqua/yellow",
                                      "yellow/pink"])],
        ["Back", None, None]
        ),
       ("Interface Options",
        ["Song Previews", onoff_opt, ('previewmusic',)],
        ["Folders", onoff_opt, ("folders",)],
        ["Timer Display", onoff_opt, ('fpsdisplay',)],
        ["Gratuitous Extras", onoff_opt, ('gratuitous',)],
        ["Display Help", onoff_opt, ("ingamehelp",)],
        ["Back", None, None]
        )
       )

  me = menus.Menu("Main Menu", m, screen)
  me.display()
