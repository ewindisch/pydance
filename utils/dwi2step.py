#! /usr/bin/env python

# dwi2step - converts DWI files from other clones to STEP files.
# this could peobably be done way better than I'm doing it, but..

import os, pygame, pygame.font, pygame.image, pygame.mixer, pygame.movie, time, sys
from pygame.locals import *

VERSION = "0.51"

# so it's currently in one routine. shut up, I'm learning python =]
def main():
  print "dwi2step, by theGREENzebra (tgz@clickass.org)"

  # set up
  print "Initialising.."

# ARROW STATUSES in arrstat
#-:   0 = no status / not initialised / top arrow
#0:   1 = shown
#1:   2 = pulse
#2:   4 = step
#3:   8 = onbeat
#4:  16 = offbeat
#5:  32 = way offbeat
#6:  64 =
#7: 128 = freeze

  # If I knew how to check whether a variable was defined, I would do
  # that instead
  bpm = ''
  gap = ''
  stepmodes = ['sixty','twtfr','steps','eight','qurtr','halfn','whole']
  stepbeats = [ 1/64.0, 1/24.0,     1 ,     2 ,     4 ,     8 ,    16 ]
  rar = 0
  bpms = []
  delay_times = []
  bpmchange_beats = []
  delay_beats = []

  print sys.argv[0]

  if len(sys.argv) > 1:
    print "Opening DWI file:",sys.argv[1],".."
    msdf = sys.argv[1]
    if msdf[-4:] != ".dwi": 
      if msdf[-4:] != ".DWI": 
        msdf += ".dwi"
    msdfile = open(msdf)
    fileline = 'crapcrap'

    stepfilename = msdf
    stepfilename = stepfilename[:-4]+".step"
    print 'Opening STEP file:',stepfilename,'..'
    stepfile = open(stepfilename,"w") #but for writing
    stepfile.write("version " + VERSION + "\n")
    print "debugging crap follows"
    print "----------------------"
    print "wrote header"
  else:
    print "You need to actually specify an DWI file to convert!"
    fileline = ''

  while fileline != '':
    print '*',
    if fileline != '\n':
      fileline = fileline.strip()
      if fileline[0:6] == '#FILE:':
        songfile = fileline[6:(len(fileline)-5)]
        print "found song filename: ", songfile
        stepfile.writelines("file "+songfile.lower()+".mp3\n")
      if fileline[0:7] == '#TITLE:':
        songname = fileline[7:(len(fileline)-1)]
        print "found songname: ", songname
        stepfile.writelines("song "+songname+"\n")
      if fileline[0:5] == '#BPM:':
        bpm = float(fileline[5:(len(fileline)-1)])
        print "found bpm: ", bpm
        stepfile.writelines("bpm "+"%.2f"%bpm+"\n")
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
      if fileline[0:8] == '#ARTIST:':
        groupname = fileline[8:(len(fileline)-1)]
        print "found groupname: ", groupname
        stepfile.writelines("group "+groupname+"\n")
      if fileline[0:5] == '#GAP:':
        gap = int(fileline[5:-1])
        print "found gap: ", gap, "( => offset = ", -gap, ")"
        stepfile.writelines("offset "+repr(-gap)+"\n")
      if fileline[0:14] == '#SINGLE:BASIC:':
        onbeat = 0
        neareof = 0
        bpmidx = 0
        delayidx = 0
        diff = int(fileline[14])
        print "\ndifficulty SINGLE BASIC,",diff,"feet. reading steps.."
        stepfile.writelines("SINGLE\n"+"BASIC "+repr(diff)+"\n")
        fileline = fileline[16:] + "\n"
        dc = ''
        stepmode = "eight"
        rar = 1
      if fileline[0:14] == '#SINGLE:TRICK:':
        onbeat = 0
        neareof = 0
        bpmidx = 0
        delayidx = 0
        diff = int(fileline[14])
        print "\ndifficulty SINGLE TRICK,",diff,"feet. reading steps.."
        stepfile.writelines("SINGLE\n"+"TRICK "+repr(diff)+"\n")
        fileline = fileline[16:] + "\n"
        dc = ''
        stepmode = "eight"
        rar = 1
      if fileline[0:15] == '#SINGLE:MANIAC:':
        onbeat = 0
        neareof = 0
        bpmidx = 0
        delayidx = 0
        diff = int(fileline[15])
        print "\ndifficulty SINGLE MANIAC,",diff,"feet. reading steps.."
        stepfile.writelines("SINGLE\n"+"MANIAC "+repr(diff)+"\n")
        fileline = fileline[17:] + "\n"
        dc = ''
        stepmode = "eight"
        rar = 1
      if fileline[0:16] == '#SINGLE:ANOTHER:':
        onbeat = 0
        neareof = 0
        bpmidx = 0
        delayidx = 0
        diff = int(fileline[16])
        print "\ndifficulty SINGLE TRICK,",diff,"feet. reading steps.."
        stepfile.writelines("SINGLE\n"+"TRICK "+repr(diff)+"\n")
        fileline = fileline[18:] + "\n"
        dc = ''
        stepmode = "eight"
        rar = 1
      
      i = 0

      while rar:
        steps = []
