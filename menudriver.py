# Code to construct pyDDR's menus

import pygame, menus, os, sys

from constants import *

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
  if list.index(mainconfig[name]):
    new_i = list.index(mainconfig[name]) + 1 % len(list)
    mainconfig[name] = list[new_i]
  else: mainconfig[name] = list[0]
  return get_rotate(name, list)

def switch_rotate_back(name, list):
  if list.index(mainconfig[name]):
    new_i = list.index(mainconfig[name]) - 1 % len(list)
    mainconfig[name] = list[new_i]
  else: mainconfig[name] = list[-1]
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

# Write out the config file
def config_write(path):
  mainconfig.write(path)
  return None, None, None
  
def fullscreen_toggle(dummy):
  mainconfig["fullscreen"] ^= 1
  # FIXME Actually change screen size somehow
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
  
  m = (["Play Game", {E_START: songselect}, songdata],
       ("Game Options",
        ["Autofail", onoff_opt, ("killsongonfail",)],
        ["Reverse", onoff_opt, ("reversescroll",)],
        ["Little", rotate_index_opt,
         ("little", ["show all", "no 16ths", "no 8ths",
                             "no 8ths or 16ths"])],
        ["Hidden", rotate_index_opt,
         ("hidden", ["off", "hide one","hide two","hide three"])],
        ["Sudden", rotate_index_opt,
         ("sudden", ["off", "hide one", "hide two", "hide three"])],
        ["Top Arrows", onoff_opt, ("toparrows",)],
        ["Scale Arrows", rotate_index_opt,
         ("arrowscale", ["shrink", "none", "grow"])],
        ["Spin Arrows", onoff_opt, ("arrowspin",)],
        ["Back", None, None]
        ),
       ("Graphic Options",
        ["Fullscreen", {E_START: fullscreen_toggle}, (None,)],
        
        ),
       ["Sort By", rotate_index_opt,
        ("sortmode", ["file", "song", "group", "bpm",
                              "difficulty", "mix"])],
       ["Save Changes", {E_START: config_write},
        ((os.path.join(rscdir, "pyddr.cfg")), )],
       # ^^^ FIXME Should that be a constant variable?
       ["Quit", None, None]
       )

  me = menus.Menu("Main Menu", m)
  me.display(screen)
