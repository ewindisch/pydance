# Store information about player records

from constants import *
import cPickle as pickle
import grades
import games

record_fn = os.path.join(rc_path, "records")

try: records = pickle.load(file(record_fn, "r"))
except: records = {}
  
# records maps the last three significant parts of a filename (the
# filename and two directories ) onto a tuple of (rank, game, name) where
# rank is a floating point number from 0 to 1; and name is the name of
# the player who made the score. A score is considered "beaten" (and
# therefore deserving of a new name value) when the new rank is
# greater than the old rank.

# The actual "grade" is calculated via grades.py, from the rank.

def add(filename, diff, game, rank, name):
  game = games.VERSUS2SINGLE.get(game, game)
  newfn = os.path.join(*filename.split(os.sep)[-3:])
  if (newfn, diff, game) in records:
    if rank > records[newfn][0]:
      records[(newfn, diff, game)][0] = (rank, name)
      return True
    return False
  else:
    records[(newfn, diff, game)] = (rank, name)
    return True

def get(filename, diff, game):
  game = games.VERSUS2SINGLE.get(game, game)
  newfn = os.path.join(*filename.split(os.sep)[-3:])
  return records.get((newfn, diff, game), (-1, ""))

def write():
  pickle.dump(records, file(record_fn, "w"))
