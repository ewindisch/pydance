import os, pygame

from constants import *

class AbstractArrow(pygame.sprite.Sprite):

  # Assist mode sound samples
  samples = {}
  for d in ["u", "d", "l", "r"]:
    samples[d] = pygame.mixer.Sound(os.path.join(sound_path,
                                                 "assist-" + d + ".ogg"))

  def __init__(self, arrow, curtime, player, song):
    pygame.sprite.Sprite.__init__(self)
    
    self.dir = arrow.dir

    # NB - Making a new surface, then blitting the image in place, is 20%
    # slower than calling image.convert() (and is longer to type).
    self.image = arrow.image.convert()

    self.width = player.game.width
    self.battle = song.battle
    self.rect = self.image.get_rect()
    self.rect.left = arrow.left

    if mainconfig['assist'] and self.dir in ArrowSprite.samples:
      self.sample = ArrowSprite.samples[self.dir]
    else: self.sample = None

    if player.scrollstyle == 2:
      self.top = 236
      self.bottom = random.choice((748, -276))
      if self.top < self.bottom:
        self.suddenzone = 480 - int(64.0 * player.sudden)
        self.hiddenzone = 236 + int(64.0 * player.hidden)
      else:
        self.suddenzone = int(64.0 * player.sudden) 
        self.hiddenzone = 236 - int(64.0 * player.hidden)
    elif player.scrollstyle == 1:
      self.top = 384
      self.bottom = -128
      self.suddenzone = int(64.0 * player.sudden)
      self.hiddenzone = 384 - int(64.0 * player.hidden)
    else:
      self.top = 64
      self.bottom = 576
      self.suddenzone = 480 - int(64.0 * player.sudden)
      self.hiddenzone = 64 + int(64.0 * player.hidden)

    self.spin = player.spin
    self.scale = player.scale
    self.speed = player.speed
    self.accel = player.accel
    self.battle = song.battle

    self.diff = self.top - self.bottom
    self.baseimage = self.image

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
      onebeat = float(60.0/curbpm) # == float(60000.0/curbpm)/1000
      doomtime = endtime - curtime
      beatsleft = float(doomtime / onebeat)
    else:
      oldbpmsub = [curtime, curbpm]
      for bpmsub in lbct:
        if bpmsub[0] <= endtime:
          onefbeat = float(60.0/oldbpmsub[1]) # == float(60000.0/curbpm)/1000
          bpmdoom = bpmsub[0] - oldbpmsub[0]
          beatsleft += float(bpmdoom / onefbeat)
          oldbpmsub = bpmsub
        else: break

      onefbeat = float(60000.0/oldbpmsub[1])/1000
      bpmdoom = endtime - oldbpmsub[0]
      beatsleft += float(bpmdoom / onefbeat)

    return beatsleft

  def kill(self):
    pygame.sprite.Sprite.kill(self)
    if self.sample: self.sample.play()

class ArrowSprite(AbstractArrow):
  def __init__ (self, arrow, curtime, endtime, player, song):
    AbstractArrow.__init__(self, arrow, curtime, player, song)
    self.hold = False
    self.endtime = endtime
    self.life  = endtime - curtime

  def update(self, curtime, curbpm, lbct):
    if self.sample and curtime >= self.endtime:
      self.sample.play()
      self.sample = None

    if curtime > self.endtime + (240.0/curbpm):
      self.kill()
      return

    if curbpm < 0.0001: return # We're stopped
    # We can't just keep going if we're stopped, because the bpm change to
    # 0 is out of lbct, and so we only use curbpm, which is 0, meaning
    # we always end up at the top.

    top = self.top

    beatsleft = self.calculate_beats(curtime, self.endtime, curbpm, lbct)

    if self.accel == 1:
      p = min(1, max(0, -0.125 * (beatsleft * self.speed - 8)))
      speed = 3 * p * self.speed + self.speed * (1 - p)
    elif self.accel == 2:
      p = min(1, max(0, -0.125 * (beatsleft * self.speed - 8)))
      speed = p * self.speed / 2.0 + self.speed * (1 - p)
    else: speed = self.speed

    top = top - int(beatsleft / 8.0 * speed * self.diff)

    self.cimage = self.baseimage
    
    self.rect = self.image.get_rect()
    if top > 480: top = 480
    self.rect.top = top

    pct = abs(float(self.rect.top - self.top) / self.diff)
    
    if self.battle:
      if pct > 4.5 / 6: self.rect.centerx = self.origcenterx
      elif pct > 2.0 / 6:
        p = (pct - 2.0/6) / (2.5 / 6)
        self.rect.centerx = (1 - p) * self.goalcenterx + p * self.origcenterx
      else: self.rect.centerx = self.goalcenterx
    else: self.rect.centerx = self.centerx

    if self.scale != 1:
      arrscale = int(pct * self.width)
      arrscale = min(self.width, max(0, arrscale))
      if self.scale > 1: # grow
      	arrscale = self.width - arrscale
      self.cimage = pygame.transform.scale(self.baseimage, (arrscale, arrscale))
    
    if self.spin:
      self.image = pygame.transform.rotate(self.cimage,(self.rect.top-64)/self.spin)
    else:
      self.image = self.cimage

    alp = 256
    if self.top < self.bottom: 
      if self.rect.top > self.suddenzone:
        alp = 256 - 4 * (self.rect.top - self.suddenzone) / self.speed
      elif self.rect.top < self.hiddenzone:
        alp = 256 - 4 * (self.hiddenzone - self.rect.top) / self.speed
    else:
      if self.rect.top < self.suddenzone:
        alp = 256 - 4 * (self.suddenzone - self.rect.top) / self.speed
      elif self.rect.top > self.hiddenzone:
        alp = 256 - 4 * (self.rect.top - self.hiddenzone) / self.speed

    if alp > 256: alp = 256
    elif alp < 0: alp = 0

    self.image.set_alpha(alp)

