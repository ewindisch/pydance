# This thing parses step files, in theory.

import sys, os, copy

DIFFICULTIES = ["BEGINNER", "BASIC", "TRICK", "MANIAC", "HARDCORE"]

def sorted_diff_list(difficulty_hash):
  diffs = []
  dhash = copy.copy(difficulty_hash)
  for d in DIFFICULTIES:
    if dhash.has_key(d):
      diffs.append(d)
      del(dhash[d])
  for key in dhash: diffs.append(key)
  return diffs

class StepFile:
  def __init__(self, filename):
    self.filename = filename
    self.steps = {}
    self.difficulty = {}
    self.diff_list = {}
    self.info = {}
    self.lyrics = []
    f = open(filename)
    # parser states
    METADATA, GAMETYPE, LYRICS, STEPS, WAITING = range(5)
    state = METADATA
    sec = diff = line = None 
    for line in f:
      line = line.strip()
      if line == "" or line[0] == "#": continue
      elif state == METADATA:
        if line == "LYRICS": state = LYRICS
        else:
          parts = line.split()
          if len(parts) == 1:
            state = GAMETYPE
            sec = line
            if self.steps.get(sec) == None: self.steps[sec] = {}
            if self.difficulty.get(sec) == None: self.difficulty[sec] = {}
          else:
            self.info[parts[0].lower()] = " ".join(parts[1:])
      elif state == GAMETYPE:
        state = STEPS
        parts = line.split()
        diff = parts[0]
        self.steps[sec][diff] = []
        self.difficulty[sec][diff] = int(parts[1])
      elif state == STEPS:
        if line == "end": state = WAITING
        self.steps[sec][diff].append(line)
      elif state == LYRICS:
        if line == "end": state = WAITING
        self.lyrics.append(line)
      elif state == WAITING:
        if line == "LYRICS": state = LYRICS
        elif line == line.upper():
          state = GAMETYPE
          sec = line
          if self.steps.get(sec) == None: self.steps[sec] = {}
          if self.difficulty.get(sec) == None: self.difficulty[sec] = {}
      else:
        print "Unknown state", state
        print "This is bad, bailing now."
        sys.exit(1)

    dir, name = os.path.split(filename)

    for t in (("banner", ".png"), ("banner", "-full.png"),
              ("bg", "-bg.png"), ("file", ".ogg"), ("file", ".mp3")):
      if self.info.has_key(t[0]):
        if not os.path.isfile(self.info[t[0]]):
          self.info[t[0]] = os.path.join(dir, self.info[t[0]])
          if not os.path.isfile(self.info[t[0]]): del(self.info[t[0]])
      if not self.info.has_key(t[0]):
        possible = os.path.join(dir, name.replace(".step", t[1]))
        possible = os.path.realpath(possible)
        if os.path.isfile(possible): self.info[t[0]] = possible

    for key in self.difficulty:
      self.diff_list[key] = sorted_diff_list(self.difficulty[key])

    if not self.info.has_key("subtitle"):
      try:
        l, r = self.info["song"].index("["), self.info["song"].rindex("]")
        if l != 0 and r > l + 1:
          self.info["subtitle"] = self.info["song"][l+1:r]
          self.info["song"] = self.info["song"][:l]
      except ValueError:
        try:
          l, r = self.info["song"].index("("), self.info["song"].rindex(")")
          if l != 0 and r > l + 1:
            self.info["subtitle"] = self.info["song"][l+1:r]
            self.info["song"] = self.info["song"][:l]
        except ValueError:
          try:
            l, r = self.info["song"].index("~"), self.info["song"].rindex("~")
            if l != 0 and r > l + 1:
              self.info["subtitle"] = self.info["song"][l+1:r]
              self.info["song"] = self.info["song"][:l]
          except ValueError:
            pass

formats = ((".step", StepFile), )


# Encapsulates and abstracts the above classes
class SongItem:
  def __init__(self, filename):
    song = None
    for pair in formats:
      if filename[-len(pair[0]):].lower() == pair[0]:
        song = pair[1](filename)
        break
    if song == None:
      print filename, "is in an unsupported format."
      raise NotImplementedError()
    self.info = song.info

    # Sanity checks
    for k in ("bpm", "offset", "song", "group", "file"):
      if not self.info.has_key(k):
        raise RuntimError

    for k in ("file", "bg", "banner"):
      if self.info.has_key(k) and not os.path.isfile(self.info[k]):
        raise RuntimeError

    self.info["bpm"] = float(self.info["bpm"])
    if self.info.has_key("offset"):
      self.info["offset"] = int(self.info["offset"])
    else: self.info['offset'] = 0
    self.steps = song.steps
    self.lyrics = song.lyrics
    self.difficulty = song.difficulty
    self.diff_list = song.diff_list
    self.filename = filename

