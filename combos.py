# Combo counting.

import pygame

from listener import Listener
from constants import *

class AbstractCombo(Listener, pygame.sprite.Sprite):

  def __init__(self, playernum, game):
    pygame.sprite.Sprite.__init__(self)
    self.sticky = mainconfig['stickycombo']
    self.lowcombo = mainconfig['lowestcombo']
    self.combo = 0
    self.laststep = 0
    self.centerx = game.sprite_center + (game.player_offset * playernum)
    self.top = 320
    
    fonts = []
    for x in range(11, 0, -1):
      fonts.append(pygame.font.Font(None, 28+int(x*1.82)))

    self.words = []
    for f in fonts:
      render = []
      for w in ('0','1','2','3','4','5','6','7','8','9','x COMBO'):
        img1 = f.render(w, 1, (16, 16, 16))
        img2 = f.render(w, 1, (224, 224, 224))
        img3 = pygame.Surface(img1.get_size())
        img3.blit(img1, (-2, 2))
        img3.blit(img1, (2, -2))
        img3.blit(img2, (0, 0))
        img3.set_colorkey(img3.get_at((0, 0)), RLEACCEL)
        render.append(img3)
      self.words.append(render)
    self.space = pygame.surface.Surface([0, 0])
    self.image = self.space

  def update(self, curtime):
    self.laststep = min(curtime, self.laststep)
    steptimediff = curtime - self.laststep

    if steptimediff < 0.36 or self.sticky:
      self.drawcount = self.combo
      drawsize = min(int(steptimediff*50), len(self.words)-1)
      if drawsize < 0: drawsize = 0
    else:
      self.drawcount = 0

    if self.drawcount >= self.lowcombo:
      render = self.words[drawsize]
      width = render[-1].get_width()
      thousands = self.drawcount /1000
      hundreds = self.drawcount / 100
      tens = self.drawcount / 10
      ones = self.drawcount % 10
      if thousands:
        thousands = render[thousands%10]
        width += thousands.get_width()      
      if hundreds:
        hundreds = render[hundreds%10]
        width += hundreds.get_width()
      if tens:
        tens = render[tens%10]
        width += tens.get_width()
      ones = render[ones]
      width += ones.get_width()
      height = render[-1].get_height()
      self.image = pygame.surface.Surface((width,height))
      self.image.set_colorkey(ones.get_at((0, 0)), RLEACCEL)
      left = 0		      
      if thousands:
        self.image.blit(thousands, (left,0))
        left+= thousands.get_width()
      if hundreds:
        self.image.blit(hundreds, (left, 0))
        left += hundreds.get_width()
      if tens:
        self.image.blit(tens, (left, 0))
        left += tens.get_width()
      self.image.blit(ones, (left, 0))
      left += ones.get_width()
      r = self.image.blit(render[-1], (left, 0))
    else :
      self.image = self.space

    self.rect = self.image.get_rect()
    self.rect.top = self.top
    self.rect.centerx = self.centerx

# Breaks the combo on anything not a marvelous, perfect, or great.
class NormalCombo(AbstractCombo):
  def stepped(self, pid, dir, curtime, rating, combo):
    if rating is None: return
    self.laststep = curtime
    self.combo += { "V": 1, "P": 1, "G": 1 }.get(rating, -self.combo)

# Breaks the combo on anything less than a great, but also doesn't
# increase it for great.
class OniCombo(AbstractCombo):
  def stepped(self, pid, dir, curtime, rating, combo):
    if rating is None: return
    self.laststep = curtime
    self.combo += { "V": 1, "P": 1, "G": 0 }.get(rating, -self.combo)

# Pump It Up-style combo; okays add to your combo too.
class PumpCombo(AbstractCombo):
  def stepped(self, pid, dir, curtime, rating, combo):
    if rating is None: return
    self.laststep = curtime
    self.combo += { "V": 1, "P": 1, "G": 1, "O": 1 }.get(rating, -self.combo)

combos = [NormalCombo, OniCombo, PumpCombo]
combo_opt = [(0, "Normal"), (1, "Oni-style"), (2, "Pump It Up-style")]
