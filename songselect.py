# The song selector; take songs with metadata, output pretty pictures,
# let people select difficulties, and dance.

import os, string, pygame, random, copy, colors
from constants import *

import spritelib, announcer

# FIXME: this needs to be moved elsewhere if we want theming
ITEM_BG = pygame.image.load(os.path.join(image_path, "ss-item-bg.png"))
NO_BANNER = pygame.image.load(os.path.join(image_path, "no-banner.png"))
BACKGROUND = os.path.join(image_path, "ss-bg.png")
MOVE_SOUND = pygame.mixer.Sound(os.path.join(sound_path, "move.ogg"))

# FIXME: We need more difficulties here
difficulty_colors = { "BEGINNER": colors.color["white"],
                      "LIGHT": colors.color["yellow"],
                      "BASIC": colors.color["orange"],
                      "STANDARD": colors.average(colors.color["red"],
                                                 colors.color["orange"]),
                      "TRICK": colors.color["red"],
                      "ANOTHER": colors.average(colors.color["yellow"],
                                                colors.color["orange"]),
                      "MANIAC": colors.color["green"],
                      "HEAVY": colors.darken(colors.color["green"]),
                      "HARDCORE": colors.color["purple"]
                     }

ITEM_SIZE = (344, 60)
ITEM_X = [240, 250, 270, 300, 340, 390, 460]
BANNER_CENTER = (133, 45)
BANNER_SIZE = (256, 80)
DIFF_BOX_SIZE = (15, 25)
DIFF_LOCATION = (8, 120)

