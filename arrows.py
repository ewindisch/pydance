import os, random, pygame
from math import sin

from constants import *

class AbstractArrow(pygame.sprite.Sprite):

  # Assist mode sound samples
  samples = {}
  for d in ["u", "d", "l", "r"]:
    samples[d] = pygame.mixer.Sound(os.path.join(sound_path,
                                                 "assist-" + d + ".ogg"))

  def __init__(self, arrow, curtime, secret, player, song):
    pygame.sprite.Sprite.__init__(self)

    self.dir = arrow.dir

    # NB - Making a new surface, then blitting the image in place, is 20%
    # slower than calling image.convert() (and is longer to type).
    self.image = arrow.image.convert()

    self.width = player.game.width
    self.battle = song.battle
    self.rect = self.image.get_rect()
    self.rect.left = arrow.left
    self.secret = secret

    if mainconfig['assist'] and self.dir in ArrowSprite.samples:
      self.sample = ArrowSprite.samples[self.dir]
    else: self.sample = None

    if player.scrollstyle == 2:
      self.top = 240 - player.game.width / 2
      self.bottom = random.choice([748, -276])
      if self.top < self.bottom:
        self.vector = 1
        self.suddenzone = 480
        self.hiddenzone = 240 - player.game.width / 2
      else:
        self.vector = -1
        self.suddenzone = -64
        self.hiddenzone = 240 - player.game.width / 2
    elif player.scrollstyle == 1:
      self.vector = -1
      self.top = 352
      self.bottom = -64
      self.suddenzone = -64
      self.hiddenzone = 352
    else:
      self.vector = 1
      self.top = 64
      self.bottom = 480
      self.suddenzone = 480
      self.hiddenzone = 64

    if player.fade & 1: # Sudden, fade in late.
      self.suddenzone -= self.vector * 160
    if player.fade & 2: # Hidden, fade out early.
      self.hiddenzone += self.vector * 160

    self.fade = player.fade

    self.spin = player.spin
    self.scale = player.scale
    self.speed = player.speed

    if self.speed == 0.444:
      # 0.444 signifies random speed. The value needs to be lower than
      # 0.5 so arrow queue up in time if they're given a 0.5 speed, and
      # also needs to not conflict with an actual possible speed. So,
      # 0.444 was good enough.
      self.speed = random.choice([0.5, 1.0, 1.0, 1.0, 1.0,
                                  1.5, 1.5, 1.5, 2.0, 2.0, 4.0, 8.0])

    self.accel = player.accel
    self.battle = song.battle

    self.diff = self.top - self.bottom
    self.baseimage = self.image

    # NB - Although "beats" refers to 16th notes elsewhere, this refers to
    # "proper" beats, meaning a quarter note.
    self.totalbeats = abs(self.diff) / 64.0

    self.goalcenterx = self.rect.centerx
    if self.battle:
      self.rect.left = 320 - int(player.game.width *
                                 (len(player.game.dirs) / 2.0 -
                                  player.game.dirs.index(self.dir)))
      self.origcenterx = self.centerx = self.rect.centerx
    else: self.centerx = self.rect.centerx = self.goalcenterx

  def calculate_beats(self, curtime, endtime, curbpm, lbct):
    beatsleft = 0
    if len(lbct) == 0:
      onebeat = 60.0 / curbpm
      doomtime = endtime - curtime
      beatsleft = doomtime / onebeat
    else:
      oldbpmsub = [curtime, curbpm]
      for bpmsub in lbct:
        if bpmsub[0] <= endtime:
          onefbeat = 60.0 / oldbpmsub[1]
          bpmdoom = bpmsub[0] - oldbpmsub[0]
          beatsleft += bpmdoom / onefbeat
          oldbpmsub = bpmsub
        else: break

      onefbeat = 60.0 / oldbpmsub[1]
      bpmdoom = endtime - oldbpmsub[0]
      beatsleft += bpmdoom / onefbeat

    return beatsleft

  def get_alpha(self, curtime, beatsleft, top):
    alp = 256

    if self.fade == 4: alp = int(alp * sin(beatsleft * 1.5708) ** 2)

    if self.top < self.bottom: 
      if top > self.suddenzone:
        alp = 256 - 4 * (top - self.suddenzone) / self.speed
      elif self.rect.top < self.hiddenzone:
        alp = 256 - 4 * (self.hiddenzone - top) / self.speed
    else:
      if top < self.suddenzone:
        alp = 256 - 4 * (self.suddenzone - top) / self.speed
      elif top > self.hiddenzone:
        alp = 256 - 4 * (top - self.hiddenzone) / self.speed

    if alp > 256: alp = 256
    elif alp < 0: alp = 0

    if self.secret: alp /= 5

    if self.hold and self.broken and curtime > self.endtime + 0.025: alp /= 2

    return alp

  def update(self, curtime, curbpm, lbct):
    if self.sample and curtime >= self.endtime:
      self.sample.play()
      self.sample = None

  def scale_spin_battle(self, image, top, pct):
    if self.scale != 1:
      if self.scale < 1: # Shrink
        new_size = [max(0, int(pct * i)) for i in image.get_size()]
      else: # Grow
        new_size = [max(0, int(i - pct * i)) for i in image.get_size()]
      image = pygame.transform.scale(image, new_size)
    
    if self.spin:
      image = pygame.transform.rotate(image, top - 64)

    rect = image.get_rect()
    rect.top = top

    if self.battle:
      if pct > 4.5 / 6: rect.centerx = self.origcenterx
      elif pct > 2.0 / 6:
        p = (pct - 2.0/6) / (2.5 / 6)
        rect.centerx = (1 - p) * self.goalcenterx + p * self.origcenterx
      else: rect.centerx = self.goalcenterx
    else: rect.centerx = self.centerx

    # Although the image size can be 0x!0, it can't ever be !0x0,
    # because X >= Y always.
    if image.get_size()[0] != 0:
      image.set_colorkey(image.get_at([0, 0]))

    return rect, image

  def kill(self):
    pygame.sprite.Sprite.kill(self)
    if self.sample: self.sample.play()

