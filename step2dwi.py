#! /usr/bin/env python

# step2dwi - converts STEP files to DWI files for other clones.
# Blatantly ripped from pyDDR's dwi2step with lots of help from Brendan on the DWI format

import os, pygame, pygame.font, pygame.image, pygame.mixer, pygame.movie, time, sys
from pygame.locals import *

# Dictionary that maps from pyDDR "xxxxx AA BB CC DD" to DWI note
# (xxxxx is qurtr, etc....)
stepmap = {
	'00 00 00 00': '0',
	'00 00 00 08': '6',
	'00 00 00 88': '6!6',
	'00 00 08 00': '8',
	'00 00 08 08': '9',
	'00 00 08 88': '9!6',
	'00 00 88 00': '8!8',
	'00 00 88 08': '9!8',
	'00 00 88 88': '9!9',
	'00 08 00 00': '2',
	'00 08 00 08': '3',
	'00 08 00 88': '3!6',
	'00 08 08 00': 'A',
	'00 08 88 00': 'A!8',
	'00 88 00 00': '2!2',
	'00 88 00 08': '3!2',
	'00 88 00 88': '3!3',
	'00 88 08 00': 'A!8',
	'00 88 88 00': 'A!A',
	'08 00 00 00': '4',
	'08 00 00 08': 'B',
	'08 00 00 88': 'B!6',
	'08 00 08 00': '7',
	'08 00 88 00': '7!8',
	'08 08 00 00': '1',
	'08 88 00 00': '1!2',
	'88 00 00 00': '4!4',
	'88 00 00 08': 'B!4',
	'88 00 00 88': 'B!B',
	'88 00 08 00': '7!4',
	'88 00 88 00': '7!7',
	'88 08 00 00': '1!4',
	'88 88 00 00': '1!1'
}

# so it's currently in one routine. shut up, I'm learning python =]
# (and I know even less Python than Brendan does. --Matt)
def main():
  print "step2dwi, by Matthew Sachs (matthewg@zevils.com)"

  # set up
  print "Initialising.."

  print sys.argv[0]

  if len(sys.argv) > 1:
    print "Opening STEP file:",sys.argv[1],".."
    stepfilename = sys.argv[1]
    if stepfilename[-4:] != ".step": 
      stepfilename += ".step"
    stepfile = open(stepfilename)
    fileline = 'crapcrap'

    # Things like chbpm need to go at top for DWIs, so we buffer and write everything out at the end.
    dwisongfile = ''
    dwititle = ''
    dwiartist = ''
    dwibpm = ''
    dwigap = ''
    dwichangebpm = ''
    dwisteps = ''
    dwinotes = ''

    gap = 0
    onbeat = 0
    currtype = '' # "SINGLE", etc.
    stepmode = ''

    dwifilename = stepfilename
    dwifilename = dwifilename[:-5]+".dwi"
    print 'Opening DWI file:',dwifilename,'..'
    dwifile = open(dwifilename,"w") #but for writing
    print "debugging crap follows"
    print "----------------------"
  else:
    print "You need to actually specify a STEP file to convert!"
    fileline = ''

  while fileline != '':
    print '*',
    if fileline != '\n':
      fileline = fileline.strip()
      line = fileline.split(None, 1)
      if line[0] == 'file':
        songfile = line[1]
        print "found song filename: ", songfile
        dwisongfile = "#FILE:"+songfile+";\n"
      elif line[0] == 'song':
        songname = line[1]
        print "found songname: ", songname
        dwititle = "#TITLE:"+songname+";\n"
      elif line[0] == 'bpm':
        bpm = float(line[1])+.05
        print "found bpm: ", "%.2f"%bpm
        dwibpm = "#BPM:"+"%.2f"%bpm+";\n"
      elif line[0] == 'chbpm':
        if dwichangebpm == '':
          dwichangebpm = '#CHANGEBPM:'
        else:
          dwichangebpm += ','
        dwichangebpm += "%.2f"%onbeat + "=" + line[1]

        print "found bpm change: at beat",onbeat,"change bpm to",line[1],"\n"
      elif line[0] == 'group':
        groupname = line[1]
        print "found groupname: ", groupname
        dwiartist = "#ARTIST:"+groupname+";\n"
      elif line[0] == 'offset':
        offset = line[1]
        gap = float(offset) + 1
        print "gap: ","%.2f"%gap
      elif line[0] == 'SINGLE':
        currtype = 'SINGLE'
      elif line[0] == 'BASIC' or line[0] == 'TRICK' or line[0] == 'MANIAC':
        dwisteps += "\n#"+currtype+":"+line[0]+":"+line[1]+":"
        onbeat = 0

        print "\ndifficulty ",currtype,line[0],line[1],"feet. reading steps.."
      elif line[0] == 'whole' or line[0] == 'halfn' or line[0] == 'qurtr' or line[0] == 'eight' or line[0] == 'steps':
        newstepmode = line[0]
        stepnote = line[1]

        dwinote = ''

        if line[0] == 'whole':
          onbeat += 16
        elif line[0] == 'halfn':
          onbeat += 8
        elif line[0] == 'qurtr':
          onbeat += 4
        elif line[0] == 'eight':
          onbeat += 2
        elif line[0] == 'steps':
          onbeat += 1

        # Change into or out of 16th-note mode
        if newstepmode == 'steps' and stepmode != 'steps':
          dwinote = '('
        elif newstepmode != 'steps' and stepmode == 'steps':
          dwinote = ')'

        if not stepmap.has_key(stepnote):
          print "ERROR: Unknown stepnote",stepnote
        else:
          if newstepmode == 'qurtr':
            dwinote += '0'
          elif newstepmode == 'halfn':
            dwinote += '000'
          elif newstepmode == 'whole':
            dwinote += '0000000'
          dwinote += stepmap[stepnote]

        stepmode = newstepmode
        dwinotes += dwinote

        #print "Got", line[0], line[1], "emitting", dwinote
      elif line[0] == 'end':
        dwisteps += dwinotes[2:len(dwinotes)+1] # It inserts an extra beat of silence at head, so kill that here
        dwisteps += ";\n"
        dwinotes = ''
      elif line[0] == 'waits':
        print "ERROR: waits not supported"
      elif line[0] == 'atsec':
        print "ERROR: atsec not supported"
      elif line[0] == 'delay':
        print "ERROR: delay not supported"
      elif line[0] == 'ready':
        pass
      elif line[0] == 'crapcrap':
        pass
      elif line[0] == 'version':
        pass
      elif line[0][0:1] == '#':
        pass
      else:
        print "ERROR: Unknown command",line[0]

    fileline = stepfile.readline()

  print "Reducing gap by one eigth note.  Old gap is", "%.2f"%gap
  mspb = 60000/bpm # milliseconds/beat
  gap -= mspb/2
  print "bpm is", "%.2f"%bpm, "mspb is", "%.2f"%mspb
  print "New gap is", "%.2f"%gap
  dwigap = "#GAP:"+"%d"%gap+";\n"

  print "Done parsing stepfile.  Writing dwifile..."
  if dwichangebpm != '':
    dwichangebpm += ";\n"
  dwifile.writelines([dwisongfile, dwititle, dwiartist, dwibpm, dwigap, dwichangebpm, dwisteps])
  print "Done!"
  
#end
    
if __name__ == '__main__': main()
