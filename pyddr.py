#! /usr/bin/env python

# pyDDR - DDR clone written in Python
# I know the dependencies suck, but in terms of programming so do I.

#import psyco
#psyco.jit()
#from psyco.classes import *

import pygame
from constants import *

from announcer import Announcer
from config import Config
from gfxtheme import GFXTheme
from player import Player
from spritelib import *

import fontfx, menudriver, fileparsers, colors, gradescreen, steps

import os, sys, glob, random, fnmatch, types, operator, copy, string

from stat import *

os.chdir(pyddr_path)

USE_GL = 0

if USE_GL:

  from spritegl import SpriteGL, GroupGL, gl_display_get_surface, gl_display_set_mode

  pygame.sprite.Sprite = SpriteGL
  pygame.sprite.Group = GroupGL
  pygame.sprite.RenderPlain = GroupGL


  pygame.display.old_get_surface = pygame.display.get_surface
  pygame.display.get_surface = gl_display_get_surface

  pygame.display.old_set_mode = pygame.display.set_mode
  pygame.display.set_mode = gl_display_set_mode


# extend the sprite class with layering support
pygame.sprite.Sprite.zindex = DEFAULTZINDEX
#def zcompare(self,other):
#  return cmp(self.zindex,other.zindex)
#pygame.sprite.Sprite.__cmp__ = zcompare

#_pixels3d   = pygame.surfarray.pixels3d
#_blit_array = pygame.surfarray.blit_array

#def (surf,color):
#  size = surf.rect.width*surf.rect.height
#  surf=surf.image
#  narray=_pixels3d(surf).astype(Float32)
#  reshape(narray,[size,3])
#  narray*=array(color).astype(Float32)
#  _blit_array(surf,narray.astype(Int8))

songdir = mainconfig['songdir']

class BGmovie(pygame.sprite.Sprite):
  def __init__ (self, filename):
    pygame.sprite.Sprite.__init__(self)        #call Sprite initializer
    self.filename = filename
    self.image = pygame.surface.Surface((640,480))
    
    if filename and not os.path.isfile(filename): #make sure the file's there
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
    self.tick = toRealTime(bpm, 1)
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
    self.tick = toRealTime(bpm, 1)
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
    etime = 0.0
    time = round(curtime / (self.tick / 6))
    done = 0
    early = late = ontime = 0
    off = -1
    for i in range(-11, 12):
      if time+i in times:
        if dir in self.steps[time+i]:
          off = i
          if off > 1: self.early += 1
          elif off < 1: self.late += 1
          else: self.ontime += 1
          done = 1
          etime = self.actualtimes[time+i]
          self.steps[time+i] = self.steps[time+i].replace(dir, "")
#          print "Before: %s" % self.steps[time+i]
#          print "Removing %s: %s" % (dir, self.steps[time+i])
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

        if off == 1:
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
#      else:
#        text = "woah"
#        print "Ack! off is", off

      if random.randrange(15) == 1:
        self.announcer.say('ingame', anncrange)
        #    print self.text, 'at', time
      self.recentsteps.insert(0, text)
      self.recentsteps.pop()

    return text, dir, etime

  def trytime(self, dir, time):
    return time in self.times and dir in self.steps[time]

  def expire_arrows(self, time):
    curtick = round((time - 2*self.tick) / (self.tick / 6))
    self.times = self.steps.keys()
    self.times.sort()
    for k in range(24):
      j = curtick - k
      if (j in self.times) and self.steps[j]:
        self.broke = 1
        self.combo = 0
        n = len(self.steps[j]) 
        del self.steps[j]
        for i in range(n):
          self.miss += 1
          self.recentsteps.insert(0, "MISS")
          self.lifebar.update_life("M")
          self.dance_score -= 8
          self.arrow_count += 1
          self.recentsteps.pop()
  
  def handle_arrow(self, key, time, etime):
      multicheck = self.tick
#      tick_6 = multicheck / 6
#      curtick = round((time + 2*multicheck) / tick_6)
      curtick = round(6 * (time/multicheck + 2))
      self.times = self.steps.keys()
      self.actualtimes[curtick] = etime
      if curtick in self.times:
        self.steps[curtick] += key
      else:
        self.steps[curtick] = key
        self.times = self.steps.keys()
        
      self.times.sort()
      isdl = 0
      for i in range(len(self.times)-1,-1,-1):
        if self.times[i] < curtick - 24:
          dellist = self.times[0:i+1]
          isdl = 1
          break
      if isdl:
        for i in dellist:
          del self.steps[i]
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

