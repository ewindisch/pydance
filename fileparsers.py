import os, stat, util, string

import games

class GenericFile:
  def __init__(self, filename, need_steps):
    self.filename = filename
    self.difficulty = {}
    self.steps = {}
    self.info = {}
    self.lyrics = []
    self.description = None
    self.need_steps = need_steps

  def strip_line(self, line):
    if line.count(self.comment) > 0: line = line[:line.index(self.comment)]
    return line.strip()

  def find_subtitle(self):
    if not self.info.has_key("subtitle"):
      for pair in (("[", "]"), ("(", ")"), ("~", "~"), ("-", "-")):
        if pair[0] in self.info["title"] and self.info["title"][-1] == pair[1]:
          l = self.info["title"][0:-1].rindex(pair[0])
          if l != 0:
            self.info["subtitle"] = self.info["title"][l+1:-1]
            self.info["title"] = self.info["title"][:l]
            break

  def find_mixname(self):
    dir, name = os.path.split(self.filename)
    mixname = os.path.split(os.path.split(dir)[0])[1]
    if mixname != "songs": self.info["mix"] = mixname

  def find_files_insanely(self):
    dir, name = os.path.split(self.filename)
    largefile = 10240 # Oh crap, I hate DWI. Shoot me now.
    found_bg = False
    found_ban = False
    if dir == "": dir = os.path.realpath(".")
    for file in os.listdir(dir):
      lfile = file.lower()
      # SimWolf should be indicted for some sort of programming crime
      # for making me write all the code below this.
      fullfile = os.path.join(dir, file)
      if lfile[-3:] == "mp3" and not self.info.has_key("filename"):
        self.info["filename"] = fullfile
      elif lfile[-3:] == "ogg"  and not self.info.has_key("filename"):
        self.info["filename"] = fullfile
      elif lfile[-3:] == "lrc":
        self.parse_lyrics(fullfile)
      elif lfile[-3:] == "jpg" or lfile[-3:] == "png":
        size = os.stat(fullfile).st_size
        try:
          lfile.index("bg")
          found_bg = True
          largefile = max(largefile, size)
          if self.info.has_key("background") and not found_ban:
            self.info["banner"] = self.info["background"]
          self.info["background"] = fullfile
        except ValueError:
          try:
            lfile.index("ban")
            found_ban = True
            largefile = max(largefile, size)
            self.info["banner"] = fullfile
          except ValueError:
            try:
              lfile.index("bn")
              found_ban = True
              largefile = max(largefile, size)
              self.info["banner"] = fullfile
            except ValueError:
              if size > largefile and not found_bg:
                largefile = size
                if self.info.has_key("background"):
                  self.info["banner"] = self.info["background"]
                self.info["background"] = fullfile
              elif not found_ban:
                self.info["banner"] = fullfile
    if (self.info.get("banner") == self.info.get("background") and
        self.info.has_key("banner")):
      del(self.info["banner"])

  # Fucking braindead file format
  # Fucking braindead DWI writers
  def parse_time(self, string):
    offset = 0
    time = 0
    if string[0] == "+":
      string = string[1:]
      offset = self.info["gap"]
    if ":" in string:
      parts = string.split(":")
      if len(parts) == 2: time = 60 * int(parts[0]) + float(parts[1])
      elif len(parts) == 3:
        time = int(parts[0]) + float(parts[1]) + float(parts[2]) / 100
    elif "." in string: time = float(string)
    else: time = int(string) / 1000.0
    return offset + time

  def parse_lyrics(self, filename):
    f = open(filename)
    offset = 0
    for line in f:
      line = line.strip()
      if line[1:7] == "offset": offset = float(line[8:-1]) / 1000.0
      if len(line) > 2 and line[1] in "0123456789":
        time = self.parse_time(line[1:line.index("]")])
        lyr = line[line.index("]") + 1:].split("|")
        lyr.reverse()
        for i in range(len(lyr)):
          if lyr[i] is not "": self.lyrics.append((time, i, lyr[i]))

  def resolve_files_sanely(self):
    dir, name = os.path.split(self.filename)
    for t in ("banner", "filename", "movie", "background"):
      if self.info.has_key(t):
        if not os.path.isfile(self.info[t]):
          self.info[t] = os.path.join(dir, self.info[t])
          if not os.path.isfile(self.info[t]): del(self.info[t])


