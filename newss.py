import os
import math
import pygame
import fontfx
import colors
import ui
import records
import grades
import dance
import random

from constants import *
from pygame.mixer import music

NO_BANNER = os.path.join(image_path, "no-banner.png")

DIFF_COLORS = { "BEGINNER": colors.color["white"],
                "LIGHT": colors.color["orange"],
                "EASY": colors.color["orange"],
                "BASIC": colors.color["orange"],
                "STANDARD": colors.color["red"],
                "STANDER": colors.color["red"], # Shit you not, 3 people.
                "TRICK": colors.color["red"],
                "MEDIUM": colors.color["red"],
                "DOUBLE": colors.color["red"],
                "ANOTHER": colors.color["red"],
                "PARA": colors.color["blue"],
                "NORMAL": colors.color["red"],
                "MANIAC": colors.color["green"],
                "HARD": colors.color["green"],
                "HEAVY": colors.color["green"],
                "HARDCORE": colors.color["purple"],
                "SMANIAC": colors.color["purple"],
                "S-MANIAC": colors.color["purple"], # Very common typo
                "CHALLENGE": colors.color["purple"],
                "CRAZY": colors.color["purple"],
                "EXPERT": colors.color["purple"]
                }

SORTS = {
  "subtitle": (lambda x, y: cmp(str(x.info["subtitle"]).lower(),
                                str(y.info["subtitle"]).lower())),
  "title": (lambda x, y: (cmp(x.info["title"].lower(),
                              y.info["title"].lower()) or
                          SORTS["subtitle"](x, y))),
  "artist": (lambda x, y: (cmp(x.info["artist"].lower(),
                               y.info["artist"].lower()) or
                           SORTS["title"](x, y))),
  "bpm": (lambda x, y: (cmp(x.info["bpm"], y.info["bpm"]) or
                        SORTS["title"](x, y))),
  "mix": (lambda x, y: (cmp(str(x.info["mix"]).lower(),
                            str(y.info["mix"]).lower()) or
                        SORTS["title"](x, y)))
  }

SORT_NAMES = ["mix", "title", "artist", "bpm"]

NUM_SORTS = len(SORT_NAMES)


SS_HELP = [
  "Up / Down changes song selection",
  "Left / Right changes difficulty setting",
  "Confirm / O / Up Right opens a folder or starts a song",
  "Escape / X / Up Left closes a folder or backs up",
  "Select / Tab takes you to a random song",
  "Start / Enter switches between screens",
  "F11 toggles fullscreen - S changes the sort mode.",
  "Enjoy pydance 0.9.0!",
  ]

# Make an outlined box. The size is given without the 4 pixel border.
# This usually gets alphaed before stuff gets put in it.
def make_box(color = [111, 255, 148], size = [130, 40]):
  s = pygame.Surface([size[0] + 8, size[1] + 8], SRCALPHA, 32)
  s.fill(color + [100])
  r = s.get_rect()
  for c in [[255, 255, 255, 170], [212, 217, 255, 170],
            [255, 252, 255, 170], [104, 104, 104, 170]]:
    pygame.draw.rect(s, c, r, 1)
    r.width -= 2
    r.height -= 2
    r.top += 1
    r.left += 1
  return s

def folder_name(name, type):
  if type == "mix": return name
  elif type == "bpm": return "%s BPM" % name
  else: return "%s: %s" % (type.capitalize(), name)

def load_banner(filename):
  banner = pygame.image.load(filename)
  size = banner.get_size()
  if size <= (100, 100): # Parapara-style... no idea what to do.
    return banner, None
  elif size == (177, 135): # KSF-style 1
    return banner, None
  elif size == (300, 200): # KSF-style 2
    banner.set_colorkey(banner.get_at([0, 0]), RLEACCEL)
    return banner, None
  elif abs(size[0] - size[1]) < 3: # "Square", need to rotate.
    banner = banner.convert()
    banner.set_colorkey(banner.get_at([0, 0]), RLEACCEL)
    return pygame.transform.rotozoom(banner, -45, 1.0), [51, 50, 256, 80]
  else: # 256x80, standard banner, I hope.
    if size != (256, 80): banner = pygame.transform.scale(banner, [256, 80])
    b2 = make_box([0, 0, 0], [256, 80])
    b2.blit(banner, [4, 4])
    return b2, None