class HoldArrowSprite(AbstractArrow):
  def __init__ (self, arrow, curtime, times, player, song):
    AbstractArrow.__init__(self, arrow, curtime, player, song)
    self.timef1 = self.endtime = times[1]
    self.hold = True
    self.timef2 = times[2]
    if self.timef2 is None: self.timef2 = self.timef1
    self.life  = self.timef2 - curtime

    self.r = 0
    self.broken = 1
    self.oimage = pygame.surface.Surface((self.width, self.width / 2))
    self.oimage.blit(self.image, (0, -self.width / 2))
    self.oimage.set_colorkey(self.oimage.get_at((0,0)), RLEACCEL)
    self.oimage2 = pygame.surface.Surface((self.width, self.width / 2))
    self.oimage2.blit(self.image, (0,0))
    self.oimage2.set_colorkey(self.oimage.get_at((0,0)), RLEACCEL)
    self.baseimage = pygame.surface.Surface((self.width, 1))
    self.baseimage.blit(self.image,(0,-self.width / 2 + 1))

  def update(self,curtime,curbpm,lbct):
    if self.sample and curtime >= self.timef1:
      self.sample.play()
      self.sample = None

    if curtime > self.timef2:
      self.kill()
      return

    if curbpm < 0.0001: return # We're stopped

    top = self.top
    bottom = self.top

    beatsleft_top = self.calculate_beats(curtime, self.timef1, curbpm, lbct)
    beatsleft_bot = self.calculate_beats(curtime, self.timef2, curbpm, lbct)

    if self.accel == 1:
      p = min(1, max(0, -0.125 * (beatsleft_top * self.speed - 8)))
      speed_top = 3 * p * self.speed + self.speed * (1 - p)
      p = min(1, max(0, -0.125 * (beatsleft_bottom * self.speed - 8)))
      speed_bottom = 3 * p * self.speed + self.speed * (1 - p)
    elif self.accel == 2:
      p = min(1, max(0, -0.125 * (beatsleft_top * self.speed - 8)))
      speed_top = p * self.speed / 2.0 + self.speed * (1 - p)
      p = min(1, max(0, -0.125 * (beatsleft_bottom * self.speed - 8)))
      speed_bottom = p * self.speed / 2.0 + self.speed * (1 - p)
    else: speed_top = speed_bottom = self.speed

    top = top - int(beatsleft_top / 8.0 * self.diff * speed_top)
    bottom = bottom - int(beatsleft_bot / 8.0 * self.diff * speed_bottom)

    if bottom > 480: bottom = 480

    if self.top < self.bottom and bottom < 64:  bottom = 64
    self.rect.bottom = bottom
 
    if top > 480: top = 480
    if self.top < self.bottom and top < 64: top = 64

    if self.top < self.bottom: self.rect.top = top
    else: self.rect.top = bottom
    
    holdsize = abs(bottom - top)
    if holdsize < 0:
      holdsize = 0
    self.cimage = pygame.surface.Surface((self.width, holdsize + self.width))
    self.cimage.set_colorkey(self.cimage.get_at((0, 0)), RLEACCEL)
    self.cimage.blit(pygame.transform.scale(self.baseimage,
                                            (self.width, holdsize)),
                     (0, self.width / 2))
    self.cimage.blit(self.oimage2,(0,0))
    self.cimage.blit(self.oimage,(0,holdsize + self.width / 2))

    self.rect = self.image.get_rect()
    if top > 480: top = 480
    self.rect.top = top

    pct = abs(float(self.rect.top - self.top) / self.diff)
    
    if self.battle:
      if pct > 4.5 / 6: self.rect.centerx = self.origcenterx
      elif pct > 2.0 / 6:
        p = (pct - 2.0/6) / (2.5 / 6)
        self.rect.centerx = (1 - p) * self.goalcenterx + p * self.origcenterx
      else: self.rect.centerx = self.goalcenterx
    else: self.rect.centerx = self.centerx

    if self.scale != 1:
      arrscale = int(pct * self.width)
      if self.scale > 1: # grow
      	arrscale = self.width - arrscale
      arrscale = min(self.width, max(0, arrscale))
      self.cimage = pygame.transform.scale(self.baseimage, (arrscale, arrscale))
    
    if self.spin:
      self.image = pygame.transform.rotate(self.cimage,(self.rect.top - 64)/self.spin)
    else:
      self.image = self.cimage

    alp = 256
    if self.top < self.bottom: 
      if self.rect.top > self.suddenzone:
        alp = 256 - 4 * (self.rect.top - self.suddenzone) / self.speed
      elif self.rect.top < self.hiddenzone:
        alp = 256 - 4 * (self.hiddenzone - self.rect.top) / self.speed
    else:
      if self.rect.bottom < self.suddenzone:
        alp = 256 - 4 * (self.suddenzone - self.rect.bottom) / self.speed
      elif self.rect.bottom > self.hiddenzone:
        alp = 256 - 4 * (self.rect.bottom - self.hiddenzone) / self.speed

    if alp > 256: alp = 256
    elif alp < 0: alp = 0

    if self.broken and (curtime > self.timef1+(0.00025*(60000.0/curbpm))):
      alp /= 2

    self.image.set_alpha(alp)
