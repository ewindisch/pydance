from constants import *
from gfxtheme import GFXTheme

import fontfx, spritelib

class Player:
  def __init__(self, pid, holdtext, combos, mode = "SINGLE"):
    self.theme = GFXTheme(mainconfig["gfxtheme"])
    if mainconfig["reversescroll"]:
      self.arrow_top = 408
      self.arrow_bot = int(-64 - (mainconfig["scrollspeed"] - 1) * 576)
    else:
      self.arrow_top = 64
      self.arrow_bot = int(576 * mainconfig["scrollspeed"])
    self.arrow_diff = float(self.arrow_top - self.arrow_bot)
    self.pid = pid
    self.score = ScoringDisp(pid, "Player " + str(pid))
    self.lifebar = LifeBarDisp(pid, self.theme)
    self.holdtext = holdtext
    self.arrow_group = spritelib.RenderLayered()
    self.judging_list = []
    self.total_judgings = mainconfig['totaljudgings']
    self.tempholding = [-1, -1, -1, -1]
    self.combos = combos
    self.judge = None
    self.song = None
    self.holds = None
    self.evt = None
    self.mode = mode

    self.sudden = mainconfig['sudden']
    self.hidden = mainconfig['hidden']

  def set_song(self, song, diff, Judge): # FIXME factor these out
    self.song = song
    arr, arrfx = self.theme.toparrows(self.song.bpm, self.arrow_top, self.pid)
    self.toparr = arr
    self.toparrfx = arrfx
    self.judging_list = []
    self.difficulty = diff
    self.score.set_text(diff)
    difflist = self.song.modediff[self.mode]
    self.holds = len(self.song.holdref[self.song.modediff[self.mode].index(self.difficulty)])
    j = Judge(self.song.bpm, self.holds,
              self.song.modeinfo[self.mode][difflist.index(self.difficulty)][1],
              self.song.totarrows[self.difficulty],
              self.difficulty)
    if self.judge != None: j.munch(self.judge)
    self.judge = j

  def start_song(self):
    self.song.play(self.mode, self.difficulty, self.pid == 0)

  def get_next_events(self):
    self.evt = self.song.get_events()
    self.fx_data = []

  def change_bpm(self, newbpm):
    if mainconfig['showtoparrows']:
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
          try:
            if (spr.timef == time) and (spr.dir == dir): spr.kill()
          except: pass
        self.toparrfx[dir].stepped(curtime, text)

    for spr in self.arrow_group.sprites():
      spr.update(curtime, self.judge.getbpm(), self.song.lastbpmchangetime,
                 self.hidden, self.sudden)
    for d in DIRECTIONS:
      self.toparr[d].update(curtime + self.song.offset * 1000)
      self.toparrfx[d].update(curtime, self.judge.combo)

  def should_hold(self, direction, curtime):
    l = self.song.holdinfo[self.song.modediff[self.mode].index(self.difficulty)]
    for i in range(len(l)):
      if l[i][0] == DIRECTIONS.index(direction):
        if ((curtime - 15.0/self.song.playingbpm > l[i][1])
            and (curtime < l[i][2])):
          return i

class ScoringDisp(pygame.sprite.Sprite):
    def __init__(self,playernum, text):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.playernum = playernum
        
        self.set_text(text)
        self.image = pygame.surface.Surface((160,48))
        self.rect = self.image.get_rect()
        self.rect.bottom = 484
        self.rect.centerx = 160+(self.playernum*320)

    def set_text(self, text):
      tx = FONTS[28].size(text)[0]+2
      self.basemode = pygame.transform.scale(fontfx.embfade(text,28,2,(tx,24),
                                                            (127,127,127)),
                                             (tx,48))
      self.baseimage = pygame.surface.Surface((128,48))
      self.baseimage.blit(self.basemode,(64-(tx/2),0))
      self.oldscore = -1 # Force a refresh

    def update(self, score):
      if score != self.oldscore:
        self.image.blit(self.baseimage,(0,0))
        scoretext = FONTS[28].render(repr(score),1,(192,192,192))
        self.image.blit(scoretext,(64-(scoretext.get_rect().size[0]/2),13))
        self.image.set_colorkey(self.image.get_at((0,0)),RLEACCEL)
        self.oldscore = score

