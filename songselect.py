# The song selector; take songs with metadata, output pretty pictures,
# let people select difficulties, and dance.

import os, string, pygame, random, copy
from constants import *

import spritelib, announcer, audio, colors, optionscreen, error, games

# FIXME: this needs to be moved elsewhere if we want theming
ITEM_BG = pygame.image.load(os.path.join(image_path, "ss-item-bg.png"))
FOLDER_BG = pygame.image.load(os.path.join(image_path, "ss-folder-bg.png"))
NO_BANNER = pygame.image.load(os.path.join(image_path, "no-banner.png"))
NO_BANNER.set_colorkey(NO_BANNER.get_at((0, 0)))
BACKGROUND = os.path.join(image_path, "ss-bg.png")
MOVE_SOUND = pygame.mixer.Sound(os.path.join(sound_path, "move.ogg"))
OPEN_SOUND = pygame.mixer.Sound(os.path.join(sound_path, "back.ogg"))

difficulty_colors = { "BEGINNER": colors.color["white"],
                      "LIGHT": colors.color["yellow"],
                      "EASY": colors.color["yellow"],
                      "BASIC": colors.color["orange"],
                      "STANDARD": colors.average(colors.color["red"],
                                                 colors.color["orange"]),
                      "TRICK": colors.color["red"],
                      "MEDIUM": colors.color["red"],
                      "ANOTHER": colors.average(colors.color["yellow"],
                                                colors.color["orange"]),
                      "MANIAC": colors.color["green"],
                      "HARD": colors.color["green"],
                      "HEAVY": colors.darken(colors.color["green"]),
                      "HARDCORE": colors.color["purple"],
                      "SMANIAC": colors.color["purple"],
                      "CHALLENGE": colors.color["purple"]
                     }

ITEM_SIZE = (344, 60)
ITEM_X = [240, 250, 270, 300, 340, 390, 460]
BANNER_CENTER = (133, 45)
BANNER_SIZE = (256, 80)
DIFF_BOX_SIZE = (15, 25)
DIFF_LOCATION = (8, 120)

# FIXME: DSU at some point in the future.
SORTS = {
  "subtitle": (lambda x, y: cmp(str(x.song.info["subtitle"]).lower(),
                                str(y.song.info["subtitle"]).lower())),
  "title": (lambda x, y: (cmp(x.song.info["title"].lower(),
                              y.song.info["title"].lower()) or
                          SORTS["subtitle"](x, y))),
  "artist": (lambda x, y: (cmp(x.song.info["artist"].lower(),
                               y.song.info["artist"].lower()) or
                           SORTS["title"](x, y))),
  "bpm": (lambda x, y: (cmp(x.song.info["bpm"], y.song.info["bpm"]) or
                        SORTS["title"](x, y))),
  "mix": (lambda x, y: (cmp(str(x.song.info["mix"]).lower(),
                            str(y.song.info["mix"]).lower()) or
                        SORTS["title"](x, y)))
  }

SORT_NAMES = ["mix", "title", "artist", "bpm"]

NUM_SORTS = len(SORT_NAMES)
BY_MIX,BY_NAME,BY_GROUP,BY_BPM = range(NUM_SORTS)

# Make a box of a specific color - these are used for difficulty ratings
def make_box(color):
  img = pygame.surface.Surface(DIFF_BOX_SIZE)
  light_color = colors.brighten(color)
  dark_color = colors.darken(color)
  img.fill(color)
  pygame.draw.line(img, light_color, (0,0), (0, DIFF_BOX_SIZE[1] - 1))
  pygame.draw.line(img, light_color, (0,0), (DIFF_BOX_SIZE[0] - 1, 0))
  pygame.draw.line(img, dark_color, (DIFF_BOX_SIZE[0]-1, DIFF_BOX_SIZE[1]-1),
                   (0, DIFF_BOX_SIZE[1] - 1))
  pygame.draw.line(img, dark_color, (DIFF_BOX_SIZE[0]-1, DIFF_BOX_SIZE[1]-1),
                   (DIFF_BOX_SIZE[0] - 1, 0))
  return img

