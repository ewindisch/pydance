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

import fontfx, menudriver, fileparsers, colors

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

class SongEvent:
  def __init__ (self, bpm, when=0.0, feet=None, next=None, extra=None, color=None):
    self.bpm  = bpm
    self.when = when
    self.feet = feet
    self.next = next
    self.extra = extra
    self.color = color
  def __repr__(self):
    rest=[]
    if self.feet: rest.append('feet=%r'%self.feet)
    if self.extra: rest.append('extra=%r'%self.extra)
    if self.extra: rest.append('color=%r'%self.color)
    return '<SongEvent when=%r bpm=%r %s>' % (self.when,self.bpm,' '.join(rest))

def emptyDictFromList(lst):
  d = {}
  for n in lst: d[n]=None
  return d

DIFFICULTYLIST = ['BASIC','TRICK','MANIAC']
DIFFICULTIES   = emptyDictFromList(DIFFICULTYLIST)
MODELIST = ['SINGLE','DOUBLE']
MODES = emptyDictFromList(MODELIST)
BEATS = {'sixty':0.25,'thrty':0.5,'twtfr':2.0/3.0,'steps':1.0,'tripl':4.0/3.0,'eight':2.0,'qurtr':4.0,'halfn':8.0,'whole':16.0} 

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
    self.oldtick = toRealTime(bpm, 1)
    self.marvelous = self.perfect = self.great = self.ok = self.boo = self.miss = 0
    self.combo = self.bestcombo = self.broke = 0
    self.steppedtime = -1000
    self.recentsteps = [' ',' ',' ']
    self.early = self.late = self.ontime = 0
    self.totalcombos = 1
    self.bpm = bpm
    self.failed_out = False
    self.oldbpm = bpm
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
        
  def changingbpm(self, bpm):
    self.oldtick = toRealTime(bpm, 1)
    self.oldbpm = bpm

  def changebpm(self, bpm):
    self.tick = toRealTime(bpm, 1)
    self.oldbpm = copy
    self.bpm = bpm
        
  def getbpm(self):
    return self.bpm

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

        if off <= 1:
          self.marvelous += 1
          self.score += 10 * self.score_coeff * self.arrow_count
          self.dance_score += 2
          self.lifebar.update_life("V")
          text = "MARVELOUS"
          anncrange = (80, 100)
        elif 1 < off <= 4:
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
      if j in self.times and self.steps[j]:
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

