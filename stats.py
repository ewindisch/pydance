from listener import Listener

# Track statistics about the kind of steps being made.
class Stats(Listener):
  def __init__(self):
    self.hold_count = 0
    self.bad_holds = 0
    self.good_holds = 0
    self.arrow_count = 0
    self.maxcombo = 0
    self.steps = { "V": 0, "P": 0, "G": 0, "O": 0, "B": 0, "M": 0 }
    self.early = self.late = self.ontime = 0

  def stepped(self, curtime, rating, combo):
    if combo > self.maxcombo: self.maxcombo = combo
    self.steps[rating] += 1
    self.arrow_count += 1

  def ok_hold(self, dir, whichone):
    self.hold_count += 1
    self.good_holds += 1

  def broke_hold(self, dir, whichone):
    self.hold_count += 1
    self.bad_holds += 1

  def __getitem__(self, item): return self.steps[item]
