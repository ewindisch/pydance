# Like DWI and SM files, CRS files are a variant of the MSD format.

# NB - If you are reading this code and are a better programmer than me,
# I apologize for this file. However, if you are reading this code and
# only *think* you are a better programmer than me, I suggest you try
# parsing CRS files quickly on your own, and then come back to this.

from constants import *
import audio
import optionscreen
import pygame
import dance
import random
import games
import colors
import util
import error
import ui

NO_BANNER = pygame.image.load(os.path.join(image_path, "no-banner.png"))

class CRSFile(object):
  # Map modifier names to internal pydance names.
  modifier_map = { "0.5x" : ("speed", 0.5),
                   "0.75x" : ("speed", 0.75),
                   "1.5x" : ("speed", 1.5),
                   "2.0x" : ("speed", 2.0),
                   "3.0x" : ("speed", 3.0),
                   "4.0x" : ("speed", 4.0),
                   "5.0x" : ("speed", 5.0),
                   "8.0x" : ("speed", 8.0),
                   "boost": ("accel", 1),
                   "break": ("accel", 2),
                   "sudden": ("fade", 1),
                   "hidden": ("fade", 2),
                   "cycle": ("fade", 4),
                   "stealth": ("fade", 5),
                   "mirror": ("transform", 1),
                   "left": ("transform", 2),
                   "right": ("transform", 3),
                   "shuffle": ("transform", -1),
                   "random": ("transform", -2),
                   "little": ("size", 2),
                   "reverse": ("scrollstyle", 1),
                   "noholds": ("holds", 0),
                   "dark": ("dark", 1),
                   }

  def __init__(self, filename, all_songs):
    self.filename = filename
    self.songs = []
    self.name = "A Course"
    self.mixname = " "
    self.all_songs = all_songs
    lines = []
    f = open(filename)
    for line in f:
      if line.find("//") != -1: line = line[:line.find("//")]
      line = line.strip()

      if len(line) == 0: continue
      elif line[0] == "#": lines.append(line[1:]) # A new tag
      else: lines[-1] += line

    for i in range(len(lines)):
      line = lines[i]
      while line[-1] == ";": line = line[:-1] # Some lines have two ;s.
      lines[i] = line.split(":")

    if os.path.split(self.filename)[0][-7:] != "courses":
      self.mixname = os.path.split(os.path.split(self.filename)[0])[1]

    for line in lines:
      if line[0] == "COURSE": self.name = ":".join(line[1:])
      elif line[0] == "SONG":
        if len(line) == 3:
          name, diff = line[1:]
          modifiers = []
        elif len(line) == 4:
          name, diff, modifiers = line[1:]
          modifiers = modifiers.split(",")
        else: continue

        if name[0:4] == "BEST" or name[0:5] == "WORST":
          raise RuntimeError("Player's best and worst is not supported.")

        name = name.replace("\\", "/") # DWI uses Windows-style separators.

        mods = {}
        for mod in modifiers:
          if mod in CRSFile.modifier_map:
            key, value = CRSFile.modifier_map[mod]
            mods[key] = value
        
        self.songs.append((name, diff, mods))

      image_name = self.filename[:-3] + "png"
      if os.path.exists(image_name):
        self.image = pygame.image.load(image_name).convert()
      else:
        self.image = NO_BANNER
        self.image.set_colorkey(self.image.get_at([0, 0]))

  def setup(self, screen, player_configs, game_config, gametype):
    self.player_configs = player_configs
    self.game_config = game_config
    self.index = 0
    self.gametype = gametype
    self.screen = screen

  def done(self):
    self.screen = self.player_configs = self.game_config = None

  def _find_difficulty(self, song, diff):
    if self.gametype not in song.difficulty: return False
    elif isinstance(diff, str):
      if diff in song.difficulty[self.gametype]: return diff
      else: return False
    elif isinstance(diff, list):
      possible = []
      for name, rating in song.difficulty[self.gametype].items():
        if rating in diff: possible.append(name)
      if len(possible) > 0: return random.choice(possible)
    return False

  def __iter__(self): return self

  def next(self):
    if self.index == len(self.songs): raise StopIteration
    
    name, diff, mods = self.songs[self.index]
    fullname = None

    a, b = 0, 0
    if diff.find("..") != -1: a, b = map(int, diff.split(".."))
    elif len(diff) < 3: a, b = int(diff), int(diff)
    if a or b: diff = range(a, b + 1)

    if name[-1] == "*": # A random song
      if "/" in name:
        folder, dummy = name.split("/")
        folder = folder.lower()
        if folder in self.all_songs:
          songs = self.all_songs[folder].values()
        else:
          error.ErrorMessage(self.screen, [folder, "was not found."])
          raise StopIteration

      else:
        songs = []
        for v in self.all_songs.values(): songs.extend(v.values())

      songs = [s for s in songs if self._find_difficulty(s, diff)]

      if len(songs) == 0:
        error.ErrorMessage(self.screen, ["No valid songs were found."])
        raise StopIteration
      else:
        song = random.choice(songs)
        diff = self._find_difficulty(song, diff)
        fullname = song.filename
        
    else:
      for path in mainconfig["songdir"].split(os.pathsep):
        fn = os.path.join(path, name)
        if os.path.isfile(fn): fullname = fn
        elif os.path.isdir(fn):
          file_list = util.find(fn, ["*.sm", "*.dwi"])
          if len(file_list) != 0: fullname = file_list[0]

        if not fullname: # Still haven't found it...
          folder, song = name.split("/")
          song = self.all_songs.get(folder.lower(), {}).get(song.lower())
          fullname = song.filename

        if fullname: break

    if not fullname:
      error.ErrorMessage(self.screen, [name, "was not found."])
      raise StopIteration

    self.index += 1

    return (fullname, [diff] * len(self.player_configs))


