# Different lifebars.

import os, pygame, fontfx

from listener import Listener
from constants import *

# The base lifebar class from which most other ones inherit.
class AbstractLifeBar(Listener, pygame.sprite.Sprite):
  def __init__(self, playernum, maxlife, songconf, game):
    pygame.sprite.Sprite.__init__(self)
    self.gameover = False
    self.maxlife = int(maxlife * songconf["diff"])
    self.image = pygame.Surface((204, 28))
    self.deltas = {}

    self.failtext = fontfx.embfade("FAILED",28,3,(80,32),(224,32,32))
    self.failtext.set_colorkey(self.failtext.get_at((0,0)), RLEACCEL)

    self.rect = self.image.get_rect()
    self.rect.top = 30
    self.rect.centerx = game.sprite_center + playernum * game.player_offset

  def failed(self):
    return self.gameover

  def stepped(self, pid, dir, curtime, rating, combo):
    if self.life >= 0:
      self.life += self.deltas.get(rating, 0)
      self.life = min(self.life, self.maxlife)

  # Inform the judge if we've failed, and adjust life.
  def update(self, judge):
    if self.gameover: return False
    
    if self.life < 0:
      # Don't set self.failed; the child does that when the graphic is updated.
      judge.failed = True
      self.life = -1
    elif self.life > self.maxlife:
      self.life = self.maxlife
        
    return True

# Regular DDR-style lifebar, life from 0 to 100.
class LifeBarDisp(AbstractLifeBar):
  def __init__(self, playernum, theme, songconf, game):
    AbstractLifeBar.__init__(self, playernum, 100, songconf, game)
    self.life = self.maxlife / 2
    self.displayed_life = self.life

    # FIXME: This might be a little harsh on misses/boos.
    self.deltas = {"V": 0.8, "P": 0.5, "G": 0.0,
                   "O": -1.0, "B": -4.0, "M": -8.0}
    self.empty = theme.theme_data.get_image('lifebar-empty.png')
    self.full = theme.theme_data.get_image('lifebar-full.png')

  def update(self, judges):
    if self.gameover and self.displayed_life <= 0: return

    if self.displayed_life < self.life:  self.displayed_life += 1
    elif self.displayed_life > self.life:  self.displayed_life -= 1

    if abs(self.displayed_life - self.life) < 1:
      self.displayed_life = self.life

    AbstractLifeBar.update(self, judges)

    if self.life < 0: self.gameover = True

    if self.displayed_life < 0: self.displayed_life = 0
    self.image.blit(self.empty, (0, 0))
    self.image.set_clip((0, 0, int(202 * self.displayed_life / 100.0), 28))
    self.image.blit(self.full, (0, 0))
    self.image.set_clip()

    if self.gameover:
      self.image.blit(self.failtext, (70, 2))

# A lifebar that only goes down.
class DropLifeBarDisp(LifeBarDisp):
  def __init__(self, playernum, theme, songconf, game):
    LifeBarDisp.__init__(self, playernum, theme, songconf, game)
    self.life = self.maxlife # Start at full life
    for k in self.deltas:
      if self.deltas[k] > 0: self.deltas[k] = 0

