#! /usr/bin/env python

# dwi2step - converts DWI files from other clones to STEP files.
# this could peobably be done way better than I'm doing it, but..

import os, pygame, pygame.font, pygame.image, pygame.mixer, pygame.movie, time, sys
from pygame.locals import *
from Numeric import *

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
  skipnum = ''
  stepmodes = ['sixty','twtfr','steps','eight','qurtr','halfn','whole']
  stepbeats = [ 1/64.0, 1/24.0,     1 ,     2 ,     4 ,     8 ,    16 ]
  rar = 0
  i = -1
  bpms = []
  beats = []
  bpmstring = ''
  gapstring = ''
  beatstring = ''

#  arrstat = zeros((4,1024,3))
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
    stepfile.write("version 0.5\n")
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
        bpm = float(fileline[5:(len(fileline)-1)])-0.05
        print "found bpm: ", bpm
      if fileline[0:11] == '#CHANGEBPM:':
        bpmchanges = 1
        parsemode = 1
        print "found bpm changes: "
        for i in fileline[11:-1]:
          if i == '=':   
            beats.append(float(beatstring))
            parsemode = 2
            bpmstring = ''
          elif i == ',':
            bpms.append(float(bpmstring))
            parsemode = 1
            beatstring = ''
          else:
            if parsemode==1:
              beatstring += i
            if parsemode==2:
              bpmstring += i
        bpms.append(float(bpmstring))
        for i in beats:
          print "  at beat",i,"change bpm to",bpms[beats.index(i)]
        print
      if fileline[0:8] == '#ARTIST:':
        groupname = fileline[8:(len(fileline)-1)]
        print "found groupname: ", groupname
        stepfile.writelines("group "+groupname+"\n")
      if fileline[0:5] == '#GAP:':
        gap = int(fileline[5:-1])
        print "found gap: ", gap
      if fileline[0:14] == '#SINGLE:BASIC:':
        onbeat = 0
        diff = int(fileline[14])
        print "\ndifficulty SINGLE BASIC,",diff,"feet. reading steps.."
        stepfile.writelines("SINGLE\n"+"BASIC "+repr(diff)+"\n")
        fileline = fileline[16:] + "\n"
        dc = ''
        stepmode = "eight"
        if skipnum < 0:
          print "padding eighths.."
          for i in range(abs(skipnum)):
            stepfile.writelines("eight 00 00 00 00\n")
            onbeat += stepbeats[stepmodes.index(stepmode)]
          i = 0
        else:
          i = skipnum
        rar = 1
      if fileline[0:14] == '#SINGLE:TRICK:':
        onbeat = 0
        diff = int(fileline[14])
        print "\ndifficulty SINGLE TRICK,",diff,"feet. reading steps.."
        stepfile.writelines("SINGLE\n"+"TRICK "+repr(diff)+"\n")
        fileline = fileline[16:] + "\n"
        dc = ''
        stepmode = "eight"
        if skipnum < 0:
          print "padding eighths.."
          for i in range(abs(skipnum)):
            stepfile.writelines("eight 00 00 00 00\n")
            onbeat += stepbeats[stepmodes.index(stepmode)]
          i = 0
        else:
          i = skipnum
        rar = 1
      if fileline[0:15] == '#SINGLE:MANIAC:':
        onbeat = 0
        diff = int(fileline[15])
        print "\ndifficulty SINGLE MANIAC,",diff,"feet. reading steps.."
        stepfile.writelines("SINGLE\n"+"MANIAC "+repr(diff)+"\n")
        fileline = fileline[17:] + "\n"
        dc = ''
        stepmode = "eight"
        if skipnum < 0:
          print "padding eighths.."
          for i in range(abs(skipnum)):
            stepfile.writelines("eight 00 00 00 00\n")
            onbeat += stepbeats[stepmodes.index(stepmode)]
          i = 0
        else:
          i = skipnum
        rar = 1
      if fileline[0:16] == '#SINGLE:ANOTHER:':
        onbeat = 0
        diff = int(fileline[16])
        print "\ndifficulty SINGLE TRICK,",diff,"feet. reading steps.."
        stepfile.writelines("SINGLE\n"+"TRICK "+repr(diff)+"\n")
        fileline = fileline[18:] + "\n"
        dc = ''
        stepmode = "eight"
        if skipnum < 0:
          print "padding eighths.."
          for i in range(abs(skipnum)):
            stepfile.writelines("eight 00 00 00 00\n")
            onbeat += stepbeats[stepmodes.index(stepmode)]
          i = 0
        else:
          i = skipnum
        rar = 1
      
      while rar:
        steps = []

        for xyz in beats:    #check to see if we need to change the bpm
          if xyz == onbeat:
            stepfile.writelines("chbpm "+repr(bpms[beats.index(onbeat)])+"\n")
            print "-- chbpm to",bpms[beats.index(onbeat)],"at beat",xyz,"--",

        dc = fileline[i]
        try:
          dc1 = fileline[i+1]
          dc2 = fileline[i+2]
        except:
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

        if dc1 == '!':    #freeze arrow
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

    if skipnum == '' and bpm != '' and gap != '':
      skipnum = int(gap / (60000/float(bpm/2))) - 1
      print "because of gap setting, will skip",skipnum,"eighth notes."
      offset = int(gap % (60000/bpm)) - 1
      print "offset:  ",offset," (from gap of",gap,")"
      stepfile.writelines("bpm "+"%.2f"%bpm+"\n")
      stepfile.writelines("offset "+repr(offset)+"\n")

    fileline = msdfile.readline()

  print "End."
#end

if __name__ == '__main__': main()
