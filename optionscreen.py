# ceci n'est pas une \'{e}cran d'option

import copy
from constants import *

import pygame
import colors
import scores, lifebars, combos, grades, judge, ui

def player_opt_driver(screen, configs):
  ev = (0, ui.QUIT)
  start = pygame.time.get_ticks()
  clrs = [colors.color["cyan"], colors.color["yellow"]]
  menu = [
    ("Speed", "speed", [(0.25, ".25x"), (0.33, "0.33x"), (0.5, "0.5x"),
                        (0.75, "0.75x"), (1, "1x"), (1.5, "1.5x"), (2, "2x"),
                        (3, "3x"), (4, "4x"), (5, "5x"), (8, "8x"),
                        (0.444, "Random")]),
    ("Steps", "transform", [(0, "Normal",), (1, "Mirror"), (2, "Left"),
                         (3, "Right"), (-1, "Shuffle"), (-2, "Random")]),
    ("Size", "size", [(1, "Tiny"), (2, "Little"), (0, "Off"), (3, "Big"),
                      (4, "Quick"), (5, "Skippy")]),
    ("Fade", "fade", [(0, "Off"), (1, "Sudden"), (2, "Hidden"),
                        (3, "Peek"), (4, "Cycle"), (5, "Stealth")]),
    ("Accel", "accel", [(2, "Brake"), (0, "None"), (1, "Boost")]),
    ("Scale", "scale", [(0, "Shrink"), (1, "Normal"), (2, "Grow")]),
    ("Scroll", "scrollstyle", [(0, "Normal"), (1, "Reverse"), (2, "Center")]),
    ("Jumps", "jumps", [(0, "Off"), (1, "On"), (2, "Wide")]),
    ("Spin", "spin", [(0, "Off"), (1, "On")]),
    ("Flat", "colortype", [(4, "Off"), (1, "On")]),
    ("Dark", "dark", [(0, "Off"), (1, "On")]),
    ("Holds", "holds", [(0, "Off"), (1, "On")]),
    ]

  while ((ui.ui.states[(0, ui.START)] or ui.ui.states[(1, ui.START)]) and
         pygame.time.get_ticks() - start < 1500): ev = ui.ui.poll()

  if ui.ui.states[(0, ui.START)] or ui.ui.states[(1, ui.START)]:
    op = OptionScreen(configs, "Player Options", menu, clrs)
    return op.display(screen)
  else: return True

def game_opt_driver(screen, config):
  ev = (0, ui.QUIT)
  start = pygame.time.get_ticks()
  menu = [
    ("Scoring", "scoring", scores.score_opt),
    ("Combos", "combo", combos.combo_opt),
    ("Grades", "grade", grades.grade_opt),
    ("Judge", "judge", judge.judge_opt),
    ("Difficulty", "judgescale",
     [(2.0 - 0.2 * i, str(i)) for i in range(10)]),
    ("Lifebar", "lifebar", lifebars.lifebar_opt),
    ("Life", "life", [(0.25, "Undead"), (0.50, "Very Low"), (0.75, "Low"),
                      (1.0, "Normal"), (1.25, "High"), (1.5, "Very High"),
                      (1.75, "Ruma")]),
    ("Oni Life", "onilives", [(i, str(i)) for i in range(1, 9)]),
    ("Secret Arrows", "secret", [(0, "Off"), (1, "Invisible"), (2, "Faint")]),
    ("Battle", "battle", [(0, "Off"), (1, "On")]),
    ]
  clrs = [colors.color["green"]]

  while ((ui.ui.states[(0, ui.SELECT)] or ui.ui.states[(1, ui.SELECT)]) and
         pygame.time.get_ticks() - start < 1500): ev = ui.ui.poll()

  if ui.ui.states[(0, ui.SELECT)] or ui.ui.states[(1, ui.SELECT)]:
    op = OptionScreen([config], "Game Options", menu, clrs)
    op.display(screen)
    return False
  else: return True
                    
