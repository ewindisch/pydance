#! /usr/bin/env python

import os, pygame, pygame.font, pygame.image, pygame.mixer, pygame.movie, time, sys
from pygame.locals import *
from Numeric import *

def main():
  print "inSTEP 0.2 STEP inputter - crappy edition"
  if len(sys.argv) < 2:
    print "ERROR: Please specify a filename to write steps out to."
    print "       A .step extension will automatically be added)"
    sys.exit()

  # set up the screen and all that stuff
  pygame.init()
  screen = pygame.display.set_mode((640, 480), HWSURFACE|DOUBLEBUF) 
  pygame.display.set_caption('inSTEP')
  pygame.mouse.set_visible(1)

  stepfilename = sys.argv[1] + ".step"  

  try:
    stepfile = open(stepfilename,"r") #but for reading
    fileexists = 1
  except:
    fileexists = 0

  if fileexists:
    print "ERROR: That STEP file already exists, and inSTEP is not an editor."
    print "Use a different filename. If you are trying to create another"
    print "difficulty for your song (EG. Trick), merge the steps with your"
    print "favorite text editor after inputting them."
    sys.exit()

  stepfile = open(stepfilename,"w") #but for writing
  print "Opened ",stepfilename, " for writing. Writing sample info to file."

  font = pygame.font.Font(None, 64)
  text = font.render('inSTEP 0.2 - crappy edition', 1, (222,222,222))
  screen.blit(text, (0,0))

  helptext = []

  helptext.append('HELP')
  helptext.append(' ')
  helptext.append('Arrow keys toggle arrows on/off')
  helptext.append('1/2/3/4/5 changes step mode')
  helptext.append('(default step mode is quarter notes)')
  helptext.append('Messages will be displayed at bottom')
  helptext.append(' ')
  helptext.append('Enter writes step to disk, clears arrows')
  helptext.append('ESC quits')

  for i in helptext:
    font = pygame.font.Font(None, 24)
    text = font.render(i, 1, (166,166,166))
    screen.blit(text, (300,80+(helptext.index(i)*20)))

  atypes = ['l','d','u','r']
  acolors = ['n','c']
  apics = []

  for atype in atypes:
    for acolor in acolors:
      fn = 'arr_' + acolor + '_' + atype + '_0.png'
      imgfile = os.path.join('themes','gfx','bryan',fn)
      arraynum = (atypes.index(atype)*2) + acolors.index(acolor)
      apics.append(pygame.image.load(imgfile).convert())
      apics[arraynum].set_colorkey( apics[arraynum].get_at((0,0)) )
      print "Loaded ",imgfile,"as img",arraynum

  blackbar = pygame.surface.Surface((640,30))
  blackbar.fill((0,0,0))

  stepfile.write("version 0.4\n")
  stepfile.write("file "+sys.argv[1]+".mp3\n")
  stepfile.write("song instep song\n")
  stepfile.write("group instep group\n")
  stepfile.write("bpm 140\n")
  stepfile.write("offset 150\n")
  stepfile.write("\n")
  stepfile.write("SINGLE\n")
  stepfile.write("BASIC 16\n")
  stepfile.write("delay 8\n")
  stepfile.write("ready\n")
  stepfile.write("delay 8\n")
  stepfile.write("\n")
  stepfile.write("eight 00 00 00 00\n")

  print "Okay, ready to write steps to file."
  steptype = 2
  stepmode = ["whole ","halfn ","qurtr ","eight ","steps "]
  steps = ['00 ','00 ','00 ','00 ']
  update = 1
  updarr = -1
  updtext = 'READY'

  while 1: 
    if update:
      for i in range(4):
        if steps[i] == '08 ':
          screen.blit(apics[(i*2)+1],(16+(64*i),360))
        else:
          screen.blit(apics[(i*2)],(16+(64*i),360))

      font = pygame.font.Font(None, 32)
      text = font.render(updtext, 1, (111,111,111))
      screen.blit(blackbar, (0,450))
      screen.blit(text, (8,450))
      update = 0
      updarr = -1

      pygame.display.flip()

    event = pygame.event.poll()
    if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
        break

    if event.type == KEYDOWN:
        update = 1
        if (event.key > 48) and (event.key < 54):
          steptype = event.key - 49
          updtext = 'step mode changed to '+stepmode[steptype]
        if event.key == 13:
          line = stepmode[steptype]
          for i in range(4):
            line += steps[i]
	  stepfile.write(line+'\n')
          for i in range(4):
            steps[i] = '00 '
          updtext = "Wrote "+line 
        if event.key == K_LEFT:
          updtext = 'toggled left arrow to '
          updarr = 0
        if event.key == K_DOWN:
          updtext = 'toggled down arrow to '
          updarr = 1
        if event.key == K_UP:
          updtext = 'toggled up arrow to '
          updarr = 2
        if event.key == K_RIGHT:
          updtext = 'toggled right arrow to '
          updarr = 3
        if updarr != -1:
          if steps[updarr] == '00 ':
            steps[updarr] = '08 '
            updtext += 'on'
          else:
            steps[updarr] = '00 '
            updtext += 'off'

  stepfile.write("\n")
  stepfile.write("end\n")
  stepfile.close()
  print "Wrote footer and closed file. Ending inSTEP session."
                   
#end
    
if __name__ == '__main__': main()