# Wrap a SongItem object in a way that we can render it.
class SongItemDisplay:
  def __init__(self, song):
    self.song = song
    self.banner = None
    self.menuimage = None
    self.isfolder = False
    self.folder = {}

  # Do the actual rendering
  def render(self):
    info = self.song.info

    # Cache it for fast access later
    if self.banner == None:
      if info["banner"]:
        # A postcondition of file parsers is that this is a valid filename
        banner = pygame.image.load(info["banner"]).convert()
        if banner.get_rect().size[0] != banner.get_rect().size[1]:
          self.banner = pygame.transform.scale(banner, BANNER_SIZE)
        else:
          # One of the older banners that we need to rotate
          # Don't scale, because it's hard to calculate and looks bad
          banner.set_colorkey(banner.get_at((0,0)), RLEACCEL)
          self.banner = pygame.transform.rotate(banner, -45)
      else:
        self.banner = NO_BANNER
        self.banner.set_colorkey(self.banner.get_at((0,0)), RLEACCEL)
      self.banner_rect = self.banner.get_rect()
      self.banner_rect.center = BANNER_CENTER
    if self.menuimage == None:
      rcolors = ["green", "orange", "yellow", "red", "purple", "aqua"]
      # Start with a random color, but...
      color = colors.color[rcolors[random.randint(0, len(rcolors) - 1)]]

      if info["mix"]: # ... pick a consistent mix color
        idx = hash(info["mix"].lower()) % len(rcolors)
        color = colors.color[rcolors[idx]]

      color = colors.brighten(color, 145)

      self.menuimage = pygame.surface.Surface(ITEM_SIZE)
      self.menuimage.blit(ITEM_BG, (0,0))
      songtext = FONTS[26].render(info["title"], 1, color)
      self.menuimage.blit(songtext, (10, 5))

      subtext_text = ""
      if info["subtitle"]: subtext_text += info["subtitle"] + " / "
      if info["mix"]: subtext_text += info["mix"] + " / "
      subtext_text  += "bpm: " + str(int(info["bpm"]))

      subtext = FONTS[14].render(subtext_text, 1, color)
      self.menuimage.blit(subtext, (30, 26))
      st = "by " + info["artist"]
      grouptext = FONTS[20].render(st, 1, color)
      self.menuimage.blit(grouptext, (15, 36))

class SongPreview:
  def __init__(self):
    self.playing = False
    self.filename = None
    self.end_time = self.start_time = 0
    if not mainconfig["previewmusic"]:
      audio.load(os.path.join(sound_path, "menu.ogg"))
      audio.play(4, 0.0)

  def preview(self, song):
    if mainconfig["previewmusic"] and not song.isfolder:
      start, length = song.song.info["preview"]
      self.filename = song.song.info["filename"]
      if self.playing: audio.fadeout(500)
      self.playing = False
      self.start_time = pygame.time.get_ticks() + 500
      self.end_time = int(self.start_time + length * 1000)
    elif song.isfolder: audio.fadeout(500)

  def update(self, time):
    if self.filename is None: pass
    elif time < self.start_time: pass
    elif not self.playing:
      try:
        audio.load(self.filename)
        audio.set_volume(0.01)
        audio.play(0, self.start_time)
        self.playing = True
      except: # Filename not found? Song is too short? SMPEG blows?
        audio.stop()
        self.playing = False
    elif time < self.start_time + 1000:
      audio.set_volume((time - self.start_time) / 1000.0)
    elif time > self.end_time - 1000:
      audio.fadeout(1000)
      self.playing = False
      self.filename = None

