from constants import *
from util import toRealTime
from gfxtheme import GFXTheme
from judge import Judge

from pygame.sprite import RenderUpdates, RenderClear

import fontfx, colors, steps, random
import lifebars

# This class keeps an ordered list of sprites in addition to the dict,
# so we can draw in the order the sprites were added.
class OrderedRenderUpdates(RenderClear):
  def __init__(self, group = ()):
    self.spritelist = []
    RenderClear.__init__(self, group)

  def sprites(self):
    return list(self.spritelist)

  # A patch has been sent to Pete in the hopes that we can avoid overriding
  # this function, and only override add_internal (pygame 1.5.6)
  def add(self, sprite):
    has = self.spritedict.has_key
    if hasattr(sprite, '_spritegroup'):
      for sprite in sprite.sprites():
        if not has(sprite):
          self.add_internal(sprite)
          sprite.add_internal(self) 
    else:
      try: len(sprite)
      except (TypeError, AttributeError):
        if not has(sprite):
          self.add_internal(sprite)
          sprite.add_internal(self) 
      else:
        for sprite in sprite:
          if not has(sprite):
            self.add_internal(sprite)
            sprite.add_internal(self) 

  def add_internal(self, sprite):
    RenderClear.add_internal(self, sprite)
    self.spritelist.append(sprite)

  def remove_internal(self, sprite):
    RenderClear.remove_internal(self, sprite)
    self.spritelist.remove(sprite)

  def draw(self, surface):
    spritelist = self.spritelist
    spritedict = self.spritedict
    surface_blit = surface.blit
    dirty = self.lostsprites
    self.lostsprites = []
    dirty_append = dirty.append
    for s in spritelist:
      r = spritedict[s]
      newrect = surface_blit(s.image, s.rect)
      if r is 0:
        dirty_append(newrect)
      else:
        if newrect.colliderect(r):
          dirty_append(newrect.union(r))
        else:
          dirty_append(newrect)
      spritedict[s] = newrect
    return dirty

# Display the score overlaying the song difficulty
class ScoringDisp(pygame.sprite.Sprite):
  def __init__(self, playernum, text, game):
    pygame.sprite.Sprite.__init__(self)
    self.score = 0
    self.set_text(text)
    self.image = pygame.surface.Surface((160, 48))
    self.rect = self.image.get_rect()
    self.rect.bottom = 484
    self.rect.centerx = game.sprite_center + playernum * game.player_offset

  def set_text(self, text):
    tx = FONTS[28].size(text)[0] + 2
    txt = fontfx.embfade(text, 28, 2, (tx, 24), colors.color["gray"])
    basemode = pygame.transform.scale(txt, (tx, 48))
    self.baseimage = pygame.surface.Surface((128, 48))
    self.baseimage.blit(basemode, (64 - (tx / 2), 0))
    self.oldscore = -1 # Force a refresh

  def update(self):
    if self.score != self.oldscore:
      self.image.blit(self.baseimage, (0,0))
      scoretext = FONTS[28].render(str(int(self.score)), 1, (192,192,192))
      self.image.blit(scoretext, (64 - (scoretext.get_rect().size[0] / 2),
                                    13))
      self.image.set_colorkey(self.image.get_at((0, 0)), RLEACCEL)
      self.oldscore = self.score

