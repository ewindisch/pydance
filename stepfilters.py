# Contains filters for the various modifiers possible

import random, math, games, copy

NOT_STEPS = ["D", "S", "L", "W", "B", "R"]

# 0 - Normal
# 1 - Mirror
# 2 - Left
# 3 - Right
# -1 - Shuffle, -2 - random

# Map A to B using table C; A[i] -> B[C[i]].
# FIXME: Use direction strings here... They're simpler.
STEP_MAPPINGS = {
  "SINGLE": [[0, 1, 2, 3], [3, 2, 1, 0], [1, 3, 0, 2], [2, 0, 3, 1]],
  "5PANEL": [[0, 1, 2, 3, 4], [3, 4, 2, 0, 1], [4, 0, 2, 1, 3],
             [1, 3, 2, 4, 5]],
  "PARAPARA": [[0, 1, 2, 3, 4], [1, 0, 2, 4, 3], [4, 0, 1, 2, 3],
               [1, 2, 3, 4, 0]],
  "6PANEL": [[0, 1, 2, 3, 4, 5], [4, 5, 3, 2, 0, 1], [2, 0, 5, 1, 3, 4],
             [1, 3, 0, 4, 5, 2]],
  "8PANEL": [[0, 1, 2, 3, 4, 5, 6, 7], [5, 6, 7, 4, 3, 0, 1, 2],
             [3, 0, 1, 7, 2, 4, 5, 6], [1, 2, 4, 0, 5, 6, 7, 3]],
  "9PANEL": [[0, 1, 2, 3, 4, 5, 6, 7, 8], [6, 7, 8, 5, 4, 3, 0, 1, 2],
             [3, 0, 1, 8, 4, 2, 5, 6, 7], [1, 2, 5, 0, 4, 6, 7, 8, 3]],
  }

MAP_EQUIVS = {
  "SINGLE": ["DOUBLE", "COUPLE", "VERSUS"],
  "5PANEL": ["5DOUBLE", "5COUPLE", "5VERSUS"],
  "6PANEL": ["6DOUBLE", "6COUPLE", "6VERSUS"],
  "8PANEL": ["8DOUBLE", "8COUPLE", "8VERSUS"],
  "9PANEL": ["9DOUBLE", "9COUPLE", "9VERSUS"],
  "PARAPARA": ["PARADOUBLE", "PARACOUPLE", "PARAVERSUS"],
  }

for mode, equivs in MAP_EQUIVS.items():
  for eq in equivs: STEP_MAPPINGS[eq] = STEP_MAPPINGS[mode]

# Compress the steps to remove empty lines. FIXME: Do this in fileparsers.
def compress(steps):
  new_steps = []
  beat_count = 0
  last_event = None
  for s in steps:
    if not isinstance(s[0], float): # Not a step
      if last_event is not None: new_steps.append([beat_count] + last_event)
      last_event = None
      beat_count = 0
      new_steps.append(s)
    elif s[1:].count(0) != (len(s) - 1) or last_event == None: # Non-empty
      if last_event is not None: new_steps.append([beat_count] + last_event)
      last_event = s[1:]
      beat_count = s[0]
    else: # Empty event
      beat_count += s[0]

  if last_event is not None: new_steps.append([beat_count] + last_event)

  return new_steps

# Rotate the steps according the player's rotation mode
# Random and shuffle aren't really rotations but... whatever.
def rotate(steps, opt, mode):

  double = (mode in games.DOUBLE)

  # Don't crash if we haven't implemented transforms for a mode yet.
  if mode not in STEP_MAPPINGS: return
  elif opt == -1:
    mapping = list(STEP_MAPPINGS[mode][0])
    random.shuffle(mapping)
  elif opt >= 0: mapping = STEP_MAPPINGS[mode][opt]
  else: mapping = None

  for s in steps:
    if s[0] not in NOT_STEPS:
      if mapping != None:
        step = list(s[1:])
        for j in range(len(step)): s[mapping[j] + 1] = step[j]
      else:
        random_steps = list(s[1:])
        random.shuffle(random_steps)
        s[1:] = random_steps

