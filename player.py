from constants import *
from gfxtheme import GFXTheme

import fontfx, spritelib, colors

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
              self.difficulty,
              self.lifebar)
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

# FIXME - Use two large images instead of a bunch of small ones
class LifeBarDisp(pygame.sprite.Sprite):
    def __init__(self, playernum, theme, previously = None):
        pygame.sprite.Sprite.__init__(self)
        self.oldlife = self.failed = 0
        self.life = 50.0

        self.image = pygame.Surface((204,28))
        self.grade = None
        self.deltas = {"V": 0.8, "P": 0.5, "G": 0.0,
                       "O": -1.0, "B": -4.0, "M": -8.0}
        self.empty = pygame.image.load(os.path.join(theme.path,
                                                     'lifebar-empty.png'))
        self.full = pygame.image.load(os.path.join(theme.path,
                                                   'lifebar-full.png'))

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
        self.life = min(self.life, 100.0)
       
    def update(self, judges):
      if self.failed: return

      if self.life <= 0:
        self.failed = 1
        judges.failed_out = True
        self.life = 0
      elif self.life > 100.0:
        self.life = 100.0
        
      if self.life == self.oldlife: return

      self.oldlife = self.life

      self.image.blit(self.empty, (0, 0))
      self.image.set_clip((0, 0, int(202 * self.life / 100.0), 28))
      self.image.blit(self.full, (0, 0))
      self.image.set_clip()

      if self.failed:
        self.image.blit(self.failtext, (70, 2) )
