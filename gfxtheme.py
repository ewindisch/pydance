# GFXTheme and associated classes.
# These handle loading the various graphics themes for pydance.

# In general, this is wrapped in what's probably way too many layers of
# abstraction. We should be able to remove some of these classes, or at
# least many of the accessor functions.

import dircache, os, games

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
      return False
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

  def __init__(self, filename):
    self.path = filename

  # Get an image from the theme.
  def get_image(self, image_name):
    try:
      return pygame.image.load(os.path.join(self.path, image_name))
    except:
      raise RuntimeError("E: %s was missing from your theme." % image_name)

  # Check to see if an image is in the theme.
  def has_image(self, image_name):
    return os.path.exists(os.path.join(self.path, image_name))

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
  def toparrows(self, bpm, ypos, pid):
    arrs = {}
    arrfx = {}
    for d in self.game.dirs:
      arrs[d] = TopArrow(bpm, d, ypos, pid, self.theme_data, self.game)
      arrfx[d] = ArrowFX(bpm, d, ypos, pid, self.theme_data, self.game)
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

  # allow access by instance['l']
  def __getitem__ (self,item):
    return getattr(self,item)

# Preload images/left offset for each arrow. 
class ScrollingArrow(object):
  def __init__ (self, theme, dir, color, left):
    self.dir = dir
    self.left = left
    self.image = theme.get_arrow("c", dir, color).convert()
    self.image.set_colorkey(self.image.get_at([0, 0]), RLEACCEL)

# FIXME: What follows probably doesn't belong here, but elsewhere. There's
# too much logic for it to be just theming data.

# Sprites for the top flashing arrows.
class TopArrow(pygame.sprite.Sprite):

  def __init__ (self, bpm, direction, ypos, pid, theme, game):
    pygame.sprite.Sprite.__init__(self)
    self.endpresstime = -1
    self.tick = toRealTime(bpm, 1);
    self.frame = 0
    self.oldframe = -1
    self.adder = 0
    self.direction = direction
    self.topimg = []

    # The 'n' state is the normal state for the top arrows. After being
    # pressed, they change to the 's' state images for a short time.
    for i in range(4):
      self.topimg.append(theme.get_arrow("n", self.direction, i).convert())
      self.topimg[i].set_colorkey(self.topimg[i].get_at((0, 0)), RLEACCEL)
    for i in range(4, 8):
      self.topimg.append(theme.get_arrow("s", self.direction, i).convert())
      self.topimg[i].set_colorkey(self.topimg[i].get_at((0, 0)), RLEACCEL)

    # FIXME: These used to be indented one more level - if stuff breaks,
    # that's why. FIXME
    self.image = self.topimg[0]
    self.rect = self.image.get_rect()
    self.rect.top = ypos
    self.rect.left = (game.left_off(pid) + game.player_offset * pid +
                      game.dirs.index(direction) * game.width)

  # The arrow was pressed, so we have to change it for some time (s state).
  def stepped(self, modifier, time):
    if modifier: self.adder = 4
    else: self.adder = 0
    self.endpresstime = time + 0.2 # Number of seconds to change it.

  def update(self, time):
    if time > self.endpresstime: self.adder = 0

    self.keyf = int(time / (self.tick / 2)) % 8
    if self.keyf > 3: self.keyf = 3
    self.frame = self.adder + self.keyf

    if self.frame != self.oldframe:
      self.image = self.topimg[self.frame]
      self.oldframe = self.frame

class ArrowFX(pygame.sprite.Sprite):
  def __init__ (self, bpm, direction, ypos, pid, theme, game):
    pygame.sprite.Sprite.__init__(self)
    self.presstime = -1000000
    self.tick = toRealTime(bpm, 1);
    self.centery = ypos + game.width / 2
    self.centerx = (game.left_off(pid) +
                    game.dirs.index(direction) * game.width + game.width / 2)
    self.pid = pid

    self.baseimg = theme.get_arrow("n", direction, 3).convert()
    self.tintimg = pygame.Surface(self.baseimg.get_size())

    self.blackbox = pygame.surface.Surface([game.width] * 2)
    self.blackbox.set_colorkey(0)
    self.image = self.blackbox
    self.rect = self.image.get_rect()
    self.displaying = 1
    self.direction = 1
    self.holdtype = 0

    style = mainconfig['explodestyle']
    self.rotating, self.scaling = style & 1, style & 2
    
  def holding(self, yesorno):
    self.holdtype = yesorno
  
  def stepped(self, time, tinttype):
    self.presstime = time
    self.tintimg = pygame.Surface(self.baseimg.get_size(), 0, 16)
    self.tintimg.blit(self.baseimg, (0,0))
    tinter = pygame.surface.Surface(self.baseimg.get_size())
    if tinttype == 'MARVELOUS':
      tinter.fill((255,255,255))
    elif tinttype == 'PERFECT':
      tinter.fill((255,255,0))
    elif tinttype == 'GREAT':
      tinter.fill((0,255,0))
    tinter.set_alpha(127)
    self.tintimg.blit(tinter,(0,0))
    self.tintimg.set_colorkey(self.tintimg.get_at((0,0)))
    self.tintimg = self.tintimg.convert()
    if self.direction == 1: self.direction = -1
    else: self.direction = 1

  def update(self, time, combo):
    steptimediff = time - self.presstime
    if (steptimediff < 0.2) or self.holdtype:
      self.displaying = 1
      self.image = self.tintimg
      if self.scaling:
        if self.holdtype:
          scale = 1.54
        else:
          scale = 1.0 + (steptimediff * 4.0) * (1.0+(combo/256.0))
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
