import os
import random
import pygame

from constants import *

class Announcer:
  def __init__(self, name):
    self.sections = {}
    self.name = None
    self.author = None
    self.rev = None
    self.date = None
    filename = None
    for path in search_paths:
      if os.path.isfile(os.path.join(path,"themes","dj",name,"djtheme.cfg")):
        filename = os.path.join(path, "themes", "dj", name)
    if filename == None:
      print "Error: Cannot load announcer theme '%s'." % name
      sys.exit(1)

    fi = open(os.path.join(filename, "djtheme.cfg"), "r")
    sec = ""
    self.lasttime = -1000000
    for line in fi:
      if line.isspace() or len(line) == 0 or line[0] == '#': pass
      elif line[0] == "[" and line.strip()[-1] == "]":
        sec = line.strip()[1:-1].lower()
        self.sections[sec] = []
      elif sec == "announcer":
        key, val = line[:line.find(' ')], line[line.find(' ')+1:].strip()
        if key == "name": self.name = val
        elif key == "author": self.author = val
        elif key == "rev": self.rev = val
        elif key == "date": self.date = val
      else:
        self.sections[sec].append(os.path.join(filename, line.strip()))

  def __play(self, filename):
    if (pygame.time.get_ticks() - self.lasttime > 6000):
      snd = pygame.mixer.Sound(filename)
      snd.play()
    self.lasttime = pygame.time.get_ticks()

  def say(self, sec, mood=(0, 100)):
    if not self.sections.has_key(sec) or len(self.sections[sec]) == 0: return
    l = len(self.sections[sec])
    # Normalize mood wrt the number of choices
    try:
      mood = (int(mood[0] / 100.0 * l), min(int(mood[1] / 100.0 * l), l - 1))
    except TypeError:
      # Use a random variance of 10% if a scalar is given
      mood = (int(max(mood / 100.0 - 0.1, 0) * l), # don't < 0
              int(min(mood / 100.0 + 0.1, 0.999) * l)) # don't == l

    self.__play(self.sections[sec][random.randint(mood[0], mood[1])])
