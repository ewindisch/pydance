import os

class StepFile: 
  METADATA, GAMETYPE, LYRICS, STEPS, WAITING = range(5)
  word_trans = { "whole": "o", "halfn": "h", "qurtr": "q", "eight": "e",
                 "tripl": "w", "steps": "s", "twtfr": "f", "thrty": "t",
                 "sixty": "x", "ready": "R", "chbpm": "B", "waits": "W",
                 "delay": "D", "tstop": "S",
                 "00": 0, "08": 1, "88": 3, "80": 2 }

  def __init__(self, filename, need_steps):
    self.filename = filename
    self.steps = {}
    self.difficulty = {}
    self.info = {}
    self.lyrics = []
    f = open(filename)
    # parser states
    state = StepFile.METADATA
    state_data = [None, None] # sec, diff, or time in lyric mode
    parsers = [self.parse_metadata, self.parse_gametype,
               self.parse_lyrics, self.parse_steps, self.parse_waiting]

    if not need_steps: parsers[StepFile.STEPS] = self.parse_dummy_steps

    for line in f:
      line = line.strip()
      if line == "" or line[0] == "#": continue
      else: state, state_data = parsers[state](line, state_data)

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
    self.info["gap"] = int(self.info.get("offset", 0))
    self.info["bpm"] = float(self.info["bpm"])
    del(self.info["song"])
    del(self.info["group"])
    del(self.info["file"])
    del(self.info["offset"])

    if self.info.has_key("bg"):
      self.info["background"] = self.info["bg"]
      del(self.info["bg"])

    self.find_subtitle()
    self.description = None

  def find_subtitle(self):
    if not self.info.has_key("subtitle"):
      for pair in (("[", "]"), ("(", ")"), ("~", "~")):
        if pair[0] in self.info["title"] and pair[1] in self.info["title"]:
          l = self.info["title"].index(pair[0])
          r = self.info["title"].rindex(pair[1])
          if l != 0 and r > l + 1:
            self.info["subtitle"] = self.info["title"][l+1:r]
            self.info["title"] = self.info["title"][:l]
            break

  def parse_metadata(self, line, data):
    if line == "LYRICS": return StepFile.LYRICS, data
    else:
      parts = line.split()
      if len(parts) == 1:
        data[0] = line
        if self.steps.get(line) == None: self.steps[line] = {}
        if self.difficulty.get(line) == None: self.difficulty[line] = {}
        return StepFile.GAMETYPE, data
      else:
        self.info[parts[0].lower()] = " ".join(parts[1:])
        return StepFile.METADATA, data

  def parse_gametype(self, line, data):
    parts = line.split()
    data[1] = parts[0]
    self.steps[data[0]][data[1]] = []
    self.difficulty[data[0]][data[1]] = int(parts[1])
    return StepFile.STEPS, data

  def parse_dummy_steps(self, line, data):
    if line == "end": return StepFile.WAITING, data
    else: return StepFile.STEPS, data

  def parse_steps(self, line, data):
    if line == "end": return StepFile.WAITING, data
    parts = line.split()
    i = 0
    for p in parts:
      try: parts[i] = StepFile.word_trans[p]
      except KeyError:
        try: parts[i] = int(p)
        except ValueError:
          try: parts[i] = float(p)
          except ValueError: pass
      i += 1
    if parts[0] == "lyric": parts = ["L", 1, " ".join(parts[1:])]
    elif parts[0] == "trans": parts = ["L", 0, " ".join(parts[1:])]
    self.steps[data[0]][data[1]].append(parts)
    return StepFile.STEPS, data

  def parse_lyrics(self, line, data):
    if line == "end": return StepFile.WAITING, data
    self.lyrics.append(line)
    return StepFile.LYRICS, data

  def parse_waiting(self, line, data):
    if line == "LYRICS": return StepFile.LYRICS, data
    elif line == line.upper():
      self.sec = line
      if not self.steps.has_key(data[0]): self.steps[data[0]] = {}
      if not self.difficulty.has_key(data[0]): self.difficulty[data[0]] = {}
      return StepFile.GAMETYPE, data

formats = ((".step", StepFile), )

DIFFICULTIES = ["BEGINNER", "LIGHT", "BASIC", "TRICK", "ANOTHER", "STANDARD",
                "MANIAC", "HEAVY", "HARDCORE", "CHALLENGE", "ONI"]

def order_sort(a, b):
  if a in DIFFICULTIES and b in DIFFICULTIES:
    return cmp(DIFFICULTIES.index(a), DIFFICULTIES.index(b))
  else: return cmp(a, b)

def sorted_diff_list(difflist):
  keys = difflist.keys()
  keys.sort((lambda a, b: cmp(difflist[a], difflist[b]) or order_sort(a, b)))
  return keys

# Encapsulates and abstracts the above classes
class SongItem:
  def __init__(self, filename, need_steps = True):
    song = None
    for pair in formats:
      if filename[-len(pair[0]):].lower() == pair[0]:
        song = pair[1](filename, need_steps)
        break
    if song == None:
      print filename, "is in an unsupported format."
      raise NotImplementedError()
    self.info = song.info

    # Sanity checks
    for k in ("bpm", "gap", "title", "artist", "filename"):
      if not self.info.has_key(k):
        raise RuntimError

    # Default values
    for k in ("subtitle", "mix", "background", "banner",
                "author", "reivison", "md5sum", "movie"):
      if not self.info.has_key(k): self.info[k] = None

    for k, v in (("valid", 1), ("endat", 0.0), ("preview", (45.0, 10.0)),
                 ("startat", 0.0), ("revision", "1970.01.01"), ("gap", 0)):
      if not self.info.has_key(k): self.info[k] = v

    for k in ("filename", "background", "banner"):
      if self.info[k] and not os.path.isfile(self.info[k]):
        raise RuntimeError

    for k in ("startat", "endat", "gap", "bpm"):
      self.info[k] = float(self.info[k])

    self.steps = song.steps
    if song.lyrics: self.lyrics = song.lyrics
    else: self.lyrics = []
    self.difficulty = song.difficulty
    self.filename = filename
    self.description = song.description
  
    self.diff_list = {}
    for key in self.difficulty:    
      self.diff_list[key] = sorted_diff_list(self.difficulty[key])
