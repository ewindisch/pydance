# This thing parses step files, in theory.

import sys, string, re

class StepFile:
  def __init__(self, filename):
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
        else: self.steps[sec][diff].append(line)
      elif state == LYRICS:
        if line == "end": state = WAITING
        else: self.lyrics.append(line)
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