class FolderDisplay:
  def __init__(self, name, type, numsongs):
    self.name = name
    self.type = type
    self.isfolder = True
    self.banner = None
    self.menuimage = None
    self.numsongs = numsongs

  def find_banner(self):
    for path in (rc_path, pyddr_path):
      filename = os.path.join(path, "banners", self.type, self.name + ".png")
      if os.path.exists(filename):
        banner = pygame.image.load(filename).convert()
        if banner.get_rect().size[0] != banner.get_rect().size[1]:
          self.banner = pygame.transform.scale(banner, BANNER_SIZE)
        else:
          banner.set_colorkey(banner.get_at((0,0)), RLEACCEL)
          self.banner = pygame.transform.rotate(banner, -45)
          self.banner.set_colorkey(self.banner.get_at((0,0)), RLEACCEL)
        break

    else:
      if self.type == "mix":
        for dir in mainconfig["songdir"].split(":"):
          dir = os.path.expanduser(dir)
          filename = os.path.join(dir, self.name, "banner.png")
          if os.path.exists(filename):
            banner = pygame.image.load(filename).convert()
            if banner.get_rect().size[0] != banner.get_rect().size[1]:
              self.banner = pygame.transform.scale(banner, BANNER_SIZE)
            else:
              banner.set_colorkey(banner.get_at((0,0)), RLEACCEL)
              self.banner = pygame.transform.rotate(banner, -45)
              self.banner.set_colorkey(self.banner.get_at((0,0)), RLEACCEL)
            break
        else:
          self.banner = NO_BANNER
          self.banner.set_colorkey(self.banner.get_at((0,0)), RLEACCEL)
      else:
        self.banner = NO_BANNER
        self.banner.set_colorkey(self.banner.get_at((0,0)), RLEACCEL)

  def render(self):
    if self.banner == None:
      self.find_banner()
      self.banner_rect = self.banner.get_rect()
      self.banner_rect.center = BANNER_CENTER
      self.menuimage = pygame.surface.Surface(ITEM_SIZE)
      self.menuimage.blit(FOLDER_BG, [0, 0])
      songtext = FONTS[36].render(self.name, 1, colors.WHITE)
      if songtext.get_size()[0] > ITEM_SIZE[0] - 20:
        songtext = pygame.transform.scale(songtext, [ITEM_SIZE[0] - 20,
                                                     songtext.get_size()[1]])
      self.menuimage.blit(songtext, [10, 5])
      grouptext = FONTS[20].render("%d songs" % self.numsongs, 1, colors.WHITE)
      self.menuimage.blit(grouptext, (15, 32))

