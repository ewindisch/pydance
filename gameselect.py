# Select the number of panels, game mode, and song selector.

from constants import *
from songselect import SongSelect
from endless import Endless

from pad import pad

import colors
import games

SELECTORS = {
  "Normal": SongSelect,
  "Endless": Endless,
  }

# We can probably autogenerate this list somehow.
# Maybe should also be in games?
MODES = {
  ("4P", "SINGLE"): "SINGLE",
  ("4P", "VERSUS"): "VERSUS",
  ("4P", "COUPLE"): "COUPLE",
  ("4P", "DOUBLE"): "DOUBLE",

  ("5P", "SINGLE"): "5PANEL",
  ("5P", "VERSUS"): "5VERSUS",
  ("5P", "COUPLE"): "5COUPLE",
  ("5P", "DOUBLE"): "5DOUBLE",

  ("6P", "SINGLE"): "6PANEL",
  ("6P", "VERSUS"): "6VERSUS",
  ("6P", "COUPLE"): "6COUPLE",
  ("6P", "DOUBLE"): "6DOUBLE",

  ("8P", "SINGLE"): "8PANEL",
  ("8P", "VERSUS"): "8VERSUS",
  ("8P", "COUPLE"): "8COUPLE",
  ("8P", "DOUBLE"): "8DOUBLE",

  ("9P", "SINGLE"): "9PANEL",
  ("9P", "VERSUS"): "9VERSUS",
  ("9P", "COUPLE"): "9COUPLE",
  ("9P", "DOUBLE"): "9DOUBLE",

  ("PARA", "SINGLE"): "PARAPARA",
  ("PARA", "VERSUS"): "PARAVERSUS",
  ("PARA", "COUPLE"): "PARACOUPLE",
  ("PARA", "DOUBLE"): "PARADOUBLE",

  ("DMX", "SINGLE"): "DMX",
  ("DMX", "VERSUS"): "DMXVERSUS",
  ("DMX", "COUPLE"): "DMXCOUPLE",
  ("DMX", "DOUBLE"): "DMXDOUBLE",
  }

# Descriptions to output on the screen for each mode.
DESCRIPTIONS = {
  "4P": "The standard up, down, left, and right arrows.",
  "5P": "Diagonals and the center.",
  "6P": "4 panel with a twist.",
  "8P": "Dance around the whole pad.",
  "9P": "Every button is used.",
  "PARA": "Wave your arms (or feet) around.",
  "DMX": "Crazy kung-fu action.",

  "SINGLE": "Play by yourself.",
  "VERSUS": "Challenge an opponent to the same steps.",
  "COUPLE": "Two people dance complementary steps.",
  "DOUBLE": "Try playing on both sides at once.",

  "Normal": "One song at a time, or set up a playlist.",
  "Endless": "Keep dancing until you fail."

  }

class GameSelect(object):
  def __init__(self, songitems, screen):
    self.screen = screen

    # Store previously selected images, to blit for each choice.
    self.images = [None, None, None]

    # FIXME: This can be changed to something more attractive later.
    self.bg = pygame.image.load(os.path.join(image_path, "bg.png"))

    # FIXME: We really need to do pretty animations and stuff.

    # Track our current state so Esc takes us back to the previous choice,
    # and not the menu.
    states = [self.select_mode, self.select_submode, self.select_selector]
    self.values = [None, None, None]
    state = 0

    while state != -1: # Esc pressed from first choice, return to menu
      val = states[state]()
      self.values[state] = val

      if val is None: state -= 1
      else: state += 1

      if state == len(states): # All choices done, start the game
        SELECTORS[self.values[2]](songitems, screen,
                                  MODES.get((self.values[0], self.values[1])))

        # After playing, reset to the first choice.
        # FIXME: Is going to the menu a better idea? Do more people exit the
        # SS to change options, or to play a different game type?

        self.values = [None, None, None]
        self.images = [None, None, None]
        state = 0

  def select_mode(self):
    return self.select_general(0, ["4P", "5P", "6P", "8P", "9P",
                                   "PARA", "DMX"])

  def select_submode(self):
    return self.select_general(1, ["SINGLE", "VERSUS", "COUPLE", "DOUBLE"])

  def select_selector(self):
    return self.select_general(2, ["Normal", "Endless"])

  # idx is the index in self.images to modify with this choice.
  def select_general(self, idx, choices):
    clock = pygame.time.Clock()
    images = {}

    for i in choices:
      images[i] = pygame.image.load(os.path.join(image_path,
                                                 "select-%s.png" % i.lower()))
      images[i].convert()

    if self.values[idx] != None: index = choices.index(self.values[idx])
    else: index = 0

    ev = pad.PASS
    while ev != pad.QUIT:

      # FIXME: If the player ID is > 0, limit the available game types
      # to 2 player modes.
      pid, ev = pad.poll()

      if ev == pad.LEFT: index -= 1
      elif ev == pad.RIGHT: index += 1
      elif ev == pad.START:
        return choices[index]

      elif ev == pad.FULLSCREEN:
        mainconfig["fullscreen"] ^= 1
        pygame.display.toggle_fullscreen()

      index %= len(choices)
      self.images[idx] = images[choices[index]]

      # Update the screen
      self.screen.blit(self.bg, [0, 0])

      for i in range(len(self.images)):
        if self.images[i] is not None:
          r = self.images[i].get_rect()
          r.center = [int(640.0 / (len(self.images) + 1) * (i + 1)), 240]
          self.screen.blit(self.images[i], r)

      text = FONTS[28].render(DESCRIPTIONS[choices[index]], 1, colors.BLACK)
      r = text.get_rect()
      r.center = [320, 420]
      self.screen.blit(text, r)

      pygame.display.update()
      clock.tick(10)

    self.images[idx] = None
    return None
