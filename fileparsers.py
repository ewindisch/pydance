# Read in various file formats and translate them to the internal structure
# that Steps and SongData want.

from constants import *

import os, stat, util, string, dircache, copy

import games

# The basic skeleton parser/song class.
class GenericFile(object):
  def __init__(self, filename, need_steps):
    self.filename = filename
    self.difficulty = {}
    self.steps = {}
    self.info = {}
    self.lyrics = []
    self.description = None
    self.need_steps = need_steps

  # Find a list of files with a given extension in the directory.
  # We call this a lot (2x / DWI/SM), so it should be as fast as possible.
  def find_files(self, formats):
    files = []

    dir = os.path.split(self.filename)[0]
    if dir == "": dir = "."

    files = [os.path.join(dir, f) for f in dircache.listdir(dir) if
             f.lower()[-3:] in formats]

    files.sort(lambda a, b: cmp(os.stat(a).st_size, os.stat(b).st_size))
    return files

  # Try to extract a subtitle from formats that don't support it (DWI, step)
  # Recognize ()s, []s, --s, or ~~s.
  def find_subtitle(self):
    if not self.info.has_key("subtitle"):
      for pair in (("[", "]"), ("(", ")"), ("~", "~"), ("-", "-")):
        if pair[0] in self.info["title"] and self.info["title"][-1] == pair[1]:
          l = self.info["title"][0:-1].rindex(pair[0])
          if l != 0:
            self.info["subtitle"] = self.info["title"][l+1:-1]
            self.info["title"] = self.info["title"][:l]
            break

  # If a filename isn't found, try joining it with the path of the song's
  # filename.
  def resolve_files_sanely(self):
    dir, name = os.path.split(self.filename)
    for t in ("banner", "filename", "movie", "background"):
      if self.info.has_key(t):
        if not os.path.isfile(self.info[t]):
          self.info[t] = os.path.join(dir, self.info[t])
          if not os.path.isfile(self.info[t]): del(self.info[t])

  # DWI has an insane number of time formats.
  def parse_time(self, string):
    offset = 0
    time = 0
    if string[0] == "+": # Any prepended + means add the offset of the file.
      string = string[1:]
      offset = self.info["gap"]
    if ":" in string:
      parts = string.split(":")
      # M:SS format; also M:SS.SS (only seen once)
      if len(parts) == 2: time = 60 * int(parts[0]) + float(parts[1])
      elif len(parts) == 3: ## M:SS:CS
        time = int(parts[0]) + float(parts[1]) + float(parts[2]) / 100
    elif "." in string: time = float(string) # seconds in a float value
    else: time = int(string) / 1000.0 # no punctuation means in milliseconds
    return offset + time

# The .dance file format, pydance's native format. It has a very close
# mapping to the internal structure. Unfortunately, Python's function
# call overhead makes parsing it remarkably slow. See docs/dance-spec.txt
# for more information.
class DanceFile(GenericFile):
  WAITING,METADATA,DESCRIPTION,LYRICS,BACKGROUND,GAMETYPE,STEPS = range(7)

  BEATS = { 'x': 0.25, 't': 0.5, 'u': 1.0/3.0, 'f': 2.0/3.0,
            's': 1.0, 'w': 4.0/3.0, 'e': 2.0,
            'q': 4.0, 'h': 8.0, 'o': 16.0, 'n': 1/12.0 }

  def __init__(self, filename, need_steps):
    GenericFile.__init__(self, filename, need_steps)

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

    if self.info.has_key("preview"):
      start, length = self.info["preview"].split()
      self.info["preview"] = (float(start), float(length))

    self.resolve_files_sanely()

  def parse_metadata(self, line, data):
    parts = line.split()
    line2 = line[len(parts[0]):].strip() # Keep multiple spaces in the value.
    self.info[parts[0]] = line2
    return DanceFile.METADATA

  def parse_waiting(self, line, data):
    if line == "DESCRIPTION": return DanceFile.DESCRIPTION
    elif line == "LYRICS": return DanceFile.LYRICS
    elif line == "BACKGROUND": return DanceFile.LYRICS
    else:
      data[0] = line
      if not self.difficulty.has_key(line):
        self.difficulty[line] = {}
        self.steps[line] = {}
      return DanceFile.GAMETYPE

  # FIXME: We don't actually parse the background change data yet.
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
      elif parts[0] in DanceFile.BEATS:
        steps = [[DanceFile.BEATS[parts[0]]], [DanceFile.BEATS[parts[0]]]]
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
      elif parts[0] in DanceFile.BEATS:
        steps = [DanceFile.BEATS[parts[0]]]
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

