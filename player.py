from constants import *
from util import toRealTime
from gfxtheme import GFXTheme
from judge import Judge

import fontfx, colors

# Display the score overlaying the song difficulty
class ScoringDisp(pygame.sprite.Sprite):
  def __init__(self, playernum, text, game):
    pygame.sprite.Sprite.__init__(self)
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

  def update(self, score):
    if score != self.oldscore:
      self.image.blit(self.baseimage, (0,0))
      scoretext = FONTS[28].render(str(score), 1, (192,192,192))
      self.image.blit(scoretext, (64 - (scoretext.get_rect().size[0] / 2),
                                    13))
      self.image.set_colorkey(self.image.get_at((0, 0)), RLEACCEL)
      self.oldscore = score

class AbstractLifeBar(pygame.sprite.Sprite):
  def __init__(self, playernum, maxlife, songconf, game):
    pygame.sprite.Sprite.__init__(self)
    self.oldlife = 0
    self.failed = False
    self.maxlife = int(maxlife * songconf["diff"])
    self.image = pygame.Surface((204, 28))
    self.deltas = {}

    self.failtext = fontfx.embfade("FAILED",28,3,(80,32),(224,32,32))
    self.failtext.set_colorkey(self.failtext.get_at((0,0)), RLEACCEL)
        
    self.rect = self.image.get_rect()
    self.rect.top = 30
    self.rect.centerx = game.sprite_center + playernum * game.player_offset

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
  def __init__(self, playernum, theme, songconf, game):
    AbstractLifeBar.__init__(self, playernum, 100, songconf, game)
    self.life = self.maxlife / 2
    self.displayed_life = self.life

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

# A lifebar that only goes down.
class DropLifeBarDisp(LifeBarDisp):
  def __init__(self, playernum, theme, songconf, game):
    LifeBarDisp.__init__(self, playernum, theme, songconf, game)
    self.life = self.maxlife
    for k in self.deltas:
      if self.deltas[k] > 0: self.deltas[k] = 0

# Lifebar where doing too good also fails you
class MiddleLifeBarDisp(AbstractLifeBar):
  def __init__(self, playernum, theme, songconf, game):
    AbstractLifeBar.__init__(self, playernum, 20, songconf, game)
    self.life = 10.0
    self.displayed_life = 10

    self.deltas = {"V": 0.8, "P": 0.5, "G": 0.0,
                       "O": -1.0, "B": -4.0, "M": -8.0}
    self.image = pygame.surface.Surface([202, 28])
    self.image.fill([255, 255, 255])

  def update(self, judges):
    if self.displayed_life < self.life:  self.displayed_life += 1
    elif self.displayed_life > self.life:  self.displayed_life -= 1

    if abs(self.displayed_life - self.life) < 1:
      self.displayed_life = self.life

    if (AbstractLifeBar.update(self, judges) == False and
        self.displayed_life <= 0): return

    if self.life == self.maxlife:
      self.failed = True
      judges.failed_out = True

    if self.displayed_life < 0: self.displayed_life = 0
    pct = 1 - abs(self.life - 10) / 10.0
    self.image.fill([int(255 * pct)] * 3)

    if self.failed:
      self.image.blit(self.failtext, (70, 2))

# Oni mode lifebar
class OniLifeBarDisp(AbstractLifeBar):

  lose_sound = pygame.mixer.Sound(os.path.join(sound_path, "loselife.ogg"))

  def __init__(self, playernum, theme, songconf, game):
    AbstractLifeBar.__init__(self, playernum, songconf["onilives"], songconf, game)

    self.life = onilives

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
  def __init__(self, player, game):
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

    self.rect.centerx = game.sprite_center + player.pid * game.player_offset

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
        
  def update(self, steptimediff, judgetype):
    if steptimediff < 0.5 or (judgetype == ('MISS' or ' ')):
      if   judgetype == "MARVELOUS":       self.image = self.marvelous
      elif judgetype == "PERFECT":         self.image = self.perfect
      elif judgetype == "GREAT":           self.image = self.great
      elif judgetype == "OK":              self.image = self.ok
      elif judgetype == "BOO":             self.image = self.boo
      elif judgetype == " ":               self.image = self.space
      elif judgetype == "MISS":            self.image = self.miss

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

  def update(self, xcombo, steptimediff):
    if steptimediff < 0.36 or self.sticky:
      self.drawcount = xcombo
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

