import os
import math
import pygame
import colors
import fontfx
import random

from constants import *

# Make an outlined box. The size is given without the 4 pixel border.
# This usually gets alphaed before stuff gets put in it.
def make_box(color = [111, 255, 148], size = [130, 40]):
  s = pygame.Surface([size[0] + 8, size[1] + 8], SRCALPHA, 32)
  s.fill(color + [100])
  r = s.get_rect()
  for c in [[255, 255, 255, 170], [212, 217, 255, 170],
            [255, 252, 255, 170], [104, 104, 104, 170]]:
    pygame.draw.rect(s, c, r, 1)
    r.width -= 2
    r.height -= 2
    r.top += 1
    r.left += 1
  return s

class TextDisplay(pygame.sprite.Sprite):
  def __init__(self, font, size, midleft, str = " "):
    pygame.sprite.Sprite.__init__(self)
    self._text = " "
    self._font = font
    self._size = size
    self._midleft = midleft
    self._render()

  def _render(self):
    self._needs_update = False
    font = fontfx.max_size(self._text, self._size[0], self._font)
    img = fontfx.shadow(self._text, font, 1, [255, 255, 255], [0, 0, 0])
    self.image = img
    self.rect = self.image.get_rect()
    self.rect.midleft = self._midleft

  def set_text(self, text):
    self._text = text
    self._needs_update = True

  def update(self, time):
    if self._needs_update: self._render()

# Crossfading help text along the top of the screen.
class HelpText(pygame.sprite.Sprite):
  def __init__(self, strs, color, bgcolor, font, center):
    pygame.sprite.Sprite.__init__(self)
    self._idx = -1
    self._strings = [(s, font.render(s, True, color, bgcolor).convert())
                     for s in strs]
    self._center = center
    self._start = pygame.time.get_ticks()
    self._fade = -1
    self._bgcolor = bgcolor
    self._end = -1
    self.update(self._start)

  def update(self, time):
    time -= self._start
    # Time to switch to the next bit of text.
    if time > self._end:
      self._idx = (self._idx + 1) % len(self._strings)
      self.image = self._strings[self._idx][1]
      self.image.set_alpha(255)
      self._fade = time + 100 * len(self._strings[self._idx][0])
      self._end = self._fade + 750

    # There's a .75 second delay during which text crossfades.
    elif time > self._fade:
      p = (time - self._fade) / 750.0
      s1 = self._strings[self._idx][1]
      s1.set_colorkey(s1.get_at([0, 0]))
      s1.set_alpha(int(255 * (1 - p)))
      
      i = (self._idx + 1) % len(self._strings)
      s2 = self._strings[i][1]
      s2.set_colorkey(s2.get_at([0, 0]))
      s2.set_alpha(int(255 * p))

      h = max(s1.get_height(), s2.get_height())
      w = max(s1.get_width(), s2.get_width())
      self.image = pygame.Surface([w, h], 0, 32)
      self.image.fill(self._bgcolor)
      self.image.set_colorkey(self.image.get_at([0, 0]))
      r = s1.get_rect()
      r.center = self.image.get_rect().center
      self.image.blit(s1, r)
      r = s2.get_rect()
      r.center = self.image.get_rect().center
      self.image.blit(s2, r)

    self.image.set_colorkey(self.image.get_at([0, 0]))
    self.rect = self.image.get_rect()
    self.rect.center = self._center

# Flashy indicator for showing current menu position.
class ActiveIndicator(pygame.sprite.Sprite):
  def __init__(self, topleft):
    pygame.sprite.Sprite.__init__(self)
    self.image = pygame.image.load(os.path.join(image_path, "indicator.png"))
    self.image.convert()
    self.image.set_colorkey(self.image.get_at([0, 0]))
    self.rect = self.image.get_rect()
    self.rect.topleft = topleft

  def move(self, pt): self.rect.topleft = pt

  def update(self, time):
    self.image.set_alpha(int(255 * (0.3 + (math.sin(time / 720.0)**2 / 3.0))))

