from constants import *

from util import toRealTime
from announcer import Announcer
import random

class Judge(object):
  def __init__ (self, bpm, holds, combos, score, display, diff, lifebar):
    self.steps = {}
    self.stats = { "V": 0, "P": 0, "G": 0, "O": 0, "B": 0, "M": 0 }
    self.combos = combos
    self.actualtimes = {}
    self.tick = toRealTime(bpm, 0.16666666666666666)
    self.early = self.late = self.ontime = 0
    self.bpm = bpm
    self.failed = False
    self.lifebar = lifebar
    self.diff = diff
    self.score = score
    self.grade = Grade()
    self.numholds = 0
    self.badholds = 0
    # combos must be told first, or the combo count is inaccurate when
    # the other listeners get it.
    announcer = Announcer(mainconfig["djtheme"])
    self.listeners = [self.combos, announcer, display, self.grade,
                      self.lifebar, self.score]
    self.holdsub = [0] * holds

  def munch(self, anotherjudge):
    self.grade.munch(anotherjudge.grade)

    self.stats = anotherjudge.stats

    self.badholds += anotherjudge.badholds
    self.holdsub += anotherjudge.holdsub

    self.early += anotherjudge.early
    self.late += anotherjudge.late
    self.ontime += anotherjudge.ontime
        
  def changebpm(self, bpm):
    if bpm >= 1: self.tick = toRealTime(bpm, 0.16666666666666666)
    self.bpm = bpm
        
  def broke_hold(self, whichone):
    if self.holdsub[whichone] != -1:
      self.holdsub[whichone] = -1
      self.badholds += 1
      self.numholds += 1
      for l in self.listeners: l.broke_hold()

  def ok_hold(self, whichone):
    self.numholds += 1
    for l in self.listeners: l.ok_hold()
    
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

    rating = None
    off = abs(off)
    if done == 1:
      if off <= 1: rating = "V"
      elif off <= 4: rating = "P"
      elif off <= 7: rating = "G"
      elif off <= 9: rating = "O"
      else: rating = "B"

    if rating != None:
      self.stats[rating] += 1
      for l in self.listeners: l.stepped(curtime, rating, self.combos.combo)

    return rating, dir, etime

  def arrow_count(self):
    c = 0
    for k in self.stats: c += self.stats[k]
    return c

  def expire_arrows(self, curtime):
    times = self.steps.keys()
    for time in times:
      if (time < curtime - self.tick * 12) and self.steps[time]:
        n = len(self.steps[time]) 
        del(self.steps[time])
        for i in range(n):
          self.stats["M"] += 1
          for l in self.listeners: l.stepped(curtime, "M", self.combos.combo)
  
  def handle_arrow(self, key, etime):
    if etime in self.steps: self.steps[etime] += key
    else: self.steps[etime] = key

# This is the "dance points" system found in DDR 8rd mix.
class Grade(object):
  def __init__(self):
    self.score = 0
    self.arrow_count = 0
    self.hold_count = 0
    self.inc = { "V": 2, "P": 2, "G": 1, "B": -4, "M": -8 }

  def ok_hold(self):
    self.hold_count += 1
    self.score += 6

  def broke_hold(self):
    self.hold_count += 1

  def stepped(self, cur_time, rating, combo):
    self.arrow_count += 1
    self.score += self.inc.get(rating, 0)

  def munch(self, agrade):
    self.score += agrade.score
    self.arrow_count += agrade.arrow_count
    self.hold_count += agrade.hold_count

  def grade(self, failed):
    max_score = float(2 * self.arrow_count + 6 * self.hold_count)

    if failed == True: return "E"
    elif max_score == 0: return "?"
    elif self.score / max_score >= 1.00: return "AAA"
    elif self.score / max_score >= 0.93: return "AA"
    elif self.score / max_score >= 0.80: return "A"
    elif self.score / max_score >= 0.65: return "B"
    elif self.score / max_score >= 0.45: return "C"
    else: return "D"
