import pygame
import announcer
import colors
import fontfx
import ui

from interface import InterfaceWindow
from constants import *

class TextSprite(pygame.sprite.Sprite):
  def __init__(self, center):
    pygame.sprite.Sprite.__init__(self)
    self._idir = 4
    self._i = 128
    self._center = center
    self._last_update = pygame.time.get_ticks() - 200

  def update(self, time):
    if time - self._last_update > 100:
      if self._i < 32: self._idir =  4
      elif self._i > 224: self._idir = -4
      self._i += self._idir

      c = [self._i, 128, 128]
      self.image = FONTS[24].render("Press Escape/Confirm/Start", True, c)
      self.rect = self.image.get_rect()
      self.rect.center = self._center
      self._last_update = time

class GradeSprite(pygame.sprite.Sprite):
  def __init__(self, center, rating):
    pygame.sprite.Sprite.__init__(self)
    rating = rating.lower()
    if rating == "!!": rating = "ee"
    self._end = pygame.time.get_ticks() + 3000
    fn = os.path.join(image_path, "rating-%s.png" % rating)
    self._image = pygame.image.load(fn).convert()
    self._size = self._image.get_size()
    self._center = center
    self.rect = self._image.get_rect()
    self.rect.center = center

  def update(self, time):
    if time < self._end:
      angle = (self._end - time) / 3.0
      zoom = (1 - (self._end - time) / 3000.0)
      img = pygame.transform.rotozoom(self._image, angle, zoom).convert()
    else:
      img = self._image
    self.image = pygame.Surface(self._size)
    r = img.get_rect()
    r.center = self.image.get_rect().center
    self.image.blit(img, r)
    self.image.set_colorkey(self.image.get_at([0, 0]))
    self.rect = self.image.get_rect()
    self.rect.center = self._center

# And here is where I blatantly steal your idea, Matt. Sorry.
class GrooveGaugeSprite(pygame.sprite.Sprite):
  def __init__(self, pos, size, records):
    pygame.sprite.Sprite.__init__(self)
    self._image = pygame.Surface(size)
    self._pos = pos
    self._end = pygame.time.get_ticks() + 3000
    self._size = size

    width = size[0]
    self._image.set_colorkey(self._image.get_at([0, 0]))
    c1 = [0, 190, 0]
    c2 = [190, 190, 0]
    c3 = [190, 0, 0]
    for i in range(width):
      p = (float(i) / float(width))
      plife = records[int(p * len(records))]
      h = size[1] - int(size[1] * plife)
      if plife > 0.5: c = colors.average(c1, c2, (plife - 0.5) / 0.5)
      else: c = colors.average(c2, c3, plife / 0.5)
      pygame.draw.line(self._image, c, [i, size[1] - 1], [i, h])
      if plife > 0.999999: self._image.set_at([i, 0], [255, 255, 255])

  def update(self, time):
    if time < self._end:
      p = 1 - ((self._end - time)  / 3000.0)
      self.image = pygame.Surface([int(self._size[0] * p), self._size[1]])
      if self.image.get_size()[0] > 0:
        self.image.set_colorkey(self.image.get_at([0, 0]))
      self.image.blit(self._image, [0, 0])
    else: self.image = self._image
    self.rect = self.image.get_rect()
    self.rect.topleft = self._pos
    self.image.set_alpha(192)

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
      self._curcount = min(int(self._count * ((time - self._start) / 1000.0)),
                           self._count)
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
      p = (time - self._start) / 1000.0
      self._curgood = min(int(self._goodcount * p), self._goodcount)
      self._curtotal = min(int(self._totalcount * p), self._totalcount)
      self._render()
    elif self._curgood != self._goodcount:
      self._curgood = self._goodcount
      self._curtotal = self._totalcount
      self._render()

class GradingScreen(InterfaceWindow):
  def __init__(self, screen, players):
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

    if self.players[0] == None: return None
    elif self.players[0].stats.arrow_count == 0: return None
    InterfaceWindow.__init__(self, screen, "grade-bg.png")
    pygame.display.update()
    
    self._sprites.add(TextSprite([320, 242]))
    plr = self.players[0]

    s = [180, 34]
    # FIXME: There is probably a shorter way to do this.
    self._sprites.add([
      StatSprite([200, 10], "MARVEL.:", plr.stats["V"], s, 0),
      StatSprite([200, 44], "PERFECT:", plr.stats["P"], s, 333),
      StatSprite([200, 78], "GREAT:", plr.stats["G"], s, 666),
      StatSprite([200, 112], "OKAY:", plr.stats["O"], s, 1000),
      StatSprite([200, 146], "BOO:", plr.stats["B"], s, 1333),
      StatSprite([200, 180], "MISS:", plr.stats["M"], s, 1333),
      StatSprite([400, 10], "Score:", int(plr.score.score), s, 666),
      HoldStatSprite([400, 44], "Holds:", plr.stats.good_holds,
                     plr.stats.hold_count, s, 1000),
      StatSprite([400, 78], "Max Combo:", plr.stats.maxcombo, s, 1333),
      StatSprite([400, 112], "Early:", plr.stats.early, s, 1666),
      StatSprite([400, 146], "Late:", plr.stats.late, s, 2000),
      StatSprite([400, 180], "TOTAL:", plr.stats.arrow_count, s, 2333)
      ])
    self._sprites.add(GradeSprite([98, 183], plr.grade.grade(plr.failed)))
    self._sprites.add(GrooveGaugeSprite([10, 22], [176, 100],
                                        plr.lifebar.record))

    if len(self.players) == 2:
      plr = self.players[1]
      self._sprites.add([
        StatSprite([15, 270], "MARVEL.:", plr.stats["V"], s, 0),
        StatSprite([15, 304], "PERFECT:", plr.stats["P"], s, 333),
        StatSprite([15, 338], "GREAT:", plr.stats["G"], s, 666),
        StatSprite([15, 372], "OKAY:", plr.stats["O"], s, 1000),
        StatSprite([15, 406], "BOO:", plr.stats["B"], s, 1333),
        StatSprite([15, 440], "MISS:", plr.stats["M"], s, 1666),
        StatSprite([215, 270], "Score:", int(plr.score.score), s, 666),
        HoldSprite([215, 304], "Holds:", plr.stats.good_holds,
                   plr.stats.hold_count, s, 1000),
        StatSprite([215, 338], "Max Combo:", plr.stats.maxcombo, s, 1333),
        StatSprite([215, 372], "Early:", plr.stats.early, s, 1666),
        StatSprite([215, 406], "Late:", plr.stats.late, s, 2000),
        StatSprite([215, 440], "TOTAL:", plr.stats.arrow_count, s, 2333),
        ])
      self._sprites.add(GradeSprite([541, 294], plr.grade.grade(plr.failed)))
      self._sprites.add(GrooveGaugeSprite([453, 370], [176, 100],
                                          plr.lifebar.record))

    ui.ui.clear()
    screenshot = False
    pid, ev = ui.ui.poll()
    clock = pygame.time.Clock()
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
        self._time_bonus += 3333

      screenshot = self.update(screenshot)
      pid, ev = ui.ui.poll()
