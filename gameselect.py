# Select the number of panels, game mode, and song selector.

from constants import *
from songselect import SongSelect
from endless import Endless

import games

SELECTORS = {
  "Normal": SongSelect,
  "Endless": Endless,
  }

DESCRIPTIONS = {
  "4P": "The standard up, down, left, and right arrows.",
  "5P": "Diagonals and the center.",
  "6P": "4 panel with a twist.",
  "8P": "Dance around the whole pad.",
  "SINGLE": "Play by yourself.",
  "VERSUS": "Challenge an opponent to the same steps.",
  "Normal": "One song at a time, or set up a playlist.",
  "Endless": "Keep dancing until you fail."
  }

for mode in games.COUPLE:
  DESCRIPTIONS[mode] = "Two people dance complementary steps."

for mode in games.DOUBLE:
  DESCRIPTIONS[mode] = "Try dancing on both pads at once."

class GameSelect(object):
  def __init__(self, songitems, screen):
    self.screen = screen

    # FIXME: This can be changed to something more attractive later.
    self.bg = pygame.image.load(os.path.join(image_path, "bg.png"))

    # FIXME: We really need to do pretty animations and stuff.

    mode = self.select_mode()
    if mode is None: return
    submode = self.select_submode(mode)
    if submode is None: return
    selector = self.select_selector()
    if selector is None: return
    
    SELECTORS[selector](songitems, screen, submode)

  def select_mode(self):
    return self.select_general(["4P", "5P", "6P", "8P"])

  def select_submode(self, mode):
    return self.select_general({
      "4P": ["SINGLE", "VERSUS", "COUPLE", "DOUBLE"],
      "5P": ["5PANEL", "5VERSUS", "5COUPLE", "5DOUBLE"],
      "6P": ["6PANEL"],
      "8P": ["8PANEL"],
      }[mode])

  def select_selector(self):
    return self.select_general(["Normal", "Endless"])

  def select_general(self, choices):
    clock = pygame.time.Clock()
    images = {}

    for i in choices:
      images[i] = pygame.image.load(os.path.join(image_path,
                                                 "select-%s.png" % i.lower()))
      images[i].convert()

    index = 0

    ev = E_PASS
    while ev != E_QUIT:
      pid, ev = event.poll()

      if ev == E_LEFT: index -= 1
      elif ev == E_RIGHT: index += 1
      elif ev == E_START:
        return choices[index]

      index %= len(choices)

      self.screen.blit(self.bg, [0, 0])
      r = images[choices[index]].get_rect()
      r.center = [320, 240]
      self.screen.blit(images[choices[index]], r)
      pygame.display.update()
      clock.tick(10)

    return None