# The old pyDDR .step format. On the surface it looks like .dance, but
# a lot of bad/inconsistent design problems make it trickier to parse.
class StepFile(GenericFile):
  METADATA, GAMETYPE, LYRICS, STEPS, WAITING = range(5)
  word_trans = { "whole": 16.0, "halfn": 8.0, "qurtr": 4.0, "eight": 2.0,
                 "tripl": 4.0/3.0, "steps": 1.0, "twtfr": 2.0/3.0,
                 "thrty": 0.5, "sixty": 0.25,
                 "ready": "R", "chbpm": "B", "waits": "W",
                 "delay": "D", "tstop": "S",
                 "00": 0, "08": 1, "88": 3, "80": 2 }

  def __init__(self, filename, need_steps):
    GenericFile.__init__(self, filename, need_steps)

    f = open(filename)

    state = StepFile.METADATA
    state_data = [None, None]
    parsers = [self.parse_metadata, self.parse_gametype,
               self.parse_lyrics, self.parse_steps, self.parse_waiting]

    if not need_steps: parsers[StepFile.STEPS] = self.parse_dummy_steps

    for line in f:
      line = line.strip()
      if line != "" and line[0] != "#":
        state, state_data = parsers[state](line, state_data)

    for old, new in (("song", "title"), ("group", "artist"),
                     ("offset", "gap"), ("bg", "background"),
                     ("file", "filename")):
      if self.info.has_key(old):
        self.info[new] = self.info[old]
        del(self.info[old])

    self.info["gap"] = int(self.info.get("gap", 0))
    self.info["bpm"] = float(self.info["bpm"])

    if self.info.has_key("version"): del(self.info["version"])

    dir, name = os.path.split(self.filename)
    for t in (("banner", ".png"), ("banner", "-full.png"),
              ("background", "-bg.png"), ("filename", ".ogg"),
              ("filename", ".mp3"), ("movie", ".mpg")):
      if not self.info.has_key(t[0]):
        possible = os.path.join(dir, name.replace(".step", t[1]))
        possible = os.path.realpath(possible)
        if os.path.isfile(possible): self.info[t[0]] = possible

    self.find_subtitle()
    self.resolve_files_sanely()

  def parse_metadata(self, line, data):
    if line == "LYRICS": return StepFile.LYRICS, [None, None]
    else:
      parts = line.split()
      if len(parts) == 1:
        data[0] = line
        if not self.difficulty.has_key(line):
          self.difficulty[line] = {}
          self.steps[line] = {}
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

  # .step's lyrics come in alternate lines (usually), the first giving the
  # second the lyric is at, and the second actually giving the lyric.
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

