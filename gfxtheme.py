# GFXTheme and associated classes.
# These handle loading the various graphics themes for pydance.

# In general, this is wrapped in what's probably way too many layers of
# abstraction. We should be able to remove some of these classes, or at
# least many of the accessor functions.

import dircache, os, games, zipfile

from cStringIO import StringIO

from listener import Listener

from constants import *
from util import toRealTime

# Wrapper classes for loading files from themes.
# Eventually, we can use ZipFile + StringIO to make it load from zip files.
class ThemeFile(object):

  # List all themes available for a game type (given as a string)
  def list_themes(cls, gametype):
    w = games.GAMES[gametype].width
    size = "%dx%d" % (w, w)
    theme_list = []
    for path in search_paths:
      check = os.path.join(path, "themes", "gfx", size)
      if os.path.isdir(check):
        for name in dircache.listdir(check):
          if cls.is_theme(os.path.join(check, name), games.GAMES[gametype]):
            theme_list.append(name)
    return theme_list

  list_themes = classmethod(list_themes)

  # Test whether a particular theme will work for a particular game type.
  # Also, whether it's a theme at all, or just some random file.
  def is_theme(cls, filename, game):
    if not os.path.isdir(filename):
      return cls.is_zip_theme(filename, game)
    elif not os.path.exists(os.path.join(filename, "is-theme")):
      return False
    elif (os.path.split(os.path.split(filename)[0])[1] !=
          "%dx%d" % (game.width, game.width)):
      return False
    else:
      for dir in game.dirs:
        possible = os.path.join(filename, "arr_%s_%s_0.png" % ("%s", dir))
        if not (os.path.exists(possible % "c") and
                os.path.exists(possible % "n")):
          return False
    return True

  is_theme = classmethod(is_theme)

  # Check if a zip file is a theme for a mode.
  def is_zip_theme(cls, filename, game):
    if filename[-3:].lower() != "zip": return False
    else:
      zip = zipfile.ZipFile(filename, "r")
      if zip.testzip():
        zip.close()
        return False
      files = zip.namelist()
      zip.close()
      if "is-theme" not in files: return False
      for dir in game.dirs:
        possible = "arr_%s_%s_0.png" % ("%s", dir)
        if not (possible % "c" in files and possible % "n" in files):
          return False
      return True

  is_zip_theme = classmethod(is_zip_theme)

  def __init__(self, filename):
    self.path = filename
    self.zip = None
    if not os.path.isdir(filename):
      self.zip = zipfile.ZipFile(filename)

  # Get an image from the theme.
  def get_image(self, image_name):
    try:
      if self.zip:
        return pygame.image.load(StringIO(self.zip.read(image_name)))
      else:
        return pygame.image.load(os.path.join(self.path, image_name))
    except:
      raise RuntimeError("E: %s was missing from your theme." % image_name)

  # Check to see if an image is in the theme.
  def has_image(self, image_name):
    if self.zip: return image_name in self.zip.namelist()
    else: return os.path.exists(os.path.join(self.path, image_name))

  # Get an arrow based on its type/direction/color.
  # If the desired arrow coloring wasn't found, fall back to the default
  # coloring (which is_theme makes sure we have).
  def get_arrow(self, type, dir, num):
    fn = "arr_%s_%s_%d.png" % (type, dir, num)
    if not self.has_image(fn): fn = "arr_%s_%s_%d.png" % (type, dir, 0)
    return self.get_image(fn)