# Tug of war lifebar, increases your lifebar and decreases your opponents'.
# The only way to lose life is to have it subtracted by your opponent.
class TugLifeBarDisp(LifeBarDisp):

  active_bars = []

  def __init__(self, playernum, theme, songconf, game):
    LifeBarDisp.__init__(self, playernum, theme, songconf, game)

    self.wontext = fontfx.embfade("WON",28,3,(80,32),(224,32,32))
    self.wontext.set_colorkey(self.failtext.get_at((0,0)), RLEACCEL)
    self.deltas = {"V": 3.0, "P": 1.5, "G": 0.75, "M": -0.5 }

    # If we're player 1, it's a new game, so delete the old lifebars.
    if playernum == 0: TugLifeBarDisp.active_bars = [self]
    else: TugLifeBarDisp.active_bars.append(self)

  def stepped(self, pid, dir, curtime, rating, combo):
    LifeBarDisp.stepped(self, pid, dir, curtime, rating, combo)
    for bar in TugLifeBarDisp.active_bars:
      if bar != self: bar.update_life_opponent(rating)
    
  def update_life_opponent(self, rating):
    if self.life >= 0: self.life -= self.deltas.get(rating, 0)

  def update(self, judges):
    if self.gameover and self.displayed_life <= 0: return

    if self.displayed_life < self.life:  self.displayed_life += 1
    elif self.displayed_life > self.life:  self.displayed_life -= 1

    if abs(self.displayed_life - self.life) < 1:
      self.displayed_life = self.life

    AbstractLifeBar.update(self, judges)

    if self.life < 0: self.gameover = True

    if self.displayed_life < 0: self.displayed_life = 0
    self.image.blit(self.empty, (0, 0))
    self.image.set_clip((0, 0, int(202 * self.displayed_life / 100.0), 28))
    self.image.blit(self.full, (0, 0))
    self.image.set_clip()

    if self.gameover == 2:
      self.image.blit(self.wontext, (70, 2))
    elif self.gameover:
      self.image.blit(self.failtext, (70, 2))
      for lifebar in TugLifeBarDisp.active_bars:
        if lifebar != self and not lifebar.gameover: lifebar.gameover = 2

# Lifebar where doing too good also fails you.
class MiddleLifeBarDisp(AbstractLifeBar):
  def __init__(self, playernum, theme, songconf, game):
    AbstractLifeBar.__init__(self, playernum, 30, songconf, game)
    self.life = 10.0
    self.displayed_life = 10

    self.deltas = {"V": 0.8, "P": 0.5, "G": 0.0,
                       "O": -1.0, "B": -4.0, "M": -8.0}
    self.image = pygame.surface.Surface([202, 28])
    self.image.fill([255, 255, 255])

  def update(self, judges):
    if self.gameover: return

    AbstractLifeBar.update(self, judges)

    if self.life == self.maxlife:
      self.gameover = True
      judges.failed_out = True

    pct = 1 - abs(self.life - 10) / 10.0
    self.image.fill([int(255 * pct)] * 3)

    if self.gameover: self.image.blit(self.failtext, (70, 2))

# Oni mode lifebar, anything that breaks a combo loses a life.
class OniLifeBarDisp(AbstractLifeBar):

  lose_sound = pygame.mixer.Sound(os.path.join(sound_path, "loselife.ogg"))

  def __init__(self, playernum, theme, songconf, game):
    AbstractLifeBar.__init__(self, playernum, songconf["onilives"],
                             songconf, game)

    self.life = self.maxlife

    self.deltas = { "O": -1, "B": -1, "M": -1}
    self.empty = theme.theme_data.get_image('oni-empty.png')
    self.bar = theme.theme_data.get_image('oni-bar.png')

    self.width = 192 / self.maxlife
    self.bar = pygame.transform.scale(self.bar, (self.width, 20))

  def set_song(self, bpm, diff, count, hold, feet):
    self.life = min(self.maxlife, self.life + 1)

  def broke_hold(self, dir, whichone):
    OniLifeBarDisp.lose_sound.play()
    self.life -= 1
       
  def stepped(self, pid, dir, curtime, rating, combo):
    AbstractLifeBar.stepped(self, pid, dir, curtime, rating, combo)
    if self.deltas.get(rating, 0) < 0: OniLifeBarDisp.lose_sound.play()

  def update(self, judges):
    if self.gameover: return

    AbstractLifeBar.update(self, judges)

    self.image.blit(self.empty, (0, 0))
    if self.life > 0:
      for i in range(self.life):
        self.image.blit(self.bar, (6 + self.width * i, 4))
    elif self.life < 0: self.gameover = True

    if self.gameover: self.image.blit(self.failtext, (70, 2) )

bars = [LifeBarDisp, OniLifeBarDisp, DropLifeBarDisp, MiddleLifeBarDisp,
        TugLifeBarDisp]

lifebar_opt = [(0, "Normal"), (1, "Battery"), (2, "Drop"), (3, "Suck"),
                (4, "Tug")]