# Apply myriad additions/deletions to the step pattern
# FIXME: Return a list rather than in-place modify.
# FIXME: Big, quick, skippy.X
def size(steps, opt):
  if opt == 1: little(steps, 4) # Tiny
  elif opt == 2: little(steps, 2) # Little
  elif opt == 3: insert_taps(steps, 4.0, 2.0, False) # Big
  elif opt == 4: insert_taps(steps, 2.0, 1.0, False) # Quick
  elif opt == 5: insert_taps(steps, 4.0, 3.0, True) # Skippy

# Remove steps that aren't on the beat
def little(steps, mod):
  beat = 0.0
  for s in steps:
    if s[0] not in NOT_STEPS:
      if beat % mod != 0: s[1:] = [0] * (len(s) - 1)
      beat += s[0]
    elif s[0] == "D": beat += s[1]

# Insert taps if a note falls on a interval-even beat, and the next step
# is interval-away. Insert the new step offset away from the original step
# (and therefore the time for the offset set is interval - offset).
# not_same makes sure the random tap inserted isn't the same as either of
# the surrounding ones.

# Inspired by Stepmania's function of the same name, in src/NoteData.cpp.
def insert_taps(steps, interval, offset, not_same):
  new_steps = []
  holds = []
  beat = 0.0
  rand = NonRandom(int(interval * offset * len(steps)))
  for i in range(len(steps) - 1):
    if isinstance(steps[i][0], float): # This is a note...
      for j in range(len(steps[i][1:])):
        if steps[i][j + 1] & 2: holds.append(j)
        elif steps[i][j + 1] & 1 and j in holds: holds.remove(j)
      
      if not isinstance(steps[i + 1][0], float):
        new_steps.append(steps[i]) # Next isn't a note.

      elif (steps[i][1:].count(0) == len(steps[i][1:]) or
            steps[i + 1][1:].count(0) == len(steps[i + 1][1:])):
        # The surrounding notes are both empty.
        new_steps.append(steps[i])

      elif len(holds) > 1: # Don't add things during two holds
        new_steps.append(steps[i])

      elif steps[i][0] == interval and beat % interval == 0: # Bingo!
        steps[i][0] = offset
        beat += offset
        new_steps.append(steps[i])

        if not_same:
          start = rand.randint(0, len(steps[i][1:]) -1)
          empty = [0] * len(steps[i][1:])
          for j in range(len(steps[i][1:])):
            checking = (start + j) % len(steps[i][1:])
            if not (steps[i][checking + 1] or steps[i + 1][checking + 1]):
              empty[checking] = 1
              break
          new_steps.append([interval - offset] + empty)
        else:
          new_step = [1] + ([0] * (len(steps[i][1:]) - 2))
          rand.shuffle(new_step)
          new_steps.append([interval - offset] + new_step)

      else: new_steps.append(steps[i])

      beat += new_steps[-1][0]
      # Stupid inaccurate floating point.
      if int(beat + 0.0000001) > int(beat): beat = int(beat + 0.0000001)
    else:
      if steps[i][0] == "D": beat += steps[i][1]
      new_steps.append(steps[i])

  steps[0:-1] = new_steps # Copy into place.

# Pretty obvious.
def remove_holds(steps, jump):
  for s in steps:
    if s[0] not in NOT_STEPS: s[1:] = [i & 1 for i in s[1:]]

# Remove secret steps; defined by the 4 bit being on, so 5, 6, or 7.
def remove_secret(steps):
  for s in steps:
    if s[0] not in NOT_STEPS:
      for i in range(len(s[1:])):
        if s[1 + i] & 4: s[1 + i] = 0

# Remove or add jumps:
def jumps(steps, jump):
  if jump == 1: remove_jumps(steps)
  elif jump == 2: wide(steps)

def remove_jumps(steps):
  side = 0 # Alternate sides so e.g. LR alternates between L and R.
  for s in steps:
    if s[0] not in NOT_STEPS:
      step = list(s[1:])
      if step.count(0) < len(step) - 1:
        if side == 1: step.reverse()
        for i in range(len(step)):
          if step[i] != 0:
            step[i] = 0
            break
        if side == 1: step.reverse()
        side ^= 1

        s[1:] = step