class DanceFile(GenericFile):
  WAITING,METADATA,DESCRIPTION,LYRICS,BACKGROUND,GAMETYPE,STEPS = range(7)

  def __init__(self, filename, need_steps):
    GenericFile.__init__(self, filename, need_steps)
    self.comment = "#"

    parsers = [self.parse_waiting, self.parse_metadata, self.parse_description,
               self.parse_lyrics, self.parse_bg, self.parse_gametype,
               self.parse_steps]

    state = DanceFile.METADATA
    state_data = [None, None]

    f = file(filename)

    for line in f:
      line = line.strip()
      if line == "" or line[0] == "#": continue
      elif line == "end": state = DanceFile.WAITING
      elif state == DanceFile.STEPS and not need_steps: pass
      else: state = parsers[state](line, state_data)

    self.resolve_files_sanely()

    if self.info.has_key("preview"):
      start, length = self.info["preview"].split()
      self.info["preview"] = (float(start), float(length))

  def parse_metadata(self, line, data):
    parts = line.split()
    line2 = line[len(parts[0]):].strip()
    self.info[parts[0]] = line2
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

  def parse_bg(self, line, data):
    return DanceFile.BACKGROUND

  def parse_gametype(self, line, data):
    data[1], diff = line.split()
    self.difficulty[data[0]][data[1]] = int(diff)
    if data[0] in games.COUPLE:
      self.steps[data[0]][data[1]] = [[], []]
    else: self.steps[data[0]][data[1]] = []
    return DanceFile.STEPS

  def parse_steps(self, line, data):
    if not self.need_steps: return DanceFile.STEPS

    parts = line.split()
    if data[0] in games.COUPLE:
      steps = [[parts[0]], [parts[0]]]
      if parts[0] in ("B", "W", "S", "D"):
        steps[0].append(float(parts[1]))
        steps[1].append(float(parts[1]))
      elif parts[0] in ("o", "h", "q", "e", "w", "s", "f", "t", "x", "n", "u"):
        steps[0].extend([int(s) for s in parts[1]])
        steps[1].extend([int(s) for s in parts[2]])
      elif parts[0] == "L":
        steps[0].extend((int(parts[1]), " ".join(parts[2:])))
        steps[1].extend((int(parts[1]), " ".join(parts[2:])))
      self.steps[data[0]][data[1]][0].append(steps[0])
      self.steps[data[0]][data[1]][1].append(steps[1])

    else:
      steps = [parts[0]]
      if parts[0] in ("B", "W", "S", "D"): steps.append(float(parts[1]))
      elif parts[0] in ("o", "h", "q", "e", "w", "s", "f", "t", "x", "n", "u"):
        steps.extend([int(s) for s in parts[1]])
      elif parts[0] == "L": steps.extend((int(parts[1]), " ".join(parts[2:])))
      self.steps[data[0]][data[1]].append(steps)
      
    return DanceFile.STEPS

  def parse_lyrics(self, line, data):
    parts = line.split()
    self.lyrics.append((float(parts[0]), int(parts[1]), " ".join(parts[2:])))
    return DanceFile.LYRICS

  def parse_description(self, line, data):
    if line == ".": self.description.append(None)
    elif self.description is None: self.description = [line]
    elif self.description[-1] is None: self.description[-1] = line
    else: self.description[-1] += " " + line

    return DanceFile.DESCRIPTION

