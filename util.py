import fnmatch, os, string

# This is the standard order to present difficulties in.
# DDR (USA home version) calls "beginner" "standard". Ignore that.
# Beginner, light, basic, another, standard, trick, maniac, heavy, challenge,
# and oni are from DDR. Smaniac is from DWI; s-maniac is a very common typo.
# Hardcore is from pydance. Para and expert are from PPP. Easy, and hard are
# from TM and PIU; medium is from TM; crazy is from PIU.
DIFFICULTY_LIST = ["BEGINNER", "EASY", "LIGHT", "BASIC", "PARA", "ANOTHER",
                   "NORMAL", "MEDIUM", "STANDARD", "TRICK", "DOUBLE", "HARD",
                   "MANIAC", "HEAVY", "HARDCORE", "CHALLENGE", "ONI",
                   "SMANIAC", "S-MANIAC", "CRAZY", "EXPERT"]

def difficulty_sort(a, b):
  if a in DIFFICULTY_LIST and b in DIFFICULTY_LIST:
    return cmp(DIFFICULTY_LIST.index(a), DIFFICULTY_LIST.index(b))
  elif a in DIFFICULTY_LIST: return -1
  elif b in DIFFICULTY_LIST: return 1
  else: return cmp(a, b)

# Return the subtitle of a song...
def find_subtitle(title):
  for pair in (("[", "]"), ("(", ")"), ("~", "~"), ("-", "-")):
    if pair[0] in title and title[-1] == pair[1]:
      l = title[0:-1].rindex(pair[0])
      if l != 0:
        subtitle = title[l:]
        title = title[:l]
        return title, subtitle
  else: return title, ""

# FIXME: We should inline this. Really.
# Or not, Psyco does it for us, basically.
def toRealTime(bpm, steps):
  return steps*0.25*60.0/bpm

# Search the directory specified by path recursively for files that match
# the shell wildcard pattern. A list of all matching file names is returned,
# with absolute paths.
def find (path, patterns):
  matches = []
  path = os.path.abspath(os.path.expanduser(path))

  if os.path.isdir(path):
    list = os.listdir(path)
    for f in list:
      filepath = os.path.join(path, f)
      if os.path.isdir(filepath):
        matches.extend(find(filepath, patterns))
      else:
        for pattern in patterns:
          if fnmatch.fnmatch(filepath.lower(), pattern):
            matches.append(filepath)
            break
  return matches

# This uses a bunch of heuristics to come up with a good titlecased
# string. Python's titlecase function sucks.
def titlecase(title):
  nonletter = 0
  uncapped = ("in", "a", "the", "is", "for", "to", "by", "of", "de", "la")
  vowels = "aeiouyAEIOUY"
  letters = string.letters + "?!'" # Yeah, those aren't letters, but...

  parts = title.split()
  if len(parts) == 0: return ""

  for i in range(len(parts)):
    nonletter = 0
    has_vowels = False
    for l in parts[i]:
      if l not in letters: nonletter += 1
      if l in vowels: has_vowels = True
    if float(nonletter) / len(parts[i]) < 1.0/3:
      if parts[i] == parts[i].upper() and has_vowels:
        parts[i] = parts[i].lower()
        if parts[i] not in uncapped:
          parts[i] = parts[i].capitalize()


  # Capitalize the first and last words in the name, unless they are
  # are "stylistically" lowercase.
  for i in (0, -1):
    if parts[i] != parts[i].lower() or parts[i] in uncapped:
      oldparts = parts[i]
      parts[i] = parts[i][0].capitalize() + oldparts[1:]

  return " ".join(parts)