#        print "b"+repr(onbeat),

        for xyz in bpmchange_beats[bpmidx:]:    #check to see if we need to change the bpm
          if xyz <= onbeat:
            stepfile.writelines("chbpm "+repr(bpms[bpmchange_beats.index(xyz)])+"\n")
            print "-- chbpm to",bpms[bpmchange_beats.index(xyz)],"at beat",onbeat,"--",
            bpmidx += 1
        for xyz in delay_beats[delayidx:]:    #check to see if we need to wait some time
          if xyz <= onbeat:
            stepfile.writelines("waits "+repr(delay_times[delay_beats.index(xyz)]/1000)+"\n")
            print "-- delay of",delay_times[delay_beats.index(xyz)]/1000,"sec. at beat",onbeat,"--",
            delayidx += 1

        dc = fileline[i]
        dc1 = dc2 = ''       #initialized here so that they are declared even on EOF/EOL
        try:
          dc1 = fileline[i+1]
          dc2 = fileline[i+2]
        except:              #EOF or EOL
          neareof = 1
          
        i += 1

        print dc,
        if dc == "0":
          steps = ['00','00','00','00']
          onbeat += stepbeats[stepmodes.index(stepmode)]
        elif dc == "1":
          steps = ['08','08','00','00']
          onbeat += stepbeats[stepmodes.index(stepmode)]
        elif dc == "2":
          steps = ['00','08','00','00']
          onbeat += stepbeats[stepmodes.index(stepmode)]
        elif dc == "3":
          steps = ['00','08','00','08']
          onbeat += stepbeats[stepmodes.index(stepmode)]
        elif dc == "4":
          steps = ['08','00','00','00']
          onbeat += stepbeats[stepmodes.index(stepmode)]
        elif dc == "5":
          steps = ['00','00','00','00']
          onbeat += stepbeats[stepmodes.index(stepmode)]
        elif dc == "6":
          steps = ['00','00','00','08']
          onbeat += stepbeats[stepmodes.index(stepmode)]
        elif dc == "7":
          steps = ['08','00','08','00']
          onbeat += stepbeats[stepmodes.index(stepmode)]
        elif dc == "8":
          steps = ['00','00','08','00']
          onbeat += stepbeats[stepmodes.index(stepmode)]
        elif dc == "9": 
          steps = ['00','00','08','08']
          onbeat += stepbeats[stepmodes.index(stepmode)]
        elif dc == "A":
          steps = ['00','08','08','00']
          onbeat += stepbeats[stepmodes.index(stepmode)]
        elif dc == "B":
          steps = ['08','00','00','08']
          onbeat += stepbeats[stepmodes.index(stepmode)]
        if dc == "(":
          stepmode = "steps"
        if dc == ")":
          stepmode = "eight"
        if dc == "[":
          stepmode = "twtfr"
        if dc == "]":
          stepmode = "eight"
        if dc == "{":
          stepmode = "sixty"
        if dc == "}":
          stepmode = "eight"
        if dc == ";":
          stepfile.writelines("end\n")
          rar = 0
        if dc == "\n":
          fileline = msdfile.readline()
          i = 0

        if (not neareof) and (dc1 == '!'):    #freeze arrow
          i += 2
          print 'hold',dc2,

          if dc2 == "1":
            steps[0] =  '8'+steps[0][1]
            steps[1] =  '8'+steps[1][1]
          elif dc2 == "2":
            steps[1] =  '8'+steps[1][1]
          elif dc2 == "3":
            steps[1] =  '8'+steps[1][1]
            steps[3] =  '8'+steps[3][1]
          elif dc2 == "4":
            steps[0] =  '8'+steps[0][1]
          elif dc2 == "6":
            steps[3] =  '8'+steps[3][1]
          elif dc2 == "7":
            steps[0] =  '8'+steps[0][1]
            steps[2] =  '8'+steps[2][1]
          elif dc2 == "8":
            steps[2] =  '8'+steps[2][1]
          elif dc2 == "9": 
            steps[2] =  '8'+steps[2][1]
            steps[3] =  '8'+steps[3][1]
          elif dc2 == "A":
            steps[1] =  '8'+steps[1][1]
            steps[2] =  '8'+steps[2][1]
          elif dc2 == "B":
            steps[0] =  '8'+steps[0][1]
            steps[3] =  '8'+steps[3][1]

        stepline = stepmode+" "
        for stepwrite in steps:    stepline += stepwrite + " "
        if steps:
#          print stepline
          stepfile.writelines(stepline+"\n")

    fileline = msdfile.readline()

  print "End."
#end

if __name__ == '__main__': main()