class StepFile(GenericFile):
  METADATA, GAMETYPE, LYRICS, STEPS, WAITING = range(5)
  word_trans = { "whole": "o", "halfn": "h", "qurtr": "q", "eight": "e",
                 "tripl": "w", "steps": "s", "twtfr": "f", "thrty": "t",
                 "sixty": "x", "ready": "R", "chbpm": "B", "waits": "W",
                 "delay": "D", "tstop": "S",
                 "00": 0, "08": 1, "88": 3, "80": 2 }

  def __init__(self, filename, need_steps):
    GenericFile.__init__(self, filename, need_steps)
    self.comment = "#"

    f = open(filename)
    # parser states
    state = StepFile.METADATA
    state_data = [None, None] # sec, diff, or time in lyric mode
    parsers = [self.parse_metadata, self.parse_gametype,
               self.parse_lyrics, self.parse_steps, self.parse_waiting]

    if not need_steps: parsers[StepFile.STEPS] = self.parse_dummy_steps

    for line in f:
      line = self.strip_line(line)
      if line != "": state, state_data = parsers[state](line, state_data)

    for old, new in (("song", "title"), ("group", "artist"),
                     ("offset", "gap"), ("bg", "background"),
                     ("file", "filename")):
      if self.info.has_key(old):
        self.info[new] = self.info[old]
        del(self.info[old])

    self.info["gap"] = int(self.info.get("gap", 0))
    self.info["bpm"] = float(self.info["bpm"])

    if self.info.has_key("version"): del(self.info["version"])

    self.resolve_files_sanely()

    dir, name = os.path.split(self.filename)
    for t in (("banner", ".png"), ("banner", "-full.png"),
              ("background", "-bg.png"), ("filename", ".ogg"),
              ("filename", ".mp3"), ("movie", ".mpg")):
      if not self.info.has_key(t[0]):
        possible = os.path.join(dir, name.replace(".step", t[1]))
        possible = os.path.realpath(possible)
        if os.path.isfile(possible): self.info[t[0]] = possible

    self.find_subtitle()
    self.description = None

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
        line2 = line[len(parts[0]):].strip()
        self.info[parts[0]] = line2
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
        self.lyrics.append((data[0] - 0.4, 1, " ".join(parts[1:])))
      elif parts[0] == "trans":
        self.lyrics.append((data[0] - 0.4, 0, " ".join(parts[1:])))
    return StepFile.LYRICS, data

  def parse_waiting(self, line, data):
    if line == "LYRICS": return StepFile.LYRICS, data
    elif line == line.upper():
      data[0] = line
      if not self.steps.has_key(data[0]): self.steps[data[0]] = {}
      if not self.difficulty.has_key(data[0]): self.difficulty[data[0]] = {}
      return StepFile.GAMETYPE, data