# Parse a file using MSD-style syntax, that is:
# #TAG:FIELD1:FIELD2:...; // indicate comments until the end of the line.
# Whitespace is stripped before and after each tag/field.
# Newlines are allowed within fields and should be removed.
# We'll assume newlines are mandatory after ;, I've never seen another
# case in the wild.
class MSDFile(GenericFile):
  def __init__(self, filename, need_steps):
    GenericFile.__init__(self, filename, need_steps)
    lines = []
    f = open(filename)
    for line in f:
      if line.find("//") != -1: line = line[:line.find("//")]
      line = line.strip()

      if len(line) == 0: continue
      elif line[0] == "#": lines.append(line[1:]) # A new tag
      else: lines[-1] += line

    for i in range(len(lines)):
      line = lines[i]
      while line[-1] == ";": line = line[:-1] # Some lines have two ;s.
      lines[i] = line.split(":")

    # Return a list of lists, [tag, field1, field2, ...]
    return lines

  def find_mixname(self):
    dir, name = os.path.split(self.filename)
    mixname = os.path.split(os.path.split(dir)[0])[1]
    if mixname != "songs": self.info["mix"] = mixname

  # MSD-style files use DWI's .lrc lyric format
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
        self.lyrics.extend([(time, i + 1, lyr[i]) for i in range(len(lyr)) if
                            lyr[i] != ""])

  # Return a list of all the images in the directory, sorted by file size
  def find_images(self):
    return self.find_files(["png", "jpg", "peg", "bmp"])

  # Find all audio files
  def find_audio(self):
    return self.find_files(["ogg", "mp3", "wav", ".xm"])

  # DWI finds files based on their image size, not on any naming conventions.
  # However, naming conventions combined with file size appears to be a
  # useful and accurate heuristic.

  # Many SMs actually contain accurate information about their filenames,
  # so do some checks to avoid unnecessary searching.
  def find_files_sanely(self):
    if not (os.path.exists(self.info.get("banner", "")) and
            os.path.exists(self.info.get("background", ""))):
      images = self.find_images()
      for image in list(images):
        image_lower = os.path.split(image)[1].lower()
        if image_lower.find("bg") != -1 or image_lower.find("back") != -1:
          self.info["background"] = image
        elif image_lower.find("ban") != -1 or image_lower.find("bn") != -1:
          self.info["banner"] = image

      if len(images) > 0:
        self.info["background"] = self.info.get("background", images[-1])
        if self.info["background"] in images:
          images.remove(self.info["background"])
      if len(images) > 0:
        self.info["banner"] = self.info.get("banner", images[-1])

    if not (os.path.exists(self.info.get("filename", ""))):
      audio = self.find_audio()
      if len(audio) > 0:
        for fn in audio:
          if fn.lower()[-3:] == "ogg":
            self.info["filename"] = fn
          elif (fn.lower()[-3:] in ["mp3", "wav"] and
                self.info.get("filename", "").lower()[-3:] != "ogg"):
            self.info["filename"] = fn

    lyrics = self.find_files(["lrc"])
    if len(lyrics) > 0: self.parse_lyrics(lyrics[0])

