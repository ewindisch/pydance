#! /usr/bin/env python

# pydance - Dancing game written in Python

#import psyco
#psyco.jit()
#from psyco.classes import *

import pygame
from constants import *

from util import toRealTime
from announcer import Announcer
from player import Player
from spritelib import *

from pygame.sprite import RenderUpdates

import fontfx, menudriver, fileparsers, colors, gradescreen, steps, audio

import os, sys, random, operator, error, util, getopt, math

os.chdir(pyddr_path)

class BGmovie(pygame.sprite.Sprite):
  def __init__ (self, filename):
    pygame.sprite.Sprite.__init__(self)
    self.filename = filename
    self.image = pygame.surface.Surface((640,480))
    
    if filename and not os.path.isfile(filename):
      print "The movie file for this song is missing."
      self.filename = None
    
    if self.filename:
      self.movie = pygame.movie.Movie(filename)
      self.movie.set_display(self.image,[(0,0),(640,480)])
    else:
      self.image.set_alpha(0, RLEACCEL) 
    self.rect = self.image.get_rect()
    self.rect.top = 0
    self.rect.left = 0
    self.oldframe = -1
    self.changed = 0
    
  def resetchange(self):
    self.changed = 0

  def update(self,curtime):
    if self.filename:
      curframe = int((curtime * 29.97) )
      if self.oldframe != curframe:
        self.changed = 1
        self.movie.render_frame(curframe)
        self.oldframe = curframe

class Judge:
  def __init__ (self, bpm, holds, feet, stepcount, diff, lifebar):
    self.steps = {}
    self.actualtimes = {}
    self.tick = toRealTime(bpm, 0.16666666666666666)
    self.marvelous = self.perfect = self.great = self.ok = self.boo = self.miss = 0
    self.combo = self.bestcombo = self.broke = 0
    self.steppedtime = -1000
    self.recentsteps = [' ',' ',' ']
    self.early = self.late = self.ontime = 0
    self.totalcombos = 1
    self.bpm = bpm
    self.failed_out = False
    self.lifebar = lifebar
    self.diff = diff
    # DDR Extreme scoring
    scorecoeff = (1000000.0 * feet) / ((stepcount * (stepcount + 1.0)) / 2.0)
    self.score_coeff = int(scorecoeff) + 1
    self.score = 0
    self.dance_score = 6 * holds
    self.badholds = 0
    self.arrow_count = 0
    self.announcer = Announcer(mainconfig["djtheme"])
    self.holdsub = []
    for i in range(holds):
      self.holdsub.append(0)

  def munch(self, anotherjudge):
    self.marvelous += anotherjudge.marvelous
    self.perfect   += anotherjudge.perfect
    self.great     += anotherjudge.great
    self.ok        += anotherjudge.ok
    self.boo      += anotherjudge.boo
    self.miss      += anotherjudge.miss

    if self.bestcombo < anotherjudge.bestcombo:
      self.bestcombo = anotherjudge.bestcombo
    self.combo = anotherjudge.combo  
    self.totalcombos += anotherjudge.totalcombos
    self.dance_score += anotherjudge.dance_score

    self.badholds += anotherjudge.badholds
    for i in anotherjudge.holdsub:
      self.holdsub.append(i)
    
    self.score += anotherjudge.score
    self.early += anotherjudge.early
    self.late += anotherjudge.late
    self.ontime += anotherjudge.ontime
        
  def changebpm(self, bpm):
    if bpm >= 1:
      self.tick = toRealTime(bpm, 0.16666666666666666)
    self.bpm = bpm
        
  def numholds(self):
    return len(self.holdsub)
    
  def botchedhold(self,whichone):
    if self.holdsub[whichone] != -1:
      self.holdsub[whichone] = -1
      self.badholds += 1
      self.dance_score -= 6
      self.lifebar.broke_hold()
    
  def handle_key(self, dir, curtime):
    times = self.steps.keys()
    times.sort()
    etime = 0.0
    done = 0
    early = late = ontime = 0
    off = -1
    for i in range(len(times)):
      if (curtime - self.tick*12) < times[i] < (curtime + self.tick*12):
        if dir in self.steps[times[i]]:
          off = (curtime-times[i]) / self.tick
          if off < 1: self.early += 1
          elif off > 1: self.late += 1
          else: self.ontime += 1
          done = 1
          etime = times[i]
          self.steps[etime] = self.steps[etime].replace(dir, "")
          break

    text = ' '
    anncrange = (0, 100)
    off = abs(off)
    if done == 1:
      self.arrow_count += 1
      if off < 7:
        self.steppedtime = curtime
        self.combo += 1
        if self.combo % 100 == 0:
          self.announcer.say("combos", self.combo / 10)
        if self.combo > self.bestcombo:
          self.bestcombo = self.combo 

        if off <= 1:
          self.marvelous += 1
          self.score += 10 * self.score_coeff * self.arrow_count
          self.dance_score += 2
          self.lifebar.update_life("V")
          text = "MARVELOUS"
          anncrange = (80, 100)
        elif off <= 4:
          self.perfect += 1
          self.score += 9 * self.score_coeff * self.arrow_count
          self.dance_score += 2
          self.lifebar.update_life("P")
          text = "PERFECT"
          anncrange = (80, 100)
        else:
          self.great += 1
          self.score += 5 * self.score_coeff * self.arrow_count
          self.dance_score += 1
          self.lifebar.update_life("G")
          text = "GREAT"
          anncrange = (70, 94)

      else:
        self.steppedtime = curtime
        self.totalcombos += 1
        self.broke = 1
        self.combo = 0
        if off < 9:
          self.ok += 1
          self.lifebar.update_life("O")
          text = "OK"
          anncrange = (40, 69)
        else:
          self.boo += 1
          self.dance_score -= 4
          self.lifebar.update_life("B")
          text = "BOO"
          anncrange = (20, 39)

      if random.randrange(15) == 1: self.announcer.say('ingame', anncrange)

      self.recentsteps.insert(0, text)
      self.recentsteps.pop()

    return text, dir, etime


  def expire_arrows(self, time):
    self.times = self.steps.keys()
    self.times.sort()
    for k in range(len(self.times)):
      if (self.times[k] < time - self.tick*12) and self.steps[self.times[k]]:
        self.broke = 1
        self.combo = 0
        n = len(self.steps[self.times[k]]) 
        del self.steps[self.times[k]]
        for i in range(n):
          self.miss += 1
          self.recentsteps.insert(0, "MISS")
          self.lifebar.update_life("M")
          self.dance_score -= 8
          self.arrow_count += 1
          self.recentsteps.pop()
  
  def handle_arrow(self, key, etime):
      self.times = self.steps.keys()
      if etime in self.times:
        self.steps[etime] += key
      else:
        self.steps[etime] = key
        self.times = self.steps.keys()


  def grade(self):
    totalsteps = (self.marvelous + self.perfect + self.great + self.ok +
                  self.boo + self.miss)

    max_score = 2.0 * totalsteps + 6.0 * self.numholds()

    if self.failed_out == True: return "E"
    elif totalsteps == 0: return "?"
    elif self.dance_score / max_score >= 1.00: return "AAA"
    elif self.dance_score / max_score >= 0.93: return "AA"
    elif self.dance_score / max_score >= 0.80: return "A"
    elif self.dance_score / max_score >= 0.65: return "B"
    elif self.dance_score / max_score >= 0.45: return "C"
    else: return "D"

