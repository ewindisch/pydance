from constants import *
from gfxtheme import GFXTheme

class Player:
  def __init__(self, pid, score, lifebar,  holdtext, arrowgroup,
               combos, holdkey, song, difficulty, mode = "SINGLE"):
    self.theme = GFXTheme(mainconfig["gfxtheme"])
    if mainconfig["reversescroll"]:
      self.arrow_top = 408
      self.arrow_bot = int(-64 - (mainconfig["scrollspeed"] - 1) * 576)
    else:
      self.arrow_top = 64
      self.arrow_bot = int(576 * mainconfig["scrollspeed"])
    self.arrow_diff = float(self.arrow_top - self.arrow_bot)
    self.pid = pid
    self.score = score
    self.lifebar = lifebar
    self.holdtext = holdtext
    self.arrow_group = arrowgroup
    self.judging_list = []
    self.total_judgings = mainconfig['totaljudgings']
    self.tempholding = [-1, -1, -1, -1]
    self.combos = combos
    self.holdkey = holdkey
    self.song = song
    self.difficulty = difficulty
    self.holds = None
    arr, arrfx = self.theme.toparrows(self.song.bpm, self.arrow_top, self.pid)
    self.toparr = arr
    self.toparrfx = arrfx
    self.evt = None
    self.mode = mode

    self.sudden = mainconfig['sudden']
    
    if int(64.0*mainconfig['hidden']): self.hidden = 1
    else: self.hidden = 0
  
  hiddenval = float(mainconfig['hidden'])

  def start_song(self, Judge, combos): # FIXME factor these out
    difflist = self.song.modediff[self.mode]
    self.song.play(self.mode, self.difficulty, self.pid == 0)
    self.holds = len(self.song.holdref[self.song.modediff[self.mode].index(self.difficulty)])
    self.judge = Judge(self.song.bpm, self.holds,
                       self.song.modeinfo[self.mode][difflist.index(self.difficulty)][1],
                       self.song.totarrows[self.difficulty],
                       self.difficulty)
    self.judge.combo = combos[self.pid]

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