class DWIFile(GenericFile):
  modes = { "{": "x", "[": "f", "(": "s", "`": "n",
            "'": "n", ")": "e", "]": "e", "}": "e" }
  times = { "x": 0.25, "f": 2.0/3.0, "s": 1.0, "e": 2.0, "n": 1/12.0 }
  steps = {
    "0": [0, 0, 0, 0],
    "1": [1, 1, 0, 0],
    "2": [0, 1, 0, 0],
    "3": [0, 1, 0, 1],
    "4": [1, 0, 0, 0],
    "6": [0, 0, 0, 1],
    "7": [1, 0, 1, 0],
    "8": [0, 0, 1, 0],
    "9": [0, 0, 1, 1],
    "A": [0, 1, 1, 0],
    "B": [1, 0, 0, 1]
    }

  def __init__(self, filename, need_steps):
    GenericFile.__init__(self, filename, need_steps)
    self.comment = "//"

    self.bpms = []
    self.freezes = []

    f = open(filename)
    tokens = "".join([self.strip_line(line) for line in f])
    tokens = tokens.replace(";", "")
    tokens = tokens.split("#")

    for token in tokens:
      if len(token) == 0: continue
      parts = token.split(":")
      if len(parts) == 4 and parts[0] in games.SINGLE:
        if not self.difficulty.has_key(parts[0]):
          self.difficulty[parts[0]] = {}
          self.steps[parts[0]] = {}
        self.difficulty[parts[0]][parts[1]] = int(float(parts[2]))
        if need_steps: self.parse_steps(parts[0], parts[1], parts[3])

      elif len(parts) == 5 and parts[0] in games.COUPLE:
        if not self.difficulty.has_key(parts[0]):
          self.difficulty[parts[0]] = {}
          self.steps[parts[0]] = {}
        self.difficulty[parts[0]][parts[1]] = int(float(parts[2]))
        if need_steps:
          self.parse_steps(parts[0], parts[1], parts[3])
          self.parse_steps(parts[0], parts[1], parts[4])

      else: # This is some sort of metadata key
        # don't support filenames. They're useless cross-platform.
        # Don't support genre, it's a dumbass tag
        if parts[0] == "GAP": self.info["gap"] = -int(float(parts[1]))
        elif parts[0] == "TITLE": self.info["title"] = ":".join(parts[1:])
        elif parts[0] == "ARTIST": self.info["artist"] = ":".join(parts[1:])
        elif parts[0] == "MD5": self.info["md5sum"] = parts[1]
        elif parts[0] == "BPM": self.info["bpm"] = float(parts[1])
        elif parts[0] == "SAMPLESTART":
          if self.info.has_key("preview"):
            self.info["preview"][0] = self.parse_time(parts[1])
          else: self.info["preview"] = [self.parse_time(parts[1]), 10]
        elif parts[0] == "SAMPLELENGTH":
          if self.info.has_key("preview"):
            self.info["preview"][1] = self.parse_time(parts[1])
          else: self.info["preview"] = [45, self.parse_time(parts[1])]
        elif parts[0] == "CHANGEBPM":
          for change in parts[1].split(","):
            beat, bpm = change.split("=")
            self.bpms.append((float(beat), float(bpm)))
        elif parts[0] == "FREEZE":
          for change in parts[1].split(","):
            beat, wait = change.split("=")
            self.freezes.append((float(beat), float(wait)/1000.0))

    self.find_mixname()
    self.find_files_insanely()
    self.find_subtitle()

# For this to be really useful we need better heuristics
#    for key in ("title", "subtitle", "artist", "mix"):
#      if self.info.has_key(key):
#        self.info[key] = util.titlecase(self.info[key])

    for game in self.difficulty:
      for odiff, ndiff in (("ANOTHER", "TRICK"), ("SMANIAC", "HARDCORE")):
        if self.difficulty[game].has_key(odiff):
          self.difficulty[game][ndiff] = self.difficulty[game][odiff]
          del(self.difficulty[game][odiff])
          if need_steps:
            self.steps[game][ndiff] = self.steps[game][odiff]
            del(self.steps[game][odiff])

  def parse_steps(self, mode, diff, steps):
    step_type = "e"
    current_time = 0
    bpmidx = 0
    freezeidx = 0
    steplist = []
    steps = steps.replace(" ", "")
    steps = list(steps)
    while len(steps) != 0:
      if steps[0] in DWIFile.modes: step_type = DWIFile.modes[steps.pop(0)]
      elif steps[0] in DWIFile.steps:
        step = list(DWIFile.steps[steps.pop(0)])
        if len(steps) > 0 and steps[0] == "!":
          steps.pop(0)
          holdstep = DWIFile.steps[steps.pop(0)]
          for i in range(len(holdstep)):
            if holdstep[i]: step[i] |= 2
        steplist.append([step_type] + step)
        current_time += DWIFile.times[step_type]

        for xyz in self.bpms[bpmidx:]:
          if current_time >= xyz[0]:
            steplist.append(["B", float(xyz[1])])
            bpmidx += 1
        for xyz in self.freezes[freezeidx:]:
          if current_time >= xyz[0]:
            steplist.append(["S", float(xyz[1])])
            freezeidx += 1
      elif steps[0] == "<":
        steps.pop(0)
        tomerge = []
        while steps[0] != ">": tomerge.append(steps.pop(0))
        steps.pop(0)
        steplist.append([step_type] + self.parse_merge(tomerge))
      else: steps.pop(0)

    if mode in games.SINGLE: self.steps[mode][diff] = steplist
    elif mode in games.COUPLE:
      if self.steps[mode].get(diff) == None: self.steps[mode][diff] = []
      self.steps[mode][diff].append(steplist)

  def parse_merge(self, steps):
    ret = [0] * 20
    while len(steps) != 0:
      if steps[0] == "!":
        steps.pop(0)
        val = DWIFile.steps[steps[0]]
        ret = [a | (2 * b) for a, b in zip(ret, val)]
      else:
        val = DWIFile.steps[steps[0]]
        ret = [a | b for a, b in zip(ret, val)]
      steps.pop(0)
      
    return ret

