# ceci n'est e'galement pas un e'cran d'option

import os
import pygame
import fontfx
import math
import colors
import ui
import scores
import combos
import grades
import judge
import lifebars

from constants import *
from interface import *

ON_OFF = [(0, "Off", ""), (1, "On", "")]

# Description gets assigned 2 both times.
PP, NAME, DESCRIPTION, VALUES = range(4)
VALUE, NAME, DESCRIPTION = range(3)

OPTIONS = {
  # Option specifier tuple:
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
                     "Rotate the steps 90 degrees to the left.",
                     "Rotate the steps 90 degrees to the right.",
                     "Swap all arrows from one direction to another.",
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
                       "Arrows go from top to bottom.",
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
                zip([0, 4],
                    ["Flat", "Normal"],
                    ["All arrows are the same.",
                     "Different arrows have different colors."])
                ),
  "dark": (True, "Dark",
           "Don't display the top arrows.",
           ON_OFF),
  "holds": (True, "Holds",
            "Allow hold ('freeze') arrows in songs.",
            ON_OFF),
  "scoring": (False, "Scoring",
              "The scoring algorithm.",
              scores.score_opt),
  "grade": (False, "Grades",
            "The gradinging algorithm.",
            grades.grade_opt),
  "combo": (False, "Combos",
             "How your combo increases.",
             combos.combo_opt),
  "judge": (False, "Judging Method",
            "How your steps are judged.",
            judge.judge_opt),
  "judgescale": (False, "Judging Windows",
                 "The margin of error for your steps.",
                 zip([2.0 - 0.2 * i for i in range(10)],
                     [str(i) for i in range(10)],
                     ["Window is twice normal size.",
                      "Window is 9/5 normal size.",
                      "Window is 8/5 normal size.",
                      "Window is 7/5 normal size.",
                      "Window is 6/5 normal size.", "",
                      "Window is 4/5 normal size.",
                      "Window is 3/5 normal size.",
                      "Window is 2/5 normal size.",
                      "Window is 1/5 normal size."])
                 ),

  "life": (False, "Life",
                 "Increase or decrease your amount of (non-battery) life.",
                 [(0.25, "Undead", "Life is 1/4 the usual amount."),
                  (0.50, "Very Low", "Life is 1/2 the usual amount."),
                  (0.75, "Low", "Life is 3/4 the usual amount."),
                  (1, "Normal", ""),
                  (1.25, "High", "Life is 5/4 the usual amount."),
                  (1.50, "Very High", "Life is 3/2 the usual amount."),
                  (1.75, "Lazarus", "Life is 7/4 the usual amount.")]
                 ),
  "lifebar": (False, "Lifebar",
              "The kind of lifebar used.",
              lifebars.lifebar_opt),
  "onilives": (False, "Oni Lives",
               "The initial / maximum life in Battery mode.",
               [(i, str(i), "") for i in range(1, 9)]),
  "secret": (False, "Secret Arrows",
             "Secret arrow display",
             [(0, "Off", "Disable secret arrows."),
              (1, "Invisible", "Enable but don't display them."),
              (2, "Faint", "Show secret arrows faintly.")]
             ),
  "battle": (False, "Battle Mode",
             "Arrows start in the center and float outwards.",
             ON_OFF),
  }
            
OPTS = [ "speed", "transform", "size", "fade", "accel", "scale",
         "scrollstyle", "jumps", "spin", "colortype", "dark", "holds",
         "scoring", "combo", "grade", "judge", "lifebar", "judgescale",
         "life", "onilives", "secret", "battle"
         ]

O_HELP = [
  "Up / Down: Select option",
  "Left / Right: Change value",
  "Start: Return to song selector",
  "F11: Toggle fullscreen"
  ]

def index_of(value, name):
  values = OPTIONS[name][VALUES]
  for i, v in zip(range(len(values)), values):
    if v[VALUE] == value: return i
  return None

def value_of(index, name):
  return OPTIONS[name][VALUES][index][VALUE]

