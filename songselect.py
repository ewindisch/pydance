# The song selector; take songs with metadata, output pretty pictures,
# let people select difficulties, and dance.

import os, string, pygame, random, copy
from constants import *

import fileparsers

# Dispatcher for file parsers - A sequence of tuples of ext, ClassToInit
formats = ((".step", fileparsers.StepFile), )

font26 = pygame.font.Font(None, 26)
font20 = pygame.font.Font(None, 20)
font12 = pygame.font.Font(None, 14)

# FIXME: this needs to be moved elsewhere if we want theming
ss_bg = pygame.image.load(os.path.join(image_path, "ss-item-bg.png"))

# FIXME: We need more difficulties here
DIFFICULTIES = ["BEGINNER", "BASIC", "TRICK", "MANIAC", "SMANIAC"]
difficulty_colors = { "BEGINNER": (210, 210, 210),
                      "BASIC": (255, 200, 75),
                      "TRICK": (252, 128, 75),
                      "MANIAC": (0, 178, 0),
                      "SMANIAC": (191, 0, 178)
                     }

ITEM_SIZE = (344, 60)
BANNER_LOCATION = (5, 5)
BANNER_SIZE = (256, 80)
DIFF_BOX_SIZE = (15, 25)
DIFF_LOCATION = (8, 120)

# Make a box of a specific color - these are used for difficulty ratings
def make_box(color):
  img = pygame.surface.Surface(DIFF_BOX_SIZE)
  light_color = map((lambda x: min(255, x + 64)), color)
  dark_color = map((lambda x: max(0, x - 64)), color)
  img.fill(color)
  pygame.draw.line(img, light_color, (0,0), (0, DIFF_BOX_SIZE[1] - 1))
  pygame.draw.line(img, light_color, (0,0), (DIFF_BOX_SIZE[0] - 1, 0))
  pygame.draw.line(img, dark_color, (DIFF_BOX_SIZE[0]-1, DIFF_BOX_SIZE[1]-1),
                   (0, DIFF_BOX_SIZE[1] - 1))
  pygame.draw.line(img, dark_color, (DIFF_BOX_SIZE[0]-1, DIFF_BOX_SIZE[1]-1),
                   (DIFF_BOX_SIZE[0] - 1, 0))
  return img

# Return a list of available difficulties in order, given a hash of them
def sorted_diff_list(difficulty_hash):
  diffs = []
  dhash = copy.copy(difficulty_hash)
  for d in DIFFICULTIES:
    if dhash.has_key(d):
      diffs.append(d)
      del(dhash[d])
  for key in dhash: diffs.append(key)
  return diffs

# Encapsulates functionality for rendering/displaying songs
# Needs to be refactored for theming of songselect
class SongItem:
  def __init__(self, filename, read_steps = True):
    song = None
    for pair in formats:
      if filename[-len(pair[0]):].lower() == pair[0]:
        song = pair[1](filename, {"read_steps": read_steps})
        break
    if song == None:
      print filename, "is in an unsupported format."
      sys.exit(1) # FIXME: Should raise an exception
    self.info = song.info
    self.info["bpm"] = float(self.info["bpm"])
    if self.info.has_key("offset"):
      self.info["offset"] = int(self.info["offset"])
    self.steps = song.steps
    self.lyrics = song.lyrics
    self.difficulty = song.difficulty
    self.diff_list = {}
    for key in self.difficulty:
      self.diff_list[key] = sorted_diff_list(self.difficulty[key])
    self.banner = None
    self.menuimage = None

  def render(self):
    if self.banner == None: #FIXME
      if self.info.has_key("banner") and self.info["banner"] != None:
        banner = pygame.image.load(self.info["banner"]).convert()
        if banner.get_rect().size[0] > banner.get_rect().size[1] * 2:
          self.banner = banner
        else:
          # One of the older banners that we need to rotate
          self.banner = pygame.transform.rotate(banner,-45)
          self.banner.set_colorkey(self.banner.get_at((0,0)), RLEACCEL)
      else:
        self.banner = pygame.image.load(os.path.join(image_path,
                                                     "no-banner.png"))
    if self.menuimage == None:
      colors = ["cyan", "aqua", "orange", "yellow", "red", "white"]
      # Start with a random color, but...
      color = lyric_colors[colors[random.randint(0, len(colors) - 1)]]

      if self.info.has_key("mix"): # ... pick a consistent color for each mix
          color = lyric_colors[colors[hash(self.info["mix"]) % len(colors)]]

      self.menuimage = pygame.surface.Surface(ITEM_SIZE)
      self.menuimage.blit(ss_bg, (0,0))
      songtext = font26.render(self.info["song"], 1, color)
      self.menuimage.blit(songtext, (10, 5))

      subtext_text = " "
      if self.info.has_key("subtitle"):
        subtext_text += "- " + self.info["subtitle"]
      if self.info.has_key("mix"):
        subtext_text = self.info["mix"] + subtext_text
        
      subtext = font12.render(subtext_text, 1, color)
      self.menuimage.blit(subtext, (30, 26))
      grouptext = font20.render("by " + self.info["group"], 1, color)
      self.menuimage.blit(grouptext, (15, 36))

