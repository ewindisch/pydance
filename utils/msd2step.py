#! /usr/bin/env python

# msd2step - converts MSD files from other clones to STEP files.
# this could peobably be done way better than I'm doing it, but..

import os, pygame, pygame.font, pygame.image, pygame.mixer, pygame.movie, time, sys
from pygame.locals import *

# so it's currently in one routine. shut up, I'm learning python =]
def main():
  print "msd2step, by theGREENzebra (tgz@clickass.org)"

  # set up
  print "Initialising.."

# ARROW STATUSES in arrstat
#-:  0 = no status / not initialised / top arrow
#0:   1 = shown
#1:   2 = pulse
#2:   4 = step
#3:   8 = onbeat
#4:  16 = offbeat
#5:  32 = way offbeat
#6:  64 =
#7: 128 =

# FORMAT OF .step FILES
# version 0.3
#
# song Better Off Alone (test remix)
# group Alice DeeJay
# file test.mp3
# bpm 137
#
# startat -1
# endat -1
# offset -150
#
# SINGLE
# BASIC 2
# delay 8
# ready
# delay 8
# steps...
# end

  rar = 0
  i = -1

  if len(sys.argv) > 1:
    print "Opening MSD file:",sys.argv[1],".."
    msdf = sys.argv[1]
    if msdf[-4:] != ".msd": 
      msdf += ".msd"
    msdfile = open(msdf)
    fileline = 'crap'

    stepfilename = msdf
    stepfilename = stepfilename[:-4]+".step"
    print 'Opening STEP file:',stepfilename,'..'
    stepfile = open(stepfilename,"w") #but for writing
    stepfile.write("version 0.3\n")
    print "debugging crap follows"
    print "----------------------"
    print "wrote header"
  else:
    print "You need to actually specify an MSD file to convert!"
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
        stepfile.writelines("bpm "+"%.2f"%bpm+"\n")
      if fileline[0:8] == '#ARTIST:':
        groupname = fileline[8:(len(fileline)-1)]
        print "found groupname: ", groupname
        stepfile.writelines("group "+groupname+"\n")
      if fileline[0:5] == '#GAP:':
        gap = int(fileline[5:(len(fileline)-1)])
        print "generic offset:  150 (tweak as needed)"
        stepfile.writelines("offset 150 \n")
      if fileline[0:14] == '#SINGLE:BASIC:':
        diff = int(fileline[14])
        print "difficulty SINGLE BASIC,",diff,"feet. reading steps.."
        stepfile.writelines("SINGLE\n"+"BASIC "+repr(diff)+"\n")
        stepfile.writelines("delay 7\n")
        fileline = fileline[16:] + "\n"
        dc = ''
        stepmode = "eight"
        i = 0
        rar = 1
      if fileline[0:14] == '#SINGLE:TRICK:':
        diff = int(fileline[14])
        print "difficulty SINGLE TRICK,",diff,"feet. reading steps.."
        stepfile.writelines("SINGLE\n"+"TRICK "+repr(diff)+"\n")
        stepfile.writelines("delay 7\n")
        fileline = fileline[16:] + "\n"
        dc = ''
        stepmode = "eight"
        i = 0
        rar = 1
      if fileline[0:15] == '#SINGLE:MANIAC:':
        diff = int(fileline[15])
        print "difficulty SINGLE MANIAC,",diff,"feet. reading steps.."
        stepfile.writelines("SINGLE\n"+"MANIAC "+repr(diff)+"\n")
        stepfile.writelines("delay 7\n")
        fileline = fileline[17:] + "\n"
        dc = ''
        stepmode = "eight"
        i = 0
        rar = 1
      if fileline[0:16] == '#SINGLE:ANOTHER:':
        diff = int(fileline[16])
        print "difficulty SINGLE TRICK,",diff,"feet. reading steps.."
        stepfile.writelines("SINGLE\n"+"TRICK "+repr(diff)+"\n")
        stepfile.writelines("delay 7\n")
        fileline = fileline[18:] + "\n"
        dc = ''
        stepmode = "eight"
        i = 0
        rar = 1

      while rar:
        dc = fileline[i]
        i += 1
        print dc,
        if dc == "0":
          stepfile.writelines(stepmode+" 00 00 00 00\n")
        elif dc == "1":
          stepfile.writelines(stepmode+" 08 08 00 00\n")
        elif dc == "2":
          stepfile.writelines(stepmode+" 00 08 00 00\n")
        elif dc == "3":
          stepfile.writelines(stepmode+" 00 08 00 08\n")
        elif dc == "4":
          stepfile.writelines(stepmode+" 08 00 00 00\n")
        elif dc == "5":
          stepfile.writelines(stepmode+" 00 00 00 00\n")
        elif dc == "6":
          stepfile.writelines(stepmode+" 00 00 00 08\n")
        elif dc == "7":
          stepfile.writelines(stepmode+" 08 00 08 00\n")
        elif dc == "8":
          stepfile.writelines(stepmode+" 00 00 08 00\n")
        elif dc == "9": 
          stepfile.writelines(stepmode+" 00 00 08 08\n")
        elif dc == "A":
          stepfile.writelines(stepmode+" 00 08 08 00\n")
        elif dc == "B":
          stepfile.writelines(stepmode+" 08 00 00 08\n")
        if dc == "(":
          stepmode = "steps"
        if dc == ")":
          stepmode = "eight"
        if dc == ";":
          stepfile.writelines("end\n")
          rar = 0
        if dc == "\n":
          fileline = msdfile.readline()
          i = 0

    fileline = msdfile.readline()

  print "End."
#end
    
if __name__ == '__main__': main()
