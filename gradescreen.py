import pygame
import announcer
import colors
import fontfx
import ui

from constants import *

class StatSprite(pygame.sprite.Sprite):
  def __init__(self, pos, title, count, size, delay):
    pygame.sprite.Sprite.__init__(self)
    self._start = pygame.time.get_ticks() + delay
    self._count = count
    self._pos = pos
    self._curcount = 0
    self._size = size
    self._title = fontfx.shadow(title, 30, colors.WHITE)
    self._render()

  def _render(self):
    self.image = pygame.Surface(self._size, SRCALPHA, 32)
    self.image.fill([0, 0, 0, 0])
    rt = self._title.get_rect()
    rt.midleft = [0, self._size[1] / 2]
    self.image.blit(self._title, rt)
    cnt = fontfx.shadow(str(self._curcount), 30, colors.WHITE)
    rc = cnt.get_rect()
    rc.midright = [self._size[0] - 1, self._size[1] / 2]
    self.image.blit(cnt, rc)
    self.rect = self.image.get_rect()
    self.rect.topleft = self._pos

  def update(self, time):
    if time < self._start: return
    elif time - self._start < 2000:
      self._curcount = int(self._count * ((time - self._start) / 1000.0))
      self._render()
    elif self._curcount != self._count:
      self._curcount = self._count
      self._render()

class HoldStatSprite(pygame.sprite.Sprite):
  def __init__(self, pos, title, goodcount, totalcount, size, delay):
    pygame.sprite.Sprite.__init__(self)
    self._start = pygame.time.get_ticks() + delay
    self._goodcount = goodcount
    self._totalcount = totalcount
    self._pos = pos
    self._curgood = 0
    self._curtotal = 0
    self._size = size
    self._title = fontfx.shadow(title, 30, colors.WHITE)
    self._render()

  def _render(self):
    self.image = pygame.Surface(self._size, SRCALPHA, 32)
    self.image.fill([0, 0, 0, 0])
    rt = self._title.get_rect()
    rt.midleft = [0, self._size[1] / 2]
    self.image.blit(self._title, rt)
    s = "%d / %d" % (self._curgood, self._curtotal)
    cnt = fontfx.shadow(s, 30, colors.WHITE)
    rc = cnt.get_rect()
    rc.midright = [self._size[0] - 1, self._size[1] / 2]
    self.image.blit(cnt, rc)
    self.rect = self.image.get_rect()
    self.rect.topleft = self._pos

  def update(self, time):
    if time < self._start: return
    elif time - self._start < 2000:
      self._curgood = int(self._goodcount * ((time - self._start) / 1000.0))
      self._curtotal = int(self._totalcount * ((time - self._start) / 1000.0))
      self._render()
    elif self._curgood != self._goodcount:
      self._curgood = self._goodcount
      self._curtotal = self._totalcount
      self._render()

