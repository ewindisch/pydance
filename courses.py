# Like DWI and SM files, CRS files are a variant of the MSD format.

from constants import *
import audio
import optionscreen
import pygame
import dance
import games
import colors
import util
import ui

NO_BANNER = pygame.image.load(os.path.join(image_path, "no-banner.png"))

# FIXME: Parse random songs (*)
# FIXME: Parse player's best
class CRSFile:
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

  def __init__(self, filename):
    self.filename = filename
    self.songs = []
    self.name = "A Course"
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

        name = name.replace("\\", "/") # DWI uses Windows-style.

        fullname = None
        for dir in mainconfig["songdir"].split(os.pathsep):
          path = os.path.join(dir, name)
          file_list = util.find(path, ["*.sm", "*.dwi"])
          if len(file_list) != 0:
            fullname = file_list[-1]
            break
        else: raise RuntimeError("Unable to find %s in song paths." % name)

        mods = {}
        for mod in modifiers:
          if mod in CRSFile.modifier_map:
            key, value = CRSFile.modifier_map[mod]
            mods[key] = value
        
        self.songs.append((fullname, diff, mods))

      image_name = self.filename[:-3] + "png"
      if os.path.exists(image_name):
        self.image = pygame.image.load(image_name).convert()
      else:
        self.image = NO_BANNER
        self.image.set_colorkey(self.image.get_at([0, 0]))
        

class CourseSelector(object):
  def __init__(self, songitems, screen, gametype):

    self.courses = []
    self.player_configs = [dict(player_config)]
    clock = pygame.time.Clock()

    if games.GAMES[gametype].players == 2:
      self.player_configs.append(dict(player_config))

    self.game_config = dict(game_config)
    self.gametype = gametype

    for dir in [pydance_path, rc_path]:
      dir = os.path.join(dir, "courses")
      filelist = util.find(dir, ["*.crs"])
      for fn in filelist:
        try: self.courses.append(CRSFile(fn))
        except RuntimeError, message: print "E:", message

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
    playlist = []
    for song in course.songs:
      # FIXME: Support modifiers
      playlist.append((song[0], [song[1]] * len(self.player_configs)))
    dance.play(screen, playlist, self.player_configs,
               self.game_config, self.gametype)

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
    pygame.display.update()
