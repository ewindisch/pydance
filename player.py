from constants import *
from util import toRealTime
from gfxtheme import GFXTheme

import fontfx, spritelib, colors

class Player:

  def __init__(self, pid, combos, config, mode = "SINGLE"):
    self.theme = GFXTheme(mainconfig["gfxtheme"])
    self.pid = pid

    self.__dict__.update(config)

    if self.scrollstyle == 2: self.top = 236
    elif self.scrollstyle == 1: self.top = 384
    else: self.top = 64
    
    self.score = ScoringDisp(pid, "Player " + str(pid))
    if mainconfig["maxonilife"] == 0:
      self.lifebar = LifeBarDisp(pid, self.theme)
    else:
      self.lifebar = OniLifeBarDisp(pid, self.theme)
    self.holdtext = HoldJudgeDisp(self)
    self.judging_list = []
    self.total_judgings = mainconfig['totaljudgings']
    self.tempholding = [-1, -1, -1, -1]
    self.combos = combos
    self.judge = None
    self.steps = None
    self.holds = None
    self.evt = None
    self.mode = mode

  def set_song(self, steps, Judge): # FIXME factor these out
    self.steps = steps
    self.arrow_group = pygame.sprite.RenderUpdates()
    arr, arrfx = self.theme.toparrows(self.steps.bpm, self.top, self.pid)
    self.toparr = arr
    self.toparrfx = arrfx
    self.judging_list = []
    self.difficulty = steps.difficulty
    self.score.set_text(steps.difficulty)
    self.evt = None
    
    holds = self.steps.holdref
    if holds: self.holds = len(holds)
    else: self.holds = 0
    j = Judge(self.steps.bpm, self.holds,
              self.steps.feet,
              self.steps.totalarrows,
              self.difficulty,
              self.lifebar)
    self.lifebar.next_song()
    if self.judge != None: j.munch(self.judge)
    self.judge = j

  def start_song(self):
    self.steps.play()

  def get_next_events(self):
    self.evt = self.steps.get_events()
    self.fx_data = []

  def change_bpm(self, newbpm):
    if self.toparrows:
      for d in self.toparr:
        self.toparr[d].tick = toRealTime(newbpm, 1)
        self.toparrfx[d].tick = toRealTime(newbpm, 1)
    self.judge.changebpm(newbpm)

  def combo_update(self, curtime):
    self.combos.update(self.judge.combo, curtime - self.judge.steppedtime)
    self.score.update(self.judge.score)
    for i in range(self.total_judgings):
      self.judging_list[i].update(i, curtime - self.judge.steppedtime,
                                  self.judge.recentsteps[i])
    self.lifebar.update(self.judge)
    self.holdtext.update(curtime)
    
  def check_sprites(self, curtime):
    self.judge.expire_arrows(curtime)
    for text, dir, time in self.fx_data:
      if (text == "MARVELOUS" or text == "PERFECT" or text == "GREAT"):
        for spr in self.arrow_group.sprites():
          try:     # kill normal arrowsprites
            if (spr.endtime == time) and (spr.dir == dir): spr.kill()
          except: pass
          try:     # unbreak hold arrows.
            if (spr.timef1 == time) and (spr.dir == dir): spr.broken = 0
          except: pass
        self.toparrfx[dir].stepped(curtime, text)

    for spr in self.arrow_group.sprites():
      spr.update(curtime, self.judge.bpm, self.steps.lastbpmchangetime)
    for d in DIRECTIONS:
      self.toparr[d].update(curtime + self.steps.offset * 1000)
      self.toparrfx[d].update(curtime, self.judge.combo)

  def should_hold(self, direction, curtime):
    l = self.steps.holdinfo
    for i in range(len(l)):
      if l[i][0] == DIRECTIONS.index(direction):
        if ((curtime - 15.0/self.steps.playingbpm > l[i][1])
            and (curtime < l[i][2])):
          return i

# Display the score overlaying the song difficulty
class ScoringDisp(pygame.sprite.Sprite):
    def __init__(self, playernum, text):
      pygame.sprite.Sprite.__init__(self)
      self.set_text(text)
      self.image = pygame.surface.Surface((160, 48))
      self.rect = self.image.get_rect()
      self.rect.bottom = 484
      self.rect.centerx = 160 + playernum * 320

    def set_text(self, text):
      tx = FONTS[28].size(text)[0] + 2
      txt = fontfx.embfade(text, 28, 2, (tx, 24), colors.color["gray"])
      basemode = pygame.transform.scale(txt, (tx, 48))
      self.baseimage = pygame.surface.Surface((128, 48))
      self.baseimage.blit(basemode, (64 - (tx / 2), 0))
      self.oldscore = -1 # Force a refresh

    def update(self, score):
      if score != self.oldscore:
        self.image.blit(self.baseimage, (0,0))
        scoretext = FONTS[28].render(str(score), 1, (192,192,192))
        self.image.blit(scoretext, (64 - (scoretext.get_rect().size[0] / 2),
                                    13))
        self.image.set_colorkey(self.image.get_at((0, 0)), RLEACCEL)
        self.oldscore = score