class SongItemDisplay(object):
  no_banner = make_box(size = [256, 80])
  tmp = pygame.image.load(NO_BANNER)
  tmp.set_colorkey(tmp.get_at([0, 0]))
  no_banner.blit(tmp, [4, 4])

  def __init__(self, song): # A SongItem object
    self._song = song
    self.difficulty = song.difficulty
    self.info = song.info
    self.filename = song.filename
    self.diff_list = song.diff_list
    self.banner = None
    self.isfolder = False
    self.folder = {}
    self.banner = None
    self.clip = None

  def render(self):
    if self.banner: return
    elif self._song.info["banner"]:
      self.banner, self.clip = load_banner(self._song.info["banner"])
    else: self.banner = SongItemDisplay.no_banner

class FolderDisplay(object):
  def __init__(self, name, type, count):
    self.name = name
    self._name = folder_name(name, type)
    self._type = type
    self.isfolder = True
    self.banner = None
    self.clip = None
    self.info = {}
    self.info["title"] = self._name
    self.info["artist"] = "%d songs" % count
    self.info["subtitle"] = None

  def render(self):
    if self.banner: return

    name = self.name.encode("ascii", "ignore")
    for path in [rc_path, pydance_path]:
      filename = os.path.join(path, "banners", self._type, name+".png")
      if os.path.exists(filename):
        self.banner, self.clip = load_banner(filename)
        break

    else:
      if self._type == "mix":
        for dir in mainconfig["songdir"].split(os.pathsep):
          dir = os.path.expanduser(dir)
          fn = os.path.join(dir, name, "banner.png")
          if os.path.exists(fn): self.banner, self.clip = load_banner(fn)

    if self.banner == None: self.banner = SongItemDisplay.no_banner

class TextDisplay(pygame.sprite.Sprite):
  def __init__(self, font, size, midleft, str = " "):
    pygame.sprite.Sprite.__init__(self)
    self._text = " "
    self._font = font
    self._size = size
    self._midleft = midleft
    self._render()

  def _render(self):
    self._needs_update = False
    font = fontfx.max_size(self._text, self._size[0], self._font)
    img = fontfx.shadow(self._text, font, 1, [255, 255, 255], [0, 0, 0])
    self.image = img
    self.rect = self.image.get_rect()
    self.rect.midleft = self._midleft

  def set_text(self, text):
    self._text = text
    self._needs_update = True

  def update(self, time):
    if self._needs_update: self._render()

# Crossfading help text along the top of the screen.
class HelpText(pygame.sprite.Sprite):
  def __init__(self, strs, color, bgcolor, font, center):
    pygame.sprite.Sprite.__init__(self)
    self._idx = -1
    self._strings = [(s, font.render(s, True, color, bgcolor).convert())
                     for s in strs]
    self._center = center
    self._start = pygame.time.get_ticks()
    self._fade = -1
    self._bgcolor = bgcolor
    self._end = -1
    self.update(self._start)

  def update(self, time):
    time -= self._start
    # Time to switch to the next bit of text.
    if time > self._end:
      self._idx = (self._idx + 1) % len(self._strings)
      self.image = self._strings[self._idx][1]
      self.image.set_alpha(255)
      self._fade = time + 100 * len(self._strings[self._idx][0])
      self._end = self._fade + 750

    # There's a .75 second delay during which text crossfades.
    elif time > self._fade:
      p = (time - self._fade) / 750.0
      s1 = self._strings[self._idx][1]
      s1.set_colorkey(s1.get_at([0, 0]))
      s1.set_alpha(int(255 * (1 - p)))
      
      i = (self._idx + 1) % len(self._strings)
      s2 = self._strings[i][1]
      s2.set_colorkey(s2.get_at([0, 0]))
      s2.set_alpha(int(255 * p))

      h = max(s1.get_height(), s2.get_height())
      w = max(s1.get_width(), s2.get_width())
      self.image = pygame.Surface([w, h], 0, 32)
      self.image.fill(self._bgcolor)
      self.image.set_colorkey(self.image.get_at([0, 0]))
      r = s1.get_rect()
      r.center = self.image.get_rect().center
      self.image.blit(s1, r)
      r = s2.get_rect()
      r.center = self.image.get_rect().center
      self.image.blit(s2, r)

    self.image.set_colorkey(self.image.get_at([0, 0]))
    self.rect = self.image.get_rect()
    self.rect.center = self._center

