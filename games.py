# This contains a bunch of information describing the different
# game types pydance supports.

class GameType(object):
  def __init__(self, **args):
    # The width in pixels of the arrows. FIXME: Height should also be
    # dependent on this, or separate variable; currently it's hardcoded
    # to 64
    self.width = 64

    # The directions to be displayed for each player.
    self.dirs = "ldur"

    # The maximum number of players for this game mode.
    self.players = 2

    #  Whether or not to parse the step data in coupled format, that is
    # as different steps depending on player ID.
    self.couple = False

    # Whether or not we should map input for two joysticks to one player
    # This also affects how the arrows are laid out.
    self.double = False

    self.__dict__.update(args)

    self.dirs = list(self.dirs)

    # The spacing between each field's edge; therefore, the width of
    # each player's field as well.
    if self.double: self.player_offset = 640 / (2 * self.players)
    else: self.player_offset = 640 / self.players

    # There isn't a double mode that we shouldn't parse as a coupled mode...
    if self.double: self.couple = True

    # The offset to start drawing the arrows at, centered within the field
    # (Unless the mode isdoubled - see left_offset(self,pid) below.
    if self.double:
      self.left_offset = (640 / (2 * self.players) -
                          self.width * len(self.dirs)) / 2
    else:
      self.left_offset = (640 / self.players - self.width * len(self.dirs)) / 2

    # The center of the playfield, for non-arrow sprites (score, lifebar, etc)
    self.sprite_center = 320 / self.players

  # In double modes, we need to have the fields adjacent and dependent on pid.
  # sprite_center will be fine; player_offset will be fine.
  def left_off(self, pid):
    if not self.double: return self.left_offset
    elif pid & 1: return 0
    else: return self.left_offset * 2

GAMES = {
  "SINGLE": GameType(players = 1),
  "VERSUS": GameType(players = 2),
  "COUPLE": GameType(couple = True),
  "DOUBLE": GameType(double = True, players = 1),
  "5PANEL": GameType(players = 1, dirs = "wkczg", width = 56),
  "5VERSUS": GameType(players = 2, dirs = "wkczg", width = 56),
  "5COUPLE": GameType(players = 2, couple = True, dirs = "wkczg", width = 56),
  "5DOUBLE": GameType(players = 1, double = True, dirs = "wkczg", width = 56),
  "6PANEL": GameType(players = 1, dirs = "lkduzr"),
  "6VERSUS": GameType(players = 2, dirs = "lkduzr", width = 48),
  "6COUPLE": GameType(players = 2, couple = True, dirs = "lkduzr", width = 48),
  "6DOUBLE": GameType(players = 1, double = True, dirs = "lkduzr", width = 48),
  "8PANEL": GameType(players = 1, dirs = "wlkduzrg"),
  "8VERSUS": GameType(players = 2, dirs = "wlkduzrg", width = 32),
  "8COUPLE": GameType(players = 2, dirs = "wlkduzrg", width = 32, couple = True),
  "8DOUBLE": GameType(players = 1, dirs = "wlkduzrg", width = 32, double = True),
  }

SINGLE = [mode for mode in GAMES if (GAMES[mode].players == 1 and
                                     not GAMES[mode].double)]
VERSUS = [mode for mode in GAMES if (GAMES[mode].players == 2 and
                                     not GAMES[mode].couple)]
COUPLE = [mode for mode in GAMES if GAMES[mode].couple]
DOUBLE = [mode for mode in GAMES if GAMES[mode].double]


for game in GAMES: GAMES[game].name = game
