# Contains filters for the various modifiers possible

# Unless otherwise stated, all functions modify the steps paseed in,
# rather than a copy.

import random, math

NOT_STEPS = ["D", "S", "L", "W", "B", "R"]

# 0 - Normal
# 1 - Mirror
# 2 - Left
# 3 - Right
# -1 - Shuffle, -2 - random

STEP_MAPPINGS = {
  "SINGLE": [[0, 1, 2, 3], [3, 2, 1, 0], [1, 3, 0, 2], [2, 0, 3, 1]],
  "DOUBLE": [[0, 1, 2, 3], [3, 2, 1, 0], [1, 3, 0, 2], [2, 0, 3, 1]],
  "COUPLE": [[0, 1, 2, 3], [3, 2, 1, 0], [1, 3, 0, 2], [2, 0, 3, 1]],
  "6PANEL": [[0, 1, 2, 3, 4, 5], [4, 5, 3, 2, 0, 1], [2, 0, 5, 1, 3, 4],
             [1, 3, 0, 4, 5, 2]],
  "8PANEL": [[0, 1, 2, 3, 4, 5, 6, 7], [5, 6, 7, 4, 3, 0, 1, 2],
             [3, 0, 1, 7, 2, 4, 5, 6], [1, 2, 4, 0, 5, 6, 7, 3]],
  }

# Rotate the steps according the player's rotation mode
# Random and shuffle aren't really rotations but... whatever.
def rotate(steps, opt, mode):
  if opt == -1:
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
def size(steps, opt):
  if opt == 1: little(steps, 4)
  elif opt == 2: little(steps, 2)

# Remove steps that aren't on the beat
def little(steps, mod):
  beat = 0.0
  for s in steps:
    if s[0] not in NOT_STEPS:
      if beat % mod != 0: s[1:] = [0] * (len(s) - 1)
      beat += s[0]
    elif s[0] == "D": beat += s[1]

def remove_holds(steps, jump):
  for s in steps:
    if s[0] not in NOT_STEPS: s[1:] = [i & 1 for i in s[1:]]

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