# Flashy indicator for showing current menu position.
class ActiveIndicator(pygame.sprite.Sprite):
  def __init__(self, topleft):
    pygame.sprite.Sprite.__init__(self)
    self.image = pygame.image.load(os.path.join(image_path, "indicator.png"))
    self.image.convert()
    self.image.set_colorkey(self.image.get_at([0, 0]))
    self.rect = self.image.get_rect()
    self.rect.topleft = topleft

  def update(self, time):
    self.image.set_alpha(int(255 * (0.3 + (math.sin(time / 720.0)**2 / 3.0))))

# Box to indicate the current difficulty level.
class DifficultyBox(pygame.sprite.Sprite):
  def __init__(self, pid, numplayers):
    pygame.sprite.Sprite.__init__(self)
    self._topleft = [19 + (233 * pid), 414]

  def set(self, diff, color, feet, grade):
    f = pygame.font.Font(None, 24)
    self.image = make_box(color)

    t1 = fontfx.shadow(diff, f, 1, [255, 255, 255], [0, 0, 0])
    r1 = t1.get_rect()
    r1.center = [self.image.get_width()/2, 14]

    t2 = fontfx.shadow("x%d - %s" % (feet, grade), f, 1,
                       [255, 255, 255],[0, 0, 0])
    r2 = t2.get_rect()
    r2.center = [self.image.get_width()/2, 34]

    self.image.blit(t1, r1)
    self.image.blit(t2, r2)

    self.rect = self.image.get_rect()
    self.rect.topleft = self._topleft
    self.image.set_alpha(140)

class ListBox(pygame.sprite.Sprite):
  def __init__(self, font, color, spacing, count, width, topleft):
    pygame.sprite.Sprite.__init__(self)
    self._idx = self._oldidx = 0
    self._h = spacing
    self._count = count
    self._w = width
    self._color = color
    self._topleft = topleft
    self.set_items([""])
    self._needs_update = True
    self._render()

  def set_items(self, items):
    c2 = [c / 8 for c in self._color]
    self._items = []

    for i in items:
      f = fontfx.max_size(i, self._w - 5, 28)
      img = fontfx.shadow(i, f, 1, self._color, c2)
      self._items.append(img)
    self._needs_update = True

  def set_index(self, idx):
    self._oldidx = self._idx
    self._idx = idx
    self._needs_update = True

  def update(self, time):
    if self._idx != self._oldidx or self._needs_update:
      self._oldidx = self._idx
      self._needs_update = False
      self._render()

  def _render(self):
    self.image = pygame.Surface([self._w, self._h * self._count],
                                SRCALPHA, 32)
    self.image.fill([0, 0, 0, 0])
    for i, y in zip(range(self._count),
                    range(self._h / 2, self._h * self._count, self._h)):
      idx = (self._idx + i) % len(self._items)
      t = self._items[idx]
      r = t.get_rect()
      r.centery = y
      r.left = 5
      self.image.blit(t, r)
    self.rect = self.image.get_rect()
    self.rect.topleft = self._topleft

class BannerDisplay(pygame.sprite.Sprite):
  def __init__(self, size, center):
    pygame.sprite.Sprite.__init__(self)
    self.isfolder = False
    self._center = center
    self._clip = None
    self._color = [255, 0, 255]
    self._next_update = -1
    self._delta = 5
    self._idx = 1

  def set_song(self, song):
    c1, c2 = [255, 255, 255], [30, 30, 30]
    self._next_update = -2 # Magic value

    song.render()

    self._title = fontfx.shadow(song.info["title"],
                                fontfx.max_size(song.info["title"], 340, 60),
                                1, c1, c2)
    self._r_t = self._title.get_rect()
    self._r_t.center = [179, 240]
    self._artist = fontfx.shadow(song.info["artist"],
                                 fontfx.max_size(song.info["artist"], 250, 40),
                                 1, c1, c2)

    self._r_a = self._artist.get_rect()
    self._r_a.center = [179, 320]

    if song.info["subtitle"]:
      self._subtitle = fontfx.shadow(song.info["subtitle"],
                                     fontfx.max_size(song.info["subtitle"],
                                                     300, 24),

                                     1, c1, c2)
      self._r_s = self._subtitle.get_rect()
      self._r_s.center = [179, 270]
    else: self._subtitle = None
    self._clip = song.clip
    self._banner = song.banner
    self._r_b = self._banner.get_rect()
    self._r_b.center = (179, 100)

  def _render(self):
    self.image = make_box(self._color, [350, 350])
    self.image.blit(self._banner, self._r_b)
    self.image.set_clip(None)
    
    self.image.blit(self._title, self._r_t)
    self.image.blit(self._artist, self._r_a)
    if self._subtitle: self.image.blit(self._subtitle, self._r_s)

    self.rect = self.image.get_rect()
    self.rect.center = self._center

  def update(self, time):
    if self._next_update == -2:
      self._next_update = time + 300
      self._render()
    elif time > self._next_update:
      self._next_update = time + 300
      if ((self._delta > 0 and self._color[self._idx] == 255) or
          (self._delta < 0 and self._color[self._idx] == 0)):
        self._idx = random.choice([i for i in range(3) if i != self._idx])
        if self._color[self._idx]: self._delta = -3
        else: self._delta = 3
      self._color[self._idx] += self._delta
      self._render()

