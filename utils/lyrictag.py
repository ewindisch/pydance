#!/usr/bin/env python
# Rewritten version of a much hacked version of findbpm
# This program adds lyrics to stepfiles or other files

import sys, time, getopt, os
import pygame, pygame.font, pygame.image, pygame.mixer
from pygame.locals import *

VERSION = "0.5"

def usage():
  print "lyrictag " + VERSION + " - time lyrics for PyDDR step files"
  print "Usage: " + sys.argv[0] + " [options]"
  print """\
  --song, -s      Music to play (Ogg Vorbis or MP3)
  --lyrics, -l    A text file containing lyrics to read from
  --output, -o    Filename for lyric data output

The lyrics in the file will be displayed, and one will be highlighted.
When the highlighted lyric is said in the song, press enter or space to
move the pointer to the next line. Backspace moves back a line.

If the output file is a PyDDR step file, the lyrics will be added to it
automatically. If no output file is given, the name of the lyric file will
have '.lyric' appended to it."""

def main():

  try:
    opts, args = getopt.getopt(sys.argv[1:], "s:l:o:hv",
                               ["song", "lyrics", "output", "help", "version"])
  except getopt.GetoptError:
    usage()
    sys.exit(2)

  lyric_file = None
  output_file = None
  song_file = None

  outfile = None

  for o, a in opts:
    if o in ("-h", "--help"):
      usage()
      sys.exit()
    elif o in ("-v", "--version"):
      print "lyrictag version " + VERSION
      sys.exit()
    elif o in ("-s", "--song"): song_file = a
    elif o in ("-l", "--lyrics"): lyric_file = a
    elif o in ("-o", "--output"): output_file = a

  if len(args) == 1:
    lyric_file = args[0]
    output_file = args[0] + ".step"
    song_file = args[0] + ".ogg"

  if song_file == None:
    if len(args) == 2: song_file = args[0]
    else: print "No song file given! Please use the --song (or -s) option"

  if lyric_file == None:
    if len(args) == 2: lyric_file = args[1]
    else: print "No lyric file given! Please use the --lyrics (or -l) option"

  if output_file == None and lyric_file != None:
    output_file = lyric_file + ".lyric"

  if not (output_file and song_file and lyric_file):
    print
    usage()
    sys.exit(3)

  text_file = open(lyric_file,"r")

  if os.access(output_file, os.W_OK) and output_file[-5:].lower() == ".step":
    outfile = open(output_file, "r+")
    for line in outfile.readlines():
      if line == "LYRICS\n":
        print "error: this step file already has lyrics"
        sys.exit(5)

  elif not os.access(output_file, os.F_OK):
    outfile = open(output_file, "w")
  elif not output_file[-6:].lower() == ".lyric":
    print "error: output file exists and is not a step file or lyric file"
    sys.exit(4)
  else:
    outfile = open(output_file, "w")
    
  outfile.write("LYRICS\n")

  lyric_text = []
  text_to_write = []
  fileline = '-'
  while fileline != '':
    fileline = text_file.readline()
    if fileline != '\n' and fileline != '':
      lyric_text.append(fileline[0:-1])
  lyric_text.append('[END OF FILE]')
 
  pygame.init()
  screen = pygame.display.set_mode((640, 480), HWSURFACE|DOUBLEBUF)
  pygame.display.set_caption('Lyric Tagger')
  screen.fill((0,0,0))

  pygame.mixer.music.load(song_file)
  pygame.mixer.music.play()
  beatstart = pygame.time.get_ticks()

  output_mode = 0 # 0 = atsec, 1 = waits
  current_time = 0
  last_time = 0

  current_line = 0
  total_lines = len(lyric_text) - 1

  font = pygame.font.Font(None, 48)

  while 1:
    time.sleep(0.0001)
    event = pygame.event.poll()

    screen.fill((0,0,0))
    for j in range(11):
      i = j - 5 
      c = i + current_line
      if c >= 0 and c <= total_lines:
        if j == 5:
          text = font.render(lyric_text[c], 1, (224, 224, 224))
        else:
          text = font.render(lyric_text[c], 1, (160, 160, 160))
        textpos = text.get_rect()
        textpos.centerx = screen.get_rect().centerx
        textpos.centery = 20 + (48*j)
        screen.blit(text, textpos)
      # show name
    pygame.display.flip()

    if event.type == QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
      break

    if not pygame.mixer.music.get_busy():
      break

    if event.type == KEYDOWN:
      if event.key == K_BACKSPACE and current_line != 0:
        current_line -= 1
        text_to_write.pop()
        text_to_write.pop()
      elif event.key == K_a:
        output_mode ^= 1
      elif current_line < total_lines:
        last_time = current_time
        current_time = pygame.time.get_ticks()/1000.0
        if output_mode == 0:
          text_to_write.append("atsec "+repr(current_time)+"\n")
        else:
          text_to_write.append("waits "+repr(current_time - last_time)+"\n")
          
        if (lyric_text[current_line][0] == "(" and
            lyric_text[current_line][-1] == ")"):
          text_to_write.append("trans "+lyric_text[current_line][1:-1]+"\n")
        else:
          text_to_write.append("lyric "+lyric_text[current_line] + "\n")
        current_line += 1

  for text in text_to_write:
    outfile.write(text)
  outfile.write("end\n")
  print "Song ended."

if __name__ == '__main__':
    main()
