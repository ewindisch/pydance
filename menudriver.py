# Code to construct pydance's menus

import pygame, menus, os, sys, copy, colors, games, ui, pad
from constants import *
from announcer import Announcer
from gfxtheme import ThemeFile
from gameselect import GameSelect

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

  onoff_opt = { ui.START: switch_onoff, menus.CREATE: get_onoff,
                 ui.LEFT: off_onoff, ui.RIGHT: on_onoff }
  offon_opt = { ui.START: switch_offon, menus.CREATE: get_offon,
                 ui.LEFT: off_offon, ui.RIGHT: on_offon }
  rotate_opt = { ui.START: switch_rotate,
                 ui.LEFT: switch_rotate_back,
                 ui.RIGHT: switch_rotate,
                 menus.CREATE: get_rotate }
  rotate_index_opt = { ui.START: switch_rotate_index,
                       ui.LEFT: switch_rotate_index_back,
                       ui.RIGHT: switch_rotate_index,
                       menus.CREATE: get_rotate_index }
  tuple_opt = { ui.START: switch_tuple,
                ui.LEFT: switch_tuple_back,
                ui.RIGHT: switch_tuple,
                menus.CREATE: get_tuple }


  m = (["Play Game", {ui.START: wrap_ctr}, (GameSelect, songdata)],
       ("Game Options",
        ["Autofail", onoff_opt, ("autofail",)],
        ["Assist Mode", onoff_opt, ("assist",)],
        ["Announcer", rotate_opt, ('djtheme', Announcer.themes())],
        ("Themes ...",
         ["4 Panel", rotate_opt,
          ("4p-theme", ThemeFile.list_themes("SINGLE"))],
         ["5 Panel", rotate_opt,
          ("5p-theme", ThemeFile.list_themes("5PANEL"))],
         ["Large 6 Panel", rotate_opt,
          ("6pl-theme", ThemeFile.list_themes("6PANEL"))],
         ["Small 6 Panel", rotate_opt,
          ("6ps-theme", ThemeFile.list_themes("6VERSUS"))],
         ["Large 8 Panel", rotate_opt,
          ("8pl-theme", ThemeFile.list_themes("8PANEL"))],
         ["Small 8 Panel", rotate_opt,
          ("8ps-theme", ThemeFile.list_themes("8VERSUS"))],
         ["Large 9 Panel", rotate_opt,
          ("9pl-theme", ThemeFile.list_themes("9PANEL"))],
         ["Small 9 Panel", rotate_opt,
          ("9ps-theme", ThemeFile.list_themes("9VERSUS"))],
         ["Parapara", rotate_opt,
          ("para-theme", ThemeFile.list_themes("PARAPARA"))],
         ["DMX", rotate_opt,
          ("dmx-theme", ThemeFile.list_themes("DMX"))],
         ["Back", None, None]
         ),
        ["Back", None, None]
        ),
       ("Graphic Options",
        ["Animation", onoff_opt, ('animation',)],
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
        ["Map Keys", {ui.START: wrap_ctr}, (pad.PadConfig, (screen,))],
        ["Save Input", onoff_opt, ('saveinput',)],
        ["Song Previews", onoff_opt, ('previewmusic',)],
        ["Folders", onoff_opt, ("folders",)],
        ["Timer Display", onoff_opt, ('fpsdisplay',)],
        ["Back", None, None]
        )
       )

  me = menus.Menu("Main Menu", m, screen)
  me.display()