class SongPreview(object):
  def __init__(self):
    self._playing = False
    self._filename = None
    self._end_time = self._start_time = 0
    if not mainconfig["previewmusic"]:
      music.load(os.path.join(sound_path, "menu.ogg"))
      music.play(4, 0.0)
 
  def preview(self, song):
    if mainconfig["previewmusic"] and not song.isfolder:
      if len(song.info["preview"]) == 2:
        # A DWI/SM/dance-style preview, an offset in the song and a length
        # to play starting at the offset.
        self._start, length = song.info["preview"]
        self._filename = song.info["filename"]
      else:
        # KSF-style preview, a separate filename to play.
        self._start, length = 0, 100
        self._filename = song.info["preview"]
      if self._playing: music.fadeout(500)
      self._playing = False
      self._start_time = pygame.time.get_ticks() + 500
      self._end_time = int(self._start_time + length * 1000)
    elif song.isfolder: music.fadeout(500)

  def update(self, time):
    if self._filename is None: pass
    elif time < self._start_time: pass
    elif not self._playing:
      try:
        music.load(self._filename)
        music.set_volume(0.01) # 0.0 stops pygame.mixer.music.
        music.play(0, self._start)
        self._playing = True
      except: # Filename not found? Song is too short? SMPEG blows?
        music.stop()
        self.playing = False
    elif time < self._start_time + 1000: # mixer.music can't fade in
      music.set_volume((time - self._start_time) / 1000.0)
    elif time > self._end_time - 1000:
      music.fadeout(1000)
      self._playing = False
      self._filename = None

