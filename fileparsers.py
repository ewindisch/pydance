# This thing parses step files, in theory.

import sys, os, copy

DIFFICULTIES = ["BEGINNER", "LIGHT", "BASIC", "TRICK", "ANOTHER", "STANDARD",
                "MANIAC", "HEAVY", "HARDCORE", "CHALLENGE"]

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
              ("bg", "-bg.png"), ("file", ".ogg"),
              ("filename", ".mp3"), ("movie", ".mpg")):
      if self.info.has_key(t[0]):
        if not os.path.isfile(self.info[t[0]]):
          self.info[t[0]] = os.path.join(dir, self.info[t[0]])
          if not os.path.isfile(self.info[t[0]]): del(self.info[t[0]])
      if not self.info.has_key(t[0]):
        possible = os.path.join(dir, name.replace(".step", t[1]))
        possible = os.path.realpath(possible)
        if os.path.isfile(possible): self.info[t[0]] = possible

    self.info["title"] = self.info["song"]
    self.info["artist"] = self.info["group"]
    self.info["filename"] = self.info["file"]
    self.info["gap"] = self.info["offset"]
    del(self.info["song"])
    del(self.info["group"])
    del(self.info["file"])
    del(self.info["offset"])

    if self.info.has_key("bg"):
      self.info["background"] = self.info["bg"]
      del(self.info["bg"])

    if not self.info.has_key("subtitle"):
      for pair in (("[", "]"), ("(", ")"), ("~", "~"), ("-", "-")):
        if pair[0] in self.info["title"] and pair[1] in self.info["title"]:
          l = self.info["title"].index(pair[0])
          r = self.info["title"].rindex(pair[1])
          if l != 0 and r > l + 1:
            self.info["subtitle"] = self.info["title"][l+1:r]
            self.info["title"] = self.info["title"][:l]
            break

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

    self.info["bpm"] = float(self.info["bpm"])
    if self.info.has_key("gap"):  self.info["gap"] = int(self.info["gap"])
    else: self.info['gap'] = 0

    # Sanity checks
    for k in ("bpm", "gap", "title", "artist", "filename"):
      if not self.info.has_key(k):
        raise RuntimError

    # Default values
    for k in ("subtitle", "mix", "background", "banner",
                "author", "reivison", "md5sum", "movie"):
      if not self.info.has_key(k): self.info[k] = None

    for k, v in (("valid", 1), ("preview", (45.0, 10.0)),
                 ("startat", 0.0), ("endat", 0.0), ("revision", "1970.01.01")):
      if not self.info.has_key(k): self.info[k] = v

    for k in ("filename", "background", "banner"):
      if self.info[k] and not os.path.isfile(self.info[k]):
        raise RuntimeError

    for k in ("startat", "endat", "gap"):
      self.info[k] = float(self.info[k])

    self.steps = song.steps
    self.lyrics = song.lyrics
    self.difficulty = song.difficulty
    self.filename = filename

    self.diff_list = {}
    for key in self.difficulty:
      self.diff_list[key] = sorted_diff_list(self.difficulty[key])