class AbstractLifeBar(pygame.sprite.Sprite):
  def __init__(self, playernum, maxlife):
    pygame.sprite.Sprite.__init__(self)
    self.oldlife = 0
    self.failed = False
    self.maxlife = maxlife
    self.image = pygame.Surface((204, 28))
    self.deltas = {}

    self.failtext = fontfx.embfade("FAILED",28,3,(80,32),(224,32,32))
    self.failtext.set_colorkey(self.failtext.get_at((0,0)))
        
    self.rect = self.image.get_rect()
    self.rect.top = 30
    self.rect.left = 58 + (320 * playernum)

  def failed(self):
    return self.failed

  def update_life(self, rating):
    if self.life > 0 and self.deltas.has_key(rating):
      self.oldlife = self.life
      self.life += self.deltas[rating]
      self.life = min(self.life, self.maxlife)

  def broke_hold(self):
    pass

  def next_song(self):
    pass
      
  def update(self, judges):
    if self.failed: return False
    
    if self.life <= 0:
      self.failed = 1
      judges.failed_out = True
      self.life = 0
    elif self.life > self.maxlife:
      self.life = self.maxlife
        
    if self.life == self.oldlife: return False

    self.oldlife = self.life

    return True

# Regular lifebar
class LifeBarDisp(AbstractLifeBar):
  def __init__(self, playernum, theme):
    AbstractLifeBar.__init__(self, playernum, 100)
    self.life = 50.0
    self.displayed_life = 50.0

    self.deltas = {"V": 0.8, "P": 0.5, "G": 0.0,
                       "O": -1.0, "B": -4.0, "M": -8.0}
    self.empty = pygame.image.load(os.path.join(theme.path,
                                                'lifebar-empty.png'))
    self.full = pygame.image.load(os.path.join(theme.path,
                                               'lifebar-full.png'))

  def update(self, judges):
    if self.displayed_life < self.life:  self.displayed_life += 1
    elif self.displayed_life > self.life:  self.displayed_life -= 1

    if abs(self.displayed_life - self.life) < 1:
      self.displayed_life = self.life

    if (AbstractLifeBar.update(self, judges) == False and
        self.displayed_life <= 0): return

    if self.displayed_life < 0: self.displayed_life = 0
    self.image.blit(self.empty, (0, 0))
    self.image.set_clip((0, 0, int(202 * self.displayed_life / 100.0), 28))
    self.image.blit(self.full, (0, 0))
    self.image.set_clip()

    if self.failed:
      self.image.blit(self.failtext, (70, 2))

# Oni mode lifebar
class OniLifeBarDisp(AbstractLifeBar):

  lose_sound = pygame.mixer.Sound(os.path.join(sound_path, "loselife.ogg"))

  def __init__(self, playernum, theme):
    AbstractLifeBar.__init__(self, playernum, mainconfig["maxonilife"])

    self.life = mainconfig["maxonilife"]

    self.deltas = { "O": -1, "B": -1, "M": -1}
    self.empty = pygame.image.load(os.path.join(theme.path, 'oni-empty.png'))
    self.bar = pygame.image.load(os.path.join(theme.path, 'oni-bar.png'))

    self.width = 192 / self.maxlife
    self.bar = pygame.transform.scale(self.bar, (self.width, 20))
        
  def next_song(self):
    self.life = min(self.maxlife, self.life + 1)

  def broke_hold(self):
    OniLifeBarDisp.lose_sound.play()
    self.life -= 1
       
  def update_life(self, rating):
    AbstractLifeBar.update_life(self, rating)
    if self.life < self.oldlife: OniLifeBarDisp.lose_sound.play()

  def update(self, judges):
    if AbstractLifeBar.update(self, judges) == False: return
    
    self.image.blit(self.empty, (0, 0))
    if self.life > 0:
      for i in range(self.life):
        self.image.blit(self.bar, (6 + self.width * i, 4))

    if self.failed:
      self.image.blit(self.failtext, (70, 2) )

class HoldJudgeDisp(pygame.sprite.Sprite):
  def __init__(self, player):
    pygame.sprite.Sprite.__init__(self)

    self.space = pygame.surface.Surface((48, 24))
    self.space.fill((0, 0, 0))

    self.image = pygame.surface.Surface((320, 24))
    self.image.fill((0, 0, 0))
    self.image.set_colorkey((0, 0, 0))

    self.okimg = fontfx.shadefade("OK",28,3,(48,24),(112,224,112))
    self.ngimg = fontfx.shadefade("NG",28,3,(48,24),(224,112,112))

    self.rect = self.image.get_rect()
    if player.scrollstyle == 2: self.rect.top = 228
    elif player.scrollstyle == 1: self.rect.top = 400
    else: self.rect.top = 56

    self.rect.left = 60 + (320 * player.pid)

    self.slotnow = ['','','','']        
    self.slotold = ['','','','']
    self.slothit = [-1,-1,-1,-1]
        
  def fillin(self, curtime, direction, value):
    self.slothit[direction] = curtime
    self.slotnow[direction] = value
    
  def update(self, curtime):
    for i in range(len(self.slotnow)):
      if (curtime - self.slothit[i] > 0.5):
        self.slotnow[i]=''
      if self.slotnow[i] != self.slotold[i]:
        x = (i*72)
        if self.slotnow[i] == 'OK':
          self.image.blit(self.okimg,(x,0))
        elif self.slotnow[i] == 'NG':
          self.image.blit(self.ngimg,(x,0))
        elif self.slotnow[i] == '':
          self.image.blit(self.space,(x,0))
        self.slotold[i] = self.slotnow[i]
          