# The DWI format, from Dance With Intensity.
class DWIFile(MSDFile):
  modes = { "{": 0.25, "[": 2.0/3.0, "(": 1.0, "`": 1.0/12.0,
            "'": 2.0, ")": 2.0, "]": 2.0, "}": 2.0 }
  steps = {
    "SINGLE": { "0": [0, 0, 0, 0], "1": [1, 1, 0, 0], "2": [0, 1, 0, 0],
                "3": [0, 1, 0, 1], "4": [1, 0, 0, 0], "6": [0, 0, 0, 1],
                "7": [1, 0, 1, 0], "8": [0, 0, 1, 0], "9": [0, 0, 1, 1],
                "A": [0, 1, 1, 0], "B": [1, 0, 0, 1] },
    "6PANEL": { "0": [0, 0, 0, 0, 0, 0], "1": [1, 0, 1, 0, 0, 0],
                "2": [0, 0, 1, 0, 0, 0], "3": [0, 0, 1, 0, 0, 1],
                "4": [1, 0, 0, 0, 0, 0], "6": [0, 0, 0, 0, 0, 1],
                "7": [1, 0, 0, 1, 0, 0], "8": [0, 0, 0, 1, 0, 0],
                "9": [0, 0, 0, 1, 0, 1], "A": [0, 0, 1, 1, 0, 0],
                "B": [1, 0, 0, 0, 0, 1], "C": [0, 1, 0, 0, 0, 0],
                "D": [0, 0, 0, 0, 1, 0], "E": [1, 1, 0, 0, 0, 0],
                "F": [0, 1, 1, 0, 0 ,0], "G": [0, 1, 0, 1, 0, 0],
                "H": [0, 1, 0, 0, 0, 1], "I": [1, 0, 0, 0, 1, 0],
                "J": [0, 0, 1, 0, 1, 0], "K": [0, 0, 0, 1, 1, 0],
                "L": [0 ,0, 0, 0, 1, 1], "M": [0, 1, 0, 0, 1, 0]
                },
    }

  steps["DOUBLE"] = steps["COUPLE"] = steps["SINGLE"]

  diff_map = { "ANOTHER": "TRICK", "SMANIAC": "HARDCORE",
               "S-MANIAC": "HARDCORE" }

  game_map = { "SOLO": "6PANEL" }

  def __init__(self, filename, need_steps):
    lines = MSDFile.__init__(self, filename, need_steps)

    self.bpms = []
    self.freezes = []

    for parts in lines:
      if len(parts) > 3:
        parts[0] = DWIFile.game_map.get(parts[0], parts[0])
        parts[1] = DWIFile.diff_map.get(parts[1], parts[1])

      rest = ":".join(parts[1:]).strip()

      # I think this is the fault of the SM editor; some DWIs have blank
      # fields (not many; basically all SMs do).
      if rest == "": continue

      # don't support filenames. They're useless cross-platform.
      # Don't support genre, it's a dumbass tag
      if parts[0] == "GAP": self.info["gap"] = -int(float(rest))
      elif parts[0] == "TITLE": self.info["title"] = rest.decode("iso-8859-1").encode("utf-8")
      elif parts[0] == "ARTIST": self.info["artist"] = rest.decode("iso-8859-1").encode("utf-8")
      elif parts[0] == "MD5": self.info["md5sum"] = rest
      elif parts[0] == "BPM": self.info["bpm"] = float(rest)
      elif parts[0] == "SAMPLESTART":
        if self.info.has_key("preview"):
          self.info["preview"][0] = self.parse_time(rest)
        else: self.info["preview"] = [self.parse_time(rest), 10]
      elif parts[0] == "SAMPLELENGTH":
        if self.info.has_key("preview"):
          self.info["preview"][1] = self.parse_time(rest)
        else: self.info["preview"] = [45, self.parse_time(rest)]
      elif parts[0] == "CHANGEBPM":
        rest = rest.replace(" ", "")
        self.bpms = [(float(beat), float(bpm)) for beat, bpm in
                     [change.split("=") for change in rest.split(",")]]
      elif parts[0] == "FREEZE":
        rest = rest.replace(" ", "")
        self.freezes = [(float(beat), float(wait)/1000) for beat, wait in
                        [change.split("=") for change in rest.split(",")]]
      elif len(parts) == 4 and parts[0] not in games.COUPLE:
        if not self.difficulty.has_key(parts[0]):
          self.difficulty[parts[0]] = {}
          self.steps[parts[0]] = {}
        self.difficulty[parts[0]][parts[1]] = int(float(parts[2]))
        if need_steps:
          self.parse_steps(parts[0], parts[1], parts[3])

      elif len(parts) == 5 and parts[0] in games.COUPLE:
        if not self.difficulty.has_key(parts[0]):
          self.difficulty[parts[0]] = {}
          self.steps[parts[0]] = {}
        self.difficulty[parts[0]][parts[1]] = int(float(parts[2]))
        if need_steps:
          self.parse_steps(parts[0], parts[1], parts[3])
          self.parse_steps(parts[0], parts[1], parts[4])

    self.find_mixname()
    self.find_subtitle()
    self.find_files_sanely()
    self.resolve_files_sanely()

  def parse_steps(self, mode, diff, steps):
    if mode not in DWIFile.steps: return
    step_type = 2.0
    current_time = 0
    bpmidx = 0
    freezeidx = 0
    steplist = []
    steps = steps.replace(" ", "")
    steps = list(steps)
    dwifile_steps = DWIFile.steps[mode]
    while len(steps) != 0:
      if steps[0] in DWIFile.modes: step_type = DWIFile.modes[steps.pop(0)]
      elif steps[0] in dwifile_steps:
        step = list(dwifile_steps[steps.pop(0)])
        if len(steps) > 0 and steps[0] == "!":
          steps.pop(0)
          possible = steps.pop(0)
          if possible in dwifile_steps:
            holdstep = dwifile_steps[possible]
          elif possible in DWIFile.modes:
            # Some DWI files have things like ...2!(2...
            step_type = DWIFile.modes[possible]
            holdstep = dwifile_steps[steps.pop(0)]
          for i in range(len(holdstep)):
            if holdstep[i]: step[i] |= 2
        steplist.append([step_type] + step)
        current_time += step_type

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
        steplist.append([step_type] + self.parse_merge(tomerge, dwifile_steps))
      else: steps.pop(0)

    if mode not in games.COUPLE: self.steps[mode][diff] = steplist
    else:
      if self.steps[mode].get(diff) == None: self.steps[mode][diff] = []
      self.steps[mode][diff].append(steplist)

  def parse_merge(self, steps, dwifile_steps):
    ret = [0] * 20
    while len(steps) != 0:
      if steps[0] == "!":
        steps.pop(0)
        val = dwifile_steps[steps[0]]
        ret = [a | (2 * b) for a, b in zip(ret, val)]
      else:
        val = dwifile_steps[steps[0]]
        ret = [a | b for a, b in zip(ret, val)]
      steps.pop(0)
      
    return ret