class GradingScreen:
  def __init__(self, judges):
    self.judges = judges

    for judge in judges:
      print "Player "+repr(judges.index(judge)+1)+":"
    
      grade = judge.grade()
      if grade != "?":
        grades = {"AAA": (100, 95), "AA": (99, 93), "A": (92, 80),
                  "B": (79, 65), "C": (64, 45), "D": (45, 25), "E": (24, 0)}
        Announcer(mainconfig["djtheme"]).say(grades[grade])
      totalsteps = (judge.marvelous + judge.perfect + judge.great +
                    judge.ok + judge.boo + judge.miss)
      steps = (grade, judge.diff, totalsteps, judge.bestcombo, judge.combo)

      numholds = judge.numholds()
      goodholds = numholds - judge.badholds

      steptypes = (judge.marvelous, judge.perfect, judge.great, judge.ok,
                   judge.boo, judge.miss, goodholds, numholds)
      print ("GRADE: %s (%s) - total steps: %d best combo" + " %d current combo: %d") % steps
      print ("V: %d P: %d G: %d O: %d B: %d M: %d - %d/%d holds") % steptypes
      print

  def make_gradescreen(self, screen):
    judge = self.judges[0]
    totalsteps = (judge.marvelous + judge.perfect + judge.great +
                  judge.ok + judge.boo + judge.miss)

    if totalsteps == 0: return None

    # dim screen
    for n in range(31):
      background.set_alpha(255-(n*4))
      screen.fill(colors.BLACK)
      background.draw(screen)
      pygame.display.flip()
      pygame.time.wait(1)

    grading = fontfx.sinkblur("GRADING",64,4,(224,72),(64,64,255))
    grading.set_colorkey(grading.get_at((0,0)))
    screen.blit(grading, (320-grading.get_rect().centerx,-8) )
    pygame.display.update()

    rows = ["MARVELOUS", "PERFECT", "GREAT", "OK", "BOO",
            "MISS", "early", "late", " ", "TOTAL", " ", "MAX COMBO",
            "HOLDS", " ", "SCORE"]

    for j in range(4):
      for i in range(len(rows)):
        fc = ((j*32)+96-(i*8))
        if fc < 0: fc=0
        gradetext = fontfx.shadefade(rows[i],28,j,(224,32), (fc,fc,fc))
        gradetext.set_colorkey(gradetext.get_at((0,0)))
        gradetextpos = gradetext.get_rect()
        gradetextpos.right = 32 + screen.get_rect().centerx + 8-j
        gradetextpos.top = 64 + (i*24) + 8-j
        r = screen.blit(gradetext, (320-FONTS[28].size(rows[i])[0]/2,
                                64 + (i*24) + 8-j))
        update_screen(r)
      pygame.time.wait(100)

    player = 0

    for judge in self.judges:
      grade = judge.grade()
      for i in range(4):
        font = pygame.font.Font(None, 100-(i*2))
        gradetext = font.render(grade, 1, (48 + i*16, 48 + i*16, 48 + i*16))
        gradetext.set_colorkey(gradetext.get_at((0,0)))
        r = screen.blit(gradetext, (200 + 250 * player - (font.size(grade))[0]/2, 150))
        update_screen(r)
        pygame.time.delay(48)

      totalsteps = (judge.marvelous + judge.perfect + judge.great + judge.ok +
                    judge.boo + judge.miss)
      rows = [judge.marvelous, judge.perfect, judge.great, judge.ok,
              judge.boo, judge.miss, judge.early, judge.late]

      for j in range(4):
        for i in range(len(rows)):
          fc = ((j*32)+96-(i*8))
          if fc < 0: fc=0
          text = "%d (%d%%)" % (rows[i], 100 * rows[i] / totalsteps)
          gradetext = fontfx.shadefade(text,28,j,(FONTS[28].size(text)[0]+8,32), (fc,fc,fc))
          gradetext.set_colorkey(gradetext.get_at((0,0)))
          graderect = gradetext.get_rect()
          graderect.top = 72 + (i*24) - j
          if player == 0:
            graderect.left = 40
          else:
            graderect.right = 600
          r = screen.blit(gradetext, graderect)
          update_screen(r)
        pygame.time.wait(100)

      # Total
      for j in range(4):
        gradetext = fontfx.shadefade(str(totalsteps),28,j,(FONTS[28].size(str(totalsteps))[0]+8,32), (fc,fc,fc))
        gradetext.set_colorkey(gradetext.get_at((0,0)))
        graderect = gradetext.get_rect()
        graderect.top = 288-j
        if player == 0:
          graderect.left = 40
        else:
          graderect.right = 600
        r = screen.blit(gradetext, graderect)
        update_screen(r)
      pygame.time.wait(100)

      # Combo
      for j in range(4):
        text = "%d (%d%%)" % (judge.bestcombo, judge.bestcombo * 100 / totalsteps)
        gradetext = fontfx.shadefade(text,28,j,(FONTS[28].size(text)[0]+8,32), (fc,fc,fc))
        gradetext.set_colorkey(gradetext.get_at((0,0)))
        graderect = gradetext.get_rect()
        graderect.top = 336-j
        if player == 0:
          graderect.left = 40
        else:
          graderect.right = 600
        r = screen.blit(gradetext, graderect)
        update_screen(r)
      pygame.time.wait(100)

      # Holds
      for j in range(4):
        text = "%d / %d" % (judge.numholds() - judge.badholds, judge.numholds())
        gradetext = fontfx.shadefade(text,28,j,(FONTS[28].size(text)[0]+8,32), (fc,fc,fc))
        gradetext.set_colorkey(gradetext.get_at((0,0)))
        graderect = gradetext.get_rect()
        graderect.top = 360-j
        if player == 0:
          graderect.left = 40
        else:
          graderect.right = 600
        r = screen.blit(gradetext, graderect)
        update_screen(r)
      pygame.time.wait(100)

      # Score
      for j in range(4):
        gradetext = fontfx.shadefade(str(judge.score), 28, j,
                                     (FONTS[28].size(str(judge.score))[0]+8,32), (fc,fc,fc))
        gradetext.set_colorkey(gradetext.get_at((0,0)))
        graderect = gradetext.get_rect()
        graderect.top = 412-j
        if player == 0:
          graderect.left = 40
        else:
          graderect.right = 600
        r = screen.blit(gradetext, graderect)
        update_screen(r)
      pygame.time.wait(100)

      player += 1

    background.set_alpha()

    return 1
    
  def make_waitscreen(self, screen):
    idir = -4
    i = 192
    screenshot = 0
    while 1:
      if i < 32:        idir =  4
      elif i > 224:     idir = -4

      i += idir
      ev = event.poll()
      if (ev[1] == E_QUIT) or (ev[1] == E_START):
        break
      elif ev[1] == E_FULLSCREEN:
        pygame.display.toggle_fullscreen()
        mainconfig["fullscreen"] ^= 1
      elif ev[1] == E_SCREENSHOT:
        print "writing next frame to screenshot.bmp"
        screenshot = 1
          
      gradetext = FONTS[32].render("Press ESC/ENTER/START",1, (i,128,128) )
      gradetextpos = gradetext.get_rect()
      gradetextpos.centerx = screen.get_rect().centerx
      gradetextpos.bottom = screen.get_rect().bottom - 16
      r = screen.blit(gradetext,gradetextpos)
      update_screen(r)
      pygame.time.wait(20)     # don't peg the CPU on the grading screen

      if screenshot:
        pygame.image.save(pygame.transform.scale(screen, (640,480)), "screenshot.bmp")
        screenshot = 0

    return

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

class DancerAnim(pygame.sprite.Sprite):
  def __init__(self,x,y):
    pygame.sprite.Sprite.__init__(self) #call Sprite initializer
    self.x = x
    self.y = y
    self.baseimage = pygame.surface.Surface((self.x,self.y))
    self.baseimage.fill((127,127,127))
    
  def update(self):
    self.image = self.baseimage
    x2 = self.x/2
    x4 = self.x/4
    x8 = self.x/8
    y2 = self.y/2
    y4 = self.y/4
    y8 = self.y/8
    pygame.draw.circle(self.image,(64,64,64),(x2,y4),x4)
    pygame.draw.polygon(self.image,(64,64,64),[(x2-x8,y4),(x2+x8,y4),(x2+x8,y4+y8),(x2-x8,y4+y8)])
    pygame.draw.polygon(self.image,(64,64,64),[(x2-x4,y4+y8),(x2+x4,y4+y8),(x2+x8,y2+y4),(x2-x8,y2+y4)])
    self.image.set_colorkey(self.image.get_at((0,0)))
    self.rect = self.image.get_rect()
    self.rect.top = 240-(self.y/2)
    self.rect.left = 480-(self.x/2)

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
    def __init__(self,playernum):
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
        self.rect.top = 112
        self.rect.left = 48+(320*self.playernum)

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
          