class SMFile(GenericFile):

  gametypes = { "dance-single": "SINGLE", "dance-double": "DOUBLE",
                "dance-couple": "COUPLE" }
  notecount = { "SINGLE": 4, "DOUBLE": 8, "COUPLE": 8 }
  notetypes = { 192: "n", 64: "x", 48: "u", 32: "t", 24: "f",
                16: "s", 12: "w", 8: "e", 4: "q", 2: "h", 1: "o" }

  step = [0, 1, 3, 1]

  def __init__(self, filename, need_steps):
    GenericFile.__init__(self, filename, need_steps)
    self.comment = "//"

    self.bpms = []
    self.freezes = []

    f = open(filename)
    tokens = "".join([self.strip_line(line) for line in f])
    tokens = tokens.replace(";", "")
    tokens = tokens.split("#")

    for token in tokens:
      if len(token) == 0: continue
      parts = token.split(":")
      if parts[0] == "OFFSET": self.info["gap"] = float(parts[1]) * 1000
      elif parts[0] == "TITLE": self.info["title"] = ":".join(parts[1:])
      elif parts[0] == "SUBTITLE": self.info["subtitle"] = ":".join(parts[1:])
      elif parts[0] == "ARTIST": self.info["artist"] = ":".join(parts[1:])
      elif parts[0] == "MUSIC": self.info["filename"] = ":".join(parts[1:])
      elif parts[0] == "BANNER": self.info["banner"] = ":".join(parts[1:])
      elif parts[0] == "BACKGROUND":
        self.info["background"] = ":".join(parts[1:])
      elif parts[0] == "MD5": self.info["md5sum"] = parts[1]
      elif parts[0] == "SAMPLESTART":
        if self.info.has_key("preview"):
          self.info["preview"][0] = float(parts[1])
        else: self.info["preview"] = [float(parts[1]), 10]
      elif parts[0] == "SAMPLELENGTH":
        if self.info.has_key("preview"):
          self.info["preview"][1] = float(parts[1])
        else: self.info["preview"] = [45, float(parts[1])]
      elif parts[0] == "BPMS":
        for change in parts[1].split(","):
          if "=" in change:
            beat, bpm = change.split("=")
            self.bpms.append((float(beat), float(bpm)))
        self.info["bpm"] = self.bpms.pop(0)[1]
      elif parts[0] == "STOPS":
        for change in parts[1].split(","):
          if "=" in change:
            beat, wait = change.split("=")
            self.freezes.append((float(beat), float(wait)/1000.0))
      elif parts[0] == "NOTES":
        if parts[1] in SMFile.gametypes:
          game = SMFile.gametypes[parts[1]]
          if not self.difficulty.has_key(game):
            self.difficulty[game] = {}
            self.steps[game] = {}
          self.difficulty[game][parts[2].upper()] = int(parts[4])
          if need_steps:
            self.steps[game][parts[2].upper()] = self.parse_steps(parts[6], game)

    self.find_mixname()
    for k in ("banner", "background", "filename"):
      if not os.path.isfile(self.info.get(k, "")):
        del(self.info[k])
    
    if not (self.info.has_key("background") or self.info.has_key("banner")):
      self.find_files_insanely()
    self.resolve_files_sanely()

  def parse_steps(self, steps, gametype):
    stepdata = []
    if gametype in games.COUPLE: stepdata = [[], []]
    beat = 0
    count = SMFile.notecount[gametype]
    bpmidx = 0
    freezeidx = 0
    measures = steps.split(",")
    for measure in measures:
      measure = measure.replace(" ", "")
      notetype = len(measure)/count
      if notetype in SMFile.notetypes:
        note = SMFile.notetypes[notetype]
      else: note = 16 * notetype
      while len(measure) != 0:
        sd = measure[0:count]
        measure = measure[count:]
        if gametype in games.COUPLE:
          step1 = [note]
          step2 = [note]
          step1.extend([SMFile.step[int(s)] for s in sd[0:count/2]])
          step2.extend([SMFile.step[int(s)] for s in sd[count/2:]])
          stepdata[0].append(step1)
          stepdata[1].append(step2)
        else:
          step = [note]
          step.extend([SMFile.step[int(s)] for s in sd])
          stepdata.append(step)

        beat += 4.0 / notetype

        for xyz in self.bpms[bpmidx:]:
          if beat >= xyz[0]:
            if gametype in games.COUPLE:
              stepdata[0].append(["B", float(xyz[1])])
              stepdata[1].append(["B", float(xyz[1])])
            else:
              stepdata.append(["B", float(xyz[1])])
            bpmidx += 1
        for xyz in self.freezes[freezeidx:]:
          if beat >= xyz[0]:
            if gametype in games.COUPLE:
              stepdata[0].append(["S", float(xyz[1])])
              stepdata[1].append(["S", float(xyz[1])])
            else:
              stepdata.append(["S", float(xyz[1])])
            freezeidx += 1

    return stepdata