class MainWindow(object):
  def __init__(self, songs, courses, screen, game):
    self._screen = screen
    self._bg = pygame.image.load(os.path.join(image_path, "newss-bg.png"))
    self._sprites = pygame.sprite.RenderUpdates()
    songs = [s for s in songs if s.difficulty.has_key(game)]
    self._songs = [SongItemDisplay(s) for s in songs]
    self._index = 0
    self._clock = pygame.time.Clock()
    self._game = game
    self._config = dict(game_config)
    self._all_songs = self._songs

    self._random_songs = [s for s in self._songs if s.info["valid"]]

    self._list = ListBox(pygame.font.Font(None, 28),
                         [255, 255, 255], 26, 16, 220, [410, 56])
    if len(self._songs) > 60 and mainconfig["folders"]:
      self._create_folders()
      name = SORT_NAMES[mainconfig["sortmode"]]
      self._create_folder_list()
    else:
      self._folders = None
      self._base_text = "All Songs"
      self._songs.sort(SORTS[SORT_NAMES[mainconfig["sortmode"] % NUM_SORTS]])
      self._list.set_items([s.info["title"] for s in self._songs])
      self._random_songs = [s for s in self._songs if s.info["valid"]]

    self._preview = SongPreview()
    self._preview.preview(self._songs[self._index])
    self._song = self._songs[self._index]

    # Both players must have the same difficulty in locked modes.
    self._locked = games.GAMES[self._game].couple

    players = games.GAMES[game].players
    self._diffs = [] # Current difficulty setting
    self._diff_widgets = [] # Difficulty widgets
    self._configs = []
    self._diff_names = [] # Last manually selected difficulty name

    for i in range(players):
      self._diffs.append(0)
      self._configs.append(dict(player_config))
      self._diff_names.append(" ")
      d = DifficultyBox(i, 2)
      if not self._song.isfolder:
        diff_name = self._song.diff_list[game][self._diffs[i]]
        rank = records.get(self._song.filename, diff_name, self._game)[0]
        grade = grades.grades[self._config["grade"]].grade_by_rank(rank)
        d.set(diff_name, DIFF_COLORS.get(diff_name, [127, 127, 127]),
              self._song.difficulty[game][diff_name], grade)
      else:
        d.set("None", [127, 127, 127], 0, "?")
      self._diff_widgets.append(d)
    
    self._sprites.add(self._diff_widgets)
    self._sprites.add(self._list)
    ActiveIndicator([405, 233]).add(self._sprites)
    self._banner = BannerDisplay([350, 300], [210, 230])
    self._banner.set_song(self._song)
    self._banner.add(self._sprites)
    self._sprites.add(HelpText(SS_HELP, [255, 255, 255], [0, 0, 0],
                               pygame.font.Font(None, 22), [206, 20]))

    self._title = TextDisplay(30, [218, 28], [415, 27])
    self._sprites.add(self._title)
    self._screen.blit(self._bg, [0, 0])
    pygame.display.update()
    self.loop()
    music.fadeout(500)
    pygame.time.wait(500)
    # FIXME Does this belong in the menu code? Probably.
    music.load(os.path.join(sound_path, "menu.ogg"))
    music.set_volume(1.0)
    music.play(4, 0.0)
    player_config.update(self._configs[0]) # Save p1's settings

  def loop(self):
    pid, ev = ui.ui.poll()
    self._list.set_index(self._index - 7)
    self._title.set_text(self._base_text + " - %d/%d" % (self._index + 1,
                                                         len(self._songs)))
    while not (ev == ui.CANCEL and (not self._folders or self._song.isfolder)):
      if pid >= len(self._diffs): pass # Inactive player
      
      elif ev == ui.UP: self._index -= 1
      elif ev == ui.DOWN: self._index += 1

      elif ev == ui.LEFT:
        if not self._song.isfolder:
          didx = (self._diffs[pid] - 1) % len(self._song.diff_list[self._game])
          self._diffs[pid] = didx
          name = self._song.diff_list[self._game][didx]
          self._diff_names[pid] = name

      elif ev == ui.RIGHT:
        if not self._song.isfolder:
          didx = (self._diffs[pid] + 1) % len(self._song.diff_list[self._game])
          self._diffs[pid] = didx
          name = self._song.diff_list[self._game][didx]
          self._diff_names[pid] = name

      elif ev == ui.SELECT:
        self._index = random.randrange(len(self._songs))

      elif ev == ui.SORT:
        s = self._songs[self._index]
        mainconfig["sortmode"] = (mainconfig["sortmode"] + 1) % NUM_SORTS
        if self._folders:
          if s.isfolder:
            self._create_folder_list()
          else:
            self._create_song_list(s.folder[SORT_NAMES[mainconfig["sortmode"]]])
            self._index = self._songs.index(s)
        else:
          self._songs.sort(SORTS[SORT_NAMES[mainconfig["sortmode"]]])
          self._index = self._songs.index(s)
          self._list.set_items([s.info["title"] for s in self._songs])

      elif ev == ui.CONFIRM:
        if self._song.isfolder:
          self._create_song_list(self._song.name)
          self._index = 0
        else:
          music.fadeout(500)
          diffs = [self._song.diff_list[self._game][self._diffs[i]]
                   for i in range(len(self._diffs))]
          dance.play(self._screen, [(self._song.filename, diffs)],
                     self._configs, self._config, self._game)
          music.fadeout(500) # The just-played song
          self._screen.blit(self._bg, [0, 0])
          pygame.display.flip()
          ui.ui.empty()
          ui.ui.clear()

      elif ev == ui.CANCEL:
        self._create_folder_list()

      elif ev == ui.FULLSCREEN:
        pygame.display.toggle_fullscreen()
        mainconfig["fullscreen"] ^= 1

      self._index %= len(self._songs)
      self._song = self._songs[self._index]

      if self._locked and ev in [ui.LEFT, ui.RIGHT]:
        for i in range(len(self._diffs)):
          self._diffs[i] = self._diffs[pid]
          self._diff_names[i] = self._diff_names[pid]

      if ev in [ui.CANCEL, ui.UP, ui.DOWN, ui.SELECT, ui.CONFIRM]:
        self._preview.preview(self._song)
        self._banner.set_song(self._song)

      if ev in [ui.CANCEL, ui.UP, ui.DOWN, ui.SELECT, ui.CONFIRM, ui.SORT]:
        self._list.set_index(self._index - 7)
        self._title.set_text(self._base_text + " - %d/%d" % (self._index + 1,
                                                             len(self._songs)))

      if ev in [ui.UP, ui.DOWN, ui.SELECT, ui.SORT, ui.CONFIRM]:
        if not self._song.isfolder:
          for i in range(len(self._diffs)):
            name = self._diff_names[i]
            if name in self._song.diff_list[self._game]:
              self._diffs[i] = self._song.diff_list[self._game].index(name)
            else: self._diffs[i] %= len(self._song.diff_list[self._game])
          
      if ev in [ui.UP, ui.DOWN, ui.LEFT, ui.RIGHT, ui.SELECT, ui.CONFIRM]:
        if not self._song.isfolder:
          for i in range(len(self._diffs)):
            name = self._song.diff_list[self._game][self._diffs[i]]
            rank = records.get(self._song.filename, name, self._game)[0]
            grade = grades.grades[self._config["grade"]].grade_by_rank(rank)
            self._diff_widgets[i].set(name,
                                      DIFF_COLORS.get(name, [127,127,127]),
                                      self._song.difficulty[self._game][name],
                                    grade)

      self.update()
      self._clock.tick(60)
      pid, ev = ui.ui.poll()

  def update(self):
    t = pygame.time.get_ticks()
    self._sprites.update(t)
    pygame.display.update(self._sprites.draw(self._screen))
    self._sprites.clear(self._screen, self._bg)
    self._preview.update(t)

  def _create_folders(self):
    mixes = {}
    artists = {}
    titles = {}
    bpms = {}

    for s in self._all_songs:
      if s.info["mix"] not in mixes: mixes[s.info["mix"]] = []
      mixes[s.info["mix"]].append(s)
      s.folder["mix"] = s.info["mix"]

      label = s.info["title"][0].capitalize()
      if label not in titles: titles[label] = []
      titles[label].append(s)
      s.folder["title"] = label

      label = s.info["artist"][0].capitalize()
      if label not in artists: artists[label] = []
      artists[label].append(s)
      s.folder["artist"] = label

      for rng in ((0, 50), (50, 100), (100, 121), (110, 120), (120, 130),
                  (130, 140), (140, 150), (150, 160), (160, 170), (170, 180),
                  (180, 190), (190, 200), (200, 225), (225, 250), (250, 275),
                  (275, 299.99999999)):
        if rng[0] < s.info["bpm"] <= rng[1]:
          label = "%3d - %3d" % rng
          if not label in bpms: bpms[label] = []
          bpms[label].append(s)
          s.folder["bpm"] = label
      if s.info["bpm"] >= 300:
        if "300+" not in bpms: bpms["300+"] = []
        bpms["300+"].append(s)
        s.folder["bpm"] = "300+"

    self._folders = { "mix": mixes, "title": titles, "artist": artists,
                      "bpm": bpms }

  def _create_folder_list(self):
    sort = SORT_NAMES[mainconfig["sortmode"]]
    lst = self._folders[sort].keys()
    lst.sort(lambda x, y: cmp(x.lower(), y.lower()))
    new_songs = [FolderDisplay(folder, sort,
                               len(self._folders[sort][folder])) for
                 folder in lst]
    self._songs = new_songs
    self._list.set_items([s.info["title"] for s in self._songs])
    self._random_songs = self._songs
    
    self._base_text = "Sort by %s" % sort.capitalize()
    
  def _create_song_list(self, folder):
    sort = SORT_NAMES[mainconfig["sortmode"]]
    songlist = self._folders[sort][folder]
    songlist.sort(SORTS[sort])

    self._songs = songlist
    self._list.set_items([s.info["title"] for s in self._songs])
    self._random_songs = [s for s in self._songs if s.info["valid"]]
    self._base_text = folder_name(folder, sort)