class ArrowSprite(AbstractArrow):
  def __init__ (self, arrow, secret, curtime, endtime, player, song):
    AbstractArrow.__init__(self, arrow, secret, curtime, player, song)
    self.hold = False
    self.endtime = endtime

  def update(self, curtime, curbpm, lbct):
    AbstractArrow.update(self, curtime, curbpm, lbct)

    if curtime > self.endtime + (240.0/curbpm):
      self.kill()
      return

    if curbpm < 0.0001: return # We're stopped
    # We can't just keep going if we're stopped, because the bpm change to
    # 0 is out of lbct, and so we only use curbpm, which is 0, meaning
    # we always end up at the top.

    beatsleft = self.calculate_beats(curtime, self.endtime, curbpm, lbct)

    if self.accel == 1:
      p = max(0, -1 / self.totalbeats * (beatsleft * self.speed - self.totalbeats))
      speed = 2 * p * self.speed + self.speed * (1 - p)
    elif self.accel == 2:
      p = min(1, -1 / self.totalbeats * (beatsleft * self.speed - self.totalbeats))
      speed = p * self.speed / 2.0 + self.speed * (1 - p)
    else: speed = self.speed

    # The second term (self.vector * ...) is a simplication of
    # int(beatsleft * speed * self.diff / self.beatsleft).
    top = self.top + self.vector * int(beatsleft * speed * 64)
    
    self.image = self.baseimage
  
    if top > 480: top = 480

    pct = abs(float(top - self.top) / self.diff)

    self.rect, self.image = self.scale_spin_battle(self.baseimage, top, pct)
    self.image.set_alpha(self.get_alpha(curtime, beatsleft, top))

class HoldArrowSprite(AbstractArrow):
  def __init__ (self, arrow, secret, curtime, times, player, song):
    AbstractArrow.__init__(self, arrow, secret, curtime, player, song)
    self.timef1 = self.endtime = times[1]
    self.hold = True
    self.timef2 = times[2]
    if self.timef2 is None: self.timef2 = self.timef1

    self.broken = True

    self.top_image = pygame.surface.Surface([self.width, self.width / 2])
    self.top_image.blit(self.image, [0, 0])
    self.top_image.set_colorkey(self.top_image.get_at([0, 0]), RLEACCEL)

    self.bottom_image = pygame.surface.Surface([self.width, self.width / 2])
    self.bottom_image.blit(self.image, [0, -self.width / 2])
    self.bottom_image.set_colorkey(self.bottom_image.get_at([0, 0]), RLEACCEL)

    self.center_image = pygame.surface.Surface([self.width, 1])
    self.center_image.blit(self.image, [0, -self.width / 2 + 1])

  def update(self, curtime, curbpm, lbct):
    AbstractArrow.update(self, curtime, curbpm, lbct)

    if curtime > self.timef2:
      self.kill()
      return

    if curbpm < 0.0001: return # We're stopped

    beatsleft_top = self.calculate_beats(curtime, self.timef1, curbpm, lbct)
    beatsleft_bot = self.calculate_beats(curtime, self.timef2, curbpm, lbct)

    if self.accel == 1:
      p = max(0, -1 / self.totalbeats * (beatsleft_top * self.speed - self.totalbeats))
      speed_top = 2 * p * self.speed + self.speed * (1 - p)
      p = max(0, -1 / self.totalbeats * (beatsleft_bot * self.speed - self.totalbeats))
      speed_bottom = 2 * p * self.speed + self.speed * (1 - p)
    elif self.accel == 2:
      p = min(1, -1 / self.totalbeats * (beatsleft_top * self.speed - self.totalbeats))
      speed_top = p * self.speed / 2.0 + self.speed * (1 - p)
      p = min(1, -1 / self.totalbeats* (beatsleft_bot * self.speed - self.totalbeats))
      speed_bottom = p * self.speed / 2.0 + self.speed * (1 - p)
    else: speed_top = speed_bottom = self.speed

    # See the notes in ArrowSprite about the derivation of this.
    if self.bottom > self.top:
      top = self.top + self.vector * int(beatsleft_top * speed_top * 64)
      bottom = self.top + self.vector * int(beatsleft_bot * speed_bottom * 64)
    else:
      top = self.top + self.vector * int(beatsleft_bot * speed_top * 64)
      bottom = self.top + self.vector * int(beatsleft_top * speed_bottom * 64)

    if bottom > 480: bottom = 480
    if top > 480: top = 480

    if self.top < self.bottom:
      bottom = max(self.top, bottom)
      top = max(self.top, top)
    else:
      bottom = min(self.top, bottom)
      top = min(self.top, top)

    pct = abs(float(top - self.top) / self.diff)
    
    holdsize = abs(bottom - top)
    if holdsize < 0: holdsize = 0
    image = pygame.Surface([self.width, holdsize + 64])
    h_img = pygame.transform.scale(self.center_image, [self.width, holdsize])
    image.blit(h_img, [0, self.width / 2])
    image.blit(self.top_image, [0, 0])
    image.blit(self.bottom_image, [0, holdsize + self.width / 2])

    self.rect, self.image = self.scale_spin_battle(image, top, pct)
    self.image.set_alpha(self.get_alpha(curtime, beatsleft_top, top))
