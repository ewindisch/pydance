# FIXME: This file needs documentation.

from constants import *
from interface import *
from pygame.font import Font

import ui
import endless, courseselect, songselect

GS_HELP = [
  "Up / Down: Change game, mode, or interface",
  "Enter / Up Right: Advance your choice",
  "Escape / Up Left: Back up or exit",
  "F11: Toggles fullscreen",
  "Enjoy pydance 0.8.3!",
  ]

GAMES = ["4 panel", "5 panel", "6 panel", "8 panel", "9 panel",
         "Parapara", "DMX", "EZ2", "EZ2 Real", "3 panel"]
TYPES = ["Single", "Versus", "Double", "Couple"]
SS = ["Normal", "Nonstop", "Endless"]

VALUES = [GAMES, TYPES, SS]

def make_versus(oldimage):
  surf = pygame.Surface([350, 300], SRCALPHA, 32)
  surf.fill([0, 0, 0, 0])
  newimage = pygame.transform.rotozoom(oldimage, 0, 0.714286)
  surf.blit(newimage, [0, 0])
  surf.blit(newimage, [100, 100])
  return surf

def make_double(oldimage):
  surf = pygame.Surface([350, 300], SRCALPHA, 32)
  surf.fill([0, 0, 0, 0])
  newimage = pygame.transform.rotozoom(oldimage, 0, 0.5)
  surf.blit(newimage, [0, 80])
  surf.blit(newimage, [175, 80])
  return surf

def make_couple(oldimage):
  surf = pygame.Surface([350, 300], SRCALPHA, 32)
  surf.fill([0, 0, 0, 0])
  image1 = pygame.transform.rotozoom(oldimage, -30, 0.714286)
  image2 = pygame.transform.rotozoom(oldimage, 30, 0.714286)
  surf.blit(image1, [-30, -40])
  surf.blit(image2, [60, 20])
  return surf

IMAGES = {
    "3 panel": "select-3p.png",
    "4 panel": "select-4p.png",
    "5 panel": "select-5p.png",
    "6 panel": "select-6p.png",
    "8 panel": "select-8p.png",
    "9 panel": "select-9p.png",
    "Parapara": "select-para.png",
    "EZ2 Real": "select-ez2real.png",
    "EZ2": "select-ez2.png",
    "DMX": "select-dmx.png",
    "Single": (lambda x: x),
    "Versus": make_versus,
    "Double": make_double,
    "Couple": make_couple,
    "Endless": "select-endless.png",
    }

SELECTORS = {
  "Endless": endless.Endless,
  "Nonstop": courseselect.CourseSelector,
  "Normal": songselect.SongSelect,
  }

MODES = {
  ("4 panel", "Single"): "SINGLE",
  ("4 panel", "Versus"): "VERSUS",
  ("4 panel", "Couple"): "COUPLE",
  ("4 panel", "Double"): "DOUBLE",

  ("3 panel", "Single"): "3PANEL",
  ("3 panel", "Versus"): "3VERSUS",
  ("3 panel", "Couple"): "3COUPLE",
  ("3 panel", "Double"): "3DOUBLE",

  ("5 panel", "Single"): "5PANEL",
  ("5 panel", "Versus"): "5VERSUS",
  ("5 panel", "Couple"): "5COUPLE",
  ("5 panel", "Double"): "5DOUBLE",

  ("6 panel", "Single"): "6PANEL",
  ("6 panel", "Versus"): "6VERSUS",
  ("6 panel", "Couple"): "6COUPLE",
  ("6 panel", "Double"): "6DOUBLE",

  ("8 panel", "Single"): "8PANEL",
  ("8 panel", "Versus"): "8VERSUS",
  ("8 panel", "Couple"): "8COUPLE",
  ("8 panel", "Double"): "8DOUBLE",

  ("9 panel", "Single"): "9PANEL",
  ("9 panel", "Versus"): "9VERSUS",
  ("9 panel", "Couple"): "9COUPLE",
  ("9 panel", "Double"): "9DOUBLE",

  ("Parapara", "Single"): "PARAPARA",
  ("Parapara", "Versus"): "PARAVERSUS",
  ("Parapara", "Couple"): "PARACOUPLE",
  ("Parapara", "Double"): "PARADOUBLE",

  ("DMX", "Single"): "DMX",
  ("DMX", "Versus"): "DMXVERSUS",
  ("DMX", "Couple"): "DMXCOUPLE",
  ("DMX", "Double"): "DMXDOUBLE",

  ("EZ2", "Single"): "EZ2SINGLE",
  ("EZ2", "Versus"): "EZ2VERSUS",
  ("EZ2", "Couple"): "EZ2COUPLE",
  ("EZ2", "Double"): "EZ2DOUBLE",

  ("EZ2 Real", "Single"): "EZ2REAL",
  ("EZ2 Real", "Versus"): "REALVERSUS",
  ("EZ2 Real", "Couple"): "REALCOUPLE",
  ("EZ2 Real", "Double"): "REALDOUBLE",
}