# Add jumps on the on-beats that have steps.
def wide(steps):
  beat = 0.0
  holds = []
  for s in steps:
    if s[0] not in NOT_STEPS:
      step = list(s[1:])

      for i in range(len(step)):
        if step[i] & 1 and i in holds: holds.remove(i)

      # Don't add jumps to things that are already jumps, or empty, or
      # during holds
      if (beat % 4 == 0 and
          step.count(0) == len(step) - 1 and
          len(holds) == 0):

        first = 0
        while step[first] == 0: first += 1 # Find the first step

        # Pseudorandom but deterministically
        to_add = int(math.sqrt(beat)) % len(step)
        if step[to_add] != 0: to_add = (to_add + 1) % len(step)
        step[to_add] = 1

        s[1:] = step

      for i in range(len(step)):
        if step[i] & 2: holds.append(i)

      beat += s[0]
    elif s[0] == "D": beat += s[1]

# Now, here's where stuff gets tricky. We have to randomly but
# deterministically generate fun steps for modes not in the file. The
# first part - the randomness - is easy:

# This is a pseudorandom number generator that we're guaranteed will
# always return the same results between different versions of Python,
# given the same seed. This makes sure the same autogenerated steps are
# made across different versions and platforms.

# A) Never change these numbers; they do ensure good randomness.
# B) Never use this module anywhere except pydance; its randomness is bad.
class NonRandom(random.Random):
  def __init__(self, seed = 1):
    self.seed(seed)
    self.m = 16807
    self.n = 2147483647

  def getstate(self): return self.seed

  def setstate(self, state): self.seed(state)

  def seed(self, seed = 1): self.seed = seed

  def jumpahead(self, n): pass

  def random(self):
    self.seed = (self.seed * self.m) % self.n
    return float(self.seed) / self.n
  
# Now for the "fun". This is a lot harder. The "core" of the work is done
# with a generic Transform object.
class Transform(object):
  def transform(self, data):
    self._update_state(data)
    return self._transform(data)

# Transform step patterns from N panel to M panel. This is most common
# type of transformation, and probably the easiest.

