# Code to construct pyDDR's menus

import pygame, menus, os, sys

from constants import *
from announcer import Announcer
from gfxtheme import GFXTheme

# A simple on/off setting, 0 or 1
def get_onoff(name):
  if mainconfig[name]: return None, "on", None
  else: return None, "off", None

def switch_onoff(name):
  mainconfig[name] ^= 1
  return get_onoff(name)

# Rotate through a list of option strings
def get_rotate(name, list):
  return None, mainconfig[name], None

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
  return None, list[mainconfig[name]], None

def switch_rotate_index(name, list):
  mainconfig[name] = (mainconfig[name] + 1) % len(list)
  return get_rotate_index(name, list)

def switch_rotate_index_back(name, list):
  mainconfig[name] = (mainconfig[name] - 1) % len(list)
  return get_rotate_index(name, list)

# Lyric color switching, does fun things
def get_color_text(name, colors):
  val = mainconfig[name]
  for color in colors:
    if color[0] == val:
      return None, color[0], color[1]
  return None, "unknown", (255, 255, 255)

def switch_color_text(name, colors):
  is_next = False
  val = mainconfig[name]
  for color in colors:
    if color[0] == val:
      is_next = True
    elif is_next:
      mainconfig[name] = color[0]
      return None, color[0], color[1]
  mainconfig[name] = colors[0][0]
  return None, colors[0][0], colors[0][1]

# Write out the config file
def config_write(path):
  mainconfig.write(path)
  return None, None, None
  
def fullscreen_toggle(dummy):
  mainconfig["fullscreen"] ^= 1
  pygame.display.toggle_fullscreen()
  return None, None, None

def do(screen, songselect, songdata):

  onoff_opt = { E_START: switch_onoff, "initial": get_onoff }
  rotate_opt = { E_START: switch_rotate,
                 E_LEFT: switch_rotate_back,
                 E_RIGHT: switch_rotate,
                 "initial": get_rotate }
  rotate_index_opt = { E_START: switch_rotate_index,
                       E_LEFT: switch_rotate_index_back,
                       E_RIGHT: switch_rotate_index,
                       "initial": get_rotate_index }

  color_opt = { E_START: switch_color_text,
                E_LEFT: switch_color_text,
                E_RIGHT: switch_color_text,
                "initial": get_color_text }

  m = (["Play Game", {E_START: songselect}, songdata],
       ("Game Options",
        ["Autofail", onoff_opt, ("killsongonfail",)],
        ["Announcer", rotate_opt, ("djtheme", Announcer.themes())],
        ["Reverse", onoff_opt, ("reversescroll",)],
        ["Little", rotate_index_opt,
         ("little", ("show all", "no 16ths", "no 8ths",
                             "no 8ths or 16ths"))],
        ["Hidden", rotate_index_opt,
         ("hidden", ("off", "hide one","hide two","hide three"))],
        ["Sudden", rotate_index_opt,
         ("sudden", ("off", "hide one", "hide two", "hide three"))],
        ["Top Arrows", onoff_opt, ("showtoparrows",)],
        ["Scale Arrows", rotate_index_opt,
         ("arrowscale", ("shrink", "normal", "grow"))],
        ["Spin Arrows", onoff_opt, ("arrowspin",)],
        ["Back", None, None]
        ),
       ("Graphic Options",
        ["Fullscreen", {E_START: fullscreen_toggle}, (None,)],
        ["Graphics", rotate_opt, ('gfxtheme', GFXTheme.themes())],
        ["Exploding", rotate_index_opt,
         ('explodestyle', ('none', 'rotate', 'scale', 'rotate & scale'))],
        ["Backgrounds", onoff_opt, ('showbackground',)],
        ["Lyrics", onoff_opt, ("showlyrics",)],
        ["Main Lyrics", color_opt, ("lyriccolor", lyric_colors)],
        ["Other Lyrics", color_opt, ("transcolor", lyric_colors)],
        ["LPS Counter", onoff_opt, ('fpsdisplay',)],
        ["Back", None, None]
        ),
       ["Sort By", rotate_index_opt,
        ("sortmode", ["file", "song", "group", "bpm",
                              "difficulty", "mix"])],
       ["Save Changes", {E_START: config_write},
        ((os.path.join(rc_path, "pyddr.cfg")), )],
       # ^^^ FIXME Should that be a constant variable?
       ["Quit", None, None]
       )

  me = menus.Menu("Main Menu", m)
  me.display(screen)