class HoldJudgeDisp(pygame.sprite.Sprite):
  def __init__(self, pid, player, game):
    pygame.sprite.Sprite.__init__(self)
    self.game = game

    self.space = pygame.surface.Surface((48, 24))
    self.space.fill((0, 0, 0))

    self.image = pygame.surface.Surface((len(game.dirs) * game.width, 24))
    self.image.fill((0, 0, 0))
    self.image.set_colorkey((0, 0, 0), RLEACCEL)

    self.okimg = fontfx.shadefade("OK", 28, 3, (48, 24), (112, 224, 112))
    self.ngimg = fontfx.shadefade("NG", 28, 3, (48, 24), (224, 112, 112))

    self.rect = self.image.get_rect()
    if player.scrollstyle == 2: self.rect.top = 228
    elif player.scrollstyle == 1: self.rect.top = 400
    else: self.rect.top = 56

    self.rect.left = game.left_off(pid) + pid * game.player_offset

    self.slotnow = [''] * len(game.dirs)
    self.slotold = list(self.slotnow)
    self.slothit = [-1] * len(game.dirs)
        
  def fillin(self, curtime, direction, value):
    self.slothit[direction] = curtime
    self.slotnow[direction] = value
    
  def update(self, curtime):
    for i in range(len(self.slotnow)):
      if (curtime - self.slothit[i] > 0.5):
        self.slotnow[i]=''
      if self.slotnow[i] != self.slotold[i]:
        x = (i * self.game.width)
        if self.slotnow[i] == 'OK':
          self.image.blit(self.okimg,(x,0))
        elif self.slotnow[i] == 'NG':
          self.image.blit(self.ngimg,(x,0))
        elif self.slotnow[i] == '':
          self.image.blit(self.space,(x,0))
        self.slotold[i] = self.slotnow[i]

class JudgingDisp(pygame.sprite.Sprite):
  def __init__(self, playernum, game):
    pygame.sprite.Sprite.__init__(self)

    self.sticky = mainconfig['stickyjudge']
    self.needsupdate = 1
    self.stepped = 0
    self.laststep = 0
    self.judgetype = " "
    self.oldzoom = -1
    self.bottom = 320
    self.centerx = game.sprite_center + (playernum * game.player_offset)
        
    # prerender the text for judging for a little speed boost
    tx = FONTS[48].size("MARVELOUS")[0]+4
    self.marvelous = fontfx.shadefade("MARVELOUS",48,4,(tx,40),(224,224,224))
    tx = FONTS[48].size("PERFECT")[0]+4
    self.perfect   = fontfx.shadefade("PERFECT"  ,48,4,(tx,40),(224,224, 32))
    tx = FONTS[48].size("GREAT")[0]+4
    self.great     = fontfx.shadefade("GREAT"    ,48,4,(tx,40),( 32,224, 32))
    tx = FONTS[48].size("OK")[0]+4
    self.ok        = fontfx.shadefade("OK"       ,48,4,(tx,40),( 32, 32,224))
    tx = FONTS[48].size("BOO")[0]+4
    self.boo      = fontfx.shadefade("BOO"      ,48,4,(tx,40),( 96, 64, 32))
    tx = FONTS[48].size("MISS")[0]+4
    self.miss      = fontfx.shadefade("MISS"     ,48,4,(tx,40),(224, 32, 32))
    self.space     = FONTS[48].render( " ",       1, (  0,   0,   0) )

    self.marvelous.set_colorkey(self.marvelous.get_at((0,0)), RLEACCEL)
    self.perfect.set_colorkey(self.perfect.get_at((0,0)), RLEACCEL)
    self.great.set_colorkey(self.great.get_at((0,0)), RLEACCEL)
    self.ok.set_colorkey(self.ok.get_at((0,0)), RLEACCEL)
    self.boo.set_colorkey(self.boo.get_at((0,0)), RLEACCEL)
    self.miss.set_colorkey(self.miss.get_at((0,0)), RLEACCEL)
    
    self.image = self.space

  def judge(self, curtime, judgetype):
    self.laststep = curtime
    self.judgetype = judgetype

  def update(self, curtime):
    self.laststep = min(curtime, self.laststep)
    steptimediff = curtime - self.laststep

    if steptimediff < 0.5 or (self.judgetype == ('MISS' or ' ')):
      if   self.judgetype == "MARVELOUS": self.image = self.marvelous
      elif self.judgetype == "PERFECT": self.image = self.perfect
      elif self.judgetype == "GREAT": self.image = self.great
      elif self.judgetype == "OK": self.image = self.ok
      elif self.judgetype == "BOO": self.image = self.boo
      elif self.judgetype == "MISS": self.image = self.miss
      elif self.judgetype == " ": self.image = self.space

      zoomzoom = steptimediff

      if zoomzoom != self.oldzoom:
        self.needsupdate = True
        if (steptimediff > 0.36) and (self.sticky == 0) and self.stepped:
          self.image = self.space
          self.stepped = 0

        if steptimediff > 0.2: zoomzoom = 0.2
        self.image = pygame.transform.rotozoom(self.image, 0, 1-(zoomzoom*2))
        self.stepped = 1

    if self.needsupdate:
      self.rect = self.image.get_rect()
      self.rect.centerx = self.centerx
      self.rect.bottom = self.bottom
      self.image.set_colorkey(self.image.get_at((0,0)), RLEACCEL)
      self.needsupdate = False

