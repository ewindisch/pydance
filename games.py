# This contains a bunch of information describing the different
# game types pydance supports.

class GameType:
  def __init__(self, **args):
    # The width in pixels of the arrows. FIXME: Height should also be
    # dependent on this, or separate variable; currently it's hardcoded
    # to 64
    self.width = 64

    # The directions to be displayed for each player.
    self.dirs = ["l", "d", "u", "r"]

    # The maximum number of players for this game mode.
    self.players = 2

    #  Whether or not to parse the step data in coupled format, that is
    # as different steps depending on player ID.
    self.couple = False

    # Whether or not we should map input for two joysticks to one player
    # This also affects how the arrows are laid out.
    self.double = False

    self.__dict__.update(args)

    # The spacing between each field's edge; therefore, the width of
    # each player's field as well.
    self.player_offset = 640 / self.players

    # The offset to start drawing the arrows at, centered within the field
    # (Unless the mode isdoubled - see left_offset(self,pid) below.
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
  "SINGLE": GameType(),
  "COUPLE": GameType(couple = True),
  "DOUBLE": GameType(couple = True, double = True),
  "6PANEL": GameType(players = 1, dirs = ["l", "k", "d", "u", "z", "r"]),
  "8PANEL": GameType(players = 1, dirs = ["w", "l", "k", "d", "u", "z", "r", "g"]),
  }

COUPLE = [mode for mode in GAMES if GAMES[mode].couple]
DOUBLE = [mode for mode in GAMES if GAMES[mode].double]
