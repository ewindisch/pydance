from constants import *

from util import toRealTime
from announcer import Announcer
import random

class Judge:
  def __init__ (self, bpm, holds, combos, feet, stepcount, diff, lifebar):
    self.steps = {}
    self.combos = combos
    self.actualtimes = {}
    self.tick = toRealTime(bpm, 0.16666666666666666)
    self.marvelous = self.perfect = self.great = self.ok = self.boo = self.miss = 0
    self.steppedtime = -1000
    self.recentsteps = [' ',' ',' ']
    self.early = self.late = self.ontime = 0
    self.bpm = bpm
    self.failed_out = False
    self.lifebar = lifebar
    self.diff = diff
    # DDR Extreme scoring
    scorecoeff = (1000000.0 * feet) / ((stepcount * (stepcount + 1.0)) / 2.0)
    self.score_coeff = int(scorecoeff) + 1
    self.score = 0
    self.dance_score = 6 * holds
    self.badholds = 0
    self.arrow_count = 0
    self.announcer = Announcer(mainconfig["djtheme"])
    self.holdsub = []
    for i in range(holds):
      self.holdsub.append(0)

  def munch(self, anotherjudge):
    self.marvelous += anotherjudge.marvelous
    self.perfect   += anotherjudge.perfect
    self.great     += anotherjudge.great
    self.ok        += anotherjudge.ok
    self.boo      += anotherjudge.boo
    self.miss      += anotherjudge.miss

    self.dance_score += anotherjudge.dance_score

    self.badholds += anotherjudge.badholds
    for i in anotherjudge.holdsub:
      self.holdsub.append(i)
    
    self.score += anotherjudge.score
    self.early += anotherjudge.early
    self.late += anotherjudge.late
    self.ontime += anotherjudge.ontime
        
  def changebpm(self, bpm):
    if bpm >= 1:
      self.tick = toRealTime(bpm, 0.16666666666666666)
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
    for i in range(len(times)):
      if (curtime - self.tick*12) < times[i] < (curtime + self.tick*12):
        if dir in self.steps[times[i]]:
          off = (curtime-times[i]) / self.tick
          if off < 1: self.early += 1
          elif off > 1: self.late += 1
          else: self.ontime += 1
          done = 1
          etime = times[i]
          self.steps[etime] = self.steps[etime].replace(dir, "")
          break

    text = ' '
    anncrange = (0, 100)
    off = abs(off)
    if done == 1:
      self.arrow_count += 1
      if off < 7:
        self.steppedtime = curtime
        self.combos.combo += 1
        if off <= 1:
          self.marvelous += 1
          self.score += 10 * self.score_coeff * self.arrow_count
          self.dance_score += 2
          self.lifebar.update_life("V")
          text = "MARVELOUS"
          anncrange = (80, 100)
        elif off <= 4:
          self.perfect += 1
          self.score += 9 * self.score_coeff * self.arrow_count
          self.dance_score += 2
          self.lifebar.update_life("P")
          text = "PERFECT"
          anncrange = (80, 100)
        else:
          self.great += 1
          self.score += 5 * self.score_coeff * self.arrow_count
          self.dance_score += 1
          self.lifebar.update_life("G")
          text = "GREAT"
          anncrange = (70, 94)

      else:
        self.steppedtime = curtime
        self.broke = 1
        self.combos.broke()
        if off < 9:
          self.ok += 1
          self.lifebar.update_life("O")
          text = "OK"
          anncrange = (40, 69)
        else:
          self.boo += 1
          self.dance_score -= 4
          self.lifebar.update_life("B")
          text = "BOO"
          anncrange = (20, 39)

      if random.randrange(15) == 1: self.announcer.say('ingame', anncrange)

      self.recentsteps.insert(0, text)
      self.recentsteps.pop()

    return text, dir, etime


  def expire_arrows(self, time):
    self.times = self.steps.keys()
    self.times.sort()
    for k in range(len(self.times)):
      if (self.times[k] < time - self.tick*12) and self.steps[self.times[k]]:
        self.broke = 1
        n = len(self.steps[self.times[k]]) 
        del self.steps[self.times[k]]
        for i in range(n):
          self.miss += 1
          self.combos.broke()
          self.recentsteps.insert(0, "MISS")
          self.lifebar.update_life("M")
          self.dance_score -= 8
          self.arrow_count += 1
          self.recentsteps.pop()
  
  def handle_arrow(self, key, etime):
      self.times = self.steps.keys()
      if etime in self.times:
        self.steps[etime] += key
      else:
        self.steps[etime] = key
        self.times = self.steps.keys()


  def grade(self):
    totalsteps = (self.marvelous + self.perfect + self.great + self.ok +
                  self.boo + self.miss)

    max_score = 2.0 * totalsteps + 6.0 * self.numholds()

    if self.failed_out == True: return "E"
    elif totalsteps == 0: return "?"
    elif self.dance_score / max_score >= 1.00: return "AAA"
    elif self.dance_score / max_score >= 0.93: return "AA"
    elif self.dance_score / max_score >= 0.80: return "A"
    elif self.dance_score / max_score >= 0.65: return "B"
    elif self.dance_score / max_score >= 0.45: return "C"
    else: return "D"