class OptionSelect(pygame.sprite.Sprite):
  def __init__(self, possible, center, index):
    pygame.sprite.Sprite.__init__(self)
    self._index = self._oldindex = index
    self._possible = possible
    self._center = center
    self._end_time = pygame.time.get_ticks()
    self._needs_update = True
    self._font = pygame.font.Font(None, 30)
    self._render(pygame.time.get_ticks())

  def update(self, time):
    if self._needs_update:
      self._render((self._end_time - time) / 200.0)

  def set_possible(self, possible, index = -1):
    self._possible = possible
    self._oldindex = self._index = index
    self._end_time = pygame.time.get_ticks()

    self._needs_update = True

  def set_index(self, index):
    self._oldindex = self._index
    self._index = index
    if self._oldindex == -1: self._oldindex = self._index
    self._end_time = pygame.time.get_ticks() + 200
    self._needs_update = True

  def _render(self, pct):
    self.image = pygame.Surface([430, 40], SRCALPHA, 32)
    self.image.fill([0, 0, 0, 0])
    self.rect = self.image.get_rect()
    self.rect.center = self._center

    if pct <= 0:
      self._needs_update = False
      offset = 0
      pct = 1
    elif self._oldindex != self._index:
      offset = (self._font.size(self._possible[self._oldindex])[0]/2 +
                self._font.size(self._possible[self._index])[0]/2 + 30)
      offset = int(pct * offset)
      if self._oldindex > self._index: offset = -offset
    else: offset = 0

    t = fontfx.shadow(self._possible[self._index],
                      pygame.font.Font(None, 30), [255, 255, 255])
    r = t.get_rect()
    r.center = [215 + offset, 20]
    self.image.blit(t, r)
    old_r = Rect(r)
    
    idx = self._index - 1
    while idx >= 0 and r.left > 0:
      t = fontfx.shadow(self._possible[idx],
                        pygame.font.Font(None, 30), [255, 255, 255])
      t2 = pygame.Surface(t.get_size())
      t2.blit(t, [0, 0])
      t2.set_colorkey(t2.get_at([0, 0]))
      r2 = t2.get_rect()
      r2.centery = 20
      r2.right = r.left - 30
      t2.set_alpha(int(200 * (r2.centerx / 215.0)))
      self.image.blit(t2, r2)
      idx -= 1
      r = r2

    idx = self._index + 1
    r = old_r
    while idx < len(self._possible) and r.right < 430:
      t = fontfx.shadow(self._possible[idx],
                        pygame.font.Font(None, 30), [255, 255, 255])
      t2 = pygame.Surface(t.get_size())
      t2.blit(t, [0, 0])
      t2.set_colorkey(t2.get_at([0, 0]))
      r2 = t2.get_rect()
      r2.centery = 20
      r2.left = r.right + 30
      t2.set_alpha(int(200 * ((430 - r2.centerx) / 215.0)))
      self.image.blit(t2, r2)
      idx += 1
      r = r2