class LyricDispKludge(pygame.sprite.Sprite):
  def __init__(self,top,clrs):
      pygame.sprite.Sprite.__init__(self) #call Sprite initializer
      self.lyrics = []
      self.times = []
      self.prender = []
      self.lasttime = -1000

      self.space = pygame.surface.Surface((1,1))
      self.space.fill(colors.BLACK)

      self.oldlyric = -1
      self.oldalp = 0
      self.baseimage = self.space
      self.image = self.baseimage
      self.colors = clrs
      self.darkcolors = colors.darken_div(clrs)
      self.topimg = top

      self.rect = self.image.get_rect()
      self.rect.top = self.topimg
      self.rect.centerx = 320
      
  def addlyric(self, time, lyric):
    newlyric = ' '
    for i in lyric:
      newlyric += i + ' '
    self.lyrics.append(newlyric)
    self.times.append(time)

    image1 = FONTS[32].render(newlyric,1,self.darkcolors)
    image2 = FONTS[32].render(newlyric,1,self.colors)
    rimage = pygame.Surface(image1.get_size(), 0, 16)
    rimage.fill((64,64,64))
    rimage.blit(image1,(-2,-2))
    rimage.blit(image1,(2,2))
    rimage.blit(image2,(0,0))
    rimage.set_colorkey(rimage.get_at((0,0)))
    image = rimage.convert()

    self.prender.append(image)
#    print "kludge addlyric:", newlyric, " at", time, " length",len(newlyric)
    
  def update(self, curtime):
    self.currentlyric = -1
    timediff = curtime - self.lasttime
    for i in self.times:
      if curtime >= i:
#        print "curtime", curtime, "  i", i, "   index", self.times.index(i)
        self.currentlyric = self.times.index(i)
        self.lasttime = i

    if self.currentlyric != self.oldlyric:
      self.image = self.prender[self.currentlyric]
      self.rect = self.image.get_rect()
      self.rect.top = self.topimg
      self.rect.centerx = 320
    
    if (self.currentlyric > -1):
      holdtime = (len(self.lyrics[self.currentlyric])*0.045)
      alp = 255
      if timediff > holdtime:
        alp = 255-(255*(timediff-holdtime))
        if alp < 0:
          alp = 0
      if alp != self.oldalp:
        alp = int(alp)
        self.image.set_alpha(alp)
        self.oldalp = alp

    self.oldlyric = self.currentlyric
      
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