# This transformation is only intended for mapping N to M when M >= N.
# Mapping down is substantially easier and doesn't require a random
# function.
class PanelTransform(Transform):

  # key is a direction; value is a list of directions that are "fun" to
  # map to. Repeating a direction makes it more likely to be chosen. No
  # direction should map to itself; making that extra-likely is taken
  # care of in the map generation algorithm already.
  accept = { "k": "uullc", "u": "kkzzc", "z": "uurrc",
             "l": "kkwwc", "c": "lluuddrrkzwg", "r": "zzggc",
             "w": "llddc", "d": "wwggc", "g": "ddrrc" }

  def __init__(self, orig_panels, new_panels, rand, freq = 0.075):
    self.orig_panels = orig_panels
    self.new_panels = new_panels
    self.freq = freq
    self.rand = rand # A NonRandom instance preseeded.

    # This is the chance (increasing by 'freq' for each datum we process)
    # that a new pseudorandom mapping table (see below) will be generated,
    # when a data transform is requested.

    self.count = 0

    # This is true if we encounter the same (exact) pattern twice in a row.
    # We never generate a new mapping table in such a case, and so preserve
    # multiple taps on the same arrow.
    self.repeating = False

    # This tracks the last two patterns transformed.
    self.last_processed = [None, None]

    # A dictionary mapping directions (characters) to a list of directions
    # (strings), that are a) "near" the original direction, and b) in
    # self.new_panels.
    self.accept = self._generate_accept()

    # A list of directions in orig_panels currently behind held.
    self.holds = []

    self._generate_transform()

  # Reduce the acceptable mapping table to only include directions from the
  # game modes in question.
  def _generate_accept(self):
    accept = {}
    for dir in PanelTransform.accept:
      if dir in self.orig_panels:
        accept[dir] = "".join([c for c in PanelTransform.accept[dir]
                               if c in self.new_panels])
    for dir in self.orig_panels:
      if not accept.has_key(dir):
        accept[dir] = "".join(self.new_panels)
    return accept

  # transform_mapping (trans) is, essentially, a scrambled list of directions
  # from orig_panels, but shoved into an array the size of new_panels.
  def _generate_transform(self):
    unmapped = list(self.orig_panels)
    trans = [None] * len(self.new_panels)

    # First, map any hold arrows to the same place they were in for the
    # last transformation, so they end at the right time.
    for d in self.holds:
      if d in self.transform_mapping:
        unmapped.remove(d)
        trans[self.transform_mapping.index(d)] = d

    # Next, give a high chance that any direction will be mapped
    # to itself, assuming it exists in the new panels. Or, always map
    # it to its old self, if no alternatives exist.

    # Originally, the "high chance" was hard coded around 0.5 to 0.75.
    # Lower values meant steps got shuffled more than desired on small
    # mappings, but higher ones resulted in small->large mappings not
    # using many of the available arrows. So, now the chance is the
    # ratio between the two sizes.

    chance = float(len(self.orig_panels)) / float(len(self.new_panels))
        
    unmapped_original = list(unmapped) # Don't modify the iterating list
    for d in unmapped_original:
      if d in self.new_panels:
        if self.rand.random() < chance or len(self.accept[d]) == 0:
          trans[self.new_panels.index(d)] = d
          unmapped.remove(d)

    # Next, go through whatever is left, and map it acceptably.
    for d in unmapped:
      accept = [a for a in self.accept[d] if
                trans[self.new_panels.index(a)] is None]

      if len(accept) != 0:
        dir = self.rand.choice(accept)
        trans[self.new_panels.index(dir)] = d
      else:
        # If possible, see if we can map to the original direction again
        # (all its neighbors may have gotten overwritten between the first
        # check and now).
        if d in self.new_panels and trans[self.new_panels.index(d)] is None:
          trans[self.new_panels.index(d)] = d

        # And finally --
        # Arrows in this direction won't get mapped to anything.
        # However, in order to avoid accidentally dropping many events
        # through poorly generated mappings, generate a new one more
        # quickly if this situation occurs.
        else: self.count = self.freq * 5

    self.transform_mapping = trans

  # Update our internal state based on the data passed in.
  def _update_state(self, steps):
    # This is a delay / BPM change / etc
    if not isinstance(steps[0], float): return

    self.count += self.freq * steps[0]

    # Check the last two events to see if this is a repeat.
    self.repeating = False
    if steps[1:] in self.last_processed:
      self.repeating = True
    self.last_processed.append(steps[1:])
    self.last_processed.pop(0)

    # If we're not repeating, see if it's time to generate a new
    # transformation table.
    if not self.repeating:
      if self.count > self.rand.random():
        self.count = 0
        self._generate_transform()

    # Note any holds, so they don't get remapped in the middle.
    for i in range(len(steps[1:])):
      if steps[i + 1] & 2:
        self.holds.append(self.orig_panels[i])
      elif steps[i + 1] & 1 and self.orig_panels[i] in self.holds:
        self.holds.remove(self.orig_panels[i])

  # Actually perform the transformation on the data.
  def _transform(self, steps):
    # This is not a note, it's a BPM change / delay / etc
    if not isinstance(steps[0], float): return copy.copy(steps)

    new_steps = [0] * (len(self.transform_mapping) + 1)
    new_steps[0] = steps[0]

    for i in range(len(steps[1:])):
      if steps[i + 1] and self.orig_panels[i] in self.transform_mapping:
        v = steps[i + 1]
        new_steps[self.transform_mapping.index(self.orig_panels[i]) + 1] = v

    return new_steps

# Transform a song's steps from one mode and difficulty to a target mode.
def generate_mode(song, difficulty, target_mode, pid):
  if target_mode in games.SINGLE: mode = "SINGLE"
  elif target_mode in games.VERSUS: mode = "VERSUS"
  elif target_mode in games.ONLY_COUPLE: mode = "COUPLE"
  elif target_mode in games.DOUBLE: mode = "DOUBLE"

  steps = song.steps[mode][difficulty]
  if mode in games.COUPLE: steps = steps[pid]

  seed = song.info["bpm"]
  if song.info["gap"] != 0: seed *= song.info["gap"]

  trans = PanelTransform(games.GAMES[mode].dirs, games.GAMES[target_mode].dirs,
                         NonRandom(int(song.info["bpm"])))

  return [trans.transform(s) for s in steps]
