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
            [255, 252, 255, 170], [88, 104, 255, 170]]:
    pygame.draw.rect(s, c, r, 1)
    r.width -= 2
    r.height -= 2
    r.top += 1
    r.left += 1
  return s

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
    self.menuimage = None
    self.isfolder = False
    self.folder = {}
    self.banner = None
    self.clip = None

  def render(self):
    if self.banner: return
    
    if self._song.info["banner"]:
      banner = pygame.image.load(self._song.info["banner"])
      size = banner.get_rect().size
      if size <= (100, 100): # Parapara-style
        self.banner = banner
      elif size == (177, 135): # KSF-style 1
        self.banner = banner
      elif size == (300, 200): # KSF-style 2
        banner = banner.convert()
        banner.set_colorkey(banner.get_at([0, 0]))
        self.banner = banner
      elif abs(size[0] - size[1]) < 3: # "Square", need to rotate.
        banner = banner.convert()
        banner.set_colorkey(banner.get_at([0, 0]), RLEACCEL)
        self.banner = pygame.transform.rotozoom(banner, -45, 1.0)
        self.clip = [51, 50, 256, 80]
      else: # 256x80, standard banner, I hope.
        banner = pygame.transform.scale(banner, [256, 80])
        self.banner = make_box([0, 0, 0], banner.get_size())
        self.banner.blit(banner, [4, 4])
    else: self.banner = SongItemDisplay.no_banner

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
  def __init__(self, items, font, color, spacing, count, width, topleft):
    pygame.sprite.Sprite.__init__(self)
    self._items = items
    self._idx = self._oldidx = 0
    self._font = font
    self._h = spacing
    self._count = count
    self._w = width
    self._color = color
    self._topleft = topleft
    self._render()

  def set_index(self, idx):
    self._oldidx = self._idx
    self._idx = idx

  def update(self, time):
    if self._idx != self._oldidx:
      self._oldidx = self._idx
      self._render()

  def _render(self):
    self.image = pygame.Surface([self._w, self._h * self._count],
                                SRCALPHA, 32)
    self.image.fill([0, 0, 0, 0])
    for i, y in zip(range(self._count),
                    range(self._h / 2, self._h * self._count, self._h)):
      idx = (self._idx + i) % len(self._items)
      t = fontfx.shadow(self._items[idx], self._font, 1, self._color,
                        [c / 8 for c in self._color])
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
    song.render()
    self._title = song.info["title"]
    self._subtitle = song.info["subtitle"]
    self._artist = song.info["artist"]
    self._clip = song.clip
    self._banner = song.banner

  def _render(self):
    self._box = make_box(self._color, [350, 350])
    self.image = pygame.Surface(self._box.get_size(), SRCALPHA, 32)
    self.image.blit(self._box, [0, 0])
    self.image.set_clip(self._clip)
    r_b = self._banner.get_rect()
    r_b.center = (self.image.get_rect().size[0] / 2, 100)
    self.image.blit(self._banner, r_b)
    self.image.set_clip(None)
    
    c1, c2 = [255, 255, 255], [30, 30, 30]

    title = fontfx.shadow(self._title, pygame.font.Font(None, 32), 2, c1, c2)
    r_t = title.get_rect()
    r_t.center = [179, 240]
    self.image.blit(title, r_t)

    artist = fontfx.shadow(self._artist, pygame.font.Font(None, 26), 2, c1, c2)
    r_a = artist.get_rect()
    r_a.center = [179, 320]
    self.image.blit(artist, r_a)

    if self._subtitle:
      subtitle = fontfx.shadow(self._subtitle, pygame.font.Font(None, 20),
                               1, c1, c2)
      r_s = subtitle.get_rect()
      r_s.center = [179, 270]
      self.image.blit(subtitle, r_s)

    self.rect = self.image.get_rect()
    self.rect.center = self._center

  def update(self, time):
    if time > self._next_update:
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
    self._preview = SongPreview()
    self._preview.preview(self._songs[self._index])
    self._clock = pygame.time.Clock()
    self._song = self._songs[self._index]
    self._game = game
    self._config = dict(game_config)

    titles = [s.info["title"] for s in songs]

    players = games.GAMES[game].players
    self._diffs = [] # Current difficulty setting
    self._diff_widgets = [] # Difficulty widgets
    self._configs = []
    self._diff_names = [] # Last manually selected difficulty name

    diff_name = self._song.diff_list[game][0]
    for i in range(players):
      self._diffs.append(0)
      self._configs.append(dict(player_config))
      self._diff_names.append(diff_name)
      d = DifficultyBox(i, 2)
      rank = records.get(self._song.filename, diff_name, game)[0]
      grade = grades.grades[self._config["grade"]].grade_by_rank(rank)
      d.set(diff_name, DIFF_COLORS.get(diff_name, [127, 127, 127]),
            self._song.difficulty[game][diff_name],
            grade)
      self._diff_widgets.append(d)
    
    self._list = ListBox(titles, pygame.font.Font(None, 28),
                         [255, 255, 255], 26, 16, 220, [410, 56])
    self._sprites.add(self._diff_widgets)
    self._sprites.add(self._list)
    ActiveIndicator([405, 233]).add(self._sprites)
    self._banner = BannerDisplay([350, 300], [210, 230])
    self._banner.set_song(self._song)
    self._banner.add(self._sprites)
    self._sprites.add(HelpText(SS_HELP, [255, 255, 255], [0, 0, 0],
                               pygame.font.Font(None, 22), [206, 20]))
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
    while ev != ui.QUIT:
      if pid >= len(self._diffs): pass # Inactive player
      
      elif ev == ui.UP:
        self._index = (self._index - 1) % len(self._songs)
        self._list.set_index(self._index - 7)
      elif ev == ui.DOWN:
        self._index = (self._index + 1) % len(self._songs)
        self._list.set_index(self._index - 7 )

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

      elif ev == ui.CONFIRM:
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

      elif ev == ui.FULLSCREEN:
        pygame.display.toggle_fullscreen()
        mainconfig["fullscreen"] ^= 1

      self._song = self._songs[self._index]

      if ev in [ui.QUIT, ui.UP, ui.DOWN, ui.SELECT]:
        self._preview.preview(self._song)
        self._banner.set_song(self._song)

      if ev in [ui.UP, ui.DOWN, ui.SELECT]:
        for i in range(len(self._diffs)):
          name = self._diff_names[i]
          if name in self._song.diff_list[self._game]:
            self._diffs[i] = self._song.diff_list[self._game].index(name)
          else: self._diffs[i] %= len(self._song.diff_list[self._game])

      if ev in [ui.UP, ui.DOWN, ui.LEFT, ui.RIGHT, ui.SELECT]:
        for i in range(len(self._diffs)):
          name = self._song.diff_list[self._game][self._diffs[i]]
          rank = records.get(self._song.filename, name, game)[0]
          grade = grades.grades[self._config["grade"]].grade_by_rank(rank)
          self._diff_widgets[i].set(name, DIFF_COLORS.get(name, [127,127,127]),
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