class OptionScreen(InterfaceWindow):
  def __init__(self, player_configs, game_config, screen):
    InterfaceWindow.__init__(self, screen, "option-bg.png")
    self._configs = player_configs
    self._config = game_config
    self._players = len(self._configs)

    self._lists = [ListBox(pygame.font.Font(None, 24), [255, 255, 255],
                           25, 9, 176, [10, 10])]
    self._text = [WrapTextDisplay(28, 430, [198, 165], centered = True,
                                  str = OPTIONS[OPTS[0]][DESCRIPTION])]
    val = self._configs[0][OPTS[0]]
    names = [v[NAME] for v in OPTIONS[OPTS[0]][VALUES]]
    desc = OPTIONS[OPTS[0]][VALUES][index_of(val, OPTS[0])][DESCRIPTION]
    self._text2 = [WrapTextDisplay(22, 430, [198, 105], centered = True,
                                  str = desc)]
    self._displayers = [OptionSelect(names, [415, 40],
                                     index_of(val, OPTS[0]))]
    self._index = [0]
    ActiveIndicator([5, 110]).add(self._sprites)
    if self._players == 2:
      self._lists.append(ListBox(pygame.font.Font(None, 24), [255, 255, 255],
                                 25, 9, 176, [453, 246]))
      self._index.append(0)
      self._text.append(WrapTextDisplay(28, 430, [10, 275], centered = True,
                                        str = OPTIONS[OPTS[0]][DESCRIPTION]))
      ActiveIndicator([448, 345]).add(self._sprites)
      val = self._configs[1][OPTS[0]]
      desc = OPTIONS[OPTS[0]][VALUES][index_of(val, OPTS[0])][DESCRIPTION]
      self._text2.append(WrapTextDisplay(22, 430, [10, 350], centered = True,
                                         str = desc))
      self._displayers.append(OptionSelect(names, [220, 440],
                                           index_of(val, OPTS[0])))

    HelpText(O_HELP, [255, 255, 255], [0, 0, 0],
             pygame.font.Font(None, 22), [320, 241]).add(self._sprites)
    self._sprites.add(self._lists + self._displayers + self._text +
                      self._text2)

    for l in self._lists: l.set_items([OPTIONS[k][1] for k in OPTS])
    self._screen.blit(self._bg, [0, 0])

    pygame.display.update()
    self.loop()

  def loop(self):
    pid, ev = ui.ui.poll()
    for i in range(len(self._lists)): self._lists[i].set_index(self._index[i])
    for i in range(self._players):
      opt = OPTS[self._index[i]]
      self._displayers[i].set_index(index_of(self._configs[i][opt], opt))

    while ev not in [ui.START, ui.CANCEL, ui.CONFIRM]:
      if pid >= self._players: pass

      elif ev == ui.UP:
        self._index[pid] = (self._index[pid] - 1) % len(OPTS)
        self._lists[pid].set_index(self._index[pid], -1)
      elif ev == ui.DOWN:
        self._index[pid] = (self._index[pid] + 1) % len(OPTS)
        self._lists[pid].set_index(self._index[pid], 1)

      elif ev == ui.LEFT:
        opt = OPTS[self._index[pid]]
        if OPTIONS[opt][PP]: index = index_of(self._configs[pid][opt], opt)
        else: index = index_of(self._config[opt], opt)
        if index > 0: index -= 1
        if OPTIONS[opt][PP]: self._configs[pid][opt] = value_of(index, opt)
        else: self._config[opt] = value_of(index, opt)
      elif ev == ui.RIGHT:
        opt = OPTS[self._index[pid]]
        if OPTIONS[opt][PP]: index = index_of(self._configs[pid][opt], opt)
        else: index = index_of(self._config[opt], opt)
        if index != len(OPTIONS[opt][VALUES]) - 1: index += 1
        if OPTIONS[opt][PP]: self._configs[pid][opt] = value_of(index, opt)
        else: self._config[opt] = value_of(index, opt)
          
      elif ev == ui.FULLSCREEN:
        pygame.display.toggle_fullscreen()
        mainconfig["fullscreen"] ^= 1

      if ev in [ui.UP, ui.DOWN]:
        values = OPTIONS[OPTS[self._index[pid]]][VALUES]
        names = [v[NAME] for v in values]
        self._displayers[pid].set_possible(names)
        self._text[pid].set_text(OPTIONS[OPTS[self._index[pid]]][DESCRIPTION])

      if ev in [ui.LEFT, ui.RIGHT, ui.UP, ui.DOWN]:
        opt = OPTS[self._index[pid]]
        if OPTIONS[opt][PP]:
          val = self._configs[pid][opt]
          idx = index_of(val, opt)
          self._displayers[pid].set_index(index_of(val, opt))
          self._text2[pid].set_text(OPTIONS[opt][VALUES][idx][DESCRIPTION])
        elif self._players > 1 and self._index[0] == self._index[1]:
          # If both players have the same non-per-player option
          # selected, we need to update both displayers.
          val = self._config[opt]
          idx = index_of(val, opt)
          for i in range(self._players):
            self._displayers[i].set_index(idx)
            self._text2[pid].set_text(OPTIONS[opt][VALUES][idx][DESCRIPTION])
        else:
          val = self._config[opt]
          idx = index_of(val, opt)
          self._displayers[pid].set_index(idx)
          self._text2[pid].set_text(OPTIONS[opt][VALUES][idx][DESCRIPTION])
      self.update()
      pid, ev = ui.ui.poll()