formats = ((".step", StepFile),
           (".dance", DanceFile),
           (".dwi", DWIFile),
           (".sm", SMFile))

DIFFICULTIES = ["BEGINNER", "LIGHT", "BASIC", "ANOTHER", "STANDARD", "TRICK",
                "MANIAC", "HEAVY", "HARDCORE", "CHALLENGE", "SMANIAC", "ONI"]

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
               "mix": "No Mix",
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
    for k in ("subtitle", "background", "banner",
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
      paras = "\n.\n".join(self.description)
      f.write("DESCRIPTION\n" + paras + "\nend\n")
      
    if self.lyrics != []:
      f.write("LYRICS\n")
      for lyr in self.lyrics:  f.write(" ".join([str(l) for l in lyr]) + "\n")
      f.write("end\n")

    for game in self.difficulty:
      for diff in self.difficulty[game]:
        f.write(game + "\n")
        f.write(diff + " " + str(self.difficulty[game][diff]) + "\n")

        if not game in games.COUPLE:
          for step in self.steps[game][diff]:
            extra = ""
            if step[0] in ("B", "W", "S", "D"): extra = str(step[1])
            elif step[0] in ("o", "h", "q", "e", "w", "s", "f", "t", "x", "u"):
              extra = "".join([str(i) for i in step[1:]])
            elif step[0] == "L": extra = " ".join([str(i) for i in step[1:]])
            f.write(step[0] + " " + extra + "\n")
          f.write("end\n")
        else:
          to_write = []
          for step1, step2 in zip(*self.steps[game][diff]):
            if step1[0] != step2[0]:
              print "Unable to convert %s %s mode steps" % (game, diff)
              break
            else:
              if step1[0] in ("B", "W", "S", "D"): extra = str(step1[1])
              elif step[0] in ("o", "h", "q", "e", "w", "s", "f", "t", "x", "n"):
                extra = "".join([str(i) for i in step1[1:]])
                extra += " " + "".join([str(i) for i in step2[1:]])
              elif step1[0] == "L":
                extra = " ".join([str(i) for i in step1[1:]])
              to_write.append(step1[0] + " " + extra + "\n")
          else:
            to_write.append("end\n")
            for line in to_write: f.write(line)
            

    f.close()
