# This thing parses step files, in theory.

import sys, os

class StepFile:
  def __init__(self, filename, read_steps = True):
    self.filename = filename
    self.steps = {}
    self.difficulty = {}
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
        elif read_steps: self.steps[sec][diff].append(line)
      elif state == LYRICS:
        if line == "end": state = WAITING
        elif read_steps: self.lyrics.append(line)
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
    for t in (("banner", ".png"), ("bg", "-bg.png"), ("file", ".ogg")):
      if not self.info.has_key(t[0]):
        possible = os.path.join(dir, name.replace(".step", t[1]))
        if os.path.isfile(possible): self.info[t[0]] = possible
#      else: self.info[t[0]] = None

    for d in ("banner", "bg", "file"):
      if self.info.has_key(d):
        # Stupid fucking Windows. 
        self.info[d] = os.path.normpath(self.info[d])
    