class SMFile(MSDFile):

  gametypes = { "dance-single": "SINGLE", "dance-double": "DOUBLE",
                "dance-couple": "COUPLE", "dance-solo": "6PANEL",
                "pump-single": "5PANEL", "pump-couple": "5COUPLE",
                "pump-double": "5DOUBLE", "para-single": "PARAPARA" }
  notecount = { "SINGLE": 4, "DOUBLE": 8, "COUPLE": 8, "PARAPARA": 5,
                "5PANEL": 5, "6PANEL": 6, "5COUPLE": 10, "5DOUBLE": 10 }

  step = [0, 1, 3, 1]

  def __init__(self, filename, need_steps):
    lines = MSDFile.__init__(self, filename, need_steps)

    self.bpms = []
    self.freezes = []

    for parts in lines:

      rest = ":".join(parts[1:]).strip()

      # A lot of SM files have blank fields; I blame the editor.
      if rest == "": continue

      if parts[0] == "OFFSET": self.info["gap"] = float(parts[1]) * 1000
      elif parts[0] == "TITLE": self.info["title"] = rest
      elif parts[0] == "SUBTITLE": self.info["subtitle"] = rest
      elif parts[0] == "ARTIST": self.info["artist"] = rest
      elif parts[0] == "CREDIT": self.info["author"] = rest
      elif parts[0] == "MUSIC": self.info["filename"] = rest
      elif parts[0] == "BANNER": self.info["banner"] = rest
      elif parts[0] == "BACKGROUND": self.info["background"] = rest
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
        rest = rest.replace(" ", "")
        self.bpms = [(float(beat), float(bpm)) for beat, bpm in
                     [change.split("=") for change in rest.split(",")]]
        self.info["bpm"] = self.bpms.pop(0)[1]
      elif parts[0] == "STOPS":
        rest = rest.replace(" ", "")
        self.freezes = [(float(beat), float(wait)) for beat, wait in
                     [change.split("=") for change in rest.split(",")]]
      elif parts[0] == "NOTES":
        if parts[1] in SMFile.gametypes:
          game = SMFile.gametypes[parts[1]]
          if not self.difficulty.has_key(game):
            self.difficulty[game] = {}
            self.steps[game] = {}
          if parts[2] == "": parts[2] = parts[3]
          if parts[2][-2] == "_": # This is a KSF-style difficulty
            parts[2] = parts[2][:-2]
          self.difficulty[game][parts[2].upper()] = int(parts[4])
          if need_steps:
            self.steps[game][parts[2].upper()] = self.parse_steps(parts[6], game)

    self.find_mixname()
    self.resolve_files_sanely()
    self.find_files_sanely()

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

      if notetype != 0: note = 16.0 / notetype
      else: beat += 4.0 # This was an empty measure

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

        beat += note / 4.0

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

