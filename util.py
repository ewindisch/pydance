import fnmatch, os, string

from constants import *

# FIXME: We should inline this. Really.
def toRealTime(bpm, steps):
  return steps*0.25*60.0/bpm

class ErrorMessage:
  def __init__(self, screen, lines):
    screen.fill((0, 0, 0))
    bg = pygame.image.load(os.path.join(image_path, "bg.png"))
    bg.set_alpha(128)
    screen.blit(bg, (0, 0))
    text = FONTS[60].render("ERROR!", 1, (0, 0, 0))
    text_rect = text.get_rect()
    text_rect.center = (320, 30)
    screen.blit(text, text_rect)

    for i in range(len(lines)):
      text = FONTS[32].render(lines[i], 1, (244, 244, 244))
      text_rect = text.get_rect()
      text_rect.center = (320, 36 * (i + 3))
      screen.blit(text, text_rect)

    text = FONTS[32].render("Press Enter/Start/Esc", 1, (160, 160, 160))
    text.set_colorkey(text.get_at((0, 0)))
    textpos = text.get_rect()
    textpos.center = (320, 440)
    screen.blit(text, textpos)

    pygame.display.flip()
    ev = (0, E_PASS)
    while ev[1] != E_START and ev[1] != E_QUIT:
      pygame.time.wait(50)
      ev = event.poll()

# Search the directory specified by path recursively for files that match
# the shell wildcard pattern. A list of all matching file names is returned,
# with absolute paths.
def find (path, patterns):
  matches = []
  path = os.path.expanduser(path)

  if os.path.isdir(path):
    list = os.listdir(path)
    for f in list:
      filepath = os.path.join(path, f)
      if os.path.isdir(filepath):
        matches.extend(find(filepath, patterns))
      else:
        for pattern in patterns:
          if fnmatch.fnmatch(filepath, pattern):
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


  for i in (0, -1):
    if parts[i] != parts[i].lower() or parts[i] in uncapped:
      oldparts = parts[i]
      parts[i] = parts[i][0].capitalize() + oldparts[1:]

  return " ".join(parts)
