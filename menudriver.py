# Code to construct pydance's menus

import pygame
import menus
import os
import sys
import games
import ui
import pad
from constants import *
from announcer import Announcer
from gfxtheme import ThemeFile
from gameselect import MainWindow as GameSelect

class Credits(pygame.sprite.Sprite):
  def __init__(self, lines):
    pygame.sprite.Sprite.__init__(self)
    self._font = pygame.font.Font(None, 16)
    self._lines = lines
    self._idx = 0
    self._update = pygame.time.get_ticks() + 7000
    self._w = max([self._font.size(l)[0] for l in self._lines])
    self._h = max([self._font.size(l)[1] for l in self._lines])
    self.update()

  def update(self):
    t = pygame.time.get_ticks()
    self.image = pygame.Surface([self._w, self._h])
    self.image.fill([255, 255, 255])
    self.rect = self.image.get_rect()
    self.rect.bottomleft = [10, 479]
    if self._update - t > 2000:
      txt = self._font.render(self._lines[self._idx], True, [0, 0, 0])
      r = txt.get_rect()
      r.center = [self._w / 2, self._h / 2]
      self.image.blit(txt, r)
    elif t < self._update:
      p = (self._update - t) / 2000.0
      wy = int(self._h * p)
      idx1 = self._idx
      idx2 = (self._idx + 1) % len(self._lines)
      txt1 = self._font.render(self._lines[idx1], True, [0, 0, 0])
      txt2 = self._font.render(self._lines[idx2], True, [0, 0, 0])
      r1 = txt1.get_rect()
      r2 = txt2.get_rect()
      r2.centerx = r1.centerx = self._w / 2
      r2.top = wy
      r1.bottom = wy
      self.image.blit(txt1, r1)
      self.image.blit(txt2, r2)
    else:
      self._idx = (self._idx + 1) % len(self._lines)
      self._update = t + 4000
      txt = self._font.render(self._lines[self._idx], True, [0, 0, 0])
      r = txt.get_rect()
      r.center = [self._w / 2, self._h / 2]
      self.image.blit(txt, r)

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

def switch_tuple_back(name, l):
  l = l[:]
  l.reverse()
  return switch_tuple(name, l)

# Wrap an object constructor
def wrap_ctr(Obj, args):
  Obj(*args)
  return None, None

def do(screen, songdata):

  onoff_opt = { ui.START: switch_onoff, ui.CONFIRM: switch_onoff,
                menus.CREATE: get_onoff, ui.LEFT: off_onoff,
                ui.RIGHT: on_onoff }
  offon_opt = { ui.START: switch_offon, ui.START: switch_offon,
	menus.CREATE: get_offon, ui.LEFT: off_offon, ui.RIGHT: on_offon }
  rotate_opt = { ui.START: switch_rotate, ui.CONFIRM: switch_rotate,
                 ui.LEFT: switch_rotate_back,
                 ui.RIGHT: switch_rotate,
                 menus.CREATE: get_rotate }
  rotate_index_opt = { ui.START: switch_rotate_index,
                       ui.CONFIRM: switch_rotate_index,
                       ui.LEFT: switch_rotate_index_back,
                       ui.RIGHT: switch_rotate_index,
                       menus.CREATE: get_rotate_index }
  tuple_opt = { ui.START: switch_tuple, ui.CONFIRM: switch_tuple,
                ui.LEFT: switch_tuple_back,
                ui.RIGHT: switch_tuple,
                menus.CREATE: get_tuple }

  sprites = pygame.sprite.RenderUpdates()
  try:
    lines = file(os.path.join(pydance_path, "CREDITS")).read().split("\n")
    lines = [l.decode("utf-8") for l in lines]
    Credits(["pydance %s" % VERSION] + lines).add(sprites)
  except:
    Credits(["pydance %s" % VERSION,
             "http://icculus.org/pyddr",
             "By Joe Wreschnig & Brendan Becker",
             "(Your CREDITS file is missing.)",
             ]).add(sprites)

  m = (["Play Game", {ui.START: wrap_ctr, ui.CONFIRM: wrap_ctr},
	(GameSelect, songdata)],
       ["Map Keys", {ui.START: wrap_ctr, ui.CONFIRM: wrap_ctr},
        (pad.PadConfig, (screen,))],
       ("Game Options",
        ["Autofail", onoff_opt, ("autofail",)],
        ["Assist Mode", tuple_opt, ("assist",
                                    [(0, "Off"),
                                     (1, "Click"),
                                     (2, "Full")])],
        ["Announcer", rotate_opt, ('djtheme', Announcer.themes())],
        ("Themes ...",
         ["4 Panel", rotate_opt,
          ("4p-theme", ThemeFile.list_themes("SINGLE"))],
         ["3 Panel", rotate_opt,
          ("3p-theme", ThemeFile.list_themes("3PANEL"))],
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
         ["EZ2", rotate_opt,
          ("ez2-theme", ThemeFile.list_themes("EZ2SINGLE"))],
         ["EZ2 Real", rotate_opt,
          ("ez2real-theme", ThemeFile.list_themes("EZ2REAL"))],
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
        ["Save Input", onoff_opt, ('saveinput',)],
        ["Song Previews", onoff_opt, ('previewmusic',)],
        ["Folders", onoff_opt, ("folders",)],
        ["Timer Display", onoff_opt, ('fpsdisplay',)],
        ["Back", None, None]
        )
       )

  me = menus.Menu("Main Menu", m, screen, sprites)
  me.display()