class ComboDisp(pygame.sprite.Sprite):
  def __init__(self, playernum, game):
    pygame.sprite.Sprite.__init__(self,)
    self.sticky = mainconfig['stickycombo']
    self.lowcombo = mainconfig['lowestcombo']
    self.combo = 0
    self.bestcombo = 0
    self.laststep = 0
    self.centerx = game.sprite_center + (game.player_offset * playernum)
    self.top = 320
    
    fonts = []
    for x in range(11, 0, -1):
      fonts.append(pygame.font.Font(None, 28+int(x*1.82)))

    self.words = []
    for f in fonts:
      render = []
      for w in ('0','1','2','3','4','5','6','7','8','9','x COMBO'):
        img1 = f.render(w, 1, (16, 16, 16))
        img2 = f.render(w, 1, (224, 224, 224))
        img3 = pygame.Surface(img1.get_size())
        img3.blit(img1, (-2, 2))
        img3.blit(img1, (2, -2))
        img3.blit(img2, (0, 0))
        img3.set_colorkey(img3.get_at((0, 0)), RLEACCEL)
        render.append(img3)
      self.words.append(render)
    self.space = pygame.surface.Surface((0,0)) #make a blank image
    self.image = self.space

  def broke(self, time):
    self.laststep = time
    self.combo = 0

  def addcombo(self, time):
    self.laststep = time
    self.combo += 1
    if self.combo > self.bestcombo: self.bestcombo = self.combo

  def update(self, curtime):
    self.laststep = min(curtime, self.laststep)
    steptimediff = curtime - self.laststep

    if steptimediff < 0.36 or self.sticky:
      self.drawcount = self.combo
      drawsize = min(int(steptimediff*50), len(self.words)-1)
      if drawsize < 0: drawsize = 0
    else:
      self.drawcount = 0

    if self.drawcount >= self.lowcombo:
      render = self.words[drawsize]
      width = render[-1].get_width()
      thousands = self.drawcount /1000
      hundreds = self.drawcount / 100
      tens = self.drawcount / 10
      ones = self.drawcount % 10
      #get width
      if thousands:
        thousands = render[thousands%10]
        width += thousands.get_width()      
      if hundreds:
        hundreds = render[hundreds%10]
        width += hundreds.get_width()
      if tens:
        tens = render[tens%10]
        width += tens.get_width()
      ones = render[ones]
      width += ones.get_width()
      height = render[-1].get_height()
      self.image = pygame.surface.Surface((width,height))
      self.image.set_colorkey(ones.get_at((0, 0)), RLEACCEL)
      left = 0		      
      #render
      if thousands:
        self.image.blit(thousands, (left,0))
        left+= thousands.get_width()
      if hundreds:
        self.image.blit(hundreds, (left, 0))
        left += hundreds.get_width()
      if tens:
        self.image.blit(tens, (left, 0))
        left += tens.get_width()
      self.image.blit(ones, (left, 0))
      left += ones.get_width()
      r = self.image.blit(render[-1], (left, 0))
    else :
      self.image = self.space #display the blank image

    self.rect = self.image.get_rect()
    self.rect.top = self.top
    self.rect.centerx = self.centerx

