# Scoring algorithms.

# Data on many algorithms taken from www.aaroninjapan.com/ddr2.html

# N = Number of steps in the song.
# F = Feet rating of the song.
# S(N) = N * (N + 1) / 2.
# n = Current step number.
# L(r) = Lookup function for the current step's rating.
# C = Current combo count.
# V(n) = The point value of the nth step.

import colors, pygame, fontfx

from listener import Listener
from constants import *

class AbstractScore(Listener, pygame.sprite.Sprite):
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

  def set_song(self, bpm, difficulty, count, holds, feet):
    self.set_text(difficulty)

  def update(self):
    if self.score != self.oldscore:
      self.image.blit(self.baseimage, (0,0))
      scoretext = FONTS[28].render(str(int(self.score)), 1, (192,192,192))
      self.image.blit(scoretext, (64 - (scoretext.get_rect().size[0] / 2), 13))
      self.image.set_colorkey(self.image.get_at((0, 0)), RLEACCEL)
      self.oldscore = self.score

# This is pydance's custom scoring algorithm. It's designed to make
# scores "fair" between different difficulty modes, and is similar
# to DDR 3rd Mix's in that respect.

# L(V) = 4, L(P) = 3.5, L(G) = 2.5, L(O) = 0.5
# V(n) = L(r) * 10,000,000 / N + 10,000,000 / S(N) * C
class PydanceScore(AbstractScore):
  def set_song(self, bpm, text, count, hold, feet):
    AbstractScore.set_song(self, bpm, text, count, hold, feet)
    if count == 0: count = 1 # Don't crash on empty songs.

    score_coeff = 10000000.0 / count
    self.combo_coeff = 10000000.0 / (count * (count + 1) / 2.0)
    self.inc = { "V": 4 * score_coeff, "P": 3.5 * score_coeff,
                 "G": 2.5 * score_coeff, "O": 0.5 * score_coeff }

  def stepped(self, cur_time, rating, combo):
    self.score += self.inc.get(rating, 0)
    self.score += combo * self.combo_coeff

# M = floor(C / 4)
# L(V) = L(P) = M * 300, L(G) = M * 100, L(O) = 100
# V(n) = M * L(r)
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

# L(V) = L(P) = 10, L(G) = 5, L(O) = 1
# V(n) = L(r) * 1,000,000 / S(N) * n
class ThirdScore(AbstractScore):
  def set_song(self, bpm, text, count, hold, feet):
    AbstractScore.set_song(self, bpm, text, count, hold, feet)
    if count == 0: count = 1
    self.arrow = 0

    p = 1000000.0 / (count * (count + 1) / 2)
    self.inc = { "V": p * 10, "P": p * 10, "G": p * 5, "O": p }

  def stepped(self, curtime, rating, combo):
    self.arrow += 1
    self.score += self.inc.get(rating, 0) * self.arrow

# L(V) = L(P) = 777, L(G) = 555
# V(n) = L(r) + C * 333
class FourthScore(AbstractScore):
  def stepped(self, cur_time, rating, combo):
    base = {"V": 777, "P": 777, "G": 555 }
    self.score += base.get(rating, 0) + combo * 333

# L(V) = L(P) = 10, L(G) = 5
# V(n) = L(r) * 500,000 * (F + 1) / S(N) * n

# The bonus for your combo or final grade is not implemented yet.
class FifthScore(AbstractScore):
  def set_song(self, bpm, text, count, hold, feet):
    AbstractScore.set_song(self, bpm, text, count, hold, feet)
    self.arrow = 0
    s = 500000.0 * (feet + 1) / float((count * (count + 1)) / 2)
    self.inc = { "V": 10 * s, "P": 10 * s, "G": 5 * s }

  def stepped(self, cur_time, rating, combo):
    self.arrow += 1
    self.score += self.inc.get(rating, 0) * self.arrow

# L(V) = 10, L(P) = 9, L(G) = 5
# V(n) = L(r) * 1,000,000 * F / S(N) * n

# The special scoring mode for Nonstop is not implemented.

# In pydance's implementation, jumps are counted as two arrows; in
# 8rd, they aren't.
class ExtremeScore(AbstractScore):
  def set_song(self, bpm, text, count, hold, feet):
    AbstractScore.set_song(self, bpm, text, count, hold, feet)
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
score_opt = [(0, "pydance"), (1, "1st"), (2, "3rd"), (3, "4th"),
              (4, "5th"), (5, "8th")]