class zztext(pygame.sprite.Sprite):
    def __init__(self,text,x,y):
      pygame.sprite.Sprite.__init__(self) #call Sprite initializer
      self.x = x
      self.y = y
      self.zoom = 0
      self.baseimage = pygame.surface.Surface((320,24))
      self.rect = self.baseimage.get_rect()
      self.rect.centerx = self.x
      self.rect.centery = self.y

      for i in (0, 1, 2, 3, 4, 5, 6, 7, 8, 15):
        font = pygame.font.Font(None, 9+i)
        stextred = (i*16)
        stextblu = (i*16)
        stextgrn = (i*16)
        gtext = font.render(text, 1, (stextred, stextblu, stextgrn))
        textpos = gtext.get_rect()
        textpos.centerx = 160
        textpos.centery = 12
        self.baseimage.blit(gtext, textpos)

      self.baseimage.set_colorkey(self.baseimage.get_at((0,0)),RLEACCEL)
      self.image = self.baseimage

    def zin(self):
      self.zoom = 1
      self.zdir = 1
      
    def zout(self):
      self.zoom = 31
      self.zdir = -1
      
    def update(self):
      if 32 > self.zoom > 0:
        self.image = pygame.transform.rotozoom(self.baseimage, 0, self.zoom/32.0)

        self.rect = self.image.get_rect()
        self.rect.centerx = self.x
        self.rect.centery = self.y
        
        self.zoom += self.zdir
      else:
        self.zdir = 0

class ComboDisp(pygame.sprite.Sprite):
  def __init__(self,playernum):
    pygame.sprite.Sprite.__init__(self) #call Sprite initializer
    self.sticky = mainconfig['stickycombo']
    self.lowcombo = mainconfig['lowestcombo']

    self.trect = 296 + (mainconfig['totaljudgings'] * 24)
    self.playernum = playernum
    self.centerx = (320*self.playernum) + 160
    
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

    self.dirty = 0

  def update(self, xcombo, steptimediff):
    if steptimediff < 0.36 or self.sticky:
      self.drawcount = xcombo
      self.drawsize = min(int(steptimediff*50), len(self.words)-1)
    else:
      self.drawcount = 0

  def draw(self, screen):
    if self.drawcount >= self.lowcombo:
      render = self.words[self.drawsize]
      width = render[-1].get_width()
      hundreds = self.drawcount / 100
      tens = self.drawcount / 10
      ones = self.drawcount % 10
      #get width
      if hundreds:
        hundreds = render[hundreds%10]
        width += hundreds.get_width()
      if tens:
        tens = render[tens%10]
        width += tens.get_width()
      ones = render[ones]
      width += ones.get_width()
      startleft = left = self.centerx - width / 2
      #render
      if hundreds:
        screen.blit(hundreds, (left, self.trect))
        left += hundreds.get_width()
      if tens:
        screen.blit(tens, (left, self.trect))
        left += tens.get_width()
      screen.blit(ones, (left, self.trect))
      left += ones.get_width()
      r = screen.blit(render[-1], (left, self.trect))
      self.dirty = Rect(startleft, r.top, r.right - startleft, r.height)

  def clear(self, screen, bgd):
    if self.dirty:
      screen.blit(bgd, self.dirty, self.dirty)
      self.dirty = 0

class HoldJudgeDisp(pygame.sprite.Sprite):
    def __init__(self, POS, playernum):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.playernum = playernum

        self.space = pygame.surface.Surface((48,24))
        self.space.fill((0,0,0))

        self.baseimage = pygame.surface.Surface((320,24))
        self.baseimage.fill((0,0,0))
        self.image = self.baseimage

        self.okimg = fontfx.shadefade("OK",28,3,(48,24),(112,224,112))
        self.ngimg = fontfx.shadefade("NG",28,3,(48,24),(224,112,112))

        self.rect = self.image.get_rect()
        self.image.set_colorkey(self.image.get_at((0,0)))
        self.rect.top = POS['top']-8
        self.rect.left = 60+(320*self.playernum)

        self.slotnow = ['','','','']        
        self.slotold = ['','','','']
        self.slothit = [-1,-1,-1,-1]
        
    def fillin(self, curtime, direction, value):
      self.slothit[direction] = curtime
      self.slotnow[direction] = value
      
    def update(self, curtime):
      for i in range(4):
        if (curtime - self.slothit[i] > 0.5):
          self.slotnow[i]=''
        if self.slotnow[i] != self.slotold[i]:
          x = (i*72)
          if self.slotnow[i] == 'OK':
            self.image.blit(self.okimg,(x,0))
          if self.slotnow[i] == 'NG':
            self.image.blit(self.ngimg,(x,0))
          if self.slotnow[i] == '':
            self.image.blit(self.space,(x,0))
          self.slotold[i] = self.slotnow[i]
          