# FIXME: Make an interfacewindow.
class GradingScreen(object):
  def __init__(self, players):
    self.players = players
    for p in players:
      if p == None: continue
      print "Player %d:" % (p.pid + 1)
      grade = p.grade.grade(p.failed)
      stepcount = p.stats.arrow_count
      steps = (grade, p.difficulty, stepcount, p.stats.maxcombo)
      ratings = (p.stats["V"], p.stats["P"], p.stats["G"],
                 p.stats["O"], p.stats["B"], p.stats["M"],
                 p.stats.good_holds, p.stats.hold_count)
      print "GRADE: %s (%s) - total steps: %d; best combo: %d" % steps
      print "V: %d P: %d G: %d O: %d B: %d M: %d - %d/%d holds" % ratings
      print

  def render(self, screen):
    if self.players[0] == None: return None
    elif self.players[0].stats.arrow_count == 0: return None
    bg = pygame.image.load(os.path.join(image_path, "grade-bg.png"))
    bg = bg.convert()
    screen.blit(bg, [0, 0])
    pygame.display.update()
    
    sprites = pygame.sprite.RenderUpdates()
    plr = self.players[0]

    s = [180, 34]
    # FIXME: There is probably a shorter way to do this.
    sprites.add([
      StatSprite([200, 10], "MARV.:", plr.stats["V"], s, 0),
      StatSprite([200, 44], "PERFECT:", plr.stats["P"], s, 333),
      StatSprite([200, 78], "GREAT:", plr.stats["G"], s, 666),
      StatSprite([200, 112], "OKAY:", plr.stats["O"], s, 1000),
      StatSprite([200, 146], "BOO:", plr.stats["B"], s, 1333),
      StatSprite([200, 180], "MISS:", plr.stats["M"], s, 1666),
      StatSprite([400, 10], "Early:", plr.stats.early, s, 666),
      StatSprite([400, 44], "Late:", plr.stats.late, s, 1000),
      StatSprite([400, 78], "Max Combo:", plr.stats.maxcombo, s, 1333),
      HoldStatSprite([400, 112], "Holds:", plr.stats.good_holds,
                     plr.stats.hold_count, s, 1666),
      StatSprite([400, 146], "Score:", int(plr.score.score), s, 2000),
      StatSprite([400, 180], "TOTAL:", plr.stats.arrow_count, s, 2333)
      ])

    if len(self.players) == 2:
      plr = self.players[1]
      sprites.add([
        StatSprite([15, 270], "MARV.:", plr.stats["V"], s, 0),
        StatSprite([15, 304], "PERFECT:", plr.stats["P"], s, 333),
        StatSprite([15, 338], "GREAT:", plr.stats["G"], s, 666),
        StatSprite([15, 372], "OKAY:", plr.stats["O"], s, 1000),
        StatSprite([15, 406], "BOO:", plr.stats["B"], s, 1333),
        StatSprite([15, 440], "MISS:", plr.stats["M"], s, 1666),
        StatSprite([215, 270], "Early:", plr.stats.early, s, 666),
        StatSprite([215, 304], "Late:", plr.stats.late, s, 1000),
        StatSprite([215, 338], "Max Combo:", plr.stats.maxcombo, s, 1333),
        HoldStatSprite([215, 372], "Holds:", plr.stats.good_holds,
                       plr.stats.hold_count, s, 1666),
        StatSprite([215, 406], "Score:", int(plr.score.score), s, 2000),
        StatSprite([215, 440], "TOTAL:", plr.stats.arrow_count, s, 2333),
        ])

    ui.ui.clear()
    screenshot = False
    pid, ev = ui.ui.poll()
    i = 192
    idir = -4
    clock = pygame.time.Clock()
    bonus = 0
    exits = [ui.QUIT]
    start = pygame.time.get_ticks()
    
    while ev not in exits:
      if ev == ui.FULLSCREEN:
        pygame.display.toggle_fullscreen()
        mainconfig["fullscreen"] ^= 1
      elif ev == ui.SCREENSHOT:
        screenshot = True
      elif (ev == ui.CONFIRM or ev == ui.START or
            pygame.time.get_ticks() - start > 3333):
        exits.extend([ui.CONFIRM, ui.START])
        ev = ui.PASS
        bonus += 3333

      if i < 32: idir =  4
      elif i > 224: idir = -4
      i += idir
      sprites.update(pygame.time.get_ticks() + bonus)

      # FIXME: Make this a sprite.
      text = FONTS[24].render("Press Escape/Confirm/Start", True, [i, 128,128])
      tr = text.get_rect()
      tr.center = [320, 240]
      pygame.display.update([screen.blit(text, tr)] + sprites.draw(screen))
      clock.tick(45)

      if screenshot:
        fn = os.path.join(rc_path, "screenshot.bmp")
        print "Saving a screenshot to", fn
        pygame.image.save(screen, fn)
        screenshot = False

      sprites.clear(screen, bg)
      pid, ev = ui.ui.poll()