class OptionScreen(object):

  bg = pygame.image.load(os.path.join(pydance_path, "images", "option-bg.png"))
  bg.set_colorkey(bg.get_at([0, 0]))
  bg.set_alpha(220)

  # Players is a list of hashes, not Player objects; it should have all
  # config information set to some value already (player_config in constants)
  def __init__(self, players, title, menu, colors):
    self.players = players
    self.current = [0] * len(players)
    self.menu = menu
    self.title = title
    self.colors = colors

  def display(self, screen):
    baseimage = pygame.transform.scale(screen, [640, 480])

    # Animate the menu opening
    if mainconfig['gratuitous']:
      t = pygame.time.get_ticks()
      eyecandyimage = pygame.surface.Surface([640, 480])
      while pygame.time.get_ticks() - t < 300:
        p = float(pygame.time.get_ticks() - t) / 300
        eyecandyimage.blit(baseimage, (0,0))
        scaledbg = pygame.transform.scale(OptionScreen.bg, [int(580 * p), 480])
        scaledbg.set_alpha(220)
        r = scaledbg.get_rect()
        r.center = [320, 240]
        up = eyecandyimage.blit(scaledbg, r)
        screen.blit(eyecandyimage, [0, 0])
        pygame.display.update(up)
    
    baseimage.blit(OptionScreen.bg, [30, 0])

    self.baseimage = baseimage
    
    screen.blit(baseimage, [0, 0])
    pygame.display.update()
    
    ev = ui.PASS
    
    while not (ev == ui.START or ev == ui.QUIT or ev == ui.MARK):
      self.render(screen)
      
      pid, ev = ui.ui.wait()
      pid = min(pid, len(self.current) - 1)

      if ev == ui.DOWN:
        self.current[pid] = (self.current[pid] + 1) % len(self.menu)
        
      elif ev == ui.UP:
        self.current[pid] = (self.current[pid] - 1) % len(self.menu)
        
      elif ev == ui.LEFT:
        optname = self.menu[self.current[pid]][1]
        cur_val = self.players[pid][optname]
        values = copy.copy(self.menu[self.current[pid]][2])
        values.reverse()
        
        next = False
        for val in values:
          if next:
            self.players[pid][optname] = val[0]
            break
          elif self.players[pid][optname] == val[0]: next = True

      elif ev == ui.RIGHT:
        optname = self.menu[self.current[pid]][1]
        cur_val = self.players[pid][optname]
        values = self.menu[self.current[pid]][2]

        next = False
        for val in values:
          if next:
            self.players[pid][optname] = val[0]
            break
          elif self.players[pid][optname] == val[0]: next = True

      elif ev == ui.FULLSCREEN:
        pygame.display.toggle_fullscreen()
        mainconfig["fullscreen"] ^= 1

    return (ev == ui.START)

  def render(self, screen):
    rect = [[45, 5], [570, 470]]
    blankimage = pygame.surface.Surface(rect[1]).convert_alpha()
    blankimage.fill([0, 0, 0, 0])

    width = 200

    for i in range(len(self.menu)):
      color = None
      for j in range(len(self.current)):
        if i == self.current[j]:
          if not color: color = self.colors[j]
          else: color = colors.average(color, self.colors[j])
      if not color: color = colors.WHITE

      item = self.menu[i]
      name, opt, values = item
      text = FONTS[24].render(name, 1, colors.BLACK)
      blankimage.blit(text, [11, 71 + 28 * i])
      text = FONTS[24].render(name, 1, color)
      blankimage.blit(text, [10, 70 + 28 * i])
      for k in range(len(values)):
        color = None
        for plr in range(len(self.players)):
          self.players[plr]
          if values[k][0] == self.players[plr][opt]:
            color = self.colors[plr]

            x = width * (plr + 1)
            y = 70 + 28 * i

            if i == self.current[plr]: FONTS[24].set_underline(True)

            text = FONTS[24].render(values[k][1], 1, colors.BLACK)
            r = text.get_rect()
            r.midtop = [x + 1, y + 1]
            blankimage.blit(text, r)

            text = FONTS[24].render(values[k][1], 1, color)
            FONTS[24].set_underline(False)
            r = text.get_rect()
            r.midtop = [x, y]
            blankimage.blit(text, r)

            if k != 0:
              left = FONTS[24].render("< ", 1, colors.BLACK)
              r = left.get_rect()
              r.topright = [x - text.get_size()[0] / 2 + 1, y + 1]
              blankimage.blit(left, r)

              left = FONTS[24].render("< ", 1, color)
              r = left.get_rect()
              r.topright = [x - text.get_size()[0] / 2, y]
              blankimage.blit(left, r)
            if k != len(values) - 1:
              right = FONTS[24].render(" >", 1, colors.BLACK)
              r = right.get_rect()
              r.topleft = [x + text.get_size()[0] / 2 + 1, y + 1]
              blankimage.blit(right, r)

              right = FONTS[24].render(" >", 1, color)
              r = right.get_rect()
              r.topleft = [x + text.get_size()[0] / 2, y]
              blankimage.blit(right, r)

    if len(self.current) > 1:
      faketext = " / ".join([str(i+1) for i in range(len(self.current))])
      faketext = "Players: " + faketext
      textimage = pygame.surface.Surface(FONTS[16].size(faketext))
      textimage.set_colorkey(textimage.get_at([0, 0]))
      text = FONTS[16].render("Players: ", 1, colors.WHITE)
      textimage.blit(text, [0, 0])
      xpos = text.get_width()
      for i in range(len(self.current)):
        text = FONTS[16].render(str(i+1), 1, self.colors[i])
        textimage.blit(text, [xpos, 0])
        xpos += text.get_width()
        if i != len(self.current) - 1:
          text = FONTS[16].render(" / ", 1, colors.WHITE)
          textimage.blit(text, [xpos, 0])
          xpos += text.get_width()

      r = textimage.get_rect()
      r.center = [blankimage.get_rect().centerx, 450]
      blankimage.blit(textimage, r)


    text = FONTS[40].render(self.title, 1, colors.BLACK)
    blankimage.blit(text, (47, 66-text.get_height()))
    text = FONTS[40].render(self.title, 1, colors.WHITE)
    blankimage.blit(text, [45, 64 - text.get_height()])

    screen.blit(self.baseimage, [0, 0])
    screen.blit(blankimage, rect)
    pygame.display.update()
