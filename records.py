# Store information about player records

from constants import *
import cPickle as pickle
import grades
import games

record_fn = os.path.join(rc_path, "records")

try: records = pickle.load(file(record_fn, "r"))
except: records = {}

def verify(recordkeys):
  for k in records.keys():
    if k[0] not in recordkeys: del(records[k])
  
# records maps the title, mix, difficulty, and game onto a tuple
# (rank, name) where rank is a floating point number from 0 to 1; and
# name is the name of the player who made the score.

# A score is considered "beaten" (and therefore deserving of a new name
# value) when the new rank is greater than the old rank.

# The actual "grade" is calculated via grades.py, from the rank. This is
# done in the song selector.

def add(recordkey, diff, game, rank, name):
  game = games.VERSUS2SINGLE.get(game, game)
  if (recordkey, diff, game) in records:
    if rank > records[(recordkey, diff, game)][0]:
      records[(recordkey, diff, game)] = (rank, name)
      return True
    return False
  else:
    records[(recordkey, diff, game)] = (rank, name)
    return True

def get(recordkey, diff, game):
  game = games.VERSUS2SINGLE.get(game, game)
  return records.get((recordkey, diff, game), (-1, ""))

def write():
  pickle.dump(records, file(record_fn, "w"))

def best(index, diff):
  index -= 1
  r = [(v[0], k[0]) for k, v in records.items() if (k[1] == diff)] 
  if len(r) == 0: return None
  r.sort()
  index %= len(r)
  return r[index][1]

def worst(index, diff):
  r = [(v[0], k[0]) for k, v in records.items() if (k[1] == diff)]
  if len(r) == 0: return None
  r.sort()
  index %= len(r)
  return r[index][1]