class Player:

  lifebars = [LifeBarDisp, OniLifeBarDisp, DropLifeBarDisp, MiddleLifeBarDisp]

  def __init__(self, pid, config, songconf, game):
    self.theme = GFXTheme(mainconfig["gfxtheme"], game)
    self.pid = pid

    self.__dict__.update(config)

    if self.scrollstyle == 2: self.top = 236
    elif self.scrollstyle == 1: self.top = 384
    else: self.top = 64
    
    self.score = ScoringDisp(pid, "Player " + str(pid), game)
    self.lifebar = Player.lifebars[songconf["lifebar"]](pid, self.theme,
                                                        songconf, game)
    self.holdtext = HoldJudgeDisp(self, game)
    self.judging_list = []
    self.tempholding = [-1] * len(game.dirs)
    self.combos = ComboDisp(pid, game)
    self.judge = None
    self.steps = None
    self.holds = None
    self.evt = None
    self.game = game

  def set_song(self, steps):
    self.steps = steps
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
    self.arrow_group = pygame.sprite.RenderUpdates()
    self.toparr_group = pygame.sprite.RenderUpdates()
    self.fx_group = pygame.sprite.RenderUpdates()
    self.text_group = pygame.sprite.RenderUpdates()
    for d in self.game.dirs:
      if mainconfig["explodestyle"] > -1: self.toparrfx[d].add(self.fx_group)
      if not self.dark: self.toparr[d].add(self.toparr_group)
    for i in range(mainconfig["totaljudgings"]):
      jd = JudgingDisp(self.pid, self.game)
      self.judging_list.append(jd)
      jd.add(self.text_group)
    self.text_group.add([self.score, self.lifebar, self.holdtext])
    if mainconfig["showcombo"]: self.text_group.add(self.combos)
    self.sprite_groups = [self.toparr_group, self.arrow_group,
                          self.fx_group, self.text_group]

  def get_next_events(self):
    self.evt = self.steps.get_events()
    self.fx_data = []

  def combo_update(self, curtime):
    self.combos.update(self.judge.combo, curtime - self.judge.steppedtime)
    self.score.update(self.judge.score)
    i = 0
    for j in self.judging_list:
      j.update(curtime - self.judge.steppedtime, self.judge.recentsteps[i])
      i += 1
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
    for d in self.game.dirs:
      self.toparr[d].update(curtime + self.steps.offset * 1000)
      self.toparrfx[d].update(curtime, self.judge.combo)

  def should_hold(self, direction, curtime):
    l = self.steps.holdinfo
    for i in range(len(l)):
      if l[i][0] == self.game.dirs.index(direction):
        if ((curtime - 15.0/self.steps.playingbpm > l[i][1])
            and (curtime < l[i][2])):
          return i

  def check_holds(self, curtime):
    # FIXME THis needs to go away
    keymap_kludge = ({"u": E_UP, "k": E_UPLEFT, "z": E_UPRIGHT,
                      "d": E_DOWN, "l": E_LEFT, "r": E_RIGHT,
                      "g": E_DOWNRIGHT, "w": E_DOWNLEFT} )

    for dir in self.game.dirs:
      self.toparrfx[dir].holding(0)
      current_hold = self.should_hold(dir, curtime)
      dir_idx = self.game.dirs.index(dir)
      if current_hold is not None:
        if event.states[(self.pid, keymap_kludge[dir])]:
          if self.judge.holdsub[self.tempholding[dir_idx]] != -1:
            self.toparrfx[dir].holding(1)
          self.tempholding[dir_idx] = current_hold
        else:
          self.judge.botchedhold(current_hold)
          self.holdtext.fillin(curtime, dir_idx, "NG")
          botchdir, timef1, timef2 = self.steps.holdinfo[current_hold]
          for spr in self.arrow_group.sprites():
            # FIXME This is insanely slow
            try:
              if spr.timef1 == timef1 and self.game.dirs.index(spr.dir) == dir_idx:
                spr.broken = True
                break
            except: pass
      else:
        if self.tempholding[dir_idx] > -1:
          if self.judge.holdsub[self.tempholding[dir_idx]] != -1:
            self.tempholding[dir_idx] = -1
            self.holdtext.fillin(curtime, dir_idx, "OK")

  def handle_key(self, ev, time):
    if ev[1] in self.game.dirs:
      self.toparr[ev[1]].stepped(1, time + self.steps.soffset)
      self.fx_data.append(self.judge.handle_key(ev[1], time))

  def check_bpm_change(self, time):
    if len(self.steps.lastbpmchangetime) > 0:
      if time >= self.steps.lastbpmchangetime[0][0]:
        newbpm = self.steps.lastbpmchangetime[0][1]
        if not self.dark:
          for d in self.toparr:
            self.toparr[d].tick = toRealTime(newbpm, 1)
            self.toparrfx[d].tick = toRealTime(newbpm, 1)
        self.judge.changebpm(newbpm)
        self.steps.lastbpmchangetime.pop(0)

  def update_sprites(self, screen):
    rects = []
    for g in self.sprite_groups: rects.extend(g.draw(screen))
    return rects

  def clear_sprites(self, screen, bg):
    for g in self.sprite_groups: g.clear(screen, bg)