DESCRIPTIONS = {
  "4 panel": "The standard up, down, left and right arrows (like Dance Dance Revolution)",
  "3 panel": "Practice using up left and up right with easier steps.",
  "5 panel": "Diagonal arrows and the center (like Pump It Up)",
  "6 panel": "Four panel plus the upper diagonal arrows (like DDR Solo)",
  "8 panel": "Everything but the center (like Technomotion)",
  "9 panel": "Everything! (like Pop'n'Stage)",
  "Parapara": "Wave your arms (or feet) around",
  "DMX": "Crazy kung-fu action (like Dance ManiaX / Freaks). Use left, up left, up right, and right.",

  "EZ2": "Three panels, two sensors, using left and right.",
  "EZ2 Real": "Three panels and four sensors.",

  "Single": "Play by yourself.",
  "Versus": "Challenge an opponent to the same steps.",
  "Couple": "Two people dance different steps to the same song.",
  "Double": "Try playing on both sides at once.",

  "Normal": "Play one song at a time.",
  "Endless": "Keep dancing until you fail.",
  "Nonstop": "Play several songs in a row.",
  }

class MainWindow(InterfaceWindow):
  def __init__(self, songs, courses, screen):
    InterfaceWindow.__init__(self, screen, "gameselect-bg.png")
    self._songs = songs
    self._courses = courses
    self._indicator_y = [152, 322, 414]
    self._message = ["Select a Game", "Select a Mode", "Select Type"]
    if len(courses) == 0 and "Nonstop" in SS: SS.remove("Nonstop")

    font = Font(None, 26)
    self._lists = [ListBox(font, [255, 255, 255], 26, 9, 220, [408, 53]),
                   ListBox(font, [255, 255, 255], 26, 3, 220, [408, 300]),
                   ListBox(font, [255, 255, 255], 26, 3, 220, [408, 393])]
    self._lists[0].set_items(GAMES)
    self._lists[1].set_items(TYPES)
    self._lists[2].set_items(SS)

    self._title = TextDisplay(24, [210, 28], [414, 26])
    self._selected = TextDisplay(48, [400, 28], [15, 380])
    self._description = WrapTextDisplay(30, 360, [25, 396])
    self._title.set_text(self._message[0])
    self._selected.set_text("4 panel")
    self._description.set_text(DESCRIPTIONS["4 panel"])
    self._sprites.add([self._title, self._selected, self._description])
    self._indicator = ActiveIndicator([405, 152], width = 230)
    self._sprites.add(self._indicator)
    self._sprites.add(HelpText(GS_HELP, [255, 255, 255], [0, 0, 0],
                               Font(None, 22), [206, 20]))
    self._sprites.add(self._lists)
    self._image = FlipImageDisplay(IMAGES.get("4 panel"), [200, 200])
    self._sprites.add(self._image)

    self._screen.blit(self._bg, [0, 0])
    self._sprites.update(pygame.time.get_ticks())
    self._sprites.draw(self._screen)
    pygame.display.update()

    self.loop()

  def loop(self):
    active = 0
    indices = [0, 0, 0]
    pid, ev = ui.ui.poll()
    
    while not (ev == ui.CANCEL and active == 0):

      if ev == ui.UP: indices[active] -= 1
      elif ev == ui.DOWN: indices[active] += 1

      elif ev == ui.FULLSCREEN:
        mainconfig["fullscreen"] ^= 1
        pygame.display.toggle_fullscreen()

      elif ev == ui.CANCEL:
        active -= 1
      elif ev in [ui.CONFIRM, ui.START]:
        if active == 2:
          SELECTORS[SS[indices[2]]](self._songs, self._courses, self._screen,
                                    MODES.get((VALUES[0][indices[0]],
                                               VALUES[1][indices[1]])))
          active = 0
          self._screen.blit(self._bg, [0, 0])
          pygame.display.update()
        else:
          active += 1

          if active == 1: self._oldimage = self._image._image # FIXME

      indices[active] %= len(VALUES[active])

      if ev in [ui.UP, ui.DOWN]:
        if ev == ui.UP: self._lists[active].set_index(indices[active], -1)
        else: self._lists[active].set_index(indices[active], 1)
        text = VALUES[active][indices[active]]
        self._selected.set_text(text)
        self._description.set_text(DESCRIPTIONS[text])
        img = IMAGES.get(text)
        if callable(img): self._image.set_image(img(self._oldimage))
        else: self._image.set_image(IMAGES.get(text))

      if ev in [ui.CONFIRM, ui.START, ui.CANCEL]:
        self._indicator.move([405, self._indicator_y[active]])
        self._title.set_text(self._message[active])
        text = VALUES[active][indices[active]]
        self._selected.set_text(text)
        self._description.set_text(DESCRIPTIONS[text])
        img = IMAGES.get(text)
        if callable(img): self._image.set_image(img(self._oldimage))
        else: self._image.set_image(IMAGES.get(text))

      self.update()
      pid, ev = ui.ui.poll()
