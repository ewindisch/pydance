# This contains a bunch of information describing the different
# game types pydance supports.

class GameType:
  def __init__(self, **args):
    self.width = 64
    self.dirs = ["l", "d", "u", "r"]
    self.players = 2
    self.couple = False
    self.double = False
    self.__dict__.update(args)
    self.left_off = (640 / self.players - self.width * len(self.dirs)) / 2

GAMES = {
  "SINGLE": GameType(),
  "COUPLE": GameType(couple = True),
  "6PANEL": GameType(players = 1, dirs = ["l", "k", "d", "u", "z", "r"]),
  }

COUPLE = [mode for mode in GAMES if GAMES[mode].couple]
DOUBLE = [mode for mode in GAMES if GAMES[mode].double]

# FIXME: This can be replaced with not in COUPLE...
SINGLE = [mode for mode in GAMES if not GAMES[mode].couple]