# Box to indicate the current difficulty level.
class DifficultyBox(pygame.sprite.Sprite):
  def __init__(self, pid, numplayers):
    pygame.sprite.Sprite.__init__(self)
    self._topleft = [19 + (233 * pid), 414]

  def set(self, diff, color, feet, grade):
    f = pygame.font.Font(None, 24)
    self.image = make_box(color)

    t1 = fontfx.shadow(diff, f, 1, [255, 255, 255], [0, 0, 0])
    r1 = t1.get_rect()
    r1.center = [self.image.get_width()/2, 14]

    t2 = fontfx.shadow("x%d - %s" % (feet, grade), f, 1,
                       [255, 255, 255],[0, 0, 0])
    r2 = t2.get_rect()
    r2.center = [self.image.get_width()/2, 34]

    self.image.blit(t1, r1)
    self.image.blit(t2, r2)

    self.rect = self.image.get_rect()
    self.rect.topleft = self._topleft
    self.image.set_alpha(140)

class ListBox(pygame.sprite.Sprite):
  def __init__(self, font, color, spacing, count, width, topleft):
    pygame.sprite.Sprite.__init__(self)
    self._h = spacing
    self._count = count
    self._w = width
    self._color = color
    self._font = font
    self._topleft = topleft

    # animation
    self._start = pygame.time.get_ticks()
    self._animate = -1
    self._animate_dir = 0
    self._offset = 0
            
    self.set_items([""])
    self._needs_update = True
    self._render()

  def set_items(self, items):
    c2 = [c / 8 for c in self._color]
    self._items = []

    for i in items:
      txt = fontfx.render_outer(i, self._w - 7, self._font)
      img = fontfx.shadow(txt, self._font, 1, self._color, c2)
      self._items.append(img)
    self._idx = self._oldidx = 0 - self._count / 2 # Reset index to 0.
    self._needs_update = True

  def set_index(self, idx):
    self._oldidx = self._idx
    self._idx = (idx - self._count / 2)
    self._needs_update = True

  def update(self, time):
    time -= self._start

    # animation disabled if there are only 2 items; there's no way to
    # tell if we should animate up or down
    if self._idx != self._oldidx and len(self._items) > 2:
      self._animate = time + 100

      if self._idx < 0 and self._oldidx > 0:
        # we wrapped around from the bottom to the top; animate items up
        self._animate_dir = 1
      elif self._idx > 0 and self._oldidx < 0:
        # we wrapped around from the bottom to the top; animate items down
      	self._animate_dir = -1
      elif self._idx < self._oldidx:
        # new index < old index; animate items down
        self._animate_dir = -1
      else:
        # old index < new index; animate items up
        self._animate_dir = 1
    
    if self._animate > time:
      self._offset = (self._animate - time) / 100.0 # 0.1 seconds
      self._offset *= self._h	                    # percentage of height
      self._offset *= self._animate_dir	            # 1 for up, -1 for down
      self._needs_update = True
    elif self._offset != 0:
      self._offset = 0
      self._needs_update = True
    
    if self._needs_update:
      self._oldidx = self._idx
      self._needs_update = False
      self._render()

  def _render(self):
    self.image = pygame.Surface([self._w, self._h * self._count],
                                SRCALPHA, 32)
    self.image.fill([0, 0, 0, 0])
    for i, y in zip(range(self._count + 2),
                    range(-self._h / 2, self._h * (self._count + 1), self._h)):
      idx = (self._idx + i - 1) % len(self._items)
      t = self._items[idx]
      r = t.get_rect()
      r.centery = y + self._offset
      r.left = 5
      self.image.blit(t, r)
    self.rect = self.image.get_rect()
    self.rect.topleft = self._topleft

