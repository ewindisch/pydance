# ceci n'est e'galement pas un e'cran d'option

import os
import pygame
import fontfx
import colors
import ui

from constants import *
from interface import *

ON_OFF = [(0, "Off", ""), (1, "On", "")]

OPTIONS = {
  # Option specifier list:
  # 0. a boolean indicating whether the option is per-player (True) or not.
  # 1. The name of the option.
  # 2. A description of the option.
  # 3. A list of 3-tuples (a, b, c) where a is the value of the option.
  #    b is the string to display for that value, and c is a string
  #    describing the value.
  "speed": (True, "Speed",
            "Adjust the speed at which the arrows scroll across the screen.",
            zip([0.25, 0.33, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5, 8],
                ["0.25x", "0.33x", "0.50x", "0.75x", "1.0x", "1.5x", "2.0x",
                 "3.0x", "4.0x", "5.0x", "8.0x"],
                [""] * 11)
            ),
  "transform": (True, "Transform",
                "Change the step patterns for the song.",
                zip([0, 1, 2, 3, -1, -2],
                    ["Normal", "Mirror", "Left", "Right", "Shuffle", "Random"],
                    ["", "Rotate the steps 180 degrees.",
                     "Rotate the steps 90 degrees to the left."
                     "Rotate the steps 90 degrees to the right."
                     "Swap all arrows from one direction to another."
                     "Use totally random directions."])
                ),
  "size": (True, "Add/Remove Steps",
           "Add or remove arrows from step patterns.",
           zip([1, 2, 0, 3, 4, 5],
               ["Tiny", "Little", "Normal", "Big", "Quick", "Skippy"],
               ["Only dance to on-beat notes.",
                "Only dance to on-beat and half-beat notes.",
                "", "Add half-beat steps between on-beat ones.",
                "Add steps between half-beat ones.",
                "Add gallops between on-beat steps."])
           ),
  "fade": (True, "Fade",
           "Fade arrows in or out while they scroll.",
           zip([0, 1, 2, 3, 4, 5],
               ["Normal", "Sudden", "Hidden", "Peek", "Cycle", "Stealth"],
               ["", "Only display arrows near the top.",
                "Only display arrows near the bottom.",
                "Only display arrows near the middle.",
                "Blink arrows in and out.",
                "No arrows are displayed."])
           ),
  "accel": (True, "Acceleration",
            "Accelerate or decelerate arrows.",
            zip([2, 0, 1],
                ["Brake", "Normal", "Boost"],
                ["Decelerate near the top", "", "Accelerate near the top."])
            ),
  "scale": (True, "Size",
            "Change arrow sizes.",
            zip([0, 1, 2],
                ["Shrink", "Normal", "Grow"],
                ["Smaller arrows near the top.", "",
                 "Smaller arrows near the bottom."])
            ),
  "scrollstyle": (True, "Direction",
                  "Change the direction arrows scroll.",
                  zip([0, 1, 2],
                      ["Normal", "Reverse", "Center"],
                      ["Arrows go from bottom to top.",
                       "Arrows go from top to bottom."
                       "Arrows go from the top and bottom to the center."])
                  ),
  "jumps": (True, "Jumps",
            "Turn jumps off, or add more.",
            zip([0, 1, 2],
                ["Off", "On", "Wide"],
                ["Remove jumps from the song.", "",
                 "Add jumps on every on-beat step."])
            ),
  "spin": (True, "Spin",
           "Rotate arrows as they go up the screen.",
           ON_OFF),
  "colortype": (True, "Colors",
                "Use colors of arrows to indicate the beat.",
                zip([0, 1],
                    ["Flat", "Normal"],
                    ["All arrows are the same.",
                     "Different arrows have different colors."])
                ),
  "dark": (True, "Dark",
           "Don't display the top arrows.",
           ON_OFF),
  "holds": (True, "Holds",
            "Allow hold ('freeze') arrows in songs.",
            ON_OFF)
  }
            
OPTS = [ "speed", "transform", "size", "fade", "accel", "scale",
         "scrollstyle", "jumps", "spin", "colortype", "dark", "holds"
            ]

O_HELP = [
  "Up / Down: Select option",
  "Left / Right: Change value",
  "Start: Return to song selector",
  "F11: Toggle fullscreen"
  ]

class OptionScreen(InterfaceWindow):
  def __init__(self, player_configs, game_config, screen):
    InterfaceWindow.__init__(self, screen, "optionscreen-bg.png")
    self._configs = player_configs
    self._config = game_config
    self._players = len(self._configs)

    self._lists = [ListBox(pygame.font.Font(None, 24), [255, 255, 255],
                           25, 9, 176, [10, 10])]
    self._index = [0]
    ActiveIndicator([5, 110]).add(self._sprites)
    if self._players == 2:
      self._lists.append(ListBox(pygame.font.Font(None, 24), [255, 255, 255],
                                 25, 9, 176, [453, 246]))
      self._index.append(0)
      ActiveIndicator([448, 345]).add(self._sprites)

    HelpText(O_HELP, [255, 255, 255], [0, 0, 0],
             pygame.font.Font(None, 22), [320, 241]).add(self._sprites)
    self._sprites.add(self._lists)

    for l in self._lists: l.set_items([OPTIONS[k][1] for k in OPTS])
    self._screen.blit(self._bg, [0, 0])

    pygame.display.update()
    self.loop()

  def loop(self):
    pid, ev = ui.ui.poll()
    for i in range(len(self._lists)): self._lists[i].set_index(self._index[i])

    while ev not in [ui.START, ui.CANCEL, ui.CONFIRM]:
      if pid >= self._players: pass

      elif ev == ui.UP:
        self._index[pid] = (self._index[pid] - 1) % len(OPTS)
        self._lists[pid].set_index(self._index[pid], -1)
      elif ev == ui.DOWN:
        self._index[pid] = (self._index[pid] + 1) % len(OPTS)
        self._lists[pid].set_index(self._index[pid], 1)
      elif ev == ui.FULLSCREEN:
        pygame.display.toggle_fullscreen()
        mainconfig["fullscreen"] ^= 1

      self.update()
      self._clock.tick(60)
      pid, ev = ui.ui.poll()
