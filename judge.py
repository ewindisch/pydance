from constants import *

from util import toRealTime
from announcer import Announcer
import random

class Judge(object):
  def __init__ (self, bpm, holds, combos, score, display, feet,
                stepcount, diff, lifebar):
    self.steps = {}
    self.stats = { "V": 0, "P": 0, "G": 0, "O": 0, "B": 0, "M": 0 }
    self.combos = combos
    self.display = display
    self.actualtimes = {}
    self.tick = toRealTime(bpm, 0.16666666666666666)
    self.early = self.late = self.ontime = 0
    self.bpm = bpm
    self.failed_out = False
    self.lifebar = lifebar
    self.diff = diff
    self.score = Score(stepcount, score)
    self.dance_score = 6 * holds
    self.badholds = 0
    self.arrow_count = 0
    self.announcer = Announcer(mainconfig["djtheme"])
    self.holdsub = []
    for i in range(holds):
      self.holdsub.append(0)

  def munch(self, anotherjudge):
    self.score.munch(anotherjudge.score)
    self.stats = anotherjudge.stats

    self.dance_score += anotherjudge.dance_score

    self.badholds += anotherjudge.badholds
    self.holdsub += anotherjudge.holdsub

    self.early += anotherjudge.early
    self.late += anotherjudge.late
    self.ontime += anotherjudge.ontime
        
  def changebpm(self, bpm):
    if bpm >= 1: self.tick = toRealTime(bpm, 0.16666666666666666)
    self.bpm = bpm
        
  def numholds(self):
    return len(self.holdsub)
    
  def botchedhold(self,whichone):
    if self.holdsub[whichone] != -1:
      self.holdsub[whichone] = -1
      self.badholds += 1
      self.dance_score -= 6
      self.lifebar.broke_hold()
    
  def handle_key(self, dir, curtime):
    times = self.steps.keys()
    times.sort()
    etime = 0.0
    done = 0
    early = late = ontime = 0
    off = -1
    for t in times:
      if (curtime - self.tick*12) < t < (curtime + self.tick*12):
        if dir in self.steps[t]:
          off = (curtime-t) / self.tick
          if off < 1: self.early += 1
          elif off > 1: self.late += 1
          else: self.ontime += 1
          done = 1
          etime = t
          self.steps[etime] = self.steps[etime].replace(dir, "")
          break

    rating = " "
    anncrange = (0, 100)
    off = abs(off)
    if done == 1:
      self.arrow_count += 1
      if off < 7:
        self.combos.addcombo(curtime)
        if off <= 1:
          self.dance_score += 2
          rating = "V"
          anncrange = (80, 100)
        elif off <= 4:
          self.dance_score += 2
          rating = "P"
          anncrange = (80, 100)
        else:
          self.dance_score += 1
          rating = "G"
          anncrange = (70, 94)

      else:
        self.combos.broke(curtime)
        if off < 9:
          rating = "O"
          anncrange = (40, 69)
        else:
          self.dance_score -= 4
          rating = "B"
          anncrange = (20, 39)

      if random.randrange(15) == 1: self.announcer.say('ingame', anncrange)

    if rating != " ":
      self.stats[rating] += 1
      self.lifebar.stepped(curtime, rating, self.combos.combo)
      self.score.stepped(curtime, rating, self.combos.combo)
      self.display.stepped(curtime, rating, self.combos.combo)

    return rating, dir, etime

  def expire_arrows(self, cur_time):
    times = self.steps.keys()
    for time in times:
      if (time < cur_time - self.tick * 12) and self.steps[time]:
        n = len(self.steps[time]) 
        del(self.steps[time])
        for i in range(n):
          self.stats["M"] += 1
          self.combos.broke(cur_time)
          self.display.stepped(cur_time, "M", self.combos.combo)
          self.lifebar.stepped(cur_time, "M", self.combos.combo)
          self.score.stepped(cur_time, "M", self.combos.combo)
          self.dance_score -= 8
          self.arrow_count += 1
  
  def handle_arrow(self, key, etime):
    if etime in self.steps: self.steps[etime] += key
    else: self.steps[etime] = key

  def grade(self):
    totalsteps = self.arrow_count

    max_score = 2.0 * totalsteps + 6.0 * self.numholds()

    if self.failed_out == True: return "E"
    elif totalsteps == 0: return "?"
    elif self.dance_score / max_score >= 1.00: return "AAA"
    elif self.dance_score / max_score >= 0.93: return "AA"
    elif self.dance_score / max_score >= 0.80: return "A"
    elif self.dance_score / max_score >= 0.65: return "B"
    elif self.dance_score / max_score >= 0.45: return "C"
    else: return "D"

class Score(object):
  def __init__(self, count, sprite):
    if count == 0: count = 1 # Don't crash on empty songs.

    self.sprite = sprite
    self.score = 0
    score_coeff = 10000000.0 / count
    self.combo_coeff = 10000000.0 / (count * (count + 1) / 2.0)
    self.inc = { "V": 4 * score_coeff, "P": 3.5 * score_coeff,
                 "G": 2.5 * score_coeff, "O": 0.5 * score_coeff }

  def stepped(self, cur_time, rating, combo):
    self.score += self.inc.get(rating, 0)
    self.score += combo * self.combo_coeff
    self.sprite.score = self.score

  def broke_hold(self): pass

  def munch(self, ascore): self.score += ascore.score