# FIXME: DSU at some point in the future.
SORTS = {
  "filename": (lambda x, y: cmp(x.song.filename, y.song.filename)),
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

SORT_NAMES = ("filename", "title", "artist", "bpm", "mix")

NUM_SORTS = len(SORT_NAMES)
BY_FILENAME,BY_NAME,BY_GROUP,BY_BPM,BY_MIX = range(NUM_SORTS)

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

  # Do the actual rendering
  def render(self):
    info = self.song.info

    # Cache it for fast access later
    if self.banner == None:
      if info["banner"]:
        # A postcondition of file parsers is that this is a valid filename
        banner = pygame.image.load(info["banner"]).convert()
        if banner.get_rect().size[0] > banner.get_rect().size[1] * 2:
          self.banner = pygame.transform.scale(banner, BANNER_SIZE)
        else:
          # One of the older banners that we need to rotate
          # Don't scale, because it's hard to calculate and looks bad
          self.banner = pygame.transform.rotate(banner,-45)
          self.banner.set_colorkey(self.banner.get_at((0,0)), RLEACCEL)
      else:
        self.banner = NO_BANNER
        self.banner.set_colorkey(self.banner.get_at((0,0)), RLEACCEL)
      self.banner_rect = self.banner.get_rect()
      self.banner_rect.center = BANNER_CENTER
    if self.menuimage == None:
      rcolors = ["green", "orange", "yellow", "red", "white",
                 "purple", "aqua"]
      # Start with a random color, but...
      color = colors.color[rcolors[random.randint(0, len(rcolors) - 1)]]

      if info["mix"]: # ... pick a consistent mix color
        idx = hash(info["mix"]) % len(rcolors)
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

class SongSelect:
  # FIXME We need to remove playSequence, by refactoring
  # it elsewhere, too
  def __init__(self, songitems, screen, playSequence,
               players = 1, gametype = "SINGLE"):
    self.songs = [SongItemDisplay(s) for s in songitems
                  if s.difficulty.has_key(gametype)]
    self.bg = pygame.image.load(BACKGROUND).convert()
    ev = (0, E_PASS)
    self.numsongs = len(self.songs)
    self.gametype = gametype
    self.player_diffs = [0]
    self.player_image = [pygame.image.load(os.path.join(image_path,
                                                        "player0.png"))]

    # FIXME This is stupid fucking crap we need to get rid of...
    # Who's in charge of those new parsers? oh right, me.
    self.diff_list = []
    self.song_list = []
    self.title_list = []
    self.screen = screen
    last_event_was_expose = False # hackery for Focus Follows Mouse

    pygame.mixer.music.fadeout(500)

    self.helpfiles = ["menuhelp-" + str(i) + ".png" for i in range(1, 6)]
    self.last_help_update = pygame.time.get_ticks() - 1000000

    pygame.display.update(self.screen.blit(self.bg, (0, 0)))
    
    not_changed_since = pygame.time.get_ticks()
    is_playing = False
    new_preview = True
    scroll_wait = pygame.time.get_ticks()

    self.index = 0
    previews = mainconfig["previewmusic"]
    preview_start = timesince = 0

    if not previews:
      pygame.mixer.music.load(os.path.join(sound_path, "menu.ogg"))
      pygame.mixer.music.play(4, 0.0)

    self.songs.sort(SORTS[SORT_NAMES[mainconfig["sortmode"] % NUM_SORTS]])
    self.update_help()
    self.render(True, True)

    while ev[1] != E_QUIT:
      self.oldindex = self.index
      changed = False
      all_changed = False
      current_time = pygame.time.get_ticks()

      if last_event_was_expose:
        changed = True
        all_changed = True

      ev = event.poll()

      if ev[1] != E_PASS:
        last_event_was_expose = False # Workaround for focus-follows-mouse

      # We keep a constant and mod it by the length of the list, so
      # unless up/down is pressed, you will always be the same difficulty
      # on the same song - and between songs that have the same difficulty
      # levels (e.g. the standard 3).

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
        self.index = (self.index - 7) % self.numsongs
        scroll_wait = current_time
        MOVE_SOUND.play()

      elif (event.states[(0, E_PGUP)] and
            current_time - scroll_wait > 1000):
        self.index = (self.index - 7) % self.numsongs
        MOVE_SOUND.play()

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
        self.index = (self.index + 7) % self.numsongs
        scroll_wait = current_time
        MOVE_SOUND.play()

      elif (event.states[(0, E_PGDN)] and
            current_time - scroll_wait > 1000):
        self.index = (self.index + 7) % self.numsongs
        MOVE_SOUND.play()

      # Easier difficulty
      elif (ev[1] == E_UP and ev[0] < len(self.player_diffs)):
        self.player_diffs[ev[0]] -= 1
        self.player_diffs[ev[0]] %= len(self.current_song.diff_list[gametype])
        changed = True
        MOVE_SOUND.play()

      # Harder difficulty
      elif (ev[1] == E_DOWN and ev[0] < len(self.player_diffs)):
        self.player_diffs[ev[0]] += 1
        self.player_diffs[ev[0]] %= len(self.current_song.diff_list[gametype])
        changed = True
        MOVE_SOUND.play()

      # Player n+1 hit start, so add a new player
      elif ev[1] == E_START and ev[0] == len(self.player_diffs):
        self.player_diffs.append(0)
        file = os.path.join(image_path, "player" + str(ev[0]) + ".png")
        self.player_image.append(pygame.image.load(file))
        self.diff_list = []
        self.song_list = []
        self.title_list = []
        changed = True

      # Player n hit start, and was already active. Remove player n and
      # everything after. Questionable UI, but we need a way to turn p2 off.
      elif ev[1] == E_START and ev[0] > 0:
        while len(self.player_diffs) > ev[0]:
          self.player_diffs.pop()
        self.diff_list = []
        self.song_list = []
        self.title_list = []
        changed = True

      # Start the dancing!
      elif ev[1] == E_START and ev[0] == 0:
        # If we added the current song with E_MARK earlier, don't readd it
        try: self.title_list[-1].index(self.current_song.info["title"])
        except: self.add_current_song()
        background = spritelib.CloneSprite(pygame.transform.scale(self.screen,
                                                                  (640,480)))
        pygame.mixer.music.fadeout(1000)
        ann = announcer.Announcer(mainconfig["djtheme"])
        ann.say("menu")

        # Wait for the announcer to finish
        try:
          while ann.chan.get_busy(): pygame.time.wait(1)
        except: pass

        # playSequence can probably derive the number of players from
        # the length of the other lists
        playSequence(len(self.player_diffs), zip(self.song_list,
                                                 self.diff_list))
        # Reset the playlist
        self.song_list = []
        self.diff_list = []
        self.title_list = []

        pygame.mixer.music.fadeout(500) # This is the just-played song

        if not previews:
          pygame.mixer.music.load(os.path.join(sound_path, "menu.ogg"))
          pygame.mixer.music.play(4, 0.0)

        while ev[1] != E_PASS: ev = event.poll() # Empty the queue
        self.screen.blit(self.bg, (0, 0))
        pygame.display.flip()
        changed = True

      # Add the current song to the playlist
      elif ev[1] == E_MARK:
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
        self.index = random.randint(0, self.numsongs - 1)

      # Change sort modes - FIXME: terrible event name
      elif ev[1] == E_SCREENSHOT:
        s = self.songs[self.index]
        self.scroll_out(self.index)
        mainconfig["sortmode"] = (mainconfig["sortmode"] + 1) % NUM_SORTS
        self.songs.sort(SORTS[SORT_NAMES[mainconfig["sortmode"]]])
        self.index = self.songs.index(s)
        self.oldindex = self.index # We're cheating!
        self.scroll_in(self.index)
        changed = True

      elif ev[1] == E_FULLSCREEN:
        pygame.display.toggle_fullscreen()
        mainconfig["fullscreen"] ^= 1
        changed = True
        all_changed = True

      elif ev[1] == E_EXPOSE:
        last_event_was_expose = True

      # This has to be after events, otherwise we do stuff to the
      # wrong song.
      self.current_song = self.songs[self.index].song

      if self.index != self.oldindex:
        new_preview = True
        not_changed_since = current_time
        pygame.mixer.music.fadeout(500)

      # Song preview support
      if previews:
        # Don't open the mixer until we "stop" (wait ~ 0.1-0.2 s) on an item.
        if (new_preview == True and
           current_time - not_changed_since > 500):
          new_preview = False
          is_playing = True
          try:
            start_time = self.songs[self.index].song.info["preview"][0]
            pygame.mixer.music.stop()
            preview_start = current_time
            pygame.mixer.music.load(self.songs[self.index].song.info["filename"])
            pygame.mixer.music.set_volume(0.01)
            pygame.mixer.music.play(0, start_time)
          except pygame.error: # The song was probably too short
            is_playing = False
            preview_start = 0

        # Fade in, then fade out
        if is_playing:
          length = self.songs[self.index].song.info["preview"][1]
          timesince = (current_time - preview_start)/2000.0
          if timesince <= 1.0:
            pygame.mixer.music.set_volume(timesince)
          elif length - 1 <= timesince <= length:
            pygame.mixer.music.set_volume(length - timesince)
          elif timesince > length:
            pygame.mixer.music.set_volume(0)
            pygame.mixer.music.stop()
            is_playing = False

      if self.index != self.oldindex:
        not_changed_since = current_time
        changed = True
        if self.index == (self.oldindex + 1) % self.numsongs:
          self.scroll_down()
        elif self.index == (self.oldindex - 1) % self.numsongs:
          self.scroll_up()
        else:
          all_changed = True
          self.scroll_out(self.oldindex)
          self.scroll_in(self.index)

      self.render(changed, all_changed)

      pygame.time.wait(30)

    pygame.mixer.music.fadeout(500)
    pygame.time.wait(500)
    # FIXME Does this belong in the menu code? Probably.
    pygame.mixer.music.load(os.path.join(sound_path, "menu.ogg"))
    pygame.mixer.music.set_volume(1.0)
    pygame.mixer.music.play(4, 0.0)

  def render(self, changed, all_changed):
    r = []
    
    bg_r = self.screen.blit(self.bg, (0,0))
    if all_changed: r.append(bg_r)

    # Difficulty list rendering
    difficulty = self.songs[self.index].song.difficulty[self.gametype]
    diff_list = self.songs[self.index].song.diff_list[self.gametype]

    if changed: # We need to rerender everything
      r += [Rect((5, 5), (256, 80)), # banner area
            Rect((5, 15), (190, 460))] # Sidebar
      # The song area is always full, so we don't need to update it

      # The song list
      for i in range(-4, 5):
        idx = (self.index + i) % self.numsongs
        self.songs[idx].render()
        x = ITEM_X[abs(i)]
        y = 210 + i * 60
        img = self.songs[idx].menuimage
        img.set_alpha(226 - (40 * abs(i)))
        r.append(self.screen.blit(self.songs[idx].menuimage, (x,y)))
        
      # The banner
      self.screen.blit(self.songs[self.index].banner,
                       self.songs[self.index].banner_rect)

      # Render this in "reverse" order, from bottom to top
      temp_list = copy.copy(self.title_list)
      temp_list.reverse()

      for i in range(len(temp_list)):
        txt = FONTS[14].render(temp_list[i], 1, colors.WHITE)
        self.screen.blit(txt,
                         (10, 480 - (FONTS[14].size("I")[1] - 2) *
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
    for i in range(1, 7):
      p = i/6.0
      q = 1 - p
      self.screen.blit(self.bg, (0,0))
      for k in range(-5, 5):
        idx = (self.oldindex + k) % self.numsongs
        self.songs[idx].render()
        x = ITEM_X[abs(k)] * q + ITEM_X[abs(k + 1)] * p
        y = 210 + int(60 * (k * q + (k + 1) * p))
        img = self.songs[idx].menuimage
        img.set_alpha(226 - int(40 * (abs(k) * q + abs(k + 1) * p)))
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

  def scroll_down(self):
    if not mainconfig["gratuitous"]: return
    r = [Rect((5, 5), (256, 80)), Rect((240, 0), (400, 480))]
    for i in range(1, 7):
      p = i/6.0
      q = 1 - p
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
    for j in range(240, 866, 25): # position to move to
      self.screen.blit(self.bg, (0,0))
      for k in range(-4, 5): # Redraw screen
        idx = (index + k) % self.numsongs
        self.songs[idx].render()
        x = max(j - 50 * k, ITEM_X[abs(k)])
        y = 210 + k * 60
        self.screen.blit(self.songs[idx].menuimage, (x,y))
      pygame.display.update(r)

  def scroll_in(self, index):
    if not mainconfig["gratuitous"]: return
    r = [Rect((5, 5), (256, 80)), Rect((240, 0), (400, 480))]
    for j in range(840, 214, -25): # position to move to
      self.screen.blit(self.bg, (0,0))
      for k in range(-4, 5): # Redraw screen
        idx = (index + k) % self.numsongs
        self.songs[idx].render()
        x = max(j - 50 * k, ITEM_X[abs(k)])
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