class LifeBarDisp(pygame.sprite.Sprite):
    def __init__(self, playernum, theme, previously = None):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.playernum = playernum
        if previously:
          self.oldlife = -1
          self.failed = previously.failed
          self.prevlife = previously.life - 25
          self.life = previously.life
        else:
          self.oldlife = self.failed = 0
          self.prevlife = 0
          self.life = 25

        self.image = pygame.Surface((204,28))
        self.blkbar = pygame.Surface((3,24))
        self.bugbar = pygame.Surface((2,24))
        self.bugbar.fill((192,192,192))
        self.grade = None
        self.vamt = 0.4
        self.pamt = 0.25
        self.gamt = 0
        self.oamt = -0.5
        self.bamt = -2
        self.mamt = -4
        
        self.redbar = pygame.image.load(os.path.join(theme.path,
                                                     'redbar.png')).convert()
        self.orgbar = pygame.image.load(os.path.join(theme.path,
                                                     'orgbar.png')).convert()
        self.yelbar = pygame.image.load(os.path.join(theme.path,
                                                     'yelbar.png')).convert()
        self.grnbar = pygame.image.load(os.path.join(theme.path,
                                                     'grnbar.png')).convert()
        self.redbar_pos = self.redbar.get_rect()
        self.orgbar_pos = self.orgbar.get_rect()
        self.yelbar_pos = self.yelbar.get_rect()
        self.grnbar_pos = self.grnbar.get_rect()
        
        self.failtext = fontfx.embfade("FAILED",28,3,(80,32),(224,32,32))
        self.failtext.set_colorkey(self.failtext.get_at((0,0)))
        
        embossbar = pygame.Surface((204,1))
        embossbar.fill((128,128,128))
        self.image.blit(embossbar,(0,0))
        self.image.blit(embossbar,(-1,1))
        embossbar.fill((192,192,192))
        self.image.blit(embossbar,(1,26))
        self.image.blit(embossbar,(0,27))
        embossbar = pygame.Surface((1,28))
        embossbar.fill((128,128,128))
        self.image.blit(embossbar,(0,0))
        self.image.blit(embossbar,(1,-1))
        embossbar.fill((192,192,192))
        self.image.blit(embossbar,(202,1))
        self.image.blit(embossbar,(203,0))

        self.rect = self.image.get_rect()
        self.rect.top = 30
        self.rect.left = 58+(320*self.playernum)

    def failed(self):
       return self.failed
       
    def update(self, judges):
      if self.life >= 0: #If you failed, you failed. You can't gain more life afterwards
        self.life = 25 + self.prevlife + (judges.marvelous * self.vamt) + (judges.perfect * self.pamt) + (judges.great * self.gamt) + (judges.ok * self.oamt) + (judges.boo * self.bamt) + (judges.miss * self.mamt)
        
        if self.life <= 0: #FAILED but we don't do anything yet
          self.failed = 1
          judges.failed_out = True
          self.life = 0
        elif self.life > 52:
          self.life = 52
        
        self.life = int(self.life)
        if self.life != self.oldlife:
          self.oldlife = self.life
#          print "life went to",self.life
          for j in range(52-self.life-1):
            self.image.blit(self.blkbar, ((2+int(self.life+j)*4), 2) )

          self.image.blit(self.bugbar,(202,2))   # because the damn bar eraser bugs out all the time

          for j in range(self.life):
            barpos = int(self.life-(j+1))
            if barpos <= 10:
              self.redbar_pos.left = 2+ barpos*4
              self.redbar_pos.top = 2
              self.image.blit(self.redbar,self.redbar_pos)
            elif barpos <= 20:
              self.orgbar_pos.left = 2+ barpos*4
              self.orgbar_pos.top = 2
              self.image.blit(self.orgbar,self.orgbar_pos)
            elif barpos <= 35:
              self.yelbar_pos.left = 2+ barpos*4
              self.yelbar_pos.top = 2
              self.image.blit(self.yelbar,self.yelbar_pos)
            elif barpos < 50:
              self.grnbar_pos.left = 2+ barpos*4
              self.grnbar_pos.top = 2
              self.image.blit(self.grnbar,self.grnbar_pos)

          if self.failed:
            self.image.blit(self.failtext, (70, 2) )
