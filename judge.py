from constants import *

from util import toRealTime
from announcer import Announcer
from listener import Listener

class AbstractJudge(Listener):
  def __init__ (self, pid):
    self.steps = {}
    self.pid = pid
    self.failed = False
    announcer = Announcer(mainconfig["djtheme"])

  def set_song(self, pid, bpm, difficulty, count, holds, feet):
    self.bpm = bpm
    self.diff = difficulty
    self.tick = toRealTime(bpm, 0.16666666666666666)
    self.holdsub = {}
    self.steps = {}

  def get_rating(self, dir, curtime):
    raise NotImplementedError("This class should not be instantiated.")

  def change_bpm(self, pid, curtime, bpm):
    if self.pid != pid: return
    if bpm >= 1: self.tick = toRealTime(bpm, 0.16666666666666666)
    self.bpm = bpm

  def broke_hold(self, pid, curtime, dir, whichone):
    if pid != self.pid: return
    if self.holdsub.get(whichone) != -1: self.holdsub[whichone] = -1

  def handle_key(self, dir, curtime):
    rating, dir, etime = self.get_rating(dir, curtime)

    return rating, dir, etime

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
    misses = ""
    for time in times:
      if (time < curtime - 0.180) and self.steps[time]:
        misses += self.steps[time]
        del(self.steps[time])
    return misses

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
    misses = ""
    for time in times:
      if (time < curtime - self.tick * 12) and self.steps[time]:
        misses += self.steps[time]
        del(self.steps[time])
    return misses
  
judges = [TimeJudge, BeatJudge]
judge_opt = [(0, "Time"), (1, "Beat")]