class SongSelect:
  def __init__(self, files, screen, gametype = "SINGLE", players = 1):
    # This is actually really inefficient when we support multiple game types.
    self.songs = map((lambda f: SongItem(f, read_steps = False)), files)
    self.songs = [s for s in self.songs if s.difficulty.has_key(gametype)]
    print "loaded",str(len(self.songs)),"songs"
    ev = (0, E_PASS)
    self.bg = pygame.image.load(os.path.join(image_path, "ss-bg.png"))
    self.numsongs = len(self.songs)
    self.gametype = gametype
    self.player_diffs = [0]
    self.player_image = [pygame.image.load(os.path.join(image_path,
                                                        "player0.png"))]
    index = 0
    self.render(screen, index)
    self.sortmodes = ["song", "group", "mix", "bpm"]
    self.sortmode = 0
    while ev[1] != E_QUIT:
      ev = event.poll()

      # This is a cheap way of keeping the same difficulty between songs:
      # We keep a constant and mod it by the length of the list, so
      # unless up/down is pressed, you will always be the same difficulty
      # on the same song - and between songs that have the same difficulty
      # levels (e.g. the standard 3).

      # Scroll up the menu list
      if (ev[1] == E_LEFT or event.states[(0, E_LEFT)] or
          event.states[(1, E_LEFT)]):
        index = (index - 1) % self.numsongs
        self.render(screen, index)
      # Down the menu list
      elif (ev[1] == E_RIGHT or event.states[(0, E_RIGHT)] or
            event.states[(1, E_RIGHT)]):
        index = (index + 1) % self.numsongs
        self.render(screen, index)

      elif (ev[1] == E_UP and ev[0] < len(self.player_diffs)):
        self.player_diffs[ev[0]] -= 1
        self.player_diffs[ev[0]] %= len(self.songs[index].diff_list[gametype])
        self.render(screen, index)
      elif (ev[1] == E_DOWN and ev[0] < len(self.player_diffs)):
        self.player_diffs[ev[0]] += 1
        self.player_diffs[ev[0]] %= len(self.songs[index].diff_list[gametype])
        self.render(screen, index)
      elif ev[1] == E_START and ev[0] == len(self.player_diffs):
        self.player_diffs.append(0)
        file = os.path.join(image_path, "player" + str(ev[0]) + ".png")
        self.player_image.append(pygame.image.load(file))
        self.render(screen, index)
      elif ev[1] == E_START and ev[0] > 0:
        while len(self.player_diffs) > ev[0]:
          self.player_diffs.pop()
        self.render(screen, index)
      elif ev[1] == E_SCREENSHOT: # 's' for sort
        s = self.songs[index]
        self.new_sort()
        index = self.songs.index(s)
        self.render(screen, index)
      pygame.time.wait(50)

  def render(self, screen, index):
    screen.blit(self.bg, (0,0))

    # The song list
    for i in range(-4, 5):
      self.songs[(index + i) % self.numsongs].render()
      x = 640 - 30 * (2 - abs(i)) - ITEM_SIZE[0]
      y = 210 + i * 60
      img = self.songs[(index + i) % self.numsongs].menuimage
      img.set_alpha(226 - (40 * abs(i)))
      screen.blit(self.songs[(index + i) % self.numsongs].menuimage, (x,y))

    r = self.songs[index].banner.get_rect()
    r.center = (BANNER_LOCATION[0] + BANNER_SIZE[0] / 2,
                BANNER_LOCATION[1] + BANNER_SIZE[1] / 2)
    screen.blit(self.songs[index].banner, r)

    # Difficulties rendering
    difficulty = self.songs[index].difficulty[self.gametype]
    diff_list = self.songs[index].diff_list[self.gametype]
    song = self.songs[index]
    # FIXME - this is kinda messy... I dislike graphics code.
    # get rid of magic numbers
    i = 0
    for d in diff_list:
      color = (127, 127, 127)
      if difficulty_colors.has_key(d):
        color = difficulty_colors[d]
      box = make_box(color)
      box.set_alpha(140)
      text = font26.render(d.lower(), 1,
                           map((lambda x: min(255, x + 64)), color))
      r = text.get_rect()
      r.center = (DIFF_LOCATION[0] + 92,
                  DIFF_LOCATION[1] + 25 * i + 12)
      screen.blit(text, r)
      for j in range(int(difficulty[d])):
        screen.blit(box, (DIFF_LOCATION[0] + 25 + 15 * j,
                          DIFF_LOCATION[1] + 25 * i))
      box.set_alpha(64)
      for j in range(int(difficulty[d]), 9):
        screen.blit(box, (DIFF_LOCATION[0] + 25 + 15 * j,
                          DIFF_LOCATION[1] + 25 * i))
      for j in range(len(self.player_diffs)):
        if diff_list.index(d) == (self.player_diffs[j] % len(diff_list)):
          screen.blit(self.player_image[j], (DIFF_LOCATION[0] + 10 + 140 * j,
                                             DIFF_LOCATION[1] + 25 * i))
      i += 1

    pygame.display.flip()

  # Eventually we can make this smarter (difficulty, etc)
  def new_sort(self):
    self.sortmode = (self.sortmode + 1) % len(self.sortmodes)
    field = self.sortmodes[self.sortmode]
    self.songs.sort((lambda x, y: cmp(x.info.get(field), y.info.get(field))))