class ArrowSprite(pygame.sprite.Sprite):

  # Assist mode sound samples
  samples = {}
  for d in ["u", "d", "l", "r"]:
    samples[d] = pygame.mixer.Sound(os.path.join(sound_path,
                                                 "assist-" + d + ".ogg"))
  
  def __init__ (self, arrow, curtime, endtime, player, song):
    pygame.sprite.Sprite.__init__(self)
    self.endtime = endtime
    self.life  = endtime - curtime
    self.curalpha = -1
    self.dir = arrow.dir
    self.image = arrow.image.convert()
    self.width = player.game.width
    self.battle = song.battle
    self.rect = arrow.image.get_rect()
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

    self.diff = self.top - self.bottom

    self.bimage = self.image
    self.arrowspin = player.spin
    self.arrowscale = player.scale
    self.speed = player.speed
    self.accel = player.accel

    self.goalcenterx = self.rect.centerx
    if self.battle:
      self.rect.left = 320 - int(player.game.width *
                                 (len(player.game.dirs) / 2.0 -
                                  player.game.dirs.index(self.dir)))
      self.origcenterx = self.centerx = self.rect.centerx
    else: self.centerx = self.rect.centerx = self.goalcenterx

  def update (self, curtime, curbpm, lbct):
    if (self.sample) and (curtime >= self.endtime -0.0125):
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

    beatsleft = 0

    if len(lbct) == 0:
      onebeat = float(60.0/curbpm) # == float(60000.0/curbpm)/1000
      doomtime = self.endtime - curtime
      beatsleft = float(doomtime / onebeat)
    else:
      oldbpmsub = [curtime, curbpm]
      for bpmsub in lbct:
        if bpmsub[0] <= self.endtime:
          onefbeat = float(60.0/oldbpmsub[1]) # == float(60000.0/curbpm)/1000
          bpmdoom = bpmsub[0] - oldbpmsub[0]
          beatsleft += float(bpmdoom / onefbeat)
          oldbpmsub = bpmsub
        else: break

      onefbeat = float(60000.0/oldbpmsub[1])/1000
      bpmdoom = self.endtime - oldbpmsub[0]
      beatsleft += float(bpmdoom / onefbeat)

    if self.accel == 1:
      p = min(1, max(0, -0.125 * (beatsleft * self.speed - 8)))
      speed = 3 * p * self.speed + self.speed * (1 - p)
    elif self.accel == 2:
      p = min(1, max(0, -0.125 * (beatsleft * self.speed - 8)))
      speed = p * self.speed / 2.0 + self.speed * (1 - p)
    else: speed = self.speed

    top = top - int(beatsleft / 8.0 * speed * self.diff)

    self.cimage = self.bimage
    
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

    if self.arrowscale != 1:
      arrscale = int(pct * self.width)
      arrscale = min(self.width, max(0, arrscale))
      if self.arrowscale > 1: # grow
      	arrscale = self.width - arrscale
      self.cimage = pygame.transform.scale(self.bimage, (arrscale, arrscale))
    
    if self.arrowspin:
      self.image = pygame.transform.rotate(self.cimage,(self.rect.top-64)/self.arrowspin)
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

    if alp != self.image.get_alpha(): self.image.set_alpha(alp)