class CourseSelector(object):
  def __init__(self, songitems, courses, screen, gametype):

    self.courses = courses
    self.player_configs = [dict(player_config)]
    clock = pygame.time.Clock()

    if games.GAMES[gametype].players == 2:
      self.player_configs.append(dict(player_config))

    self.game_config = dict(game_config)
    self.gametype = gametype

    self.courses.sort(lambda a, b: cmp(a.filename, b.filename))

    screen.fill(colors.BLACK)

    self.course_idx = 0

    ev = ui.ui.poll()

    while ev[1] != ui.QUIT:
      ev = ui.ui.poll()

      if ev[1] == ui.START:

        if optionscreen.player_opt_driver(screen, self.player_configs):
          self.play(screen)

        audio.load(os.path.join(sound_path, "menu.ogg"))
        audio.play(4, 0.0)

        ui.ui.clear()

      elif ev[1] == ui.SELECT:
        optionscreen.game_opt_driver(screen, self.game_config)

      elif ev[1] == ui.LEFT:
        self.course_idx = (self.course_idx - 1) % len(self.courses)
      elif ev[1] == ui.RIGHT:
        self.course_idx = (self.course_idx + 1) % len(self.courses)

      self.render(screen)
      clock.tick(30)

    player_config.update(self.player_configs[0])

  def play(self, screen):
    course = self.courses[self.course_idx]
    course.setup(screen, self.player_configs, self.game_config, self.gametype)
    dance.play(screen, course, self.player_configs,
               self.game_config, self.gametype)
    course.done()

  def render(self, screen):
    screen.fill(colors.BLACK)

    course = self.courses[self.course_idx]
    img = course.image
    r = img.get_rect()
    r.center = [320, 240]
    screen.blit(img, r)
    txt = FONTS[48].render(course.name, True, colors.WHITE)
    r = txt.get_rect()
    r.center = [320, 100]
    screen.blit(txt, r)
    txt = FONTS[32].render(course.mixname, True, colors.WHITE)
    r = txt.get_rect()
    r.center = [320, 50]
    screen.blit(txt, r)
    pygame.display.update()