# We have to detect KSFs via 'Song.ext' rather than the actual KSF
# files, since they're split up.
class KSFFile(MSDFile):

  def __init__(self, filename, need_steps):
    GenericFile.__init__(self, filename, need_steps)

    self.info = {"artist": "Unknown", "title": "Unknown"}
    self.difficulty = {}
    self.steps = {}

    self.info["filename"] = filename

    path = os.path.split(filename)[0]
    for fn in dircache.listdir(path):
      fullname = os.path.join(path, fn)
      fn_lower = fn.lower()
      if fn_lower[-3:] == "ksf": self.parse_ksf(fullname)
      elif fn_lower[:4] == "disc": self.info["banner"] = fullname
      elif fn_lower[:5] == "intro": self.info["preview"] = fullname
      elif fn_lower[:4] == "back" or fn_lower[:5] == "title":
        self.info["background"] = fullname

    self.find_mixname()
    try:
      self.info["title"] = self.info["title"].decode("cp949").encode("utf-8")
      self.info["artist"] = self.info["artist"].decode("cp949").encode("utf-8")
    except LookupError: pass # Encoding support not available.

  def parse_ksf(self, filename):
    steps = []

    mode = "5PANEL"

    name = os.path.split(filename)[1]

    holding = []

    parts = name.split("_")
    if len(parts) == 1:
      couple = True
      difficulty = "NORMAL"
      mode = "5DOUBLE"
      steps = [[], []]
    else:
      difficulty = parts[0]
      couple = (parts[1][0] == "2")
      if couple:
        steps = [[], []]
        mode = "5COUPLE"

    for line in file(filename):
      line = line.strip()
      if line[0] == "#":
        line = line[1:]
        while line[-1] == ";": line = line[:-1]
        parts = line.split(":")

        if parts[0] == "TITLE" and parts[1] != "":
          pts = parts[1].split(" - ")
          if len(pts) == 3:
            self.info["artist"], self.info["title"], difficulty = pts
          elif len(pts) == 2: self.info["artist"], self.info["title"] = pts
          elif len(pts) == 1: self.info["title"] = pts[0]
        elif parts[0] == "BPM": self.info["bpm"] = float(parts[1])
        elif parts[0] == "TICKCOUNT": note_type = 4.0 / float(parts[1])
        elif parts[0] == "STARTTIME": self.info["gap"] = -float(parts[1]) * 10
      elif line[0] == "2": break
      elif self.need_steps:
        if couple:
          s = []
          for i in range(5):
            if line[i] == "4":
              if i not in holding:
                holding.append(i)
                s.append(3)
              else: s.append(0)
            elif line[i] == "1": s.append(1)
            elif line[i] == "0":
              if i in holding:
                holding.remove(i)
                steps[0][-1][i + 1] = 1
                s.append(0)
              else: s.append(0)
          steps[0].append([note_type] + s)

          s = []
          for i in range(5, 10):
            if line[i] == "4":
              if i not in holding:
                holding.append(i)
                s.append(3)
              else: s.append(0)
            elif line[i] == "1": s.append(1)
            elif line[i] == "0":
              if i in holding:
                holding.remove(i)
                steps[1][-1][i - 4] = 1
                s.append(0)
              else: s.append(0)
          steps[1].append([note_type] + s)
        else:
          s = []
          for i in range(5):
            if line[i] == "4":
              if i not in holding:
                holding.append(i)
                s.append(3)
              else: s.append(0)
            elif line[i] == "1": s.append(1)
            elif line[i] == "0":
              if i in holding:
                holding.remove(i)
                steps[-1][i + 1] = 1
                s.append(0)
              else: s.append(0)
          steps.append([note_type] + s)
      else: break

    ratings = { "EASY": 3, "NORMAL": 5, "HARD": 7, "CRAZY": 9 }
    difficulty = difficulty.upper()

    if not self.difficulty.has_key(mode):
      self.difficulty[mode] = {}
      self.steps[mode] = {}
    self.difficulty[mode][difficulty] = ratings.get(difficulty, 5)
    self.steps[mode][difficulty] = steps

# Sort by difficulty rating, or by a preset list if equal.
def sorted_diff_list(difflist):
  keys = difflist.keys()
  keys.sort((lambda a, b: cmp(difflist[a], difflist[b]) or
             util.difficulty_sort(a, b)))
  return keys