class HoldArrowSprite(pygame.sprite.Sprite):
  def __init__ (self, arrow, curtime, times, player, song):
    pygame.sprite.Sprite.__init__(self)
    self.timef1 = times[1]
    self.timef2 = times[2]
    if self.timef2 is None: self.timef2 = self.timef1
    self.image = arrow.image.convert()
    self.rect = arrow.image.get_rect()
    self.rect.left = arrow.left
    self.life  = self.timef2 - curtime
    self.battle = song.battle
    self.width = player.game.width
    if player.scrollstyle == 2:
      self.top = 236
      self.bottom = random.choice((748, -276))
      if self.top < self.bottom:
        self.suddenzone = 480 - int(64.0 * player.sudden)
        self.hiddenzone = 236 + int(64.0 * player.hidden)
      else:
        self.suddenzone = 64 + int(64.0 * player.sudden) 
        self.hiddenzone = 300 - int(64.0 * player.hidden)
    elif player.scrollstyle == 1:
      self.top = 384
      self.bottom = -128
      self.suddenzone = 64 + int(64.0 * player.sudden)
      self.hiddenzone = 448 - int(64.0 * player.hidden)
    else:
      self.top = 64
      self.bottom = 576
      self.suddenzone = 480 - int(64.0 * player.sudden)
      self.hiddenzone = 64 + int(64.0 * player.hidden)

    self.diff = self.top - self.bottom
    self.curalpha = -1
    self.dir = arrow.dir
    self.playedsound = None
    if mainconfig['assist'] and self.dir in ArrowSprite.samples:
      self.sample = ArrowSprite.samples[self.dir]
    else:
      self.playedsound = 1
    self.r = 0
    self.broken = 1
    self.oimage = pygame.surface.Surface((self.width, self.width / 2))
    self.oimage.blit(self.image, (0, -self.width / 2))
    self.oimage.set_colorkey(self.oimage.get_at((0,0)), RLEACCEL)
    self.oimage2 = pygame.surface.Surface((self.width, self.width / 2))
    self.oimage2.blit(self.image, (0,0))
    self.oimage2.set_colorkey(self.oimage.get_at((0,0)), RLEACCEL)
    self.bimage = pygame.surface.Surface((self.width, 1))
    self.bimage.blit(self.image,(0,-self.width / 2 + 1))

    self.arrowspin = player.spin
    self.arrowscale = player.scale
    self.speed = player.speed
    self.accel = player.accel
    
    self.goalcenterx = self.rect.centerx
    if self.battle:
      self.rect.left = 320 - int(player.game.width *
                                 (len(player.game.dirs) / 2.0 -
                                  player.game.dirs.index(self.dir)))
      self.origcenterx = self.centerx = self.rect.centerx
    else: self.centerx = self.rect.centerx = self.goalcenterx

  def update(self,curtime,curbpm,lbct):
    if (self.playedsound is None) and (curtime >= self.timef1 -0.0125):
      self.sample.play()
      self.playedsound = 1

    if curtime > self.timef2:
      self.kill()
      return
      
    if curbpm < 0.0001: return # We're stopped

    top = self.top
    bottom = self.top

    beatsleft_top = 0
    beatsleft_bottom = 0

    if len(lbct) == 0:
      onebeat = float(60.0/curbpm)
      doomtime = self.timef1 - curtime
      if self.broken == 0 and doomtime < 0: doomtime = 0
      beatsleft_top = float(doomtime / onebeat)

      doomtime = self.timef2 - curtime
      beatsleft_bottom = float(doomtime / onebeat)
    else:
      oldbpmsub = [curtime, curbpm]
      bpmbeats = 0
      for bpmsub in lbct:
        if bpmsub[0] <= self.timef1:
          onefbeat = float(60.0/oldbpmsub[1])
          bpmdoom = bpmsub[0] - oldbpmsub[0]
          beatsleft_top += float(bpmdoom / onefbeat)
          oldbpmsub = bpmsub
        else: break

      onefbeat = float(60.0/oldbpmsub[1])
      bpmdoom = self.timef1 - oldbpmsub[0]
      beatsleft_top += float(bpmdoom / onefbeat)

      oldbpmsub = [curtime, curbpm]
      for bpmsub in lbct:
        if bpmsub[0] <= self.timef2:
          onefbeat = float(60.0/oldbpmsub[1])
          bpmdoom = bpmsub[0] - oldbpmsub[0]
          beatsleft_bottom += float(bpmdoom / onefbeat)
          oldbpmsub = bpmsub
        else: break

      onefbeat = float(60.0/oldbpmsub[1])
      bpmdoom = self.timef2 - oldbpmsub[0]
      beatsleft_bottom += float(bpmdoom / onefbeat)

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
    bottom = bottom - int(beatsleft_bottom / 8.0 * self.diff * speed_bottom)

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
    self.cimage.blit(pygame.transform.scale(self.bimage,
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

    if self.arrowscale != 1:
      arrscale = int(pct * self.width)
      if self.arrowscale > 1: # grow
      	arrscale = self.width - arrscale
      arrscale = min(self.width, max(0, arrscale))
      self.cimage = pygame.transform.scale(self.bimage, (arrscale, arrscale))
    
    if self.arrowspin:
      self.image = pygame.transform.rotate(self.cimage,(self.rect.top - 64)/self.arrowspin)
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

    if alp != self.image.get_alpha(): self.image.set_alpha(alp)

class Player(object):

  def __init__(self, pid, config, songconf, game):
    self.theme = GFXTheme(mainconfig.get("%s-theme" % game.theme, "default"),
                          pid, game)
    self.pid = pid

    self.__dict__.update(config)

    if self.scrollstyle == 2: self.top = 236
    elif self.scrollstyle == 1: self.top = 384
    else: self.top = 64
    
    self.score = ScoringDisp(pid, "Player " + str(pid), game)
    self.judging_disp = JudgingDisp(self.pid, game)
    Lifebar = lifebars.bars[songconf["lifebar"]]
    self.lifebar = Lifebar(pid, self.theme, songconf, game)
    self.judging_list = []
    self.combos = ComboDisp(pid, game)
    
    self.game = game

    if self.game.double: self.judge = [None, None]
    else: self.judge = None

  def set_song(self, song, diff, lyrics):
    self.difficulty = diff
    self.score.set_text(diff)

    if self.game.double:
      self.holding = [[-1] * len(self.game.dirs), [-1] * len(self.game.dirs)]
      if self.transform == 1:
        # In double mirror mode, we have to swap the step sets for this
        # player's pids. This ensures, e.g., 1R becomes 2L, rather than 1L.
        self.steps = [steps.Steps(song, diff, self, self.pid * 2 + 1,
                                  lyrics, self.game.name),
                      steps.Steps(song, diff, self, self.pid * 2,
                                  lyrics, self.game.name)]
      else:
        self.steps = [steps.Steps(song, diff, self, self.pid * 2,
                                  lyrics, self.game.name),
                      steps.Steps(song, diff, self, self.pid * 2 + 1,
                                  lyrics, self.game.name)]

      self.length = max(self.steps[0].length, self.steps[1].length)

      self.ready = min(self.steps[0].ready, self.steps[1].ready)

      arr1, arrfx1 = self.theme.toparrows(self.steps[0].bpm,
                                          self.top, self.pid * 2)
      arr2, arrfx2 = self.theme.toparrows(self.steps[1].bpm,
                                          self.top, self.pid * 2 + 1)
      self.arrows = [self.theme.arrows(self.pid * 2),
                     self.theme.arrows(self.pid * 2 + 1)]
      self.toparr = [arr1, arr2]
      self.toparrfx = [arrfx1, arrfx2]
      self.holdtext = [HoldJudgeDisp(self.pid * 2, self, self.game),
                       HoldJudgeDisp(self.pid * 2 + 1, self, self.game)]

      for i in range(2):
        if self.steps[i].holdref: holds = len(self.steps[i].holdref)
        else: holds = 0
        j = Judge(self.steps[i].bpm, holds, self.combos, self.score,
                  self.judging_disp, self.steps[i].feet,
                  self.steps[i].totalarrows, self.difficulty, self.lifebar)
        if self.judge[i] != None: j.munch(self.judge[i])
        self.judge[i] = j

    else:
      self.holding = [-1] * len(self.game.dirs)
      self.steps = steps.Steps(song, diff, self, self.pid, lyrics,
                               self.game.name)
      self.length = self.steps.length
      self.ready = self.steps.ready
      arr, arrfx = self.theme.toparrows(self.steps.bpm, self.top, self.pid)
      self.holdtext = HoldJudgeDisp(self.pid, self, self.game)
      self.toparr = arr
      self.toparrfx = arrfx
      self.arrows = self.theme.arrows(self.pid)

      if self.steps.holdref: holds = len(self.steps.holdref)
      else: holds = 0
      j = Judge(self.steps.bpm, holds, self.combos, self.score,
                self.judging_disp, self.steps.feet, self.steps.totalarrows,
                self.difficulty, self.lifebar)
      if self.judge != None: j.munch(self.judge)
      self.judge = j

    self.lifebar.next_song()

  def get_judge(self):
    if self.game.double:
      # judge[0] may be None, if no songs were found in Endless mode.
      if self.judge[0]: self.judge[0].munch(self.judge[1])
      return self.judge[0]
    else: return self.judge

  def start_song(self):
    self.toparr_group = RenderUpdates()
    self.fx_group = RenderUpdates()
    self.text_group = RenderUpdates()
    self.text_group.add([self.score, self.lifebar, self.judging_disp])
    self.text_group.add(self.holdtext)

    if mainconfig["showcombo"]: self.text_group.add(self.combos)

    if self.game.double:
      self.arrow_group = [OrderedRenderUpdates(),
                          OrderedRenderUpdates()]

      for i in range(2):
        self.steps[i].play()
        for d in self.game.dirs:
          if mainconfig["explodestyle"] > -1:
            self.toparrfx[i][d].add(self.fx_group)
          if not self.dark: self.toparr[i][d].add(self.toparr_group)
      self.sprite_groups = [self.toparr_group, self.arrow_group[0],
                            self.arrow_group[1], self.fx_group,
                            self.text_group]
    else:
      self.steps.play()
      self.arrow_group = OrderedRenderUpdates()
      for d in self.game.dirs:
        if mainconfig["explodestyle"] > -1: self.toparrfx[d].add(self.fx_group)
        if not self.dark: self.toparr[d].add(self.toparr_group)
      self.sprite_groups = [self.toparr_group, self.arrow_group,
                            self.fx_group, self.text_group]

  def get_next_events(self, song):
    if self.game.double:
      self.fx_data = [[], []]
      for i in range(2):
        self._get_next_events(song, self.arrow_group[i], self.arrows[i],
                              self.steps[i], self.judge[i])
    else:
      self.fx_data = []
      self._get_next_events(song, self.arrow_group, self.arrows, self.steps,
                            self.judge)

  def _get_next_events(self, song, arrows, arrow_gfx, steps, judge):
    evt = steps.get_events()
    if evt is not None:
      events, nevents, time, bpm = evt
      for ev in events:
        if ev.feet:
          for (dir, num) in zip(self.game.dirs, ev.feet):
            if num & 1: judge.handle_arrow(dir, ev.when)

      newsprites = []
      for ev in nevents:
        if ev.feet:
          for (dir, num) in zip(self.game.dirs, ev.feet):
            dirstr = dir + repr(int(ev.color) % self.colortype)
            if num & 1 and not num & 2:
              ns = ArrowSprite(arrow_gfx[dirstr], time, ev.when, self, song)
              newsprites.append(ns)
            elif num & 2:
              holdindex = steps.holdref.index((self.game.dirs.index(dir),
                                               ev.when))
              ns = HoldArrowSprite(arrow_gfx[dirstr], time,
                                   steps.holdinfo[holdindex], self, song)
              newsprites.append(ns)
                       
      arrows.add(newsprites)



  def csl_update(self, curtime, judge, holdtext):
    self.combos.update(curtime)
    self.score.update()
    self.judging_disp.update(curtime)
    self.lifebar.update(judge)
    holdtext.update(curtime)
    
  def check_sprites(self, curtime, arrows, steps, fx_data, toparr, toparrfx, judge):
    judge.expire_arrows(curtime)
    for text, dir, time in fx_data:
      if (text == "MARVELOUS" or text == "PERFECT" or text == "GREAT"):
        for spr in arrows.sprites():
          try:     # kill normal arrowsprites
            if (spr.endtime == time) and (spr.dir == dir): spr.kill()
          except: pass
          try:     # unbreak hold arrows.
            if (spr.timef1 == time) and (spr.dir == dir): spr.broken = 0
          except: pass
          toparrfx[dir].stepped(curtime, text)

    arrows.update(curtime, judge.bpm, steps.lastbpmchangetime)
    for d in self.game.dirs:
      toparr[d].update(curtime + steps.offset * 1000)
      toparrfx[d].update(curtime, judge.combos.combo)

  def should_hold(self, steps, direction, curtime):
    l = steps.holdinfo
    for i in range(len(l)):
      if l[i][0] == self.game.dirs.index(direction):
        if ((curtime - 15.0/steps.playingbpm > l[i][1])
            and (curtime < l[i][2])):
          return i

  def check_holds(self, curtime, arrows, steps, judge, toparrfx, holding, holdtext, pid):
    # FIXME THis needs to go away
    keymap_kludge = { "u": E_UP, "k": E_UPLEFT, "z": E_UPRIGHT,
                      "d": E_DOWN, "l": E_LEFT, "r": E_RIGHT,
                      "g": E_DOWNRIGHT, "w": E_DOWNLEFT, "c": E_CENTER }

    for dir in self.game.dirs:
      toparrfx[dir].holding(0)
      current_hold = self.should_hold(steps, dir, curtime)
      dir_idx = self.game.dirs.index(dir)
      if current_hold is not None:
        if event.states[(pid, keymap_kludge[dir])]:
          if judge.holdsub[holding[dir_idx]] != -1:
            toparrfx[dir].holding(1)
          holding[dir_idx] = current_hold
        else:
          judge.botchedhold(current_hold)
          holdtext.fillin(curtime, dir_idx, "NG")
          botchdir, timef1, timef2 = steps.holdinfo[current_hold]
          # FIXME it's slow.
          for spr in arrows.sprites():
            try:
              if (spr.timef1 == timef1 and
                  self.game.dirs.index(spr.dir) == dir_idx):
                spr.broken = True
                break
            except: pass
      else:
        if holding[dir_idx] > -1:
          if judge.holdsub[holding[dir_idx]] != -1:
            holding[dir_idx] = -1
            holdtext.fillin(curtime, dir_idx, "OK")

  def handle_key(self, ev, time):
    if ev[1] not in self.game.dirs: return

    if self.game.double:
      pid = ev[0] & 1
      self.toparr[pid][ev[1]].stepped(1, time + self.steps[pid].soffset)
      self.fx_data[pid].append(self.judge[pid].handle_key(ev[1], time))
    else:
      self.toparr[ev[1]].stepped(1, time + self.steps.soffset)
      self.fx_data.append(self.judge.handle_key(ev[1], time))

  def check_bpm_change(self, time, steps, judge, toparr, toparrfx):
    if len(steps.lastbpmchangetime) > 0:
      if time >= steps.lastbpmchangetime[0][0]:
        newbpm = steps.lastbpmchangetime[0][1]
        if not self.dark:
          for d in toparr:
            toparr[d].tick = toRealTime(newbpm, 1)
            toparrfx[d].tick = toRealTime(newbpm, 1)
        judge.changebpm(newbpm)
        steps.lastbpmchangetime.pop(0)

  def clear_sprites(self, screen, bg):
    for g in self.sprite_groups: g.clear(screen, bg)

  def game_loop(self, time, screen):
    if self.game.double:
      for i in range(2):
        self.check_holds(time, self.arrow_group[i], self.steps[i],
                         self.judge[i], self.toparrfx[i], self.holding[i],
                         self.holdtext[i], self.pid * 2 + i)
        self.check_bpm_change(time, self.steps[i], self.judge[i],
                              self.toparr[i], self.toparrfx[i])
        self.check_sprites(time, self.arrow_group[i], self.steps[i],
                           self.fx_data[i], self.toparr[i], self.toparrfx[i],
                           self.judge[i])
        self.csl_update(time, self.judge[i], self.holdtext[i])
    else:
      self.check_holds(time, self.arrow_group, self.steps, self.judge,
                       self.toparrfx, self.holding, self.holdtext, self.pid)
      self.check_bpm_change(time, self.steps, self.judge, self.toparr,
                            self.toparrfx)
      self.check_sprites(time, self.arrow_group, self.steps, self.fx_data,
                         self.toparr, self.toparrfx, self.judge)
      self.csl_update(time, self.judge, self.holdtext)

    rects = []
    for g in self.sprite_groups: rects.extend(g.draw(screen))
    return rects