class fpsDisp(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
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
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
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

# Search the directory specified by path recursively for files that match
# the shell wildcard pattern. A list of all matching file names is returned,
# with absolute paths.
def find (path, pattern):
  matches = []
  path = os.path.expanduser(path)

  if os.path.isdir(path):
    list = os.listdir(path)
    for f in list:
      filepath = os.path.join(path, f)
      if os.path.isdir(filepath):
        matches.extend(find(filepath, pattern))
      else:
        if fnmatch.fnmatch(filepath, pattern):
          matches.append(filepath)
  return matches

class ArrowSprite(CloneSprite):

  # Assist mode sound samples
  samples = {}
  for d in DIRECTIONS:
    samples[d] = pygame.mixer.Sound(os.path.join(sound_path,
                                                 "assist-" + d + ".ogg"))
  
  def __init__ (self, spr, curtime, endtime, playernum, POS):
    CloneSprite.__init__(self, spr, ARROWZINDEX)
    self.endtime = endtime
    self.life  = endtime - curtime
    self.curalpha = -1
    self.dir = spr.fn[-7:-6]
    if mainconfig['assist']: self.sample = ArrowSprite.samples[self.dir]
    else: self.sample = None
    self.pos = copy.copy(POS)
    if self.pos['mode'] == 'switchy':
      self.pos = POS
    if (self.pos['mode'] == 'centered') or (self.pos['mode'] == 'switchy'):
      if random.choice([True, False]):
        self.pos['bot'] = int(236 + (mainconfig['scrollspeed']*512))
      else:
        self.pos['bot'] = int(236 - (mainconfig['scrollspeed']*512))
      self.pos['diff'] = float(self.pos['top']-self.pos['bot'])
    self.playernum = playernum
    self.bimage = self.image
    self.arrowspin = mainconfig["arrowspin"]
    self.arrowscale = mainconfig["arrowscale"]
    
    self.centerx = self.rect.centerx+(self.playernum*320)
    
  def update (self,curtime,curbpm,lbct,hidden,sudden):
    if (self.sample) and (curtime >= self.endtime -0.0125):
      self.sample.play()
      self.sample = None

    if curtime > self.endtime + (240.0/curbpm): # == 0.004 * 60000 / curbpm
      self.kill()
      return

    self.rect = self.image.get_rect()
    self.rect.centerx = self.centerx

    self.top = self.pos['top']
    
    if len(lbct) == 0:
      onebeat = float(60000.0/curbpm)/1000
      doomtime = self.endtime - curtime
      beatsleft = float(doomtime / onebeat)
      self.top = self.top - int( (beatsleft/8.0)*self.pos['diff'] )
    else:
      oldbpmsub = [curtime,curbpm]
      bpmbeats = 0
      for bpmsub in lbct:
        if bpmsub[0] <= self.endtime:
          onefbeat = float(60000.0/oldbpmsub[1])/1000
          bpmdoom = bpmsub[0] - oldbpmsub[0]
          bpmbeats = float(bpmdoom / onefbeat)
          self.top = self.top - int(bpmbeats*self.pos['diff']/8.0)
          oldbpmsub = bpmsub
        else: break

      onefbeat = float(60000.0/oldbpmsub[1])/1000
      bpmdoom = self.endtime - oldbpmsub[0]
      bpmbeats = float(bpmdoom / onefbeat)
      self.top = self.top - int(bpmbeats*self.pos['diff']/8.0)

    if self.top > 480:
      self.top = 480
    self.rect.top = self.top
    
    self.cimage = self.bimage
    
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

    alp = 0
    self.curalpha = self.get_alpha()

    if self.pos['top'] < self.pos['bot']:
      hiddenzone = ( (self.pos['top']) + int(64.0*hidden) )
      suddenzone = ( (64+self.pos['bot']) - int(64.0*sudden) )
      atest = self.rect.top
    else:    # test for alpha using the bottom of the arrow instead of the top in the case of reverse scrolling
      hiddenzone = ( (self.pos['bot']) + int(64.0*hidden) )
      suddenzone = ( (64+self.pos['top']) - int(64.0*sudden) )
      atest = self.rect.bottom-64

    if atest < hiddenzone:
      alp = 255-(hiddenzone-atest)*4
    elif atest > hiddenzone:
      if atest < suddenzone:
        alp = (suddenzone-atest)*4
    if alp > 255:    alp = 255
    elif alp < 0:    alp = 0
    if alp != self.curalpha:
      self.image.set_alpha(alp)

class HoldArrowSprite(CloneSprite):
  def __init__ (self, spr, curtime, times, lastbpmtime, playernum, POS, zindex=ARROWZINDEX):
    CloneSprite.__init__(self,spr,zindex=zindex)
    self.timef1 = times[1]
    self.timef2 = times[2]
    self.timef = times[2]
    self.life  = times[2]-curtime
    self.lastbpmtime = lastbpmtime
    self.pos = copy.copy(POS)
    if self.pos['mode'] == 'switchy':
      self.pos = POS
    if (self.pos['mode'] == 'centered') or (self.pos['mode'] == 'switchy'):
      if random.choice([0,1]):
        self.pos['bot'] = int(236 + (mainconfig['scrollspeed']*512))
      else:
        self.pos['bot'] = int(236 - (mainconfig['scrollspeed']*512))
      self.pos['diff'] = float(self.pos['top']-self.pos['bot'])
    self.playernum = playernum
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
    self.arrowspin = float(mainconfig["arrowspin"])
    self.arrowscale = float(mainconfig["arrowscale"])
    
    self.centerx = self.rect.centerx+(self.playernum*320)
    
  def update (self,curtime,curbpm,lbct,hidden,sudden):
    # assist
    if (self.playedsound is None) and (curtime >= self.timef1 -0.0125): #- (0.001*(60000.0/curbpm))):
      self.sample.play()
      self.playedsound = 1

    if curtime > self.timef2:  #+ (0.001*(60000.0/curbpm)):
      self.kill()
      return
      
    self.rect = self.image.get_rect()
    self.rect.centerx = self.centerx

    self.top = self.pos['top']
    self.bottom = self.pos['top'] #+ int(self.pos['diff']/8.0)

    finaltime = 0
    if len(lbct)<2: # single run (I hope)
      onebeat = float(60000.0/curbpm)/1000
      doomtime = self.timef1 - curtime
      if self.broken == 0:
        if doomtime < 0:
          doomtime = 0
      beatsleft = float(doomtime / onebeat)
      self.top = self.top - int( (beatsleft/8.0)*self.pos['diff'] )
      doomtime = self.timef2 - curtime
      beatsleft = float(doomtime / onebeat)
      self.bottom = self.bottom - int( (beatsleft/8.0)*self.pos['diff'] )
    else:
      oldbpmsub = [curtime,curbpm]
      bpmbeats = 0
      for bpmsub in lbct:
        if bpmsub[0] <= self.timef1 or bpmsub <= self.timef2:
          onefbeat = float(60000.0/oldbpmsub[1])/1000
          bpmdoom = bpmsub[0] - oldbpmsub[0]
          bpmbeats = float(bpmdoom / onefbeat)
	  if bpmsub[0] <= self.timef1:
	    self.top = self.top - int(bpmbeats*self.pos['diff']/8.0)
          if bpmsub[0] <= self.timef2:
            self.bottom = self.bottom - int(bpmbeats*self.pos['diff']/8.0)
          oldbpmsub = bpmsub

      onefbeat = float(60000.0/oldbpmsub[1])/1000
      bpmdoom = self.timef1 - oldbpmsub[0]
      bpmbeats = float(bpmdoom / onefbeat)
      self.top = self.top - int(bpmbeats*self.pos['diff']/8.0)
      bpmdoom = self.timef2 - oldbpmsub[0]
      bpmbeats = float(bpmdoom / onefbeat)
      self.bottom = self.bottom - int(bpmbeats*self.pos['diff']/8.0)

    if self.bottom > 480:
      self.bottom = 480
    if self.pos['top'] < self.pos['bot']:
      if self.bottom < 64:
        self.bottom = 64
    self.rect.bottom = self.bottom
 
    if self.top > 480:
      self.top = 480
    if self.pos['top'] < self.pos['bot']:
      if self.top < 64:
        self.top = 64

    if self.pos['top'] < self.pos['bot']:
      self.rect.top = self.top
    else:
      self.rect.top = self.bottom
    
#    print "top",self.top,"bottom",self.bottom
    holdsize = abs(self.bottom-self.top)
    if holdsize < 0:
      holdsize = 0
    self.cimage = pygame.surface.Surface((64,holdsize+64))
    self.cimage.set_colorkey(self.cimage.get_at((0,0)))
    self.cimage.blit( pygame.transform.scale(self.bimage, (64,holdsize)), (0,32) )
    self.cimage.blit(self.oimage2,(0,0))
    self.cimage.blit(self.oimage,(0,holdsize+32))

    if self.arrowscale != 1:
      arrscale = int(float((self.rect.top-64)/416.0)*64)
      if self.arrowscale > 1: # grow
      	arrscale = 64 - arrscale
      self.cimage = pygame.transform.scale(self.bimage, (arrscale, arrscale))
    
    if self.arrowspin:
      self.image = pygame.transform.rotate(self.cimage,(self.rect.top-64)/self.arrowspin)
    else:
      self.image = self.cimage

    alp = 255
    self.curalpha = self.get_alpha()

    if self.pos['top'] < self.pos['bot']:
      hiddenzone = ( (self.pos['top']) + int(64.0*hidden) )
      suddenzone = ( (64+self.pos['bot']) - int(64.0*sudden) )
      atest = self.rect.top
    else:    # test for alpha using the bottom of the arrow instead of the top in the case of reverse scrolling
      hiddenzone = ( (self.pos['bot']) + int(64.0*hidden) )
      suddenzone = ( (64+self.pos['top']) - int(64.0*sudden) )
      atest = self.rect.bottom-64

    if atest < hiddenzone:
      alp = 255-(hiddenzone-atest)*4
    elif atest > hiddenzone:
      if atest < suddenzone:
        alp = (suddenzone-atest)*4
    if alp > 255:    alp = 255
    elif alp < 0:    alp = 0
    if self.broken and (curtime > self.timef1+(0.00025*(60000.0/curbpm))):
      alp /= 2
    if alp != self.curalpha:
      self.image.set_alpha(alp)
  
#    print "alpha ",alp

def SetDisplayMode(mainconfig):
  global screen
  
  try:
    if mainconfig["vesacompat"]:
      screen = pygame.display.set_mode((640, 480), 16)
    
    elif mainconfig["fullscreen"]:
      if osname == "macosx":
        screen = pygame.display.set_mode((640, 480), FULLSCREEN, 16)
      else:
        screen = pygame.display.set_mode((640, 480), HWSURFACE|DOUBLEBUF|FULLSCREEN, 16)
    
    else:
      screen = pygame.display.set_mode((640, 480), HWSURFACE|DOUBLEBUF, 16)
  except:
    print "Can't get a 16 bit display!" 
    sys.exit()

def main():
  global screen
  print "pyDDR, by theGREENzebra (tgz@clickass.org)"
  print "Initialising.."

  # set up the screen and all that other stuff
  pygame.init()

  # FIXME Debug mode has been broken for like, 4 releases, take it out

  # Search recursively for files
  fileList = []
  for dir in songdir.split(os.pathsep):
    print "Searching", dir
    fileList += find(dir, '*.step')

  totalsongs = len(fileList)
  parsedsongs = 0
  songs = []

  SetDisplayMode(mainconfig)
  
  pygame.display.set_caption('pyDDR')
  pygame.mouse.set_visible(0)

  pygame.mixer.music.load(os.path.join(sound_path, "menu.ogg"))
  try:
    pygame.mixer.music.play(4, 0.0)
  except TypeError:
    print "Sorry, pyDDR needs a more up to date Pygame or SDL than you have."
    sys.exit()

  background = BlankSprite(screen.get_size())

  pbar = fontfx.TextProgress(FONTS[60], "Found " + str(totalsongs) +
                             " files. Loading...", colors.WHITE, colors.BLACK)
  r = pbar.render(0).get_rect()
  r.center = (320, 240)
  for f in fileList:
#    try: songs.append(fileparsers.SongItem(f))
    songs.append(fileparsers.SongItem(f, False))
#    except:
#      print "Error loading " + f
    img = pbar.render(parsedsongs / totalsongs)
    pygame.display.update(screen.blit(img, r))
    parsedsongs += 100.0

  ev = event.poll()
  while ev[1] != E_PASS: ev = event.poll()

  if len(songs) < 1:
    print "You don't have any songs, and you need one. Go to http://icculus.org/pyddr/"
    sys.exit(1)

  menudriver.do(screen, (songs, screen, playSequence))
  mainconfig.write(os.path.join(rc_path, "pyddr.cfg"))

def blatantplug():
  xiphlogo = pygame.image.load(os.path.join(image_path, "xifish.png")).convert()
  pygamelogo = pygame.image.load(os.path.join(image_path, "pygamelogo.png")).convert()
  oddlogo = pygame.image.load(os.path.join(image_path, "oddlogos.png")).convert()
  xiphlogo.set_colorkey(xiphlogo.get_at((0,0)))
  pygamelogo.set_colorkey(pygamelogo.get_at((0,0)))
  oddlogo.set_colorkey(oddlogo.get_at((0,0)))
  xiphlogo.set_alpha(32)
  pygamelogo.set_alpha(32)
  oddlogo.set_alpha(32)
  xiphlogorect = xiphlogo.get_rect()
  pygamelogorect = pygamelogo.get_rect()
  oddlogorect = oddlogo.get_rect()
  
  oddlogorect.centerx = 320;  oddlogorect.centery = 128
  pygamelogorect.centerx = 320;  pygamelogorect.centery = 256
  xiphlogorect.centerx = 320;  xiphlogorect.centery = 384
    
  pygame.mixer.music.load(os.path.join(sound_path, "menu.ogg"))
  pygame.mixer.music.play(0,14.75)
  pygame.mixer.music.set_volume(0)
  
  for i in range(26):
    screen.fill((i*8,i*8,i*8))
    pygame.display.flip()
    pygame.mixer.music.set_volume(i/2.0)
    pygame.time.delay(16)
    
  pygame.time.delay(225)

  screen.blit(pygamelogo,pygamelogorect)
  screen.blit(oddlogo,oddlogorect)
  screen.blit(xiphlogo,xiphlogorect)
  pygame.display.flip()

  pygame.time.delay(225)
  
  plugtext = ["You have been playing pyDDR","by Brendan Becker","which is available at:", "http://icculus.org/pyddr/", " ", "If you like it, please donate a few bucks!", "The programmer is unemployed! =]", " ", "it was made possible by:", "Python, SDL, Pygame, and Xiph.org"]
  for i in plugtext:
    mrtext = FONTS[48].render(i,1,(plugtext.index(i)*8,plugtext.index(i)*8,plugtext.index(i)*8))
    mrtextrect = mrtext.get_rect()
    mrtextrect.centerx = 320
    mrtextrect.top = plugtext.index(i)*43
    screen.blit(mrtext,mrtextrect)
    pygame.display.flip()
    pygame.time.delay(225)

  pygame.time.delay(4500)

  background = CloneSprite(pygame.transform.scale(screen, (640,480)))
  for n in range(63):
    background.set_alpha(255-(n*4))
    screen.fill(colors.BLACK)
    background.draw(screen)
    pygame.display.flip()
    pygame.time.wait(1)

  print "pyDDR exited properly."
  sys.exit()    


def playSequence(numplayers, playlist):
  global screen

  ARROWPOS = {}
  #DCY: Bottom of 640 gives lots of "update rejecting"    
  if mainconfig['reversescroll'] == 2:
    ARROWPOS['top']  = 236
    ARROWPOS['bot']  = int(236 + (mainconfig['scrollspeed']*512))
    ARROWPOS['mode'] = 'centered'
  elif mainconfig['reversescroll'] == 3:    # this is more of a bug than a feature but some people might like it
    ARROWPOS['top']  = 236
    ARROWPOS['bot']  = int(236 + (mainconfig['scrollspeed']*512))
    ARROWPOS['mode'] = 'switchy'
  elif mainconfig['reversescroll']:
    ARROWPOS['top']  = 408
    ARROWPOS['bot']  = int(-64 - (mainconfig['scrollspeed']-1)*576)
    ARROWPOS['mode'] = 'reverse'
  else:
    ARROWPOS['top']  = 64
    ARROWPOS['bot']  = int(576 * mainconfig['scrollspeed'])
    ARROWPOS['mode'] = 'normal'

  ARROWPOS['diff'] = float(ARROWPOS['top']-ARROWPOS['bot'])

  players = []
  for playerID in range(numplayers):
    plr = Player(playerID, ARROWPOS, HoldJudgeDisp(ARROWPOS,playerID), ComboDisp(playerID))
    players.append(plr)
    
  for songfn, diff in playlist:
    current_song = fileparsers.SongItem(songfn)
    pygame.mixer.quit()
    prevscr = pygame.transform.scale(screen, (640,480))
#    screen.fill(colors.BLACK)
    songdata = steps.SongData(current_song)

    for pid in range(len(players)): #FIXME new lyrics system
      players[pid].set_song(steps.Steps(current_song, diff[pid],
                                        lyrics = songdata.lyricdisplay),
                                        Judge)

    if dance(songdata, players, ARROWPOS, prevscr):
      break # Failed

  judges = [player.judge for player in players]

  if mainconfig['grading']:
    grade = gradescreen.GradingScreen(judges)
    background = pygame.transform.scale(screen, (640,480))
    if grade.make_gradescreen(screen, background):
      grade.make_waitscreen(screen)

  return judges

def dance(song, players, ARROWPOS, prevscr):
  global screen

  songFailed = False

  background = BlankSprite(screen.get_size())

  pygame.mixer.init()

  # render group, almost[?] every sprite that gets rendered
  rgroup = RenderLayered()
  # text group, EG. judgings and combos
  tgroup = RenderLayered()  
  # special group for top arrows
  sgroup = RenderLayered()
  # special group for arrowfx
  fgroup = RenderLayered()
  
  # lyric display group
  lgroup = RenderLayered()

  # background group
  bgroup = RenderLayered()

  if song.movie != None:
    backmovie = BGmovie(song.movie)
    backmovie.image.set_alpha(mainconfig['bgbrightness'], RLEACCEL)
  else:
    backmovie = BGmovie(None)
    
  backimage = BGimage(song.background)

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
#      backmovie.add(bgroup)
  else:
    background.fill(colors.BLACK)

  for pid in range(len(players)):
    players[pid].score.add(tgroup)
    players[pid].lifebar.add(tgroup)
    players[pid].holdtext.add(tgroup)
    for i in range(mainconfig['totaljudgings']):
      pj = JudgingDisp(pid)
      players[pid].judging_list.append(pj)
      pj.add(tgroup)
    

  fpstext = fpsDisp()
  timewatch = TimeDisp()

  colortype = mainconfig['arrowcolors']
  if colortype == 0:
    colortype = 1

  if mainconfig['fpsdisplay']:
    tgroup.add(fpstext)
    tgroup.add(timewatch)

  if mainconfig['showlyrics']:
    lgroup.add(song.lyricdisplay.channels.values())
#    song.lyricdisplay.add(lgroup)

  showcombo = mainconfig['showcombo']
  
  bg = pygame.Surface(screen.get_size())
  bg.fill((0,0,0))

  songtext = zztext(song.title, 480,12)
  grptext = zztext(song.artist, 160,12)

  songtext.zin()
  grptext.zin()

  tgroup.add(songtext)
  tgroup.add(grptext)
  tgroup.add(timewatch)

  screenshot=0

  song.init()

  if song.crapout != 0:
    font = None
    text = None
    text = FONTS[192].render('ERROR!', 1, (48,48,48))
    textpos = text.get_rect()
    textpos.centerx = 320
    textpos.centery = 240
    screen.blit(text, textpos)

    font = None
    text = None

    if song.crapout == 1:
      text = FONTS[32].render("The type of music file this song is in isn't recognised", 1, (224,224,224))
    elif song.crapout == 2:
      text = FONTS[32].render("The music file ("+song.file+") for this song wasn't found", 1, (224,224,224))

    text.set_colorkey(text.get_at((0,0)))
    textpos = text.get_rect()
    textpos.centerx = 320
    textpos.centery = 216
    screen.blit(text, textpos)

    text = FONTS[32].render("Press ENTER", 1, (160,160,160))
    text.set_colorkey(text.get_at((0,0)))
    textpos = text.get_rect()
    textpos.centerx = 320
    textpos.centery = 264
    screen.blit(text, textpos)

    pygame.display.flip()

    while 1:
      ev = event.poll()
      if ev[1] == E_START or ev[1] == E_QUIT: break
      pygame.time.wait(50)
    
    print "Unable to play this song."
    return 0 #player didn't fail, so return 0 here.
  
  screenshot = 0

#  print "playmode: %r difficulty %r modes %r" % (playmode,difficulty,song.modes)
#  print "Total arrows are %d " % song.totarrows[difficulty]
  if mainconfig['assist']:
    pygame.mixer.music.set_volume(0.6)
  else:
    pygame.mixer.music.set_volume(1.0)

  if (mainconfig['strobe']):
    extbox = Blinky(song.bpm)
    extbox.add(tgroup)

  song.play()
  for plr in players:
    plr.start_song()
    for arrowID in DIRECTIONS:
      if mainconfig['explodestyle'] > -1:
        plr.toparrfx[arrowID].add(fgroup)
      if mainconfig['showtoparrows']:
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
    else: curtime = pygame.mixer.music.get_pos()/1000.0

    key = []

    ev = event.poll()

    for i in range(len(players)):
      if (event.states[(i, E_START)] and event.states[(i, E_RIGHT)]):
        print "Holding right plus start quits pyDDR."
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
        players[playerID].toparr[keyPress].stepped(1, curtime+(players[playerID].steps.offset*1000))
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
                plr.judge.handle_arrow(dir, curtime, ev.when)
         
        for ev in nevents:
          if ev.feet:
            for (dir,num) in zip(DIRECTIONS, ev.feet):
              if num & 1:
                if not (num & 2):
                  ArrowSprite(plr.theme.arrows[dir+repr(int(ev.color)%colortype)].c, curtime, ev.when, plr.pid, ARROWPOS).add([plr.arrow_group, rgroup])

              if num & 2:
                holdindex = plr.steps.holdref.index((DIRECTIONS.index(dir),ev.when))
                HoldArrowSprite(plr.theme.arrows[dir+repr(int(ev.color)%colortype)].c, curtime, plr.steps.holdinfo[holdindex], plr.steps.lastbpmchangetime[0], plr.pid, ARROWPOS).add([plr.arrow_group, rgroup])

    for plr in players:
      if len(plr.steps.lastbpmchangetime) > 0:
        if (curtime >= plr.steps.lastbpmchangetime[0][0]):
          nbpm = plr.steps.lastbpmchangetime[0][1]
          for plr in players:
            plr.change_bpm(nbpm)
            print "Last changed BPM at", plr.steps.lastbpmchangetime[0]
            plr.steps.lastbpmchangetime.pop(0)
     
    for plr in players: plr.check_sprites(curtime)

    if(mainconfig['strobe']):
      extbox.update(curtime+(players[0].steps.offset*1000.0))
    
    song.lyricdisplay.update(curtime)

    for plr in players: plr.combo_update(curtime)
    
    backimage.update()
    
    if backmovie.filename:
      backmovie.update(curtime)
      if backmovie.changed or (fpstext.fpsavg > 30):
        backmovie.resetchange()
        background.fill(colors.BLACK)
        screen.blit(background.image,(0,0))
        screen.blit(backmovie.image,(0,0))

    songtext.update()
    grptext.update()

    if mainconfig["fpsdisplay"]:
      fpstext.update(curtime)
      timewatch.update(curtime)

    # more than one display.update will cause flicker
#    bgroup.draw(screen)
    sgroup.draw(screen)
    #dgroup.draw(screen)
#    rgroup.draw(screen)

    for plr in players:
      plr.arrow_group.draw(screen)
    
    fgroup.draw(screen)
    tgroup.draw(screen)
    lgroup.draw(screen)
    if showcombo:
      for plr in players:
        plr.combos.draw(screen)
    
    pygame.display.update()

    if screenshot:
      pygame.image.save(pygame.transform.scale(screen, (640,480)), "screenshot.bmp")
      screenshot = 0

    if not backmovie.filename:
      if showcombo:
        for plr in players:
          plr.combos.clear(screen, background.image)
      
      lgroup.clear(screen,background.image)
      tgroup.clear(screen,background.image)
      fgroup.clear(screen,background.image)
  #    rgroup.clear(screen,background.image)
      for plr in players:
        plr.arrow_group.clear(screen,background.image)
      #dgroup.clear(screen,background.image)
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