class BannerDisplay(pygame.sprite.Sprite):
  def __init__(self, size, center):
    pygame.sprite.Sprite.__init__(self)
    self.isfolder = False
    self._center = center
    self._clip = None
    self._color = [255, 0, 255]
    self._next_update = -1
    self._delta = 5
    self._idx = 1

  def set_song(self, song):
    c1, c2 = [255, 255, 255], [30, 30, 30]
    self._next_update = -2 # Magic value

    song.render()

    self._title = fontfx.shadow(song.info["title"],
                                fontfx.max_size(song.info["title"], 340, 60),
                                1, c1, c2)
    self._r_t = self._title.get_rect()
    self._r_t.center = [179, 240]
    self._artist = fontfx.shadow(song.info["artist"],
                                 fontfx.max_size(song.info["artist"], 250, 40),
                                 1, c1, c2)

    self._r_a = self._artist.get_rect()
    self._r_a.center = [179, 320]

    if song.info["subtitle"]:
      self._subtitle = fontfx.shadow(song.info["subtitle"],
                                     fontfx.max_size(song.info["subtitle"],
                                                     300, 24),

                                     1, c1, c2)
      self._r_s = self._subtitle.get_rect()
      self._r_s.center = [179, 270]
    else: self._subtitle = None
    self._clip = song.clip
    self._banner = song.banner
    self._r_b = self._banner.get_rect()
    self._r_b.center = (179, 100)

  def _render(self):
    self.image = make_box(self._color, [350, 350])
    self.image.blit(self._banner, self._r_b)
    self.image.set_clip(None)
    
    self.image.blit(self._title, self._r_t)
    self.image.blit(self._artist, self._r_a)
    if self._subtitle: self.image.blit(self._subtitle, self._r_s)

    self.rect = self.image.get_rect()
    self.rect.center = self._center

  def update(self, time):
    if self._next_update == -2:
      self._next_update = time + 300
      self._render()
    elif time > self._next_update:
      self._next_update = time + 300
      if ((self._delta > 0 and self._color[self._idx] == 255) or
          (self._delta < 0 and self._color[self._idx] == 0)):
        self._idx = random.choice([i for i in range(3) if i != self._idx])
        if self._color[self._idx]: self._delta = -3
        else: self._delta = 3
      self._color[self._idx] += self._delta
      self._render()

class WrapTextDisplay(pygame.sprite.Sprite):
  def __init__(self, font, size, topleft, str = " "):
    pygame.sprite.Sprite.__init__(self)
    self._text = " "
    self._font = font
    self._size = size
    self._topleft = topleft
    self._render()

  def _render(self):
    self._needs_update = False
    lines = []
    words = self._text.split()
    start = 0
    for i in range(len(words)):
      if self._font.size(" ".join(words[start:i + 1]))[0] > self._size[0]:
        t = self._font.render(" ".join(words[start:i]), True, [255, 255, 255])
        lines.append(t)
        start = i
    t = self._font.render(" ".join(words[start:]), True, [255, 255, 255])
    lines.append(t)        

    self.image = pygame.Surface(self._size, SRCALPHA, 32)
    self.image.fill([0, 0, 0, 0])
    for i in range(len(lines)):
      self.image.blit(lines[i], [0, i * self._font.get_linesize()])
    self.rect = self.image.get_rect()
    self.rect.topleft = self._topleft

  def set_text(self, text):
    self._text = text
    self._needs_update = True

  def update(self, time):
    if self._needs_update: self._render()

class InterfaceWindow(object):
  def __init__(self, screen, bg_fn):
    self._screen = screen
    self._bg = pygame.image.load(os.path.join(image_path, bg_fn)).convert()
    self._sprites = pygame.sprite.RenderUpdates()
    self._screen.blit(self._bg, [0, 0])
    self._callbacks = {} #FIXME: TODO

  def update(self):
    self._sprites.update(pygame.time.get_ticks())
    pygame.display.update(self._sprites.draw(self._screen))
    self._sprites.clear(self._screen, self._bg)
    