class Song:
  def __init__ (self, fn, path=None):
    # note that I'm only copying DIFFICULTIES because it's the right size..
    self.fn = fn
    self.modes = modes = MODES.copy()
    self.modelist = []
    self.modediff = {}
    self.modeinfo = {}
    self.modeinfodict = {}
    if path is None:
      path = os.path.dirname(fn)
    self.path = path
    for key in MODELIST: modes[key]=DIFFICULTIES.copy()
    curTime = 0.0
    curBPM = 0.0
    self.length = 0.0
    self.offset = 0.0
    self.isValid = 0
    self.crapout = 0
    self.startsec = 0.0
    self.endsec = -1.0
    self.bpm = 146.0
    self.lastbpmchangetime = [[0.0,self.bpm]]
    self.bgfile = ' '
    self.file = None
    self.moviefile = ' '
    self.playingbpm = 146.0    # while playing, event handler will use this for arrow control
    self.mixerclock = mainconfig['mixerclock']
    self.lyricdisplay = LyricDispKludge(400,
                                        colors.color[mainconfig['lyriccolor']])
    self.transdisplay = LyricDispKludge(428,
                                        colors.color[mainconfig['transcolor']])
    little = mainconfig["little"]
    coloringmod = 0
    self.totarrows = {}
    self.holdinfo = [None,None,None]
    self.holdref = [None,None,None]
    numholds = 1
    holdlist = []
    releaselist = []
    holdtimes = []
    releasetimes = []
    holding = [0,0,0,0]
    chompNext = None
    difficulty = None
    for fileline in open(fn).readlines():
      fileline = fileline.strip()
      if fileline == '' or fileline[0] == '#': continue
      fsplit = fileline.split()
      firstword = fsplit[0]
      if len(fsplit)>1:                nextword, rest = fsplit[1], fsplit[1:]
      else:                            nextword, rest = None, None
      if chompNext is not None:
        if len(chompNext) == 1:
          # look for the DIFFICULTY keyword, we already know which MODE
          modeDict, = chompNext
          curTime = float(self.offset)
          curBPM = self.bpm
          difficulty = firstword
          self.totarrows[difficulty] = 0
          modeDict[difficulty] = SongEvent(when=curTime,bpm=curBPM,extra=int(rest[0]))
          chompNext = modeDict,modeDict[difficulty]
        elif len(chompNext) == 2:
          modeDict, tail = chompNext
          if firstword == 'end':
            # mark the end of the song
            if self.length < curTime + toRealTime(curBPM,BEATS['halfn']):
              self.length = curTime + toRealTime(curBPM,BEATS['halfn'])

            # reset the colormask to the first one          
            coloringmod = 0

            # append the hold info for this mode
            if difficulty:
              self.holdinfo[DIFFICULTYLIST.index(difficulty)] = zip(holdlist,holdtimes,releasetimes)
              self.holdref[DIFFICULTYLIST.index(difficulty)] = zip(holdlist,holdtimes)

            # reset all the hold arrow stuff and operate on next mode
            holdlist = []
            releaselist = []
            holdtimes = []
            releasetimes = []
            holding = [0,0,0,0]
            numholds = 1
            
            chompNext = None
          elif firstword == 'atsec':
            curTime = float(nextword)
            tail.next = SongEvent(when=curTime,bpm=curBPM,extra='ATSEC')
            chompNext = modeDict, tail.next
          elif firstword == 'waits':
            curTime += float(nextword)
            tail.next = SongEvent(when=curTime,bpm=curBPM,extra='WAITS')
            chompNext = modeDict, tail.next
          elif firstword == 'ready':     
            tail.next = SongEvent(when=curTime,bpm=curBPM,extra='READY')
            coloringmod = 0
            chompNext = modeDict, tail.next
          elif firstword in BEATS.keys():
            cando = 1
            # make sure that this arrow is allowed in the current mode
            if (little==1) and (coloringmod%4==1):    cando = 0
            if (little==1) and (coloringmod%4==3):    cando = 0
            if (little==2) and (coloringmod%4==2):    cando = 0
            if (little==3) and (coloringmod%4==1):    cando = 0
            if (little==3) and (coloringmod%4==2):    cando = 0
            if (little==3) and (coloringmod%4==3):    cando = 0
            # make sure that we're not creating an arrow event with no arrows
            arrtotal = 0
            for i in rest:
              arrtotal += int(i)
            # create it
            if cando and arrtotal:
              feetstep = map(lambda x: int(x,16),rest)

              arrowcount = 0                             # keep track of the total arrows that will be hit at curtime
              for checkforjumps in range(4):             # guess what this function does
                  if (feetstep[checkforjumps] & 8):
                      if arrowcount and mainconfig['badknees'] and (holding[checkforjumps] == 0):
                          feetstep[checkforjumps] = 0    #don't xor, there could be a jump-hold
                      arrowcount += 1
              for checkforholds in range(4):             # guess what this function does
                  didnothold = 1
                  if (feetstep[checkforholds] & 128) and (holding[checkforholds] == 0):
                      holdtimes.insert(numholds,curTime)
                      holdlist.insert(numholds,checkforholds)
                      numholds += 1
                      holding[checkforholds] = numholds-1  # set the holding status to what's being held
                      didnothold = 0
                  elif ((feetstep[checkforholds] & 128) or (feetstep[checkforholds] & 8)) and holding[checkforholds] and didnothold:
                      releasetimes.insert(holding[checkforholds],curTime)
                      releaselist.insert(holding[checkforholds],checkforholds)
                      feetstep[checkforholds] = 0       # drop the whole event in the event of a broken stepfile
                      holding[checkforholds] = 0
              tail.next = SongEvent(when=curTime,
                                    bpm=curBPM,
                                    feet=feetstep,
                                    extra=firstword,
                                    color=(coloringmod%4))
              for arrowadder in feetstep:
                if arrowadder & 8:
                  self.totarrows[difficulty] += 1
              chompNext = modeDict, tail.next
            curTime += toRealTime(curBPM,BEATS[firstword])
            coloringmod += BEATS[firstword]
          elif firstword == 'delay':
            curTime += toRealTime(curBPM,BEATS['qurtr']*float(nextword))
            coloringmod += (4*float(nextword))
            tail.next = SongEvent(when=curTime,bpm=curBPM,extra="DELAY")
            chompNext = modeDict, tail.next
          elif firstword == 'chbpm':
            curBPM = float(nextword)
            tail.next = SongEvent(when=curTime,bpm=curBPM,extra="CHBPM")
            chompNext = modeDict, tail.next
          elif firstword == 'tstop':
            tail.next = SongEvent(when=curTime,bpm=float(nextword),extra="TSTOP")
            curTime += float(nextword)/1000
            print "found total stop at",curTime
            chompNext = modeDict, tail.next
          elif firstword == 'lyric':
             self.lyricdisplay.addlyric(curTime-0.4,rest)
             tail.next = SongEvent(when=curTime,bpm=curBPM,extra=('LYRIC',rest))
             chompNext = None,tail.next
          elif firstword == 'trans':
             self.transdisplay.addlyric(curTime-0.4,rest)
             tail.next = SongEvent(when=curTime,bpm=curBPM,extra=('TRANS',rest))
             chompNext = None,tail.next
      elif firstword == 'LYRICS':
        curTime = 0.0
        curBPM = self.bpm
        difficulty = None
        self.lyrics = SongEvent(when=curTime,bpm=curBPM)
        chompNext = None,self.lyrics
      elif firstword == 'song':        self.song = " ".join(rest)
      elif firstword == 'group':       self.group = " ".join(rest)
      elif firstword == 'bpm':
        self.bpm = float(nextword) 
        if mainconfig['onboardaudio']:
          self.bpm = self.bpm * float(48000/44128.0)
        self.playingbpm = self.bpm
      elif firstword in modes.keys():  chompNext=(modes[firstword],)
      elif firstword == 'file':        self.file = " ".join(rest)
      elif firstword == 'bg':
        self.bgfile = os.path.join(os.path.split(fn)[0], " ".join(rest))
      elif firstword == 'movie':
        self.moviefile = os.path.join(os.path.split(fn)[0], " ".join(rest))
      elif firstword == 'startat':     self.startsec = float(nextword)
      elif firstword == 'endat':       self.endsec = float(nextword)
      elif firstword == 'offset':      
        self.offset = float(-int(nextword)-mainconfig['masteroffset'])/1000.0
        if mainconfig['onboardaudio']:
          self.offset = self.offset * float(48000/44128.0)
      elif firstword == 'version':     self.version = float(nextword)
    for mkey,mval in modes.items():
      if mval is not None:
        for dkey,dval in mval.items():
          if dval is None: del(mval[dkey])
        if len(mval.keys()) == 0: mval = None
      if mval is None: del(modes[key])
    if len(modes.keys()): 
      print repr(self)
    self.isValid=1
    # setup lists to make it easy and in order for the osong selector
    self.modelist = filter(lambda m,modes=modes: modes.has_key(m), MODELIST)

    if path is None:
      self.path = os.path.dirname(fn)

    if self.file is None:
      self.file = string.join(fn[len(self.path)+1:-5].split("/")[-1:],"")
      for ext in [".ogg",".mp3",".wav",".mid"]:
        if os.path.isfile(os.path.join(self.path,self.file+ext)):
          self.file = self.file+ext

    self.osfile=os.path.join(self.path,self.file)

    for m in self.modelist:
      # get filtered list of difficulties in proper order
      self.modediff[m] = filter(lambda d,diffs=modes[m]: diffs.has_key(d), DIFFICULTYLIST)
      tmp = []
      # head of every difficulty list is just difficulty info, get info and discard head
      for d in self.modediff[m]:
        tmp.append(modes[m][d].extra)
        modes[m][d] = modes[m][d].next
      # zip together the difficulties and their "hardness" for easy usage
      self.modeinfo[m] = zip(self.modediff[m],tmp)
      self.modeinfodict[m] = dict(self.modeinfo[m])

  def init(self):
    try:
      pygame.mixer.music.load(self.osfile)
    except pygame.error:
      print "Not a supported filetype"
      self.crapout = 1
    if self.startsec > 0.0:
      print "Skipping %f seconds" % self.startsec

  def play(self,mode,difficulty,actuallyplay):
    try:
      if self.crapout == 0 and actuallyplay:
        pygame.mixer.music.play(0, self.startsec)
    except TypeError:
      print "Sorry, pyDDR needs a more up to date Pygame or SDL than you have."
      sys.exit(1)

    self.curtime = 0.0
    self.tickstart = pygame.time.get_ticks()
    self.head = self.fhead = self.modes[mode][difficulty]

  def kill(self):