class ComboDisp(pygame.sprite.Sprite):
  def __init__(self,playernum):
    pygame.sprite.Sprite.__init__(self)
    self.sticky = mainconfig['stickycombo']
    self.lowcombo = mainconfig['lowestcombo']

    self.trect = 296 + (mainconfig['totaljudgings'] * 24)
    self.centerx = (320*playernum) + 160
    
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
        img3.set_colorkey(img3.get_at((0, 0)))
        render.append(img3)
      self.words.append(render)
    self.space = pygame.surface.Surface((0,0)) #make a blank image
    self.image = self.space
    self.rect = Rect(0,0,0,0)

  def update(self, xcombo, steptimediff):
    if steptimediff < 0.36 or self.sticky:
      self.drawcount = xcombo
      self.drawsize = min(int(steptimediff*50), len(self.words)-1)
      if self.drawsize < 0: self.drawsize = 0
    else:
      self.drawcount = 0
    if self.drawcount >= self.lowcombo:
      render = self.words[self.drawsize]
      width = render[-1].get_width()
      thousands = self.drawcount /1000
      hundreds = self.drawcount / 100
      tens = self.drawcount / 10
      ones = self.drawcount % 10
      #get width
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
      self.image.set_colorkey(ones.get_at((0, 0)))
      left = 0		      
      #render
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
      self.rect = self.image.get_rect()
      self.rect.top=self.trect
      self.rect.left=self.centerx - width/ 2
    else :
      self.image = self.space #display the blank image

