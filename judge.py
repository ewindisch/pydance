from constants import *

from util import toRealTime
from announcer import Announcer
import random

class AbstractJudge(object):
  def __init__ (self, bpm, holds, combos, score, display, grade, diff, lifebar):
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
    self.grade = grade
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

    if anotherjudge.failed: self.failed = True

    for k, v in anotherjudge.stats.items(): self.stats[k] += v

    self.badholds += anotherjudge.badholds
    self.holdsub += anotherjudge.holdsub

    self.early += anotherjudge.early
    self.late += anotherjudge.late
    self.ontime += anotherjudge.ontime

  def get_rating(self, dir, curtime):
    raise NotImplementedError("This class should not be instantiated.")
        
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
    rating, dir, etime = self.get_rating(dir, curtime)

    if rating != None:
      self.stats[rating] += 1
      for l in self.listeners: l.stepped(curtime, rating, self.combos.combo)

    return rating, dir, etime

  def arrow_count(self):
    c = 0
    for k in self.stats: c += self.stats[k]
    return c

  def handle_arrow(self, key, etime):
    if etime in self.steps: self.steps[etime] += key
    else: self.steps[etime] = key

  def expire_arrows(self, curtime):
    raise NotImplementedError("This class should not be instantiated.")

class TimeJudge(AbstractJudge):
  def get_rating(self, dir, curtime):
    times = self.steps.keys()
    times.sort()
    etime = 0.0
    rating = None
    for t in times:
      if dir in self.steps[t]:
        offset = abs(curtime - t)
        if offset < 0.0225: rating = "V"
        elif offset < 0.045: rating = "P"
        elif offset < 0.090: rating = "G"
        elif offset < 0.135: rating = "O"
        elif offset < 0.180: rating = "B"

        if rating != None:
          etime = t
          self.steps[etime] = self.steps[etime].replace(dir, "")
          break

    return rating, dir, etime

  def expire_arrows(self, curtime):
    times = self.steps.keys()
    for time in times:
      if (time < curtime - 0.180) and self.steps[time]:
        n = len(self.steps[time]) 
        del(self.steps[time])
        for i in range(n):
          self.stats["M"] += 1
          for l in self.listeners: l.stepped(curtime, "M", self.combos.combo)

class BeatJudge(AbstractJudge):
  def get_rating(self, dir, curtime):
    times = self.steps.keys()
    times.sort()
    etime = 0.0
    done = 0
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

    return rating, dir, etime

  def expire_arrows(self, curtime):
    times = self.steps.keys()
    for time in times:
      if (time < curtime - self.tick * 12) and self.steps[time]:
        n = len(self.steps[time]) 
        del(self.steps[time])
        for i in range(n):
          self.stats["M"] += 1
          for l in self.listeners: l.stepped(curtime, "M", self.combos.combo)
  
judges = [TimeJudge, BeatJudge]
judge_opt = [(0, "Time"), (1, "Beat")]
