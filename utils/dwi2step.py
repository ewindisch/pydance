#! /usr/bin/env python

# dwi2step - converts DWI files from other clones to STEP files.

# 2003-03-30 Refactoring done by Stephen Thorne <stephen@thorne.id.au>

import os, time, sys

VERSION = "0.52"

class DwiFile:
  def __init__(self, filename):
    self.filename = filename
    self.file = open(filename)

  def readline(self):
    return self.file.readline()

  def valid(self):
    return self.file

  def basename(self):
    return self.filename[:-4]

# Represents a single dance
class Dance:
  def __init__(self, category, difficulty):
    self.category = category
    self.difficulty = difficulty
    self.moves = []

  def addMove(self,move):
    self.moves.append(move)

  def addBeatChange(self, bc):
    self.moves.append(bc)

  def addPause(self, pause):
    self.moves.append(pause)
    
  def getDance(self):
    ret = "SINGLE\n%s %d\n" % (self.category, self.difficulty)
    for move in self.moves:
      ret += move.getLine()
    ret += "end\n"
    return ret

# A detail about a dance, i.e. artist or song filename
class Detail:
  dwi2step = { 
    '#ARTIST:':('group', 'groupname'), 
    '#GAP:':('offset', 'gap'),
    '#FILE:':('file', 'song filename'), 
    '#TITLE:':('song', 'songname'),
    '#BPM:':('bpm', 'bpm'),
    '#GENRE:':('', 'genre')}

  def __init__(self, label, detail):
    self.detail = detail
    (self.key, self.label) = self.dwi2step[label]

    if self.key == 'file': self.detail = (self.detail[:-4]).lower() + ".mp3"
    if self.key == 'offset': self.detail = - int(self.detail)
    if self.key == 'bpm': self.detail = "%.2f" % float(self.detail)
    
  def getFound(self):
    return "found %s: %s" % (self.label, self.detail)

  def writeline(self, stepfile):
    if self.key == '':
      return
    stepfile.writelines("%s %s\n" % (self.key, self.detail))

# A beat
class Beat:
  stepmodes = {'{':('sixty',1/64.0), '[':('twtfr',1/24.0), '(':('steps',1.0), 
    ')':('eight',2.0), ']':('eight',2.0), '}':('eight',2.0)}

  def __init__(self, dc):
    if dc == '': dc = ']'
    (self.mode, self.time) = self.stepmodes[dc]

  def getTime(self):
    return self.time

  def getMode(self):
    return self.mode

# Move, e.g. Up+Left
class Move:
  moves = {
    '0':['0','0','0','0'], 
    '1':['8','8','0','0'], 
    '2':['0','8','0','0'], 
    '3':['0','8','0','8'],
    '4':['8','0','0','0'], 
    '5':['0','0','0','0'], 
    '6':['0','0','0','8'], 
    '7':['8','0','8','0'],
    '8':['0','0','8','0'], 
    '9':['0','0','8','8'], 
    'A':['0','8','8','0'], 
    'B':['8','0','0','8']}

  def __init__(self, dc, stepmode):
    self.stepmode = stepmode
    self.steps = self.moves[dc]
    self.holds = self.moves['0']
  
  def hold(self, dc2):
    self.holds = self.moves[dc2]

  def getLine(self):
    ret = self.stepmode.getMode()
    for xy in zip(self.holds, self.steps):
      ret += " " + xy[0] + xy[1]
    return ret + "\n"

class BeatChange:
  def __init__(self, bpm):
    self.bpm = bpm

  def getLine(self):
    return "chbpm "+repr(self.bpm)+"\n"

  def getBeat(self):
    return self.bpm

class Pause:
  def __init__(self, pause):
    self.pause = pause

  def getLine(self):
    return "waits " + repr(self.pause / 1000) + "\n"

  def getPause(self):
    return self.pause / 1000

def main():
  print "dwi2step, by theGREENzebra (tgz@clickass.org)"

  if not len(sys.argv) > 1:
    print "You need to actually specify an DWI file to convert!"
    fileline = ''
    return

  print sys.argv[0]

  print "Opening DWI file:",sys.argv[1],".."
  msdf = reduce((lambda x,y:x+" "+y), sys.argv[1:])
  if msdf[-4:] != ".dwi": 
    if msdf[-4:] != ".DWI": 
      msdf += ".dwi"
  msdfile = DwiFile(msdf)

  if not msdfile.valid():
    print 'fatal error reading .dwi file, exiting'
    return

  convert(msdfile)