class fpsDisp(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.oldtime = -10000000
        self.loops = 0
        self.image = pygame.surface.Surface((1,1))
        self.lowest = 1000
        self.highest = -1
        self.fpses = []

    def fpsavg(self):
      return reduce(operator.add,self.fpses[2:])/(len(self.fpses)-2)

    def update(self, time):
      self.loops += 1
      if (time - self.oldtime) > 1:
        text = repr(self.loops) + " loops/sec"
        self.image = FONTS[16].render(text,1,(160,160,160))
        self.rect = self.image.get_rect()
        self.image.set_colorkey(self.image.get_at((0,0)))
        self.rect.bottom = 480
        self.rect.right = 640

        if self.loops > self.highest:
          self.highest = self.loops
        if (self.loops < self.lowest) and len(self.fpses)>2:
          self.lowest = self.loops

        self.fpses.append(self.loops)
        self.oldtime = time
        self.loops = 0

class Blinky(pygame.sprite.Sprite):
  def __init__ (self, bpm):
    pygame.sprite.Sprite.__init__(self)
    self.tick = toRealTime(bpm, 1);
    self.frame = 0
    self.oldframe = -100
    self.topimg = []
    
    im = pygame.surface.Surface((48,40))
    im.fill((1,1,1))
    self.topimg.append(im.convert())
    self.topimg.append(im.convert())
    im.fill((255,255,255))

    for i in range(2):          
      self.topimg.append(im.convert())

    self.image = self.topimg[3]
    self.rect = self.image.get_rect()
    self.rect.top = 440
    self.rect.left = 592

  def update(self,time):
    self.frame = int(time / (self.tick / 2)) % 8
    if self.frame > 3:        self.frame = 3

    if self.frame != self.oldframe:
      self.image = self.topimg[self.frame]
      self.oldframe = self.frame

class JudgingDisp(pygame.sprite.Sprite):
    def __init__(self,playernum):
        pygame.sprite.Sprite.__init__(self)

        self.total = mainconfig['totaljudgings']
        self.sticky = mainconfig['stickyjudge']
        self.needsupdate = 1
        self.playernum = playernum
        self.stepped = 0
        self.oldzoom = -1
        
        # prerender the text for judging for a little speed boost
        tx = FONTS[48].size("MARVELOUS")[0]+4
        self.marvelous = fontfx.shadefade("MARVELOUS",48,4,(tx,40),(224,224,224))
        tx = FONTS[48].size("PERFECT")[0]+4
        self.perfect   = fontfx.shadefade("PERFECT"  ,48,4,(tx,40),(224,224, 32))
        tx = FONTS[48].size("GREAT")[0]+4
        self.great     = fontfx.shadefade("GREAT"    ,48,4,(tx,40),( 32,224, 32))
        tx = FONTS[48].size("OK")[0]+4
        self.ok        = fontfx.shadefade("OK"       ,48,4,(tx,40),( 32, 32,224))
        tx = FONTS[48].size("BOO")[0]+4
        self.boo      = fontfx.shadefade("BOO"      ,48,4,(tx,40),( 96, 64, 32))
        tx = FONTS[48].size("MISS")[0]+4
        self.miss      = fontfx.shadefade("MISS"     ,48,4,(tx,40),(224, 32, 32))
        self.space     = FONTS[48].render( " ",       1, (  0,   0,   0) )

        self.marvelous.set_colorkey(self.marvelous.get_at((0,0)),RLEACCEL)
        self.perfect.set_colorkey(self.perfect.get_at((0,0)),RLEACCEL)
        self.great.set_colorkey(self.great.get_at((0,0)),RLEACCEL)
        self.ok.set_colorkey(self.ok.get_at((0,0)),RLEACCEL)
        self.boo.set_colorkey(self.boo.get_at((0,0)),RLEACCEL)
        self.miss.set_colorkey(self.miss.get_at((0,0)),RLEACCEL)

        self.image = self.space
        
    def update(self, listnum, steptimediff, judgetype):
      if steptimediff < 0.5 or (judgetype == ('MISS' or ' ')):
        if   judgetype == "MARVELOUS":       self.image = self.marvelous
        elif judgetype == "PERFECT":         self.image = self.perfect
        elif judgetype == "GREAT":           self.image = self.great
        elif judgetype == "OK":              self.image = self.ok
        elif judgetype == "BOO":             self.image = self.boo
        elif judgetype == " ":               self.image = self.space
        elif judgetype == "MISS":            self.image = self.miss

        zoomzoom = steptimediff

        if zoomzoom != self.oldzoom:
          self.needsupdate = 1
          if (steptimediff > 0.36) and (self.sticky == 0) and self.stepped:
            self.image = self.space
            self.stepped = 0
          if listnum == 0:
            if steptimediff > 0.2:                zoomzoom = 0.2
            self.image = pygame.transform.rotozoom(self.image, 0, 1-(zoomzoom*2))
            self.stepped = 1
          else:
            self.image = pygame.transform.rotozoom(self.image, 0, 0.6)

      if self.needsupdate:
        self.rect = self.image.get_rect()
        self.image.set_colorkey(self.image.get_at((0,0)))
        self.rect.bottom = 320+(listnum*24)
        self.rect.centerx = 160+(self.playernum*320)
        self.needsupdate = 0

class TimeDisp(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.oldtime = "-1000"
        self.image = pygame.surface.Surface((1,1))
        self.rect = self.image.get_rect()
        self.rect.top = 25
        self.rect.centerx = 320
        self.blahmod = 0
        
    def update(self, time):
      nowtime = repr(time)[:repr(time).index('.')+3]
      if (nowtime != self.oldtime) and (self.blahmod > 1):
        self.image = FONTS[40].render(nowtime,1,(224,224,224))
        self.image.set_colorkey(self.image.get_at((0,0)),RLEACCEL)
        self.oldtime = nowtime
        self.rect = self.image.get_rect()
        self.rect.top = 25
        self.rect.centerx = 320
        self.blahmod = 0
      else:
        self.blahmod += 1

class ArrowSprite(CloneSprite):

  # Assist mode sound samples
  samples = {}
  for d in DIRECTIONS:
    samples[d] = pygame.mixer.Sound(os.path.join(sound_path,
                                                 "assist-" + d + ".ogg"))
  
  def __init__ (self, spr, curtime, endtime, player, song):
    CloneSprite.__init__(self, spr)
    self.endtime = endtime
    self.life  = endtime - curtime
    self.curalpha = -1
    self.dir = spr.fn[-7:-6]
    self.battle = song.battle

    if mainconfig['assist']: self.sample = ArrowSprite.samples[self.dir]
    else: self.sample = None

    if player.scrollstyle == 2:
      self.top = 236
      self.bottom = random.choice((748, -276))
      if self.top < self.bottom:
        self.suddenzone = 480 - int(64.0 * player.sudden)
        self.hiddenzone = 236 + int(64.0 * player.hidden)
      else:
        self.suddenzone = int(64.0 * player.sudden) 
        self.hiddenzone = 236 - int(64.0 * player.hidden)
    elif player.scrollstyle == 1:
      self.top = 384
      self.bottom = -128
      self.suddenzone = int(64.0 * player.sudden)
      self.hiddenzone = 384 - int(64.0 * player.hidden)
    else:
      self.top = 64
      self.bottom = 576
      self.suddenzone = 480 - int(64.0 * player.sudden)
      self.hiddenzone = 64 + int(64.0 * player.hidden)

    self.diff = self.top - self.bottom

    self.bimage = self.image
    self.arrowspin = player.spin
    self.arrowscale = player.scale
    self.speed = player.speed
    self.accel = player.accel

    self.goalcenterx = self.rect.centerx + 320 * player.pid
    if self.battle:
      self.rect.centerx += 146
      self.origcenterx = self.centerx = self.rect.centerx
    else: self.centerx = self.rect.centerx = self.goalcenterx

  def update (self, curtime, curbpm, lbct):
    if (self.sample) and (curtime >= self.endtime -0.0125):
      self.sample.play()
      self.sample = None

    if curtime > self.endtime + (240.0/curbpm):
      self.kill()
      return

    top = self.top

    beatsleft = 0

    if len(lbct) == 0:
      onebeat = float(60.0/curbpm) # == float(60000.0/curbpm)/1000
      doomtime = self.endtime - curtime
      beatsleft = float(doomtime / onebeat)
    else:
      oldbpmsub = [curtime, curbpm]
      for bpmsub in lbct:
        if bpmsub[0] <= self.endtime:
          onefbeat = float(60.0/oldbpmsub[1]) # == float(60000.0/curbpm)/1000
          bpmdoom = bpmsub[0] - oldbpmsub[0]
          beatsleft += float(bpmdoom / onefbeat)
          oldbpmsub = bpmsub
        else: break

      onefbeat = float(60000.0/oldbpmsub[1])/1000
      bpmdoom = self.endtime - oldbpmsub[0]
      beatsleft += float(bpmdoom / onefbeat)

    if self.accel == 1:
      p = min(1, max(0, -0.125 * (beatsleft * self.speed - 8)))
      speed = 3 * p * self.speed + self.speed * (1 - p)
    elif self.accel == 2:
      p = min(1, max(0, -0.125 * (beatsleft * self.speed - 8)))
      speed = p * self.speed / 2.0 + self.speed * (1 - p)
    else: speed = self.speed

    top = top - int(beatsleft / 8.0 * speed * self.diff)

    self.cimage = self.bimage
    
    self.rect = self.image.get_rect()
    if top > 480: top = 480
    self.rect.top = top
    
    if self.battle:
      pct = abs(float(self.rect.top - self.top) / self.diff)
      if pct > 4.5 / 6: self.rect.centerx = self.origcenterx
      elif pct > 2.5 / 6:
        p = (pct - 2.5/6) / (2.0 / 6)
        self.rect.centerx = (1 - p) * self.goalcenterx + p * self.origcenterx
      else: self.rect.centerx = self.goalcenterx
    else: self.rect.centerx = self.centerx

    if self.arrowscale != 1:
      arrscale = int(float((self.rect.top-64)/416.0)*64)
      arrscale = min(64, max(0, arrscale))
      if self.arrowscale > 1: # grow
      	arrscale = 64 - arrscale
      self.cimage = pygame.transform.scale(self.bimage, (arrscale, arrscale))
    
    if self.arrowspin:
      self.image = pygame.transform.rotate(self.cimage,(self.rect.top-64)/self.arrowspin)
    else:
      self.image = self.cimage

    alp = 256
    if self.top < self.bottom: 
      if self.rect.top > self.suddenzone:
        alp = 256 - 4 * (self.rect.top - self.suddenzone) / self.speed
      elif self.rect.top < self.hiddenzone:
        alp = 256 - 4 * (self.hiddenzone - self.rect.top) / self.speed
    else:
      if self.rect.top < self.suddenzone:
        alp = 256 - 4 * (self.suddenzone - self.rect.top) / self.speed
      elif self.rect.top > self.hiddenzone:
        alp = 256 - 4 * (self.rect.top - self.hiddenzone) / self.speed

    if alp > 256: alp = 256
    elif alp < 0: alp = 0

    if alp != self.image.get_alpha():  self.image.set_alpha(alp)

class HoldArrowSprite(CloneSprite):
  def __init__ (self, spr, curtime, times, player, song):
    CloneSprite.__init__(self, spr)
    self.timef1 = times[1]
    self.timef2 = times[2]
    self.timef = times[2]
    self.life  = times[2]-curtime
    self.battle = song.battle
    if player.scrollstyle == 2:
      self.top = 236
      self.bottom = random.choice((748, -276))
      if self.top < self.bottom:
        self.suddenzone = 480 - int(64.0 * player.sudden)
        self.hiddenzone = 236 + int(64.0 * player.hidden)
      else:
        self.suddenzone = 64 + int(64.0 * player.sudden) 
        self.hiddenzone = 300 - int(64.0 * player.hidden)
    elif player.scrollstyle == 1:
      self.top = 384
      self.bottom = -128
      self.suddenzone = 64 + int(64.0 * player.sudden)
      self.hiddenzone = 448 - int(64.0 * player.hidden)
    else:
      self.top = 64
      self.bottom = 576
      self.suddenzone = 480 - int(64.0 * player.sudden)
      self.hiddenzone = 64 + int(64.0 * player.hidden)

    self.diff = self.top - self.bottom
    self.curalpha = -1
    self.dir = spr.fn[-7:-6]
    self.playedsound = None
    if mainconfig['assist']:
      self.sample = pygame.mixer.Sound(os.path.join(sound_path, "assist-" + self.dir + ".ogg"))
    else:
      self.playedsound = 1
    self.r = 0
    self.broken = 1
    self.oimage = pygame.surface.Surface((64,32))
    self.oimage.blit(self.image,(0,-32))
    self.oimage.set_colorkey(self.oimage.get_at((0,0)))
    self.oimage2 = pygame.surface.Surface((64,32))
    self.oimage2.blit(self.image,(0,0))
    self.oimage2.set_colorkey(self.oimage.get_at((0,0)))
    self.bimage = pygame.surface.Surface((64,1))
    self.bimage.blit(self.image,(0,-31))

    self.arrowspin = player.spin
    self.arrowscale = player.scale
    self.speed = player.speed
    self.accel = player.accel
    
    self.goalcenterx = self.rect.centerx + 320 * player.pid
    if self.battle:
      self.rect.centerx += 146
      self.origcenterx = self.centerx = self.rect.centerx
    else: self.centerx = self.rect.centerx = self.goalcenterx

  def update(self,curtime,curbpm,lbct):
    if (self.playedsound is None) and (curtime >= self.timef1 -0.0125):
      self.sample.play()
      self.playedsound = 1

    if curtime > self.timef2:
      self.kill()
      return
      
    top = self.top
    bottom = self.top

    beatsleft_top = 0
    beatsleft_bottom = 0

    if len(lbct) == 0:
      onebeat = float(60.0/curbpm)
      doomtime = self.timef1 - curtime
      if self.broken == 0 and doomtime < 0: doomtime = 0
      beatsleft_top = float(doomtime / onebeat)

      doomtime = self.timef2 - curtime
      beatsleft_bottom = float(doomtime / onebeat)
    else:
      oldbpmsub = [curtime, curbpm]
      bpmbeats = 0
      for bpmsub in lbct:
        if bpmsub[0] <= self.timef1:
          onefbeat = float(60.0/oldbpmsub[1])
          bpmdoom = bpmsub[0] - oldbpmsub[0]
          beatsleft_top += float(bpmdoom / onefbeat)
          oldbpmsub = bpmsub
        else: break

      onefbeat = float(60.0/oldbpmsub[1])
      bpmdoom = self.timef1 - oldbpmsub[0]
      beatsleft_top += float(bpmdoom / onefbeat)

      oldbpmsub = [curtime, curbpm]
      for bpmsub in lbct:
        if bpmsub[0] <= self.timef2:
          onefbeat = float(60.0/oldbpmsub[1])
          bpmdoom = bpmsub[0] - oldbpmsub[0]
          beatsleft_bottom += float(bpmdoom / onefbeat)
          oldbpmsub = bpmsub
        else: break

      onefbeat = float(60.0/oldbpmsub[1])
      bpmdoom = self.timef2 - oldbpmsub[0]
      beatsleft_bottom += float(bpmdoom / onefbeat)

    if self.accel == 1:
      p = min(1, max(0, -0.125 * (beatsleft_top * self.speed - 8)))
      speed_top = 3 * p * self.speed + self.speed * (1 - p)
      p = min(1, max(0, -0.125 * (beatsleft_bottom * self.speed - 8)))
      speed_bottom = 3 * p * self.speed + self.speed * (1 - p)
    elif self.accel == 2:
      p = min(1, max(0, -0.125 * (beatsleft_top * self.speed - 8)))
      speed_top = p * self.speed / 2.0 + self.speed * (1 - p)
      p = min(1, max(0, -0.125 * (beatsleft_bottom * self.speed - 8)))
      speed_bottom = p * self.speed / 2.0 + self.speed * (1 - p)
    else: speed_top = speed_bottom = self.speed

    top = top - int(beatsleft_top / 8.0 * self.diff * speed_top)
    bottom = bottom - int(beatsleft_bottom / 8.0 * self.diff * speed_bottom)

    if bottom > 480: bottom = 480

    if self.top < self.bottom and bottom < 64:  bottom = 64
    self.rect.bottom = bottom
 
    if top > 480: top = 480
    if self.top < self.bottom and top < 64: top = 64

    if self.top < self.bottom: self.rect.top = top
    else: self.rect.top = bottom
    
    holdsize = abs(bottom - top)
    if holdsize < 0:
      holdsize = 0
    self.cimage = pygame.surface.Surface((64,holdsize+64))
    self.cimage.set_colorkey(self.cimage.get_at((0,0)))
    self.cimage.blit( pygame.transform.scale(self.bimage, (64,holdsize)), (0,32) )
    self.cimage.blit(self.oimage2,(0,0))
    self.cimage.blit(self.oimage,(0,holdsize+32))

    self.rect = self.image.get_rect()
    if top > 480: top = 480
    self.rect.top = top
    
    if self.battle:
      pct = abs(float(self.rect.top - self.top) / self.diff)
      if pct > 4.5 / 6: self.rect.centerx = self.origcenterx
      elif pct > 2.5 / 6:
        p = (pct - 2.5/6) / (2.0 / 6)
        self.rect.centerx = (1 - p) * self.goalcenterx + p * self.origcenterx
      else: self.rect.centerx = self.goalcenterx
    else: self.rect.centerx = self.centerx

    if self.arrowscale != 1:
      arrscale = int(float((self.rect.top-64)/416.0)*64)
      if self.arrowscale > 1: # grow
      	arrscale = 64 - arrscale
      self.cimage = pygame.transform.scale(self.bimage, (arrscale, arrscale))
    
    if self.arrowspin:
      self.image = pygame.transform.rotate(self.cimage,(self.rect.top-64)/self.arrowspin)
    else:
      self.image = self.cimage

    alp = 256
    if self.top < self.bottom: 
      if self.rect.top > self.suddenzone:
        alp = 256 - 4 * (self.rect.top - self.suddenzone) / self.speed
      elif self.rect.top < self.hiddenzone:
        alp = 256 - 4 * (self.hiddenzone - self.rect.top) / self.speed
    else:
      if self.rect.bottom < self.suddenzone:
        alp = 256 - 4 * (self.suddenzone - self.rect.bottom) / self.speed
      elif self.rect.bottom > self.hiddenzone:
        alp = 256 - 4 * (self.rect.bottom - self.hiddenzone) / self.speed

    if alp > 256: alp = 256
    elif alp < 0: alp = 0

    if self.broken and (curtime > self.timef1+(0.00025*(60000.0/curbpm))):
      alp /= 2

    if alp != self.image.get_alpha(): self.image.set_alpha(alp)

class ReadyGoSprite(pygame.sprite.Sprite):
  def __init__(self, time):
    pygame.sprite.Sprite.__init__(self)
    ready = os.path.join(pyddr_path, "images", "ready.png")
    go = os.path.join(pyddr_path, "images", "go.png")
    self.time = time
    self.ready = pygame.image.load(ready).convert()
    self.ready.set_colorkey(self.ready.get_at((0, 0)), RLEACCEL)
    self.go = pygame.image.load(go).convert()
    self.go.set_colorkey(self.go.get_at((0, 0)), RLEACCEL)
    self.pick_image(min(0, time))

  def update(self, cur_time):
    if cur_time > self.time: self.kill()
    elif self.alive(): self.pick_image(cur_time)

  def pick_image(self, cur_time):
    ttl = self.time - cur_time # time to live
    if ttl < 0.25:
      self.image = self.go
      alpha = ttl / 0.25
    elif ttl < 0.750:
      self.image = self.go
      alpha = 1
    elif ttl < 1.00:
      self.image = self.go
      alpha = (1 - ttl) / 0.25
    elif ttl < 1.5:
      self.image = self.ready
      alpha = (ttl - 1.0) / 0.5
    elif cur_time < 0.5:
      self.image = self.ready
      alpha = cur_time / 0.5
    else:
      self.image = self.ready
      alpha = 1

    self.image.set_alpha(int(256 * alpha))
    self.rect = self.image.get_rect()
    self.rect.center = (320, 240)
      
def SetDisplayMode(mainconfig):
  try:
    flags = HWSURFACE | DOUBLEBUF
    if osname == "macosx": flags = 0
    if mainconfig["vesacompat"]: flags = 0
    elif mainconfig["fullscreen"]: flags |= FULLSCREEN
    screen = pygame.display.set_mode((640, 480), flags, 16)
  except:
    print "Can't get a 16 bit display!" 
    sys.exit()
  return screen

def main():
  global screen

  print "pydance, by theGREENzebra (tgz@clickass.org)"
  print "Initialising.."

  # FIXME Debug mode has been broken for like, 4 releases, take it out

  # Search recursively for files
  fileList = []
  for dir in mainconfig["songdir"].split(os.pathsep):
    print "Searching", dir
    fileList += util.find(dir, ('*.step', '*.dance', '*.dwi', '*.sm')) # Python's matching SUCKS

  totalsongs = len(fileList)
  parsedsongs = 0
  songs = []

  screen = SetDisplayMode(mainconfig)
  
  pygame.display.set_caption('pydance ' + VERSION)
  pygame.mouse.set_visible(0)

  audio.load(os.path.join(sound_path, "menu.ogg"))
  audio.play(4, 0.0)

  background = BlankSprite(screen.get_size())

  pbar = fontfx.TextProgress(FONTS[60], "Found " + str(totalsongs) +
                             " files. Loading...", colors.WHITE, colors.BLACK)
  r = pbar.render(0).get_rect()
  r.center = (320, 240)
  for f in fileList:
    try: songs.append(fileparsers.SongItem(f, False))
    except None: print "Error loading " + f
    img = pbar.render(parsedsongs / totalsongs)
    pygame.display.update(screen.blit(img, r))
    parsedsongs += 100.0

  ev = event.poll()
  while ev[1] != E_PASS: ev = event.poll()

  if len(songs) < 1:
    error.ErrorMessage(screen,
                      ("You don't have any songs or step files. Check out",
                       "http://icculus.org/pyddr/get.php",
                       "and download some free ones."
                       " ", " ", " ",
                       "If you already have some, make sure they're in",
                       mainconfig["songdir"]))
    print "You don't have any songs. http://icculus.org/pyddr/get.php."
    sys.exit(1)

  menudriver.do(screen, (songs, screen, playSequence))
  audio.stop()
  pygame.display.quit()
  mainconfig.write(os.path.join(rc_path, "pydance.cfg"))

def playSequence(playlist, configs, songconf, playmode):
  global screen

  numplayers = len(configs)

  first = True

  players = []
  for playerID in range(numplayers):
    plr = Player(playerID, ComboDisp(playerID), configs[playerID], songconf)
    players.append(plr)

  for songfn, diff in playlist:
    current_song = fileparsers.SongItem(songfn)
    pygame.mixer.quit()
    prevscr = pygame.transform.scale(screen, (640,480))
    songdata = steps.SongData(current_song, songconf)

    for pid in range(len(players)):
      players[pid].set_song(steps.Steps(current_song, diff[pid], players[pid],
                                        songdata.lyricdisplay, playmode),
                                        Judge)

    print "Playing", songfn
    print songdata.title, "by", songdata.artist
  
    if dance(songdata, players, prevscr, first):
      break # Failed
    first = False

  judges = [player.judge for player in players]

  if mainconfig['grading']:
    grade = gradescreen.GradingScreen(judges)
    background = pygame.transform.scale(screen, (640,480))
    if grade.make_gradescreen(screen, background):
      grade.make_waitscreen(screen)

  return judges

def dance(song, players, prevscr, ready_go):
  global screen

  songFailed = False

  background = BlankSprite(screen.get_size())

  pygame.mixer.init()

  # render group, almost[?] every sprite that gets rendered
  rgroup = RenderUpdates()
  # text group, EG. judgings and combos
  tgroup =  RenderUpdates()  
  # special group for top arrows
  sgroup =  RenderUpdates()
  # special group for arrowfx
  fgroup =  RenderUpdates()
  
  # lyric display group
  lgroup = RenderUpdates()

  # background group
  bgroup = RenderUpdates()

  if song.movie != None:
    backmovie = BGmovie(song.movie)
    background.fill(colors.BLACK)
  else:
    backmovie = BGmovie(None)
    
  backimage = BGimage(song.background)

  ready_go_time = 100
  for player in players:
    ready_go_time = min(player.steps.ready, ready_go_time)
  rgs = ReadyGoSprite(ready_go_time)
  tgroup.add(rgs)

  if mainconfig['showbackground'] > 0:
    if backmovie.filename == None:
      bgkludge = pygame.image.load(song.background).convert()
      bgkrect = bgkludge.get_rect()
      if (bgkrect.size[0] == 320) and (bgkrect.size[1] == 240):
        bgkludge = pygame.transform.scale2x(bgkludge)
      else:
        bgkludge = pygame.transform.scale(bgkludge,(640,480))
      bgkludge.set_alpha(mainconfig['bgbrightness'], RLEACCEL)
      background.image = pygame.surface.Surface((640,480))
      background.image.blit(bgkludge,(0,0))
      backimage.add(bgroup)
      
      q = mainconfig['bgbrightness'] / 256.0
      for i in range(0, 101, 5):
        p = i / 100.0
        bgkludge.set_alpha(256 * p * q, RLEACCEL)
        prevscr.set_alpha(256 * (1 - p) * q, RLEACCEL)
        screen.fill(colors.BLACK)
        screen.blit(prevscr,(0,0))
        screen.blit(bgkludge,(0,0))
        pygame.display.flip()
        pygame.time.delay(1)
    else:
      background.fill(colors.BLACK)
      screen.fill(colors.BLACK)
      pygame.display.flip()
  else:
    background.fill(colors.BLACK)
    screen.fill(colors.BLACK)
    pygame.display.flip()

  for pid in range(len(players)):
    players[pid].score.add(tgroup)
    players[pid].lifebar.add(tgroup)
    players[pid].holdtext.add(tgroup)
    for i in range(mainconfig['totaljudgings']):
      pj = JudgingDisp(pid)
      players[pid].judging_list.append(pj)
      pj.add(tgroup)

  strobe = mainconfig["strobe"]
  if strobe:
    extbox = Blinky(song.bpm)
    extbox.add(tgroup)

  fpsdisplay = mainconfig["fpsdisplay"]
  if mainconfig['fpsdisplay']:
    fpstext = fpsDisp()
    timewatch = TimeDisp()
    tgroup.add(fpstext)
    tgroup.add(timewatch)

  if mainconfig['showlyrics']:
    lgroup.add(song.lyricdisplay.channels.values())

  showcombo = mainconfig['showcombo']
  if showcombo:
    for plr in players:
      tgroup.add(plr.combos)
  
  songtext = fontfx.zztext(song.title, 480,12)
  grptext = fontfx.zztext(song.artist, 160,12)

  songtext.zin()
  grptext.zin()

  tgroup.add((songtext, grptext))

  song.init()

  if song.crapout != 0:
    error.ErrorMessage(screen, ("The audio file for this song", song.filename,
                               "could not be found."))
    return False # The player didn't fail.

  screenshot = 0

  if mainconfig['assist']: audio.set_volume(0.6)
  else: audio.set_volume(1.0)

  song.play()
  for plr in players:
    plr.start_song()
    for arrowID in DIRECTIONS:
      if mainconfig['explodestyle'] > -1:
        plr.toparrfx[arrowID].add(fgroup)
      if not plr.dark:
        plr.toparr[arrowID].add(sgroup)
      
  while 1:
    if mainconfig['autofail']:
      songFailed = True
      for plr in players:
        if plr.lifebar.failed == 0:
          songFailed = False
          break
      if songFailed:
        song.kill()

    for plr in players: plr.get_next_events()

    if song.is_over(): break
    else: curtime = audio.get_pos()/1000.0

    key = []

    ev = event.poll()

    for i in range(len(players)):
      if (event.states[(i, E_START)] and event.states[(i, E_RIGHT)]):
        print "Holding right plus start quits pydance."
        sys.exit()
      elif (event.states[(i, E_START)] and event.states[(i, E_LEFT)]):
        ev = (0, E_QUIT)
        break
      else:
        pass

    while ev[1] != E_PASS:
      if ev[1] == E_QUIT: break
      elif ev[1] == E_FULLSCREEN:
        pygame.display.toggle_fullscreen()
        mainconfig["fullscreen"] ^= 1
      elif ev[1] == E_SCREENSHOT:
        screenshot = 1
      elif ev[1] == E_LEFT: key.append((ev[0], 'l'))
      elif ev[1] == E_RIGHT: key.append((ev[0], 'r'))
      elif ev[1] == E_UP: key.append((ev[0], 'u'))
      elif ev[1] == E_DOWN: key.append((ev[0], 'd'))

      ev = event.poll()

    if ev[1] == E_QUIT: return False
  
    for keyAction in key:
      playerID = keyAction[0]
      if playerID < len(players):
        keyPress = keyAction[1]
        players[playerID].toparr[keyPress].stepped(1, curtime+(players[playerID].steps.soffset))
        players[playerID].fx_data.append(players[playerID].judge.handle_key(keyPress, curtime) )

    # This maps the old holdkey system to the new event ID one
    # We should phase this out
    keymap_kludge = ({"u": E_UP, "d": E_DOWN, "l": E_LEFT, "r": E_RIGHT})

    for plr in players:
      for checkhold in DIRECTIONS:
        plr.toparrfx[checkhold].holding(0)
        currenthold = plr.should_hold(checkhold, curtime)
        dirID = DIRECTIONS.index(checkhold)
        if currenthold is not None:
          if event.states[(plr.pid, keymap_kludge[checkhold])]:
            if plr.judge.holdsub[plr.tempholding[dirID]] != -1:
              plr.toparrfx[checkhold].holding(1)
            plr.tempholding[dirID] = currenthold
          else:
            plr.judge.botchedhold(currenthold)
            plr.holdtext.fillin(curtime, dirID, "NG")
            botchdir, timef1, timef2 = plr.steps.holdinfo[currenthold]
            for spr in plr.arrow_group.sprites():
              try:
                if (spr.timef1 == timef1) and (DIRECTIONS.index(spr.dir) == dirID): spr.broken = 1
              except: pass
        else:
          if plr.tempholding[dirID] > -1:
            if plr.judge.holdsub[plr.tempholding[dirID]] != -1:
              plr.tempholding[dirID] = -1
              plr.holdtext.fillin(curtime,dirID,"OK")
    
      if plr.evt is not None:
        # handle events that are happening now
        events,nevents,curtime,bpm = plr.evt
        
        for ev in events:
          if ev.feet:
            for (dir,num) in zip(DIRECTIONS,ev.feet):
              if num & 1:
                plr.judge.handle_arrow(dir, ev.when)
         
        for ev in nevents:
          if ev.feet:
            for (dir,num) in zip(DIRECTIONS, ev.feet):
              dirstr = dir + repr(int(ev.color) % plr.colortype)
              groups = (plr.arrow_group, rgroup)
              if num & 1:
                if not (num & 2):
                  ArrowSprite(plr.theme.arrows[dirstr].c,
                              curtime, ev.when, plr, song).add(groups)

              if num & 2:
                holdindex = plr.steps.holdref.index((DIRECTIONS.index(dir),
                                                     ev.when))
                HoldArrowSprite(plr.theme.arrows[dirstr].c, curtime,
                                plr.steps.holdinfo[holdindex], plr, song).add(groups)

    for plr in players:
      if len(plr.steps.lastbpmchangetime) > 0:
        if (curtime >= plr.steps.lastbpmchangetime[0][0]):
          nbpm = plr.steps.lastbpmchangetime[0][1]
          plr.change_bpm(nbpm)
          #print "Last changed BPM at", plr.steps.lastbpmchangetime[0]
          plr.steps.lastbpmchangetime.pop(0)
     
    for plr in players: plr.check_sprites(curtime)

    if strobe:
      extbox.update(curtime+(players[0].steps.soffset))
    
    song.lyricdisplay.update(curtime)

    for plr in players: plr.combo_update(curtime)
        
    if backmovie.filename:
      backmovie.update(curtime)
      if backmovie.changed or (fpstext.fpsavg > 30):
        backmovie.resetchange()
#        screen.blit(background.image,(0,0))
        screen.blit(backmovie.image,(0,0))

    songtext.update()
    grptext.update()
    rgs.update(curtime)

    if fpsdisplay:
      fpstext.update(curtime)
      timewatch.update(curtime)

    # more than one display.update will cause flicker
    rectlist = sgroup.draw(screen) #rectlist = list of changed rectangles

    for plr in players:
      rectlist.extend( plr.arrow_group.draw(screen))
    
    rectlist.extend( fgroup.draw(screen))
    rectlist.extend( tgroup.draw(screen))
    rectlist.extend( lgroup.draw(screen))

    if not backmovie.filename: pygame.display.update(rectlist)
    else: pygame.display.update()

    if screenshot:
      pygame.image.save(pygame.transform.scale(screen, (640,480)),
                        os.path.join(rc_path, "screenshot.bmp"))
      screenshot = 0

    if not backmovie.filename:
      lgroup.clear(screen,background.image)
      tgroup.clear(screen,background.image)
      fgroup.clear(screen,background.image)
      for plr in players:
        plr.arrow_group.clear(screen,background.image)
      sgroup.clear(screen,background.image)

    if (curtime > players[0].steps.length - 1) and (songtext.zdir == 0) and (songtext.zoom > 0):
      songtext.zout()
      grptext.zout()

  try:
    print "LPS for this song was %d tops, %d on average, %d at worst." % (fpstext.highest, fpstext.fpsavg(), fpstext.lowest)
  except:
    pass
    
  return songFailed

if __name__ == '__main__': main()