# An even higher-level interface than ThemeFile, that sets up the sprites
# for many of the images.
class GFXTheme(object):

  def __init__(self, name, pid, game):
    self.name = name
    self.game = game
    self.path = None
    self.pid = pid
    size = "%dx%d" % (game.width, game.width)
    for path in search_paths:
      if os.path.exists(os.path.join(path, "themes", "gfx", size, name)):
        self.path = os.path.join(path, "themes", "gfx", size, name)

    if self.path == None:
      raise RuntimeError("E: Cannot load theme '%s/%s'." % (size, name))

    self.theme_data = ThemeFile(self.path)

  # FIXME: Can probably be moved to __init__ and stored as members.
  def arrows(self, pid):
    return ArrowSet(self.theme_data, self.game, pid)

  # FIXME: Can probably be moved to __init__ and stored as members.
  def toparrows(self, ypos, pid):
    arrs = {}
    arrfx = {}
    for d in self.game.dirs:
      arrs[d] = TopArrow(d, ypos, pid, self.theme_data, self.game)
      arrfx[d] = ArrowFX(d, ypos, pid, self.theme_data, self.game)
    return arrs, arrfx

# The scrolling arrows for this game mode.
class ArrowSet(object):
  def __init__ (self, theme, game, pid):
    arrows = {}
    base_left = game.left_off(pid) + pid * game.player_offset
    for dir in game.dirs:
      left = base_left + game.width * game.dirs.index(dir)
      for cnum in range(4):
        if cnum == 3: color = 1
        else: color = cnum
        arrows[dir+repr(cnum)] = ScrollingArrow(theme, dir, color, left)

    # allow access by instance.l or instance.arrows['l']
    for n in arrows: self.__dict__[n] = arrows[n] 
    self.arrows = arrows

  # allow access by instance['l'] - FIXME - Still necessary?
  def __getitem__ (self,item):
    return getattr(self,item)

# Preload images/left offset for each arrow. 
class ScrollingArrow(object):
  def __init__ (self, theme, dir, color, left):
    self.dir = dir
    self.left = left
    self._image = theme.get_arrow("c", dir, color).convert()
    if self._image.get_width() != self._image.get_height():
      w = self._image.get_width()
      h = self._image.get_height()
      frames = h / w
      if frames * w != h: raise RuntimeError("Theme image is %dx%d." % (w, h))

      self._images = []
      for i in range(frames):
        s = pygame.Surface([w, w])
        s.blit(self._image, [0, -i * w])
        self._images.append(s)
      self._beatcount = len(self._images) / 4
      self._image = None

  def get_image(self, beat):
    if self._image: return self._image
    else:
      beat %= self._beatcount
      beat /= self._beatcount
      pct = beat - int(beat)
      i = int(float(len(self._images)) * pct)
      return self._images[i]

# FIXME: What follows probably doesn't belong here, but elsewhere. There's
# too much logic for it to be just theming data.

# Sprites for the top flashing arrows.
class TopArrow(Listener, pygame.sprite.Sprite):

  def __init__ (self, direction, ypos, pid, theme, game):
    pygame.sprite.Sprite.__init__(self)
    self.pid = pid
    self.endpresstime = -1
    self.frame = 0
    self.oldframe = -1
    self.adder = 0
    self.dir = direction
    self.topimg = []

    # The 'n' state is the normal state for the top arrows. After being
    # pressed, they change to the 's' state images for a short time.
    for i in range(4):
      self.topimg.append(theme.get_arrow("n", direction, i).convert())
      self.topimg[i].set_colorkey(self.topimg[i].get_at((0, 0)), RLEACCEL)
    for i in range(4, 8):
      self.topimg.append(theme.get_arrow("s", direction, i).convert())
      self.topimg[i].set_colorkey(self.topimg[i].get_at((0, 0)), RLEACCEL)

    self.image = self.topimg[0]
    self.rect = self.image.get_rect()
    self.rect.top = ypos
    self.rect.left = (game.left_off(pid) + game.player_offset * pid +
                      game.dirs.index(direction) * game.width)

  # The arrow was pressed, so we have to change it for some time (s state).
  def stepped(self, pid, dir, time, rating, combo):
    if self.pid != pid or self.dir != dir or rating == "M": return

    self.adder = 4
    self.endpresstime = time + 0.25 # Number of seconds to change it for.

  def set_song(self, pid, bpm, diff, count, holds, feet):
    self.tick = toRealTime(bpm, 1)

  def change_bpm(self, pid, curtime, newbpm):
    if self.pid != pid: return
    self.tick = toRealTime(newbpm, 1)

  def update(self, time, offset):
    if time > self.endpresstime: self.adder = 0

    time += 1000 * offset
    self.keyf = int(time / (self.tick / 2)) % 8
    if self.keyf > 3: self.keyf = 3
    self.frame = self.adder + self.keyf

    if self.frame != self.oldframe:
      self.image = self.topimg[self.frame]
      self.oldframe = self.frame

