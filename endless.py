# Support for endless song playing!

import random, copy, colors, audio, error, optionscreen
from constants import *

RESOLUTION = (640, 480)
BACKGROUND = os.path.join(image_path, "endless-bg.png")

DIFFICULTIES = ["BEGINNER", "LIGHT", "BASIC", "ANOTHER", "STANDARD", "TRICK",
                "MANIAC", "HEAVY", "HARDCORE", "CHALLENGE", "ONI"]

def python_sucks_sort(a, b):
  if a in DIFFICULTIES and b in DIFFICULTIES:
    return cmp(DIFFICULTIES.index(a), DIFFICULTIES.index(b))
  elif a in DIFFICULTIES: return -1
  elif b in DIFFICULTIES: return 1
  else: return cmp(a, b)

def check_constraints(constraints, diff):
  for c in constraints:
    if not c.meets(diff): return False
  return True

# For selecting songs
class Constraint:
  def __init__(self, kind = "name", value = "BASIC"):
    self.kind = kind
    self.value = value

  def meets(self, diffs):
    if self.kind == "name":
      if diffs.has_key(self.value): return True
      else: return False
    elif self.kind == "number":
      for k in diffs:
        if diffs[k] in range(self.value[0], self.value[1] + 1): return True
      return False

  def diff(self, diffs):
    if self.kind == "name": return self.value
    elif self.kind == "number":
      for k in diffs:
        if diffs[k] in range(self.value[0], self.value[1] + 1): return k

# Generate a playlist forever
class FakePlaylist:
  def __init__(self, songs, constraints, screen, mode):
    self.songs = [s for s in songs if (s.info["valid"] and
                                       check_constraints(constraints,
                                                        s.difficulty[mode]))]
    self.working = []
    self.mode = mode
    self.constraints = constraints
    self.numplayers = len(constraints)
    self.screen = screen

  def __iter__(self):
    return self

  def next(self):
    if len(self.songs) == 0:
      error.ErrorMessage(self.screen,
                        ("The difficulty settings you chose result",
                         "in no songs being available to play."))
      raise StopIteration
    elif len(self.working) == 0: self.working = copy.copy(self.songs)
    i = random.randint(0, len(self.working) - 1)
    song = self.working[i]
    del(self.working[i])
    return (song.filename,
            [c.diff(song.difficulty[self.mode]) for c in self.constraints])

class Endless:
  def __init__(self, songitems, screen, playSequence, gametype):
    self.player_configs = [copy.copy(player_config)]
    self.game_config = copy.copy(game_config)
    songitems = [s for s in songitems if s.difficulty.has_key(gametype)]
    oldaf = mainconfig["autofail"]
    diffs = []
    diff_count = {} # if we see a difficulty 2 times or more, use it
    for song in songitems:
      if song.difficulty.has_key(gametype):
        for d in song.difficulty[gametype]:
          if diff_count.has_key(d) and d not in diffs : diffs.append(d)
          else: diff_count[d] = True

    diffs.sort(python_sucks_sort)

    if len(diffs) == 0:
      error.ErrorMessage(screen, ("You need more songs to play Endless Mode.",
                                 "Otherwise, it's just really boring."))
      return

    mainconfig["autofail"] = 1

    self.constraints = [Constraint()]
    self.bg = pygame.image.load(BACKGROUND)
    self.screen = screen
    self.firsttime = True

    audio.load(os.path.join(sound_path, "menu.ogg"))
    audio.play(4, 0.0)

    self.render()

    ev = (0, E_PASS)

    while ev[1] != E_QUIT:
      ev = event.wait()

      # Start game
      if ev[0] == 0 and ev[1] == E_START:

        if optionscreen.player_opt_driver(screen, self.player_configs):
          playSequence(FakePlaylist(songitems, self.constraints,
                                    screen, gametype),
                       self.player_configs, self.game_config, gametype)

        audio.load(os.path.join(sound_path, "menu.ogg"))
        audio.play(4, 0.0)

        while ev[1] != E_PASS: ev = event.poll()

      if ev[0] == 0 and ev[1] == E_SELECT:
        optionscreen.game_opt_driver(screen, self.game_config)

      # Player 2 on
      elif ev[0] == len(self.constraints) and ev[1] == E_START:
        self.constraints.append(Constraint())
        self.player_configs.append(copy.copy(player_config))

      # Player 2 off
      elif ev[0] < len(self.constraints) and ev[1] == E_START:
        while len(self.constraints) > ev[0]:
          self.constraints.pop()
          self.player_configs.pop()

      # Ignore unknown events
      elif ev[0] >= len(self.constraints): pass

      elif ev[1] == E_LEFT and self.constraints[ev[0]].kind != "name":
        self.constraints[ev[0]].kind = "name"
        self.constraints[ev[0]].value = diffs[0]
      elif ev[1] == E_RIGHT and self.constraints[ev[0]].kind != "number":
        self.constraints[ev[0]].kind = "number"
        self.constraints[ev[0]].value = [1, 3]
      elif ev[1] == E_UP: # easier
        if self.constraints[ev[0]].kind == "name":
          newi = max(0, diffs.index(self.constraints[ev[0]].value) - 1)
          self.constraints[ev[0]].value = diffs[newi]
        elif self.constraints[ev[0]].kind == "number":
          newmin = max(self.constraints[ev[0]].value[0] - 1, 1)
          self.constraints[ev[0]].value = [newmin, newmin + 2]

      elif ev[1] == E_DOWN: # harder
        if self.constraints[ev[0]].kind == "name":
          newi = min(len(diffs) - 1,
                     diffs.index(self.constraints[ev[0]].value) + 1)
          self.constraints[ev[0]].value = diffs[newi]
        elif self.constraints[ev[0]].kind == "number":
          newmin = min(self.constraints[ev[0]].value[0] + 1, 9)
          self.constraints[ev[0]].value = [newmin, newmin + 2]

      self.render()

    mainconfig["autofail"] = oldaf

  # FIXME - Calculate rects instead?
  def render(self):
    self.screen.blit(self.bg, (0,0))

    for i in range(len(self.constraints)):
      c = self.constraints[i]
      ptext = FONTS[60].render("Player " + str(i + 1), 1, colors.WHITE)
      ctext = vtext = None
      if c.kind == "name":
        ctext = FONTS[48].render("Select by Difficulty", 1, colors.WHITE)
        vtext = FONTS[40].render(c.value.capitalize(), 1, colors.WHITE)
      elif c.kind == "number":
        ctext = FONTS[48].render("Select by Rating", 1, colors.WHITE)
        vtext = FONTS[40].render("Between " + str(c.value[0]) + " and " +
                                 str(c.value[1]), 1, colors.WHITE)

        vtext.set_colorkey(vtext.get_at((0,0)), RLEACCEL)
        ctext.set_colorkey(ctext.get_at((0,0)), RLEACCEL)

      ptext_r = ptext.get_rect()
      ptext_r.center = (RESOLUTION[0] / 4 + 2 * i * (RESOLUTION[0] / 4),
                        50)
      ctext_r = ctext.get_rect()
      ctext_r.center = (RESOLUTION[0] / 4 + 2 * i * (RESOLUTION[0] / 4),
                        RESOLUTION[1] / 3)
      vtext_r = vtext.get_rect()
      vtext_r.center = (RESOLUTION[0] / 4 + 2 * i * (RESOLUTION[0] / 4),
                        RESOLUTION[1] / 2)

      self.screen.blit(ptext, ptext_r)
      self.screen.blit(ctext, ctext_r)
      self.screen.blit(vtext, vtext_r)

    pygame.display.flip()