#    self.ss.stop()
    pygame.mixer.music.stop()

  def get_time(self):
    if self.mixerclock:
      self.curtime = float(pygame.mixer.music.get_pos())/1000.0 # -self.tickstart causes desync
    else:
      self.curtime = float(pygame.time.get_ticks() - self.tickstart)/1000.0
    return self.curtime

  def get_events(self):
    events,nevents = [],[]
    time = self.get_time()
    end = self.endsec
    head = self.head
    fhead = self.fhead
    arrowtime = None
    bpm = None
    events_append,nevents_append = events.append,nevents.append
    while (head and head.when <= (time + 2*toRealTime(head.bpm, 1))):
#    while (head and head.when <= (time + 2*toRealTime(self.playingbpm, 1))):
      events_append(head)
      head=head.next
    self.head = head

    if (time>=end and end>0):
      self.kill()
      return None
    elif not pygame.mixer.music.get_busy():
      self.kill()
#      print "not busy"
      return None
    
    if head and fhead:
      bpm = self.playingbpm
      arrowtime = 512.0/bpm
      ntime = time + arrowtime
      while (fhead and fhead.when <= ntime):
        self.playingbpm = fhead.bpm
        nevents_append(fhead)
        fhead=fhead.next
      self.fhead=fhead
    return events,nevents,time,bpm

  def isOver(self):
    if (not pygame.mixer.music.get_busy()) or (self.endtime>0 and self.curtime>=self.endtime):
      return 1
    return 0
  
  def __nonzero__ (self):
    return self.isValid
    
  def __repr__ (self):
    return '<song song=%r group=%r bpm=%s file=%r>'%(self.song,self.group,repr(self.bpm)[:7],self.file)

#  def __getattr__ (self,attr):
#    # act like a pygame.movie instance
#    return getattr(self.ss,attr)

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

#DCY: Bottom of 640 gives lots of "update rejecting"    
if mainconfig['reversescroll']:
  ARROWTOP  = 408
  ARROWBOT  = int(-64 - (mainconfig['scrollspeed']-1)*576)
else:
  ARROWTOP  = 64
  ARROWBOT  = int(576 * mainconfig['scrollspeed'])

ARROWDIFF = float(ARROWTOP-ARROWBOT)

class ArrowSprite(CloneSprite):
  def __init__ (self, spr, curtime, endtime, bpm, playernum, zindex=ARROWZINDEX):
    CloneSprite.__init__(self,spr,zindex=zindex)
    self.timeo = curtime
    self.timef = endtime
    self.life  = endtime-curtime
    self.bpm = bpm
    self.curalpha = -1
    self.dir = spr.fn[-7:-6]
    if mainconfig['assist']:
      self.playedsound = None
      self.sample = pygame.mixer.Sound(os.path.join(sound_path, "assist-" + self.dir + ".ogg"))
    else:
      self.playedsound = 1
    self.r = 0
    self.playernum = playernum
    self.bimage = self.image
    self.arrowspin = float(mainconfig["arrowspin"])
    self.arrowscale = float(mainconfig["arrowscale"])
    
    self.centerx = self.rect.centerx+(self.playernum*320)
    
  def update (self,curtime,curbpm,lbct,hidden,sudden):
    # assist
    if (self.playedsound is None) and (curtime >= self.timef -0.0125): #- (0.001*(60000.0/curbpm))):
      self.sample.play()
      self.playedsound = 1

    if curtime > self.timef + (0.001*(60000.0/curbpm)):
      self.kill()
      return
      
    self.rect = self.image.get_rect()
    self.rect.centerx = self.centerx

    self.top = ARROWTOP
    finaltime = 0
    
    if len(lbct)<2:
      onebeat = float(60000.0/curbpm)/1000
      doomtime = self.timef - curtime
      beatsleft = float(doomtime / onebeat)
      self.top = self.top - int( (beatsleft/8.0)*ARROWDIFF )
    else:
      oldbpmsub = [curtime,curbpm]
      bpmbeats = 0
      for bpmcheck in range(len(lbct[-1])-1):
        bpmsub = lbct[bpmcheck+1]