# Encapsulates and abstracts the above classes
class SongItem(object):

  formats = ((".step", StepFile),
             (".dance", DanceFile),
             (".dwi", DWIFile),
             (".sm", SMFile),
             ("song.ogg", KSFFile),
             ("song.mp3", KSFFile),
             ("song.wav", KSFFile))

  defaults = { "valid": 1,
               "mix": "No Mix",
               "endat": 0.0,
               "preview": (45.0, 10.0),
               "startat": 0.0,
               "revision": "1970.01.01",
               "gap": 0 }

  # A table of equivalencies between step sets; if the value doesn't
  # exist, it should be made the same as the key.
  equivs = { "SINGLE": "VERSUS",
             "5PANEL": "5VERSUS",
             "6PANEL": "6VERSUS",
             "8PANEL": "8VERSUS",
             "9PANEL": "9VERSUS",
             "PARAPARA": "PARAVERSUS",
             }
  
  def __init__(self, filename, need_steps = True):
    song = None
    for pair in SongItem.formats:
      if filename[-len(pair[0]):].lower() == pair[0]:
        song = pair[1](filename, need_steps)
        break
    if song == None:
      raise RuntimeError(filename + " is an unsupported format.")
    self.info = song.info

    # Sanity checks
    for k in ("bpm", "title", "artist", "filename"):
      if not self.info.has_key(k):
        raise RuntimeError(filename + " is missing: " + k)

    for k in ("subtitle", "title", "artist", "author", "mix"):
      try:
        if self.info.has_key(k): self.info[k] = self.info[k].decode("utf-8")
      except UnicodeError:
        print "W: Non-Unicode key in %s: %s" % (filename, k)

    # Default values
    for k in ("subtitle", "background", "banner",
                "author", "revision", "md5sum", "movie"):
      self.info[k] = self.info.get(k, None)


    for k in SongItem.defaults:
      self.info[k] = self.info.get(k, SongItem.defaults[k])

    for k in ("filename",):
      if self.info[k] and not os.path.isfile(self.info[k]):
        raise RuntimeError("%s is missing %s" % (filename, k))

    for k in ("banner", "background"):
      if self.info[k] and not os.path.isfile(self.info[k]):
        self.info[k] == None

    for k in ("startat", "endat", "gap", "bpm"):
      self.info[k] = float(self.info[k])

    self.info["valid"] = int(self.info["valid"])

    self.steps = song.steps
    if song.lyrics: self.lyrics = song.lyrics
    else: self.lyrics = []
    self.difficulty = song.difficulty
    self.filename = filename
    self.description = song.description

    if self.info["mix"] == "": self.info["mix"] = "No Mix Available"

    for k, v in SongItem.equivs.items():
      if self.difficulty.has_key(k) and not self.difficulty.has_key(v):
        self.difficulty[v] = self.difficulty[k]
        self.steps[v] = self.steps[k]


    if mainconfig["autogen"]:
      # Fill in non-defined game modes, if possible.
      for game in games.GAMES:
        if game in self.difficulty: continue # This mode is defined already.

        # Try to do "real DDR" modes first, then Pump modes.

        elif game in games.SINGLE:
          if "SINGLE" in self.difficulty:
            self.difficulty[game] = copy.copy(self.difficulty["SINGLE"])
          elif "5PANEL" in self.difficulty:
            self.difficulty[game] = copy.copy(self.difficulty["5PANEL"])
        
        elif game in games.VERSUS:
          if "VERSUS" in self.difficulty:
            self.difficulty[game] = copy.copy(self.difficulty["VERSUS"])
          elif "5VERSUS" in self.difficulty:
            self.difficulty[game] = copy.copy(self.difficulty["5VERSUS"])

        elif game in games.DOUBLE:
          if "DOUBLE" in self.difficulty:
            self.difficulty[game] = copy.copy(self.difficulty["DOUBLE"])
          elif "5DOUBLE" in self.difficulty:
            self.difficulty[game] = copy.copy(self.difficulty["5DOUBLE"])

        elif game in games.COUPLE:
          if "COUPLE" in self.difficulty:
            self.difficulty[game] = copy.copy(self.difficulty["COUPLE"])
          elif "5COUPLE" in self.difficulty:
            self.difficulty[game] = copy.copy(self.difficulty["5COUPLE"])

    self.diff_list = {}
    for key in self.difficulty:    
      self.diff_list[key] = sorted_diff_list(self.difficulty[key])