def convert(msdfile):
  # set up
  print "Initialising.."

  # If I knew how to check whether a variable was defined, I would do
  # that instead
  bpms = []
  delay_times = []
  bpmchange_beats = []
  delay_beats = []
  stepfilename = msdfile.basename()+".step"
  print 'Opening STEP file:',stepfilename,'..'
  stepfile = open(stepfilename,"w") #but for writing
  stepfile.write("version " + VERSION + "\n")
  print "debugging crap follows"
  print "----------------------"
  print "wrote header"

  dance = None

  line = '\n'
  while line != '':
    line = msdfile.readline()
    print '*',
    if line != '\n':
      fileline = line.strip()
      for i in ('#ARTIST:', '#GAP:', '#FILE:', '#TITLE:', '#BPM:', '#GENRE:'):
        if fileline[0:len(i)] == i:
          detail = Detail(i, fileline[len(i):-1])
          print detail.getFound()
          detail.writeline(stepfile)
          
      if fileline[0:11] == '#CHANGEBPM:':
        parsemode = 1
        beat_string = ''
        bpmchange_string = ''
        print "found bpm changes: "
        for i in fileline[11:-1]:
          if i == '=':   
            bpmchange_beats.append(float(beat_string))
            parsemode = 2
            bpmchange_string = ''
          elif i == ',':
            bpms.append(float(bpmchange_string))
            parsemode = 1
            beat_string = ''
          else:
            if parsemode==1:
              beat_string += i
            if parsemode==2:
              bpmchange_string += i
        bpms.append(float(bpmchange_string))
        for i in bpmchange_beats:
          print "  at beat",i,"change bpm to",bpms[bpmchange_beats.index(i)]
        print
      if fileline[0:8] == '#FREEZE:':
        parsemode = 1
        beat_string = ''
        delay_string = ''
        print "frozen beats: "
        for i in fileline[8:-1]:
          if i == '=':
            delay_beats.append(float(beat_string))
            parsemode = 2
            delay_string = ''
          elif i == ',':
            delay_times.append(float(delay_string))
            parsemode = 1
            beat_string = ''
          else:
            if parsemode==1:
              beat_string += i
            if parsemode==2:
              delay_string += i
        delay_times.append(float(delay_string))
        for i in delay_beats:
          print "  at beat",i,"freeze",delay_times[delay_beats.index(i)]
        print
      if fileline[0:8] == '#SINGLE:':
        onbeat = 0
        neareof = 0
        bpmidx = 0
        delayidx = 0
        dc = ''
        stepmode = Beat('')
        for i in ('BASIC','TRICK','MANIAC','ANOTHER'):
          if fileline[8:8+len(i)] == i:
            try:
              difficulty = int(fileline[9+len(i):11+len(i)])
            except:
              difficulty = int(fileline[9+len(i)])
            fileline = fileline[10+len(i):] + "\n"

            if i == 'ANOTHER': # this is a trick.
              i = 'TRICK'

            print "\ndifficulty SINGLE %s, %s feet. reading steps.." % (i, difficulty)
            dance = Dance(i, difficulty)
            break
            
      i = 0

      while not dance == None and not fileline == '':
        dc = fileline[i]

        if dc == "\n":
          # Go to the next line, but continue reading the file.
          fileline = msdfile.readline()
          i = 0
          continue
        if dc == ";":
          # The song is over!
          stepfile.write(dance.getDance())
          dance = None
          break

        move = None
        i += 1

        if dc in ('0','1','2','3','4','5','6','7','8','9','A','B'): # Its a Move!
          move = Move(dc, stepmode)
          onbeat += stepmode.getTime()
        elif dc in ('(',')','[',']','{','}'): # Its a Beat Change!
          stepmode = Beat(dc)

        if move == None:
          continue

        # Freeze Arrow Lookahead
        if len(fileline)>i+1 and fileline[i] == '!':    
          dc2 = fileline[i+1]
          i += 2
          print 'hold',dc2,
          move.hold(dc2)

        dance.addMove(move) # Add the move (and possibly the hold) to the dance

        for xyz in bpmchange_beats[bpmidx:]:    #check to see if we need to change the bpm
          if onbeat >= xyz:
            beatChange = BeatChange(bpms[bpmchange_beats.index(xyz)])
            dance.addBeatChange(beatChange)
            print "-- chbpm to",beatChange.getBeat(),"at beat",onbeat,"--"
            bpmidx += 1
        for xyz in delay_beats[delayidx:]:    #check to see if we need to wait some time
          if onbeat >= xyz:
            pause = Pause(delay_times[delay_beats.index(xyz)])
            dance.addPause(pause)
            print "-- delay of",pause.getPause(),"sec. at beat",onbeat,"--"
            delayidx += 1

  # In case someone didn't put a ; at the end of a dance in a .dwi file.
  if not dance == None:
    stepfile.write(dance.getDance())

  print "End."

if __name__ == '__main__': main()