#        print "bpmsub[0]",bpmsub[0],"curtime",curtime
        if bpmsub[0] <= self.timef:
#          print "adjusting for",bpmsub,
#          onefbeat = float(60000.0/bpmsub[1])/1000
          onefbeat = float(60000.0/curbpm)/1000
          bpmdoom = bpmsub[0] - oldbpmsub[0]
          bpmbeats = float(bpmdoom / onefbeat)
#          print "bpmbeats",bpmbeats
          self.top = self.top - int(bpmbeats*ARROWDIFF/8.0)
          oldbpmsub = bpmsub
      if not finaltime:
#        print "adjusting for finaltime",
        onefbeat = float(60000.0/oldbpmsub[1])/1000
#        onefbeat = float(60000.0/curbpm)/1000
        bpmdoom = self.timef - oldbpmsub[0] 
        bpmbeats = float(bpmdoom / onefbeat)
#        print "bpmbeats",bpmbeats
        self.top = self.top - int(bpmbeats*ARROWDIFF/8.0)
        finaltime = 1
            
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

    hiddenzone = ( 64 + int(64.0*hidden) )
    suddenzone = ( 480 - int(64.0*sudden) )
    alp = 0
    self.curalpha = self.get_alpha()
    if self.rect.top < hiddenzone:
      alp = 255-(hiddenzone-self.rect.top)*4
    if self.rect.top > hiddenzone:
      if self.rect.top < suddenzone:
        alp = (suddenzone-self.rect.top)*4
    if alp < 0:      alp = 0
    if alp > 255:    alp = 255
    if alp != self.curalpha:
      self.image.set_alpha(alp)

class HoldArrowSprite(CloneSprite):
  def __init__ (self, spr, curtime, times, bpm, lastbpmtime, playernum, zindex=ARROWZINDEX):
    CloneSprite.__init__(self,spr,zindex=zindex)
    self.timeo = curtime
    self.timef1 = times[1]
    self.timef2 = times[2]
    self.timef = times[2]
    self.life  = times[2]-curtime
    self.bpm = bpm
    self.lastbpmtime = lastbpmtime
    self.playernum = playernum
    self.curalpha = -1
    self.dir = spr.fn[-7:-6]
    self.playedsound = None
    if mainconfig['assist']:
      self.sample = pygame.mixer.Sound(os.path.join(sound_path, "assist-" + self.dir + ".ogg"))
    else:
      self.playedsound = 1
    self.r = 0
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

    self.top = ARROWTOP
    self.bottom = ARROWTOP #+ int(ARROWDIFF/8.0)

    finaltime = 0
    if len(lbct)<2: # single run (I hope)
      onebeat = float(60000.0/curbpm)/1000
      doomtime = self.timef1 - curtime
      if doomtime < 0:
        doomtime = 0
      beatsleft = float(doomtime / onebeat)
      self.top = self.top - int( (beatsleft/8.0)*ARROWDIFF )
      doomtime = self.timef2 - curtime
      beatsleft = float(doomtime / onebeat)
      self.bottom = self.bottom - int( (beatsleft/8.0)*ARROWDIFF )
    else:
      oldbpmsub = [curtime,curbpm]
      bpmbeats = 0
      for bpmcheck in range(len(lbct[-1])-1):
        bpmsub = lbct[bpmcheck+1]
#        print "bpmsub[0]",bpmsub[0],"curtime",curtime
        if bpmsub[0] <= self.timef1 or bpmsub <= self.timef2:
#          print "adjusting for",bpmsub,
#          onefbeat = float(60000.0/bpmsub[1])/1000
          onefbeat = float(60000.0/curbpm)/1000
          bpmdoom = bpmsub[0] - oldbpmsub[0]
          bpmbeats = float(bpmdoom / onefbeat)
#          print "bpmbeats",bpmbeats
	  if bpmsub[0] <= self.timef1:
	    self.top = self.top - int(bpmbeats*ARROWDIFF/8.0)
          if bpmsub[0] <= self.timef2:
            self.bottom = self.bottom - int(bpmbeats*ARROWDIFF/8.0)
          oldbpmsub = bpmsub
      if not finaltime:
#        print "adjusting for finaltime",
        onefbeat = float(60000.0/oldbpmsub[1])/1000
#        onefbeat = float(60000.0/curbpm)/1000
        bpmdoom = self.timef1 - oldbpmsub[0]
        bpmbeats = float(bpmdoom / onefbeat)
#        print "bpmbeats1=",bpmbeats1," bpmbeats2=",bpmbeats2
        self.top = self.top - int(bpmbeats*ARROWDIFF/8.0)
        bpmdoom = self.timef2 - oldbpmsub[0]
        bpmbeats = float(bpmdoom / onefbeat)
        self.bottom = self.bottom - int(bpmbeats*ARROWDIFF/8.0)
        finaltime = 1

    if self.bottom > 480:
      self.bottom = 480
    if self.bottom < 64:
      self.bottom = 64
    self.rect.bottom = self.bottom
 
    if self.top > 480:
      self.top = 480
    if self.top < 64:
      self.top = 64
    self.rect.top = self.top
    