class SongSelect:
  # FIXME We need to remove playSequence, by refactoring it elsewhere, too
  def __init__(self, songitems, screen, playSequence, gametype):
    self.songs = [SongItemDisplay(s) for s in songitems
                  if s.difficulty.has_key(gametype)]

    self.all_songs = self.songs

    if len(self.songs) == 0:
      error.ErrorMessage(screen,
                         ["You don't have any songs with steps",
                          "for the game mode (%s) that you" % gametype.lower(),
                          "selected.",
                          " ", "Install more songs, or try a different mode."])
      return

    self.bg = pygame.image.load(BACKGROUND).convert()
    ev = (0, E_PASS)
    self.numsongs = len(self.songs)

    self.gametype = gametype
    self.player_image = [pygame.image.load(os.path.join(image_path,
                                                        "player0.png"))]

    locked = games.GAMES[gametype].locked

    self.diff_list = []
    self.song_list = []
    self.title_list = []
    self.screen = screen
    last_event_was_expose = False # hackery for Focus Follows Mouse

    audio.fadeout(500)

    self.helpfiles = ["menuhelp-" + str(i) + ".png" for i in range(1, 6)]
    self.last_help_update = pygame.time.get_ticks() - 1000000

    pygame.display.update(self.screen.blit(self.bg, (0, 0)))
    
    not_changed_since = pygame.time.get_ticks()
    scroll_wait = pygame.time.get_ticks()

    self.index = 0
    preview = SongPreview()

    self.game_config = copy.copy(game_config)

    self.player_diffs = [0]
    self.player_configs = [copy.copy(player_config)]
    self.player_diff_names = [self.songs[self.index].song.diff_list[self.gametype][self.player_diffs[0]]]

    if self.numsongs > 60 and mainconfig["folders"]:
      self.set_up_folders()
      name = SORT_NAMES[mainconfig["sortmode"]]
      folder = self.folders[name].keys()[0]
      self.set_up_songlist(folder)
    else:
      self.folders = None
      self.songs.sort(SORTS[SORT_NAMES[mainconfig["sortmode"] % NUM_SORTS]])
    self.update_help()
    self.render(True)

    while ev[1] != E_QUIT:
      loop_start_time = pygame.time.get_ticks()

      self.oldindex = self.index
      changed = False
      current_time = pygame.time.get_ticks()

      if last_event_was_expose:
        changed = True

      ev = event.poll()

      if ev[1] != E_PASS:
        last_event_was_expose = False # Workaround for focus-follows-mouse

      # We keep a constant and mod it by the length of the list, so
      # unless up/down is pressed, you will always be the same difficulty
      # on the same song - and between songs that have the same difficulty
      # levels (e.g. the standard 3).

      # Also we store the name of the last manually selected difficulty
      # and go to it if the song has it.

      # Scroll up the menu list
      if ev[1] == E_LEFT:
        self.index = (self.index - 1) % self.numsongs
        scroll_wait = current_time
        MOVE_SOUND.play()

      elif ((event.states[(0, E_LEFT)] or event.states[(1, E_LEFT)]) and
            current_time - scroll_wait > 1000):
        self.index = (self.index - 1) % self.numsongs
        MOVE_SOUND.play()

      elif ev[1] == E_PGUP:
        MOVE_SOUND.play()
        self.scroll_out(self.index)
        self.index = (self.index - 7) % self.numsongs
        scroll_wait = current_time

      elif (event.states[(0, E_PGUP)] and
            current_time - scroll_wait > 1000):
        MOVE_SOUND.play()
        self.scroll_out(self.index)
        self.index = (self.index - 7) % self.numsongs

      # Down the menu list
      elif ev[1] == E_RIGHT:
        self.index = (self.index + 1) % self.numsongs
        scroll_wait = current_time
        MOVE_SOUND.play()
  
      elif ((event.states[(0, E_RIGHT)] or event.states[(1, E_RIGHT)]) and
            current_time - scroll_wait > 1000):
        self.index = (self.index + 1) % self.numsongs
        MOVE_SOUND.play()

      elif ev[1] == E_PGDN:
        MOVE_SOUND.play()
        self.scroll_out(self.index)
        self.index = (self.index + 7) % self.numsongs
        scroll_wait = current_time

      elif (event.states[(0, E_PGDN)] and
            current_time - scroll_wait > 1000):
        MOVE_SOUND.play()
        self.scroll_out(self.index)
        self.index = (self.index + 7) % self.numsongs

      # Easier difficulty
      elif (ev[1] == E_UP and ev[0] < len(self.player_diffs)):
        if not self.songs[self.index].isfolder:
          self.player_diffs[ev[0]] -= 1
          self.player_diffs[ev[0]] %= len(self.current_song.diff_list[gametype])
          self.player_diff_names[ev[0]] = self.current_song.diff_list[gametype][self.player_diffs[ev[0]]]
          changed = True
          MOVE_SOUND.play()

      # Harder difficulty
      elif (ev[1] == E_DOWN and ev[0] < len(self.player_diffs)):
        if not self.songs[self.index].isfolder:
          self.player_diffs[ev[0]] += 1
          self.player_diffs[ev[0]] %= len(self.current_song.diff_list[gametype])
          self.player_diff_names[ev[0]] = self.current_song.diff_list[gametype][self.player_diffs[ev[0]]]
          changed = True
          MOVE_SOUND.play()

      # Player n+1 hit start, so add a new player
      elif ev[1] == E_START and ev[0] == len(self.player_diffs):
        self.player_diffs.append(self.player_diffs[0])
        self.player_diff_names.append(self.player_diff_names[0])

        file = os.path.join(image_path, "player" + str(ev[0]) + ".png")
        self.player_image.append(pygame.image.load(file))
        self.player_configs.append(copy.copy(player_config))
        self.diff_list = []
        self.song_list = []
        self.title_list = []
        changed = True

      # Player n hit start, and was already active. Remove player n and
      # everything after. Questionable UI, but we need a way to turn p2 off.
      elif ev[1] == E_START and ev[0] > 0:
        while len(self.player_diffs) > ev[0]:
          self.player_diffs.pop()
          self.player_diff_names.pop()
          self.player_configs.pop()
        self.diff_list = []
        self.song_list = []
        self.title_list = []
        changed = True

      # Open up a new folder
      elif ev[1] == E_START and ev[0] == 0 and self.songs[self.index].isfolder:
        OPEN_SOUND.play()
        self.scroll_out(self.index)
        self.set_up_songlist(self.songs[self.index].name)
        self.scroll_in(self.index)
        self.oldindex = self.index
        event.empty()
        changed = True

      # Start the dancing!
      elif ev[1] == E_START and ev[0] == 0:
        # If we added the current song with E_MARK earlier, don't readd it
        try: self.title_list[-1].index(self.current_song.info["title"])
        except: self.add_current_song()
        background = spritelib.CloneSprite(pygame.transform.scale(self.screen,
                                                                  (640,480)))
        ann = announcer.Announcer(mainconfig["djtheme"])
        ann.say("menu")
        # Wait for the announcer to finish
        try:
          while ann.chan.get_busy(): pygame.time.wait(1)
        except: pass

        if optionscreen.player_opt_driver(screen, self.player_configs):
          audio.fadeout(500)

          playSequence(zip(self.song_list, self.diff_list),
                       self.player_configs, self.game_config, gametype)

          audio.fadeout(500) # This is the just-played song

          preview = SongPreview()

          while ev[1] != E_PASS: ev = event.poll() # Empty the queue
          self.screen.blit(self.bg, (0, 0))
          pygame.display.flip()

        changed = True

        # Reset the playlist
        self.song_list = []
        self.diff_list = []
        self.title_list = []

      # Add the current song to the playlist
      elif ev[1] == E_MARK:
        MOVE_SOUND.play()
        self.add_current_song()
        changed = True

      # Remove the most recently added song
      elif ev[1] == E_UNMARK:
	if self.title_list != []:
          self.title_list.pop()
          self.diff_list.pop()
          self.song_list.pop()
          changed = True

      # Remove all songs on the playlist
      elif ev[1] == E_CLEAR:
        self.title_list = []
        self.diff_list = []
        self.song_list = []
        changed = True

      elif ev[1] == E_SELECT:
        if optionscreen.game_opt_driver(screen, self.game_config):
          self.scroll_out(self.index)
          OPEN_SOUND.play()
          self.index = random.randint(0, len(self.all_songs) - 1)
          s = self.all_songs[self.index]
          if self.folders:
            self.set_up_songlist(s.folder[SORT_NAMES[mainconfig["sortmode"]]])
          self.index = self.songs.index(s)
	changed = True

      # Change sort modes - FIXME: terrible event name
      elif ev[1] == E_SCREENSHOT:
        s = self.songs[self.index]
        self.scroll_out(self.index)
        mainconfig["sortmode"] = (mainconfig["sortmode"] + 1) % NUM_SORTS
        if self.folders:
          if not s.isfolder:
            self.set_up_songlist(s.folder[SORT_NAMES[mainconfig["sortmode"]]])
            self.index = self.songs.index(s)
          else:
            keys = self.folders[SORT_NAMES[mainconfig["sortmode"]]].keys()
            keys.sort()
            self.set_up_songlist(keys[0])
            self.index = 0
        else:
          self.songs.sort(SORTS[SORT_NAMES[mainconfig["sortmode"]]])
          self.index = self.songs.index(s)
          self.oldindex = self.index # We're cheating!
        changed = True

      elif ev[1] == E_FULLSCREEN:
        pygame.display.toggle_fullscreen()
        mainconfig["fullscreen"] ^= 1
        changed = True

      elif ev[1] == E_EXPOSE:
        last_event_was_expose = True

      # This has to be after events, otherwise we do stuff to the
      # wrong song.
      if not self.songs[self.index].isfolder:
        self.current_song = self.songs[self.index].song

      if locked and ev[1] in [E_UP, E_DOWN] and ev[0] < len(self.player_diffs):
        for i in range(len(self.player_diffs)):
          self.player_diffs[i] = self.player_diffs[ev[0]]
          self.player_diff_names[i] = self.player_diff_names[ev[0]]

      if self.index != self.oldindex and not self.songs[self.index].isfolder:
        for i in range(len(self.player_diff_names)):
          name = self.player_diff_names[i]
          if name in self.current_song.diff_list[self.gametype]:
            self.player_diffs[i] = self.current_song.diff_list[self.gametype].index(name)
        not_changed_since = current_time

      preview.update(current_time)

      if self.index != self.oldindex:
        not_changed_since = current_time
        preview.preview(self.songs[self.index])
        changed = True
        if self.index == (self.oldindex + 1) % self.numsongs:
          self.scroll_down()
        elif self.index == (self.oldindex - 1) % self.numsongs:
          self.scroll_up()
        else:
          changed = True
          self.scroll_in(self.index)

      self.render(changed)

      pygame.time.wait(50 - (pygame.time.get_ticks() - loop_start_time))

    audio.fadeout(500)
    pygame.time.wait(500)
    # FIXME Does this belong in the menu code? Probably.
    audio.load(os.path.join(sound_path, "menu.ogg"))
    audio.set_volume(1.0)
    audio.play(4, 0.0)

  def render(self, changed):
    r = []
    
    bg_r = self.screen.blit(self.bg, (0,0))
    if changed: r.append(bg_r)

    # Difficulty list rendering
    if not self.songs[self.index].isfolder:
      difficulty = self.songs[self.index].song.difficulty[self.gametype]
      diff_list = self.songs[self.index].song.diff_list[self.gametype]
    else:
      diff_list = []

    if changed: # We need to rerender everything
      # The song list
      for i in range(-4, 5):
        idx = (self.index + i) % self.numsongs
        self.songs[idx].render()
        x = ITEM_X[abs(i)]
        y = 210 + i * 60
        img = self.songs[idx].menuimage
        img.set_alpha(226 - (40 * abs(i)))
        self.screen.blit(self.songs[idx].menuimage, (x,y))
        
      # The banner
      self.screen.blit(self.songs[self.index].banner,
                       self.songs[self.index].banner_rect)

      # Render this in "reverse" order, from bottom to top
      temp_list = copy.copy(self.title_list)
      temp_list.reverse()

      for i in range(len(temp_list)):
        txt = FONTS[14].render(temp_list[i], 1, colors.WHITE)
        self.screen.blit(txt, (10, 480 - (FONTS[14].size("I")[1] - 2) *
                               (i + 2)))

      # Sort mode
      stxt = FONTS[20].render("sort by " + SORT_NAMES[mainconfig["sortmode"]],
                              1, colors.WHITE)
      rec = stxt.get_rect()
      rec.center = (DIFF_LOCATION[0] + 90, DIFF_LOCATION[1] - 10)
      self.screen.blit(stxt, rec)
  
      i = 0
      for d in diff_list:
        # Difficulty name
        text = d.lower()

        color = colors.color["gray"]
        if difficulty_colors.has_key(d):  color = difficulty_colors[d]

        if difficulty[d] >= 10: text += " - x" + str(difficulty[d])

        text = FONTS[26].render(text.lower(), 1, colors.brighten(color, 64))
        rec = text.get_rect()
        rec.center = (DIFF_LOCATION[0] + 92, DIFF_LOCATION[1] + 25 * i + 12)
        self.screen.blit(text, rec)

        # Difficulty boxes
        if difficulty[d] < 10:
          box = make_box(colors.brighten(color, 32))
          box.set_alpha(140)

          # Active boxes
          for j in range(int(difficulty[d])):
            self.screen.blit(box, (DIFF_LOCATION[0] + 25 + 15 * j,
                                   DIFF_LOCATION[1] + 25 * i))
          # Inactive boxes
          box.set_alpha(64)
          for j in range(int(difficulty[d]), 9):
            self.screen.blit(box, (DIFF_LOCATION[0] + 25 + 15 * j,
                                   DIFF_LOCATION[1] + 25 * i))
            
        # Player selection icons
        for j in range(len(self.player_diffs)):
          if diff_list.index(d) == (self.player_diffs[j] % len(diff_list)):
            self.screen.blit(self.player_image[j],
                             (DIFF_LOCATION[0] + 10 + 140 * j,
                              DIFF_LOCATION[1] + 25 * i))
        i += 1

    # Key help display
    if mainconfig["ingamehelp"]:
      self.update_help()
      r.append(self.screen.blit(self.helpimage,
                                (5, DIFF_LOCATION[1] + len(diff_list) * 26)))

    pygame.display.update(r)

  def scroll_up(self):
    if not mainconfig["gratuitous"]: return
    r = [Rect((5, 5), (256, 80)), Rect((240, 0), (400, 480))]
    end_time = pygame.time.get_ticks() + 75
    cur_time = pygame.time.get_ticks()
    while cur_time < end_time:
      cur_time = pygame.time.get_ticks()
      q = min(1, max(0, (end_time - cur_time) / 75.0))
      p = 1 - q
      self.screen.blit(self.bg, (0,0))
      for k in range(-5, 5):
        idx = (self.oldindex + k) % self.numsongs
        self.songs[idx].render()
        x = ITEM_X[abs(k)] * q + ITEM_X[abs(k + 1)] * p
        y = 210 + int(60 * (k * q + (k + 1) * p))
        img = self.songs[idx].menuimage
        img.set_alpha(226 - int(40 * (abs(k) * q + abs(k + 1) * p)))
        self.screen.blit(self.songs[idx].menuimage, (x,y))
      self.songs[self.oldindex].banner.set_alpha(256 * q)
      self.screen.blit(self.songs[self.oldindex].banner,
                       self.songs[self.oldindex].banner_rect)
      self.songs[self.index].banner.set_alpha(256 * p)
      self.screen.blit(self.songs[self.index].banner,
                       self.songs[self.index].banner_rect)
      pygame.display.update(r)
    self.songs[self.oldindex].banner.set_alpha(256)
    self.songs[self.index].banner.set_alpha(256)

  def scroll_down(self):
    if not mainconfig["gratuitous"]: return
    r = [Rect((5, 5), (256, 80)), Rect((240, 0), (400, 480))]
    end_time = pygame.time.get_ticks() + 75
    cur_time = pygame.time.get_ticks()
    while cur_time < end_time:
      cur_time = pygame.time.get_ticks()
      q = min(1, max(0, (end_time - cur_time) / 75.0))
      p = 1 - q
      self.screen.blit(self.bg, (0,0))
      for k in range(-4, 6):
        idx = (self.oldindex + k) % self.numsongs
        self.songs[idx].render()
        x = ITEM_X[abs(k)] * q + ITEM_X[abs(k - 1)] * p
        y = 210 + int(60 * (k * q + (k - 1) * p))
        img = self.songs[idx].menuimage
        img.set_alpha(226 - int(40 * (abs(k) * q + abs(k - 1) * p)))
        self.screen.blit(self.songs[idx].menuimage, (x,y))
      self.songs[self.oldindex].banner.set_alpha(255 * q)
      self.screen.blit(self.songs[self.oldindex].banner,
                       self.songs[self.oldindex].banner_rect)
      self.songs[self.index].banner.set_alpha(255 * p)
      self.screen.blit(self.songs[self.index].banner,
                       self.songs[self.index].banner_rect)
      pygame.display.update(r)
    self.songs[self.oldindex].banner.set_alpha(255)
    self.songs[self.index].banner.set_alpha(255)

  def scroll_out(self, index):
    if not mainconfig["gratuitous"]: return
    r = [Rect((5, 5), (256, 80)), Rect((240, 0), (400, 480))]
    end_time = pygame.time.get_ticks() + 200
    cur_time = pygame.time.get_ticks()
    while cur_time < end_time:
      cur_time = pygame.time.get_ticks()
      q = min(1, max(0, (end_time - cur_time) / 200.0))
      p = 1 - q
      self.screen.blit(self.bg, (0,0))
      for k in range(-4, 5): # Redraw screen
        idx = (index + k) % self.numsongs
        self.songs[idx].render()
        x = max(240 + int((866 - 240) * p) - 50 * k, ITEM_X[abs(k)])
        y = 210 + k * 60
        self.screen.blit(self.songs[idx].menuimage, (x,y))
      pygame.display.update(r)

  def scroll_in(self, index):
    if not mainconfig["gratuitous"]: return
    r = [Rect((5, 5), (256, 80)), Rect((240, 0), (400, 480))]
    end_time = pygame.time.get_ticks() + 150
    cur_time = pygame.time.get_ticks()
    while cur_time < end_time:
      cur_time = pygame.time.get_ticks()
      q = min(1, max(0, (end_time - cur_time) / 150.0))
      p = 1 - q