class ArrowFX(Listener, pygame.sprite.Sprite):
  def __init__ (self, direction, ypos, pid, theme, game):
    pygame.sprite.Sprite.__init__(self)
    self.presstime = -1000000
    self.centery = ypos + game.width / 2
    self.centerx = (game.left_off(pid) +
                    game.dirs.index(direction) * game.width + game.width / 2)
    self.pid = pid

    self.dir = direction

    self.baseimg = theme.get_arrow("n", direction, 3).convert()
    self.tintimg = pygame.Surface(self.baseimg.get_size())

    self.blackbox = pygame.surface.Surface([game.width] * 2)
    self.blackbox.set_colorkey(0)
    self.image = self.blackbox
    self.rect = self.image.get_rect()
    self.displaying = 1
    self.direction = 1
    self.holdtype = 0
    self.colors = { "V": [255, 255, 255],
                    "P": [255, 255, 0],
                    "G": [0, 255, 0] }

    style = mainconfig['explodestyle']
    self.rotating, self.scaling = style & 1, style & 2
    
  def set_song(self, pid, bpm, diff, count, holds, feet):
    self.tick = toRealTime(bpm, 1)

  def change_bpm(self, pid, curtime, newbpm):
    if self.pid != pid: return
    self.tick = toRealTime(newbpm, 1)

  def holding(self, yesorno):
    self.holdtype = yesorno
  
  def stepped(self, pid, dir, time, tinttype, combo):
    if pid != self.pid or dir != self.dir: return
    elif not tinttype or tinttype == "M": return

    self.combo = combo
    self.presstime = time
    self.tintimg = pygame.Surface(self.baseimg.get_size(), 0, 16)
    self.tintimg.blit(self.baseimg, (0,0))
    tinter = pygame.surface.Surface(self.baseimg.get_size())
    tinter.fill(self.colors.get(tinttype, [0, 0, 255]))
    tinter.set_alpha(127)
    self.tintimg.blit(tinter,(0,0))
    self.tintimg.set_colorkey(self.tintimg.get_at([0, 0]))
    self.tintimg = self.tintimg.convert()
    if self.direction == 1: self.direction = -1
    else: self.direction = 1

  def update(self, time):
    steptimediff = time - self.presstime
    if (steptimediff < 0.2) or self.holdtype:
      self.displaying = 1
      self.image = self.tintimg
      if self.scaling:
        if self.holdtype:
          scale = 1.54
        else:
          scale = 1.0 + (steptimediff * 4.0) * (1.0+(self.combo/256.0))
        newsize = [max(0, int(x*scale)) for x in self.image.get_size()]
        self.image = pygame.transform.scale(self.image, newsize)
      if self.rotating:
        angle = steptimediff * 230.0 * self.direction
        self.image = pygame.transform.rotate(self.image, angle)
      if self.holdtype == 0:
        tr = 224-int(1024.0*steptimediff)
      else:
        tr = 112
      self.image.set_alpha(tr)
            
    if self.displaying:
      if steptimediff > 0.2 and (self.holdtype == 0):
        self.image = self.blackbox
        self.displaying = 0
      self.rect = self.image.get_rect()
      self.rect.center = self.centerx, self.centery

      self.rect.left += (320 * self.pid)