#    print "top",self.top,"bottom",self.bottom
    holdsize = self.bottom-self.top
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

    hiddenzone = ( 64 + int(64.0*hidden) )
    suddenzone = ( 480 - int(64.0*sudden) )
    alp = 255
    self.curalpha = self.get_alpha()
    if self.rect.top < hiddenzone:
      alp = 255-(hiddenzone-self.rect.top)*4
    if self.rect.top > hiddenzone:
      if self.rect.top < suddenzone:
        alp = (suddenzone-self.rect.top)*4
    if alp < 0:      alp = 0
    if alp > 255:    alp = 255
    if alp != self.curalpha:
      self.image.set_alpha(alp)
  
#    print "alpha ",alp

def text_fadeon(screen, font, message, center, fadetime=500):
    start = pygame.time.get_ticks()
    ticktime = fadetime / 30
    for i in range(31):
      color = 8*i, 8*i, 8*i
      text = font.render(message, 1, color, (0,0,0))
      trect = text.get_rect()
      trect.center = center
      r = screen.blit(text, trect)
      update_screen(r)
      pygame.time.delay(ticktime*i - (pygame.time.get_ticks() - start))
def text_fadeoff(screen, font, message, center, fadetime=300):
    start = pygame.time.get_ticks()
    ticktime = fadetime / 30
    for i in range(31):
      color = 8*(30-i), 8*(30-i), 8*(30-i)
      text = font.render(message, 1, color, (0,0,0))
      trect = text.get_rect()
      trect.center = center
      r = screen.blit(text, trect)
      update_screen(r)
      pygame.time.delay(ticktime*i - (pygame.time.get_ticks() - start))


def update_screen_hardware(dirty=None):
    pass
def update_screen_doublebuffer(dirty=None):
    pygame.display.flip()
def update_screen_software(dirty=None):
    pygame.display.update(dirty)
update_screen = update_screen_software

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
  global screen, background, playmode
  print "pyDDR, by theGREENzebra (tgz@clickass.org)"
  print "Initialising.."

  # set up the screen and all that other stuff
  pygame.init()

  players = 1

  # DEBUG MODE - user just wants to test a step file
  debugmode = 0
  if len(sys.argv) > 1:
    debugmode = 1
    stepspecd = sys.argv[1]
    if stepspecd[-5:] != ".step":
      stepspecd += ".step"
    stepspecd = os.path.join(songdir,stepspecd)
    if len(sys.argv) > 2:
      difficulty = [string.upper(sys.argv[2])]
      if len(sys.argv) > 3:
        difficulty.append(string.upper(sys.argv[3]))
        players = 2
    else:
      difficulty = ['BASIC']

  SetDisplayMode(mainconfig)
  
  pygame.display.set_caption('pyDDR')
  pygame.mouse.set_visible(0)

  global update_screen
  if (screen.get_flags()&DOUBLEBUF == DOUBLEBUF):
      update_screen = update_screen_doublebuffer
  elif screen.get_flags()&HWSURFACE:
      update_screen = update_display_hardware
  #else it defaults to software update rect

  pygame.mixer.music.load(os.path.join(sound_path, "menu.ogg"))
  try:
    pygame.mixer.music.play(4, 0.0)
  except TypeError:
    print "Sorry, pyDDR needs a more up to date Pygame or SDL than you have."
    sys.exit()

  background = BlankSprite(screen.get_size())

  playmode = 'SINGLE'
  
  if debugmode:
    print "Entering debug mode. Not loading the song list."
    totalsongs = 1
  else:
    # Search recursively for all STEP files
    fileList = []
    for dir in songdir.split(os.pathsep):
      print "Searching", dir
      fileList += find(dir, '*.step')

  totalsongs = len(fileList)
  parsedsongs = 0
  songs = []

  pbar = fontfx.TextProgress(FONTS[60], "Found " + str(totalsongs) +
                             " files. Loading...", colors.WHITE, colors.BLACK)
  for f in fileList:
    try: songs.append(fileparsers.SongItem(f))
    except:
      print "Error loading " + f
    img = pbar.render(parsedsongs / totalsongs)
    r = img.get_rect()
    r.center = (320, 240)
    screen.blit(img, r)
    pygame.display.flip()
    parsedsongs += 100.0

  ev = event.poll()
  while ev[1] != E_PASS: ev = event.poll()

  difWrap = 2*len(DIFFICULTIES)

  if len(songs) < 1:
    print "You don't have any songs, and you need one. Go here: http://icculus.org/pyddr/"
    sys.exit()

  menudriver.do(screen, (songs, screen, playSequence, GradingScreen))
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

  players = []
  for playerID in range(numplayers):
    plr = Player(playerID, HoldJudgeDisp(playerID), ComboDisp(playerID), DIFFICULTYLIST)
    players.append(plr)
    
  for songfn, diff in playlist:
    current_song = Song(songfn)
    pygame.mixer.quit()
    prevscr = pygame.transform.scale(screen, (640,480))
    screen.fill(colors.BLACK)

    for pid in range(len(players)):
      players[pid].set_song(copy.copy(current_song), diff[pid], Judge)

    if dance(current_song, players): break # Failed
    
  return [player.judge for player in players]

