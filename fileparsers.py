import os

# FIXME: DanceFile and StepFile can easily share a parent class.

class DanceFile:
  WAITING, METADATA, DESCRIPTION, LYRICS, GAMETYPE, STEPS = range(6)

  def __init__(self, filename, need_steps):
    self.filename = filename
    self.difficulty = {}
    self.steps = {}
    self.info = {}
    self.lyrics = {}
    self.description = None
    self.need_steps = need_steps

    parsers = [self.parse_waiting, self.parse_metadata, self.parse_description,
               self.parse_lyrics, self.parse_gametype, self.parse_steps]

    state = DanceFile.METADATA
    state_data = [None, None]

    f = file(filename)

    for line in f:
      line = line.strip()
      if line == "" or line[0] == "#": continue
      elif line == "end": state = DanceFile.WAITING
      else: state = parsers[state](line, state_data)

    dir, name = os.path.split(filename)

    for t in ("banner", "filename", "movie", "background"):
      if self.info.has_key(t):
        if not os.path.isfile(self.info[t]):
          self.info[t] = os.path.join(dir, self.info[t])
          if not os.path.isfile(self.info[t]): del(self.info[t])

    if self.info.has_key("preview"):
      start, length = self.info["preview"].split()
      self.info["preview"] = (float(start), float(length))

  def parse_metadata(self, line, data):
    parts = line.split()
    self.info[parts[0]] = " ".join(parts[1:])
    return DanceFile.METADATA

  def parse_waiting(self, line, data):
    if line == "DESCRIPTION": return DanceFile.DESCRIPTION
    elif line == "LYRICS": return DanceFile.LYRICS
    else:
      data[0] = line
      if not self.difficulty.has_key(line):
        self.difficulty[line] = {}
        self.steps[line] = {}
      return DanceFile.GAMETYPE

  def parse_gametype(self, line, data):
    data[1], diff = line.split()
    self.difficulty[data[0]][data[1]] = int(diff)
    self.steps[data[0]][data[1]] = []
    return DanceFile.STEPS

  def parse_steps(self, line, data):
    if not self.need_steps: return DanceFile.STEPS
    parts = line.split()
    steps = [parts[0]]
    if parts[0] in ("B", "W", "S", "D"): steps.append(float(parts[1]))
    elif parts[0] in ("o", "h", "q", "e", "w", "s", "f", "t", "x"):
      steps.extend([int(s) for s in parts[1]])
    elif parts[0] == "L": steps.extend((int(parts[1]), " ".join(parts[2:])))

    self.steps[data[0]][data[1]].append(steps)
    return DanceFile.STEPS

  def parse_lyrics(self, line, data):
    parts = line.split()
    self.lyrics.append((float(parts[0]), int(parts[1]), " ".join(parts[2:])))
    return DanceFile.LYRICS

  def parse_description(self, line, data):
    return DanceFile.DESCRIPTION

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
    f = file(filename)
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

    if self.info.has_key("version"): del(self.info["version"])

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
    if line == "LYRICS": return StepFile.LYRICS, [None, None]
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
    if parts[0] == "lyric":
      parts = ["L", 1, " ".join([str(i) for i in parts[1:]])]
    elif parts[0] == "trans":
      parts = ["L", 0, " ".join([str(i) for i in parts[1:]])]
    self.steps[data[0]][data[1]].append(parts)
    return StepFile.STEPS, data

  def parse_lyrics(self, line, data):
    if line == "end": return StepFile.WAITING, data
    else:
      parts = line.split()
      if parts[0] == "atsec": data[0] = float(parts[1])
      elif parts[0] == "waits": data[0] += float(parts[1])
      elif parts[0] == "lyric":
        self.lyrics.append((data[0], 1, " ".join(parts[1:])))
      elif parts[0] == "trans":
        self.lyrics.append((data[0], 0, " ".join(parts[1:])))
    return StepFile.LYRICS, data

  def parse_waiting(self, line, data):
    if line == "LYRICS": return StepFile.LYRICS, data
    elif line == line.upper():
      data[0] = line
      if not self.steps.has_key(data[0]): self.steps[data[0]] = {}
      if not self.difficulty.has_key(data[0]): self.difficulty[data[0]] = {}
      return StepFile.GAMETYPE, data

formats = ((".step", StepFile),
           (".dance", DanceFile))

DIFFICULTIES = ["BEGINNER", "LIGHT", "BASIC", "ANOTHER", "STANDARD", "TRICK",
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

  defaults = { "valid": 1,
               "endat": 0.0,
               "preview": (45.0, 10.0),
               "startat": 0.0,
               "revision": "1970.01.01",
               "gap": 0 }
  
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
    for k in ("bpm", "title", "artist", "filename"):
      if not self.info.has_key(k):
        raise RuntimeError

    # Default values
    for k in ("subtitle", "mix", "background", "banner",
                "author", "revision", "md5sum", "movie"):
      if not self.info.has_key(k): self.info[k] = None

    for k in SongItem.defaults:
      if not self.info.has_key(k): self.info[k] = SongItem.defaults[k]

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

  def write(self, filename):
    f = file(filename, "w")

    # Write metadata
    for key in ("filename", "title", "subtitle", "artist", "mix", "bpm",
                "startat", "endat", "background", "banner", "md5sum",
                "gap", "author", "movie", "revision", "valid"):
      if (self.info[key] is not None and
          self.info[key] != SongItem.defaults.get(key)):
        f.write(key + " " + str(self.info[key]) + "\n")

    self.info["gap"] = int(self.info["gap"])
      
    if self.info["preview"] != SongItem.defaults["preview"]:
      f.write("preview " + str(self.info["preview"][0]) + " " +
              str(self.info["preview"][1]) + "\n")

    f.write("end\n")

    if self.description is not None:
      paras = description.split("\n ").join("\n .\n")
      f.write("DESCRIPTION\n" + paras + "\nend\n")
      
    if self.lyrics != []:
      f.write("LYRICS\n")
      for lyr in lyrics:  f.write(" ".join([str(l) for l in lyrics]) + "\n")
      f.write("end\n")

    for game in self.difficulty:
      for diff in self.difficulty[game]:
        f.write(game + "\n")
        f.write(diff + " " + str(self.difficulty[game][diff]) + "\n")
        for step in self.steps[game][diff]:
          extra = ""
          if step[0] in ("B", "W", "S", "D"): extra = str(step[1])
          elif step[0] in ("o", "h", "q", "e", "w", "s", "f", "t", "x"):
            extra = "".join([str(i) for i in step[1:]])
          elif step[0] == "L": extra = " ".join([str(i) for i in step[1:]])
          f.write(step[0] + " " + extra + "\n")
        f.write("end\n")

    f.close()
