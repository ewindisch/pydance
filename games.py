# This contains a bunch of information describing the different
# game types pyDDR supports.

# This does make sense, really. You'll see why when we have double and
# 6panel support.

# Oh hell, I wish I was working in Ruby.
class GameType:
  def __init__(self, **args):
    self.__dict__.update(args)


GAMES = {
  "SINGLE": GameType(couple = False, directions = ["u", "d", "l", "r"],
                     locked = False),
  "COUPLE": GameType(couple = True, directions = ["u", "d", "l", "r"],
                     locked = True),
  }

COUPLE = [mode for mode in GAMES if GAMES[mode].couple]
SINGLE = [mode for mode in GAMES if not GAMES[mode].couple]