def dance(song, players):
  global screen,background,playmode

  songFailed = True

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

  # dancer group
  #dgroup = RenderLayered()

  if song.moviefile != ' ':
    backmovie = BGmovie(song.moviefile)
    backmovie.image.set_alpha(mainconfig['bgbrightness'], RLEACCEL)
  else:
    backmovie = BGmovie(None)
    
  if song.bgfile != ' ':
    backimage = BGimage(song.bgfile)
  else:
    try:
      bifn = song.fn[:-5] + '-bg.png'
      backimage = BGimage(bifn)
    except pygame.error:
      bifn = os.path.join(image_path, 'bg.png')
      backimage = BGimage(os.path.join(image_path, 'bg.png'))

  if mainconfig['showbackground'] > 0:
    if backmovie.filename == None:
      bgkludge = pygame.transform.scale(pygame.image.load(bifn),(640,480)).convert()
      bgkludge.set_alpha(mainconfig['bgbrightness'], RLEACCEL)
      background.image = pygame.surface.Surface((640,480))
      background.image.blit(bgkludge,(0,0))
      backimage.add(bgroup)
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

#  dancer = DancerAnim(200,400)
#  dancer.add(dgroup)
  
  colortype = mainconfig['arrowcolors']
  if colortype == 0:
    colortype = 1

  if mainconfig['fpsdisplay']:
    tgroup.add(fpstext)
    tgroup.add(timewatch)

  if mainconfig['showlyrics']:
    song.lyricdisplay.add(lgroup)
    song.transdisplay.add(lgroup)

  showcombo = mainconfig['showcombo']
  
  bg = pygame.Surface(screen.get_size())
  bg.fill((0,0,0))

  songtext = zztext(song.song,480,12)
  grptext = zztext(song.group,160,12)

  songtext.zin()
  grptext.zin()

  tgroup.add(songtext)
  tgroup.add(grptext)
  tgroup.add(timewatch)

  bgroup.draw(screen)

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

  for plr in players:
    plr.start_song()
    for arrowID in DIRECTIONS:
      if mainconfig['explodestyle'] > -1:
        plr.toparrfx[arrowID].add(fgroup)
      if mainconfig['showtoparrows']:
        plr.toparr[arrowID].add(sgroup)
      
  oldbpm = song.playingbpm
  bpmchanged = 0
  
  while 1:
    if mainconfig['autofail']:
      songFailed = 1
      for plr in players:
        if plr.lifebar.failed == 0:
          songFailed = 0
          break
      if songFailed:
        song.kill()

    for plr in players: plr.get_next_events()

    if players[0].evt is None:
      if song.isOver():
        break
    else:
      # we need the current time for a few things, and it should be the same for all players
      curtime = players[0].evt[2]
    
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

    if ev[1] == E_QUIT: break
  
    for keyAction in key:
      playerID = keyAction[0]
      if playerID < len(players):
        keyPress = keyAction[1]
        players[playerID].toparr[keyPress].stepped(1, curtime+(song.offset*1000))
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
        else:
          if plr.tempholding[dirID] > -1:
            if plr.judge.holdsub[plr.tempholding[dirID]] != -1:
              plr.tempholding[dirID] = -1
              plr.holdtext.fillin(curtime,dirID,"OK")
    
      if plr.evt is not None:
        # handle events that are happening now
        events,nevents,curtime,bpm = plr.evt
        
        for ev in events:
          #print "current event: %r"%ev
          if ev.extra == 'CHBPM':
            if (bpm != plr.judge.getbpm()):
              plr.judge.changingbpm(ev.bpm)
          elif ev.extra == 'TSTOP' and plr.pid == 0:
            # FIXME only pause for the first player
            pygame.time.wait(ev.bpm)
          if ev.feet:
            for (dir,num) in zip(DIRECTIONS,ev.feet):
              if num & 8:
                plr.judge.handle_arrow(dir, curtime, ev.when)
         
        for ev in nevents:
          #print "future event: %r"%ev
          if ev.extra == 'CHBPM' and plr.pid == 0:
            song.lastbpmchangetime.append([ev.when,ev.bpm])
            print [ev.when,ev.bpm], "was added to the bpm changelist"
          
          if ev.feet:
            for (dir,num) in zip(DIRECTIONS, ev.feet):
              if num & 8:
                if not (num & 128):
                  ArrowSprite(plr.theme.arrows[dir+repr(int(ev.color)%colortype)].c, curtime, ev.when, ev.bpm, plr.pid).add([plr.arrow_group, rgroup])

              if num & 128:
                diffnum = DIFFICULTYLIST.index(plr.difficulty)
                holdindex = song.holdref[diffnum].index((DIRECTIONS.index(dir),ev.when))
                HoldArrowSprite(plr.theme.arrows[dir+repr(int(ev.color)%colortype)].c, curtime, song.holdinfo[diffnum][holdindex], ev.bpm, song.lastbpmchangetime[0], plr.pid).add([plr.arrow_group, rgroup])
          
    if len(song.lastbpmchangetime) > 1:
      if (curtime >= song.lastbpmchangetime[1][0]):
        nbpm = song.lastbpmchangetime[1][1]
        for plr in players:  plr.change_bpm(nbpm)
        print "BPM changed from", oldbpm, "to", nbpm
        print "Last changed BPM at", song.lastbpmchangetime
        oldbpm = nbpm
        song.lastbpmchangetime.pop(0)
        bpmchanged = 0
     
    for plr in players: plr.check_sprites(curtime)

    if(mainconfig['strobe']):
      extbox.update(curtime+(song.offset*1000.0))
    
    song.lyricdisplay.update(curtime)
    song.transdisplay.update(curtime)

    for plr in players: plr.combo_update(curtime)
    
#    dancer.update()
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

    if (curtime > song.length - 1) and (songtext.zdir == 0) and (songtext.zoom > 0):
      songtext.zout()
      grptext.zout()

  try:
    print "LPS for this song was %d tops, %d on average, %d at worst." % (fpstext.highest, fpstext.fpsavg(), fpstext.lowest)
  except:
    pass
    
  return songFailed

if __name__ == '__main__': main()