#    for j in range(840, 214, -25): # position to move to
      self.screen.blit(self.bg, (0,0))
      for k in range(-4, 5): # Redraw screen
        idx = (index + k) % self.numsongs
        self.songs[idx].render()
        x = max(214 + int((840 - 214) * q) - 50 * k, ITEM_X[abs(k)])
        y = 210 + k * 60
        self.songs[idx].menuimage.set_alpha(226 - (40 * abs(k)))
        self.screen.blit(self.songs[idx].menuimage, (x,y))
      pygame.display.update(r)

  def add_current_song(self):
    self.song_list.append(self.current_song.filename)
    l = len(self.current_song.diff_list[self.gametype])
    new_diff = map((lambda i: self.current_song.diff_list[self.gametype][i%l]),
                   self.player_diffs)
    self.diff_list.append(new_diff)
    # Pseudo-pretty difficulty tags
    text = self.current_song.info["title"] + " "
    for d in self.diff_list[-1]: text += "/" + d[0]
    self.title_list.append(text)

  def update_help(self):
    delta = pygame.time.get_ticks() - self.last_help_update
    if delta < 1000:
      self.helpimage.set_alpha(int(256.0 * (delta / 1000.0)))
    elif delta < 5000:
      pass
    elif delta < 6000:
      self.helpimage.set_alpha(int(256.0 - (256.0 * (delta - 5000)/1000.0)))
    elif delta > 6000:
      fn = self.helpfiles.pop(0)
      self.helpfiles.append(fn)
      fn = os.path.join(image_path, fn)
      self.helpimage = pygame.image.load(fn).convert()
      self.helpimage.set_colorkey(self.helpimage.get_at((0,0)), RLEACCEL)
      self.helpimage.set_alpha(0)
      self.last_help_update = pygame.time.get_ticks()

  def set_up_folders(self):
    mixnames = {}
    artists = {}
    titles = {}
    bpms = {}

    for si in self.all_songs:
      if not mixnames.has_key(si.song.info["mix"]):
        mixnames[si.song.info["mix"]] = []
      mixnames[si.song.info["mix"]].append(si)
      si.folder["mix"] = si.song.info["mix"]

      label = si.song.info["title"][0].capitalize()
      if not titles.has_key(label): titles[label] = []
      titles[label].append(si)
      si.folder["title"] = label

      label = si.song.info["artist"][0].capitalize()
      if not artists.has_key(label): artists[label] = []
      artists[label].append(si)
      si.folder["artist"] = label

      for rng in ((0, 50), (50, 100), (100, 121), (110, 120),
                  (120, 130), (130, 140), (140, 150), (150, 160), (160, 170),
                  (170, 180), (180, 190), (190, 200), (200, 225), (225, 250),
                  (250, 275), (275, 300)):
        label = "%d-%d" % rng
        if rng[0] < si.song.info["bpm"] <= rng[1]:
          if not bpms.has_key(label): bpms[label] = []
          bpms[label].append(si)
          si.folder["bpm"] = label
      if si.song.info["bpm"] >= 300:
        if not bpms.has_key("300+"): bpms["300+"] = []
        bpms["300+"].append(si)
        si.folder["bpm"] = "300+"

    self.folders = { "mix": mixnames, "title": titles,
                     "artist": artists, "bpm": bpms }

  def set_up_songlist(self, selected_folder):
    sort = SORT_NAMES[mainconfig["sortmode"]]

    songlist = self.folders[sort][selected_folder]
    folderlist = self.folders[sort].keys()

    folderlist.sort(lambda x, y: cmp(x.lower(), y.lower()))
    songlist.sort(SORTS[sort])

    new_songs = []
    for folder in folderlist:
      new_songs.append(FolderDisplay(folder, sort,
                                     len(self.folders[sort][folder])))
      if folder == selected_folder: new_songs.extend(songlist)

    self.songs = new_songs
    self.numsongs = len(self.songs)
    self.index = folderlist.index(selected_folder)
    self.oldindex = -2
