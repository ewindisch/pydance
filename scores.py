# Scoring algorithms.

# Data on many algorithms taken from www.aaroninjapan.com/ddr2.html

import colors, pygame, fontfx

from constants import *

class AbstractScore(pygame.sprite.Sprite):
  def __init__(self, pid, text, game):
    pygame.sprite.Sprite.__init__(self)
    self.score = 0
    self.set_text(text)
    self.image = pygame.surface.Surface((160, 48))
    self.rect = self.image.get_rect()
    self.rect.bottom = 484
    self.rect.centerx = game.sprite_center + pid * game.player_offset

  def set_text(self, text):
    tx = FONTS[28].size(text)[0] + 2
    txt = fontfx.embfade(text, 28, 2, (tx, 24), colors.color["gray"])
    basemode = pygame.transform.scale(txt, (tx, 48))
    self.baseimage = pygame.surface.Surface((128, 48))
    self.baseimage.blit(basemode, (64 - (tx / 2), 0))
    self.oldscore = -1 # Force a refresh

  def set_song(self, text, count, feet):
    self.set_text(text)

  def update(self):
    if self.score != self.oldscore:
      self.image.blit(self.baseimage, (0,0))
      scoretext = FONTS[28].render(str(int(self.score)), 1, (192,192,192))
      self.image.blit(scoretext, (64 - (scoretext.get_rect().size[0] / 2), 13))
      self.image.set_colorkey(self.image.get_at((0, 0)), RLEACCEL)
      self.oldscore = self.score

  def stepped(self, cur_time, rating, combo): pass

  def broke_hold(self): pass

  def ok_hold(self): pass

# This is pydance's custom scoring algorithm. It's designed to make
# scores "fair" between different difficulty modes, and is similar
# to DDR 3rd Mix's in that respect.

# Each song has a maximum score of 50e6, 40e6 from steps, 10e6 from combos.
# Steps are scored between 4 and 0 based only on their rating; combos
# are scored by a monotonically increasing function.
class PydanceScore(AbstractScore):
  def set_song(self, text, count, feet):
    AbstractScore.set_song(self, text, count, feet)
    if count == 0: count = 1 # Don't crash on empty songs.

    score_coeff = 10000000.0 / count
    self.combo_coeff = 10000000.0 / (count * (count + 1) / 2.0)
    self.inc = { "V": 4 * score_coeff, "P": 3.5 * score_coeff,
                 "G": 2.5 * score_coeff, "O": 0.5 * score_coeff }

  def stepped(self, cur_time, rating, combo):
    self.score += self.inc.get(rating, 0)
    self.score += combo * self.combo_coeff

# "DDR 1st Mix's scoring system. For every step:
# Multiplier (M) = (# of steps in your current combo / 4) rounded down
# "Good" step = M * 100 (and this ends your combo)
# "Great" step = M * M * 100
# "Perfect" step = M * M * 300"
class FirstScore(AbstractScore):
  def __init__(self, pid, text, game):
    AbstractScore.__init__(self, pid, text, game)
    self.combo = 0

  def stepped(self, cur_time, rating, combo):
    if self.combo == combo == 0: return # No points when combo is 0.

    self.combo += 1

    if combo == 0: # The rating can't be great or better, since combo == 0.
      if rating == "O": self.score += self.combo / 4 * 100
      self.combo = 0
    else:
      if rating == "G":
        self.score += self.combo * self.combo / 4 * 100
      else: # Must be a better-than-great.
        self.score += self.combo * self.combo / 4 * 300

# "First, we need to calculate the base step score P:

#       Let N = Total number of steps in song
#       P = 1,000,000 / (N * (N + 1) / 2) 

# From this, if the step is "Perfect", multiply P by 10.
# Likewise, if the step is "Great", multiply P by 5.
# Finally, a "Good" is just the value of P.

# Let us call this new value S

# If this is the 2nd step, multiply S by 2,
# If this is the 3rd step, multiply S by 3,
# and so on... "
class ThirdScore(AbstractScore):
  def set_song(self, text, count, feet):
    AbstractScore.set_song(self, text, count, feet)
    if count == 0: count = 1
    self.arrow = 0

    p = 1000000.0 / (count * (count + 1) / 2)
    self.inc = { "V": p * 10, "P": p * 10, "G": p * 5, "O": p }

  def stepped(self, curtime, rating, combo):
    self.arrow += 1
    self.score += self.inc.get(rating, 0) * self.arrow

# Very simple; RTFS.
class FourthScore(AbstractScore):
  def stepped(self, cur_time, rating, combo):
    base = {"V": 777, "P": 777, "G": 555 }
    self.score += base.get(rating, 0) + combo * 333

# We don't calculate the grade bonus at the end.
class FifthScore(AbstractScore):
  def set_song(self, text, count, feet):
    AbstractScore.set_song(self, text, count, feet)
    self.arrow = 0
    s = 500000.0 * (feet + 1) / float((count * (count + 1)) / 2)
    self.inc = { "V": 10 * s, "P": 10 * s, "G": 5 * s }

  def stepped(self, cur_time, rating, combo):
    self.arrow += 1
    self.score += self.inc.get(rating, 0) * self.arrow

# "A single step's points are calculated as follows:
#   Let p = score multiplier (Marv. = 10, Perfect = 9, Great = 5, other = 0)
#    N = total number of steps and freeze steps
#    n = number of the current step or freeze step (varies from 1 to N)
#    B = Base value of the song (1,000,000 X the number of feet difficulty)
# So, the score for one step is:
#       one_step_score = p * (B/S) * n
# Where S = The sum of all integers from 1 to N."

# The special scoring mode for Nonstop is not implemented.

# In pydance's implementation, jumps are counted as two arrows; in
# 8rd, they aren't.
class ExtremeScore(AbstractScore):
  def set_song(self, text, count, feet):
    AbstractScore.set_song(self, text, count, feet)
    if count == 0: count = 1 # Don't crash on empty songs.

    self.arrow = 0
    score_coeff = (1000000.0 * feet) / ((count * (count + 1.0)) / 2.0)
    self.inc = { "V": 10 * score_coeff, "P": 9 * score_coeff,
                 "G": 5 * score_coeff }

  def stepped(self, cur_time, rating, combo):
    self.arrow += 1
    self.score += self.inc.get(rating, 0) * self.arrow

scores = [PydanceScore, FirstScore, ThirdScore, FourthScore,
          FifthScore, ExtremeScore]
scores_opt = [(0, "pydance"), (1, "1st"), (2, "3rd"), (3, "4th"),
              (4, "5th"), (5, "8th")]
