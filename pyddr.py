#! /usr/bin/env python

# pyDDR - DDR clone written in Python
# I know the dependencies suck, but in terms of programming so do I.
# SONG SELECTOR

#import psyco
#psyco.jit()
#from psyco.classes import *


from announcer import Announcer
from config import Config
import pygame, pygame.surface, pygame.font, pygame.image, pygame.mixer, pygame.movie, pygame.sprite
import os, sys, glob, random, fnmatch, types, operator, copy, string
import pygame.transform

osname = None
if os.name == "nt": osname = "nt"
elif os.name == "posix":
  if os.path.islink("/System/Library/CoreServices/WindowServer"):
    osname = "macosx"
  elif os.environ.has_key("HOME"):
    osname = "posix"
else:
  print "Your platform (%s) is not supported by pyDDR. We're going to call it"
  print "POSIX, and then just let it crash."

# Run pyDDR from anywhere
pyddr_path = os.path.split(os.path.abspath(sys.argv[0]))[0]
sys.path.append(pyddr_path)
os.chdir(pyddr_path)

rscdir = None

if osname == "posix":
  rscdir = os.path.join(os.environ["HOME"], ".pyddr")
  if not os.path.isdir(rscdir): os.mkdir(rscdir)
elif osname == "macosx":
  rscdir = os.path.join(os.environ["HOME"], "Library", "Preferences", "pyDDR")
elif osname == "nt":
  rscdir = "."

if not os.path.isdir(rscdir): os.mkdir(rscdir)

import fontfx
from pygame.locals import *
from stat import *

#phasing out numeric/surfarray
#import pygame.surfarray
#from Numeric import *

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


pygame_time_get_ticks = pygame.time.get_ticks
BLACK=(0,0,0)
WHITE=(255,255,255)

# extend the sprite class with layering support
DEFAULTZINDEX,PADZINDEX,ARROWZINDEX,XANIMZINDEX,BARSZINDEX = range(5)
pygame.sprite.Sprite.zindex = DEFAULTZINDEX
#def zcompare(self,other):
#  return cmp(self.zindex,other.zindex)
#pygame.sprite.Sprite.__cmp__ = zcompare

class QuitGame:
  def __init__(self,reason):
    self.reason = reason

  def __str__(self):
    return self.reason
  
#_pixels3d   = pygame.surfarray.pixels3d
#_blit_array = pygame.surfarray.blit_array

#def (surf,color):
#  size = surf.rect.width*surf.rect.height
#  surf=surf.image
#  narray=_pixels3d(surf).astype(Float32)
#  reshape(narray,[size,3])
#  narray*=array(color).astype(Float32)
#  _blit_array(surf,narray.astype(Int8))

#MAIN CONFIG FILE

mainconfig = Config({ # Wow we have a lot of options
  "gfxtheme": "classic", "djtheme": "none", "songdir": ".",
  "stickycombo": 1,  "lowestcombo": 4,  "totaljudgings": 1,  "stickyjudge": 1,
  "lyriccolor": "0,244,244",  "transcolor": "0,244,122",
  "mixerclock": 0, "onboardaudio": 0, "masteroffset": 0,
  "reversescrolls": 0, "scrollspeed": 1,
  "explodestyle": 3, "arrowspin": 0, "arrowshrink": 0, "arrowgrow": 0,
  "joy_left": 4, "joy_right": 5, "joy_up": 7, "joy_down": 6,
  "joy_start": 9, "joy_select": 8, "joy_pgup": 1, "joy_pgdown": 3,
  "mat_buttons": 12, "mat_axes": 6,
  "vesacompat": 0, "fullscreen": 0,
  "sortmode": 0, "sortpersist": 1,
  "previewmusic": 1,
  "showbackground": 1, "bgbrightness": 127,
  "sudden": 0, "hidden": 0, "little": 0, "assist": 0,
  "arrowcolors": 4, "fpsdisplay": 1, "showlyrics": 1,
  "showcombo": 1, "showtoparrows": 1,
  "killsongonfail": 0,
  "grading": 1,
  "keyboard": "qwerty"
  })

if osname == "posix":
  mainconfig.load("/etc/pyddr.cfg", True)
elif osname == "macosx":
  mainconfig.load("/Library/Preferences/pyDDR/pyddr.cfg")

mainconfig.load("pyddr.cfg")
mainconfig.load(os.path.join(rscdir, "pyddr.cfg"))

DefaultThemeDir = os.path.join('themes','gfx')
theme = mainconfig['gfxtheme']
songdir = mainconfig['songdir']
anncname = mainconfig['djtheme']
annc = Announcer(os.path.join('themes','dj',anncname,'djtheme.cfg'))

p1d = p1u = p1l = p1r = p2l = p2r = p2u = p2d = 0

# Keyboard configuration
if mainconfig["keyboard"] == "qwerty":
  p1u, p1d, p1l, p1r = K_i, K_k, K_j, K_l
  p2u, p2d, p2l, p2r = K_UP, K_DOWN, K_LEFT, K_RIGHT
elif mainconfig["keyboard"] == "dvorak":
  p1u, p1d, p1l, p1r = K_c, K_t, K_h, K_n
  p2u, p2d, p2l, p2r = K_UP, K_DOWN, K_LEFT, K_RIGHT  

if mainconfig["p1_keys"]: p1u, p1d, p1l, p1r = eval(mainconfig["p1_keys"])
if mainconfig["p2_keys"]: p2u, p2d, p2l, p2r = eval(mainconfig["p2_keys"])

"""
def colorMultiply(surf,color):
  size = surf.rect.width*surf.rect.height
  surf=surf.image
  try:
    narray=_pixels3d(surf).astype(Float32)
    reshape(narray,[size,3])
    narray*=array(color).astype(Float32)
    _blit_array(surf,narray.astype(Int8))
  except:
    surfNew=surf.convert(32)
    narray=_pixels3d(surfNew).astype(Float32)
    narray*=array(color).astype(Float32)
    _blit_array(surfNew,narray.astype(Int8))
    surf.blit(surfNew,(0,0))
"""

class Theme:
  def __init__(self,name,themeDir=DefaultThemeDir):
    self.name = name
    self.themeDir = themeDir
    self.load()

  def load(self):
    name=self.name
    if self.themeDir: 
      path=os.path.join(self.themeDir,name)
    else:
      path=name
    self.arrows = ArrowSet(path)
    self.bars   = BarSet(path)
    self.xanim  = Xanim(path)

  def __repr__(self):
    return '<Theme name=%r>'%self.name

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

def toRealTime(bpm,steps):
  if bpm != 0:
    return steps*0.25*60.0/bpm
  else:
    return steps*0.25*60.0/146

class BGimage(pygame.sprite.Sprite):
  def __init__ (self, filename):
    pygame.sprite.Sprite.__init__(self)        #call Sprite initializer
    self.image = pygame.transform.scale(pygame.image.load(filename),(640,480)).convert()
    self.image.set_alpha(int(mainconfig['bgbrightness']), RLEACCEL)
    self.rect = self.image.get_rect()
    self.rect.top = 0
    self.rect.left = 0
    self.needsupdate = 0

  def update(self):
    if self.needsupdate:
      self.rect = self.image.get_rect()
      self.rect.top = 0
      self.rect.left = 0

class BGmovie(pygame.sprite.Sprite):
  def __init__ (self, filename):
    pygame.sprite.Sprite.__init__(self)        #call Sprite initializer
    self.filename = filename
    self.image = pygame.surface.Surface((640,480))
    if filename:
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
      curframe = int( (curtime * 29.97) )
      if self.oldframe != curframe:
        self.changed = 1
        self.movie.render_frame(curframe)
        self.oldframe = curframe

class keykludge:
  def __init__ (self):
    self.directionlist = ['l','d','u','r']
    self.holdingstates = [ 0 , 0 , 0 , 0 ]
  
  def pressed(self,direction):
    self.holdingstates[self.directionlist.index(direction)] = 1
    
  def letgo(self,direction):
    self.holdingstates[self.directionlist.index(direction)] = 0
    
  def shouldhold(self,direction,curtime,list,bpm):
    for i in range(len(list)):
      if list[i][0] == self.directionlist.index(direction):
        if (curtime - (15.0/float(bpm)) > list[i][1]) and (curtime < list[i][2]):
          return i
    
  def checkstate(self,direction):
    return self.holdingstates[self.directionlist.index(direction)]


class Judge:
  def __init__ (self, bpm, holds, feet, stepcount, diff):
    self.steps = {}
    self.actualtimes = {}
    self.tick = toRealTime(bpm, 1)
    self.oldtick = toRealTime(bpm, 1)
    self.marvelous = self.perfect = self.great = self.ok = self.crap = self.shit = self.miss = 0
    self.combo = self.bestcombo = self.broke = 0
    self.steppedtime = -1000
    self.recentsteps = [' ',' ',' ']
#    self.table = string.maketrans("", "")
    self.early = self.late = self.ontime = 0
    self.totalcombos = 1
    self.bpm = bpm
    self.oldbpm = bpm
    self.diff = diff
    scorecoeff = (((5000000.0 * (feet + 1.0)) / 10.0) /
                  (stepcount * (stepcount + 1.0) / 2.0)) # 5th mix
    self.score_coeff = int(scorecoeff) + 1
    self.score = 0
    self.badholds = 0
    self.holdsub = []
    for i in range(holds):
      self.holdsub.append(0)
    
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
      if off < 7:
        self.steppedtime = curtime
        self.combo += 1
        if self.combo > self.bestcombo:
          self.bestcombo = self.combo 

        if off <= 1:
          self.marvelous += 1
          self.score += 20 * self.score_coeff * self.combo
          text = "MARVELOUS"
          anncrange = (80, 100)
        elif 1 < off <= 4:
          self.perfect += 1
          self.score += 10 * self.score_coeff * self.combo
          text = "PERFECT"
          anncrange = (80, 100)
        else:
          self.great += 1
          self.score += 5 * self.score_coeff * self.combo
          text = "GREAT"
          anncrange = (70, 94)

      else:
        self.steppedtime = curtime
        self.totalcombos += 1
        self.broke = 1
        self.combo = 0
        if off < 9:
          self.ok += 1
          text = "OK"
          self.score += 2 * self.score_coeff
          anncrange = (40, 69)
        elif off < 11:
          self.crap += 1
          text = "CRAPPY"
          anncrange = (20, 39)
        else:
          self.shit += 1
          text = "SHIT"
          anncrange = (6, 30)
#      else:
#        text = "woah"
#        print "Ack! off is", off

      if random.randrange(15) == 1:
        annc.say('ingame',anncrange)
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
          self.recentsteps.pop()
  
  def handle_arrow(self, key, time, etime):
      multicheck = self.tick
      tick_6 = multicheck / 6
      curtick = round((time + 2*multicheck) / tick_6)
      self.times = self.steps.keys()
      self.actualtimes[curtick] = etime
      if curtick in self.times:
        self.steps[curtick] += key
        match = 1
      else:
        self.steps[curtick] = key
        self.times = self.steps.keys()
        match = 1
        
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
                  self.crap + self.shit + self.miss)

    if totalsteps == 0: return "?"

    marvpct = self.marvelous * 100.0 / totalsteps
    perfectpct = self.perfect * 100.0 / totalsteps
    greatpct = self.great * 100.0 / totalsteps
    okpct = self.ok * 100.0 / totalsteps
    crappypct = self.crap * 100.0 / totalsteps
    shitpct = self.shit * 100.0 / totalsteps
    misspct = self.miss * 100.0 / totalsteps
    mpg_count = self.marvelous + self.perfect + self.great

    #pick a grade
    if self.marvelous == totalsteps: return '!!!'
    elif self.marvelous + self.perfect == totalsteps: return 'wow'
    elif (marvpct + perfectpct >= 92) and (mpg_count == totalsteps):
      return 'SSS'
    elif ((self.marvelous + self.perfect >= self.great) and
          (mpg_count == totalsteps)):
      return 'SS'
    elif mpg_count == totalsteps:
      return 'S'
    elif ((mpg_count >= totalsteps*0.8) and (misspct <= 2) and
          (shitpct <= 4) and (crappypct <= 6) and (okpct <= 8)):
      return 'A'
    elif ((mpg_count >= totalsteps*0.6) and (misspct <= 4) and
          (shitpct <= 8) and (crappypct <= 12) and (okpct <= 16)):
      return 'B'
    elif ((mpg_count >= totalsteps*0.4) and (misspct <= 6) and
          (shitpct <= 12) and (crappypct <= 18) and (okpct <= 24)):
      return 'C'
    elif ((mpg_count >= totalsteps*0.2) and (misspct <= 8) and
          (shitpct <= 16) and (crappypct <= 24) and (okpct <= 32)):
      return "D"
    else: return "doh!"



class GradingScreen:
  def __init__(self, judges):
    self.judges = judges

    for judge in judges:
      print "Player "+repr(judges.index(judge)+1)+":"
    
      grade = judge.grade()
      totalsteps = (judge.marvelous + judge.perfect + judge.great +
                    judge.ok + judge.crap + judge.shit + judge.miss)
      steps = (grade, judge.diff, totalsteps, judge.bestcombo, judge.combo)

      numholds = judge.numholds()
      goodholds = numholds - judge.badholds

      steptypes = (judge.marvelous, judge.perfect, judge.great,
                   judge.ok, judge.crap, judge.shit, judge.miss, goodholds,
                   numholds)
      print ("GRADE: %s (%s) - total steps: %d best combo" +
             " %d current combo: %d") % steps

      print ("V: %d P: %d G: %d O: %d C: " +
             "%d S: %d M: %d - %d/%d holds") % steptypes
      print

  def make_gradescreen(self, screen):
    judge = self.judges[0]
    totalsteps = (judge.marvelous + judge.perfect + judge.great +
                  judge.ok + judge.crap + judge.shit + judge.miss)

    if totalsteps == 0: return None

    # flash screen, whee
    for i in range(16):
      bg = pygame.Surface(screen.get_size())
      bg.fill(((15-i)*16,(15-i)*16,(15-i)*16))
      screen.blit(bg, (0,0))
      pygame.display.flip()

    font = pygame.font.Font(None, 28)

    grading = fontfx.sinkblur("GRADING",64,4,(224,72),(64,64,255))
    screen.blit(grading, (320-grading.get_rect().centerx,-8) )
    pygame.display.update()

    rows = ["MARVELOUS", "PERFECT", "GREAT", "OK", "CRAPPY", "ACK",
            "MISS", "early", "late", "TOTAL", " ", "MAX COMBO",
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
        r = screen.blit(gradetext, (320-font.size(rows[i])[0]/2,
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
                    judge.crap + judge.shit + judge.miss)
      rows = [judge.marvelous, judge.perfect, judge.great, judge.ok,
              judge.crap, judge.shit, judge.miss, judge.early, judge.late]

      testf = pygame.font.Font(None,28)

      for j in range(4):
        for i in range(len(rows)):
          fc = ((j*32)+96-(i*8))
          if fc < 0: fc=0
          text = "%d (%d%%)" % (rows[i], 100 * rows[i] / totalsteps)
          gradetext = fontfx.shadefade(text,28,j,(testf.size(text)[0]+8,32), (fc,fc,fc))
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
        gradetext = fontfx.shadefade(str(totalsteps),28,j,(testf.size(str(totalsteps))[0]+8,32), (fc,fc,fc))
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
        text = "%d (%d%%)" % (judge.bestcombo,
                              judge.bestcombo * 100 / totalsteps)
        gradetext = fontfx.shadefade(text,28,j,(testf.size(text)[0]+8,32), (fc,fc,fc))
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
        gradetext = fontfx.shadefade(text,28,j,(testf.size(text)[0]+8,32), (fc,fc,fc))
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
                                     (testf.size(str(judge.score))[0]+8,32), (fc,fc,fc))
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

    return 1

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

    def plunk(self):
      self.zoom = 8
      
    def update(self):
      if self.zoom > 0:
        self.image = pygame.transform.rotozoom(self.baseimage, 0, self.zoom)

        self.rect = self.image.get_rect()
        self.rect.centerx = self.x
        self.rect.centery = self.y
        
        self.zoom -= 1

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
    self.sticky = int(mainconfig['stickycombo'])
    self.lowcombo = int(mainconfig['lowestcombo'])

    self.trect = 296+(int(mainconfig['totaljudgings'])*24)
    self.playernum = playernum - 1
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
        self.playernum = playernum-1

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
  def __init__(self,top,colors):
      pygame.sprite.Sprite.__init__(self) #call Sprite initializer
      self.lyrics = []
      self.times = []
      self.prender = []
      self.lasttime = -1000

      self.space = pygame.surface.Surface((1,1))
      self.space.fill((0,0,0))

      self.oldlyric = -1
      self.oldalp = 0
      self.baseimage = self.space
      self.image = self.baseimage
      self.font = pygame.font.Font(None,32)
      self.colors = colors
      self.darkcolors = map((lambda x: int(x / 3.5)), self.colors)
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

    image1 = self.font.render(newlyric,1,self.darkcolors)
    image2 = self.font.render(newlyric,1,self.colors)
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
        self.font = pygame.font.Font(None, 16)
        self.lowest = 1000
        self.highest = -1
        self.fpses = []

    def fpsavg(self):
      return reduce(operator.add,self.fpses[2:])/(len(self.fpses)-2)

    def update(self, time):
      self.loops += 1
      if (time - self.oldtime) > 1:
        text = repr(self.loops) + " loops/sec"
        self.image = self.font.render(text,1,(160,160,160))
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

class TopArrow(pygame.sprite.Sprite):
  def __init__ (self, bpm, direction, ypos, playernum):
    pygame.sprite.Sprite.__init__(self)        #call Sprite initializer
    self.presstime = -1
#    self.steps = {}
    self.tick = toRealTime(bpm, 1);
    self.frame = 0
    self.oldframe = -1
    self.state = 'n'
    self.filepref = 'arr_'
    self.adder = 0
    self.direction = direction
    self.topimg = []
    self.playernum = playernum-1
    self.ypos = ypos

    for i in range(8):
      if i < 4:        ftemp = 'n_'
      else:            ftemp = 's_'
      fn = os.path.join('themes','gfx',theme,'arr_') + ftemp + self.direction + '_' + repr(i) + '.png'
      self.topimg.append(pygame.image.load(fn))
      self.topimg[i].set_colorkey(self.topimg[i].get_at((0,0)),RLEACCEL)

      self.image = self.topimg[0]
      self.rect = self.image.get_rect()
      self.rect.top = self.ypos
      if self.direction == 'l':        self.rect.left = 12
      if self.direction == 'd':        self.rect.left = 88
      if self.direction == 'u':        self.rect.left = 164
      if self.direction == 'r':        self.rect.left = 240

      self.rect.left += (320*self.playernum)

  def stepped(self, modifier, time):
    if modifier:    self.adder = 4
    else:           self.adder = 0
    self.presstime = time

  def update(self,time):
    if time > (self.presstime+0.2):        self.adder = 0

    self.keyf = int(time / (self.tick / 2)) % 8
    if self.keyf > 3:        self.keyf = 3
    self.frame = self.adder + self.keyf

    if self.frame != self.oldframe:
      self.image = self.topimg[self.frame]
      self.oldframe = self.frame

class Blinky(pygame.sprite.Sprite):
  def __init__ (self, bpm):
    pygame.sprite.Sprite.__init__(self)        #call Sprite initializer
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

class ArrowFX(pygame.sprite.Sprite):
  def __init__ (self, bpm, direction, ypos, playernum):
    pygame.sprite.Sprite.__init__(self)        #call Sprite initializer
    self.presstime = -1000000
    self.tick = toRealTime(bpm, 1);
    self.centery = ypos + 32
    self.centerx = {'l':44, 'd':120, 'u':196, 'r':272}[direction]
    self.playernum = playernum-1
    
    fn = os.path.join('themes','gfx',theme,'arr_n_') + direction + '_3.png'
    self.baseimg = pygame.image.load(fn).convert(16)
    self.tintimg = pygame.Surface(self.baseimg.get_size(), 0, 16)

    self.blackbox = pygame.surface.Surface((64,64))
    self.blackbox.set_colorkey(0)
    self.image = self.blackbox
    self.rect = self.image.get_rect()
    self.displaying = 1
    self.direction = 1
    self.holdtype = 0

    style = int(mainconfig['explodestyle'])
    self.rotating, self.scaling = {3:(1,1), 2:(0,1), 1:(1,0), 0:(0,0)}[style]
    
  def holding(self, yesorno):
    self.holdtype = yesorno
  
  def stepped(self, time, tinttype):
    self.presstime = time
    self.tintimg = pygame.Surface(self.baseimg.get_size(), 0, 16)
    self.tintimg.blit(self.baseimg, (0,0))
    tinter = pygame.surface.Surface((64,64))
    if tinttype == 'PERFECT':
      tinter.fill((255,255,0))
    if tinttype == 'MARVELOUS':
      tinter.fill((255,255,255))
    if tinttype == 'GREAT':
      tinter.fill((0,255,0))
    tinter.set_alpha(127)
    self.tintimg.blit(tinter,(0,0))
    self.tintimg.set_colorkey(self.tintimg.get_at((0,0)))
    self.tintimg = self.tintimg.convert() #_alpha() #rotozoom wants _alpha 
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
        newsize = [x*scale for x in self.image.get_size()]
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

      self.rect.left += (320*self.playernum)

class LifeBarDisp(pygame.sprite.Sprite):
    def __init__(self,playernum):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.playernum = playernum-1
        self.oldlife = self.failed = 0
        self.life = 25
        self.image = pygame.Surface((204,28))
        self.blkbar = pygame.Surface((3,24))
        self.bugbar = pygame.Surface((2,24))
        self.bugbar.fill((192,192,192))
        self.grade = None
        self.vamt = 0.4
        self.pamt = 0.25
        self.gamt = 0
        self.oamt = -0.5
        self.camt = -1
        self.samt = -2
        self.mamt = -4
        
        self.redbar = pygame.image.load(os.path.join('themes','gfx',theme,'redbar.png')).convert()
        self.orgbar = pygame.image.load(os.path.join('themes','gfx',theme,'orgbar.png')).convert()
        self.yelbar = pygame.image.load(os.path.join('themes','gfx',theme,'yelbar.png')).convert()
        self.grnbar = pygame.image.load(os.path.join('themes','gfx',theme,'grnbar.png')).convert()
        self.redbar_pos = self.redbar.get_rect()
        self.orgbar_pos = self.orgbar.get_rect()
        self.yelbar_pos = self.yelbar.get_rect()
        self.grnbar_pos = self.grnbar.get_rect()
        
        self.failtext = fontfx.embfade("FAILED",28,3,(80,32),(224,32,32))
        self.failtext.set_colorkey(self.failtext.get_at((0,0)))
        
        embossbar = pygame.Surface((204,1))
        embossbar.fill((128,128,128))
        self.image.blit(embossbar,(0,0))
        self.image.blit(embossbar,(-1,1))
        embossbar.fill((192,192,192))
        self.image.blit(embossbar,(1,26))
        self.image.blit(embossbar,(0,27))
        embossbar = pygame.Surface((1,28))
        embossbar.fill((128,128,128))
        self.image.blit(embossbar,(0,0))
        self.image.blit(embossbar,(1,-1))
        embossbar.fill((192,192,192))
        self.image.blit(embossbar,(202,1))
        self.image.blit(embossbar,(203,0))

        self.rect = self.image.get_rect()
        self.rect.top = 30
        self.rect.left = 58+(320*self.playernum)

    def failed(self):
       return self.failed
       
    def update(self, judges):
      tstmp = judges.marvelous + judges.perfect + judges.great + judges.ok + judges.crap + judges.shit + judges.miss
      if tstmp: 
        self.life += judges.combo*8 / tstmp
        self.life += judges.bestcombo*8 / tstmp

      self.life = 25
      self.life += judges.marvelous * self.vamt
      self.life += judges.perfect * self.pamt
      self.life += judges.great * self.gamt
      self.life += judges.ok * self.oamt
      self.life += judges.crap * self.camt
      self.life += judges.shit * self.samt
      self.life += judges.miss * self.mamt

      if self.life < 0:
        #FAILED but we don't do anything yet
        self.failed = 1
        self.life = 0

      if self.life > 52:
        self.life = 52
      if int(self.life) != int(self.oldlife):
#        print "life went to",self.life
        for j in range(52-self.life-1):
          self.image.blit(self.blkbar, ((2+int(self.life+j)*4), 2) )

        self.image.blit(self.bugbar,(202,2))   # because the damn bar eraser bugs out all the time

        for j in range(self.life):
          barpos = int(self.life-(j+1))
          if barpos <= 10:
            self.redbar_pos.left = 2+ barpos*4
            self.redbar_pos.top = 2
            self.image.blit(self.redbar,self.redbar_pos)
          if barpos > 10 and barpos <= 20:
            self.orgbar_pos.left = 2+ barpos*4
            self.orgbar_pos.top = 2
            self.image.blit(self.orgbar,self.orgbar_pos)
          if barpos > 20 and barpos <= 35:
            self.yelbar_pos.left = 2+ barpos*4
            self.yelbar_pos.top = 2
            self.image.blit(self.yelbar,self.yelbar_pos)
          if barpos > 35 and barpos < 50:
            self.grnbar_pos.left = 2+ barpos*4
            self.grnbar_pos.top = 2
            self.image.blit(self.grnbar,self.grnbar_pos)

      if self.failed:
        self.image.blit(self.failtext, (70, 2) )

      self.oldlife = self.life

class JudgingDisp(pygame.sprite.Sprite):
    def __init__(self,playernum):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer

        self.total = int(mainconfig['totaljudgings'])
        self.sticky = int(mainconfig['stickyjudge'])
        self.needsupdate = 1
        self.playernum = playernum-1
        self.stepped = 0
        self.oldzoom = -1
        
        # prerender the text for judging for a little speed boost
        font = pygame.font.Font(None, 48)
        tx = font.size("MARVELOUS")[0]+4
        self.marvelous = fontfx.shadefade("MARVELOUS",48,4,(tx,40),(224,224,224))
        tx = font.size("PERFECT")[0]+4
        self.perfect   = fontfx.shadefade("PERFECT"  ,48,4,(tx,40),(224,224, 32))
        tx = font.size("GREAT")[0]+4
        self.great     = fontfx.shadefade("GREAT"    ,48,4,(tx,40),( 32,224, 32))
        tx = font.size("OK")[0]+4
        self.ok        = fontfx.shadefade("OK"       ,48,4,(tx,40),( 32, 32,224))
        tx = font.size("CRAPPY")[0]+4
        self.crappy    = fontfx.shadefade("CRAPPY"   ,48,4,(tx,40),(128, 32,128))
        tx = font.size("ACK")[0]+4
        self.shit      = fontfx.shadefade("ACK"      ,48,4,(tx,40),( 96, 64, 32))
        tx = font.size("MISS")[0]+4
        self.miss      = fontfx.shadefade("MISS"     ,48,4,(tx,40),(224, 32, 32))
        self.space     = font.render( " ",       1, (  0,   0,   0) )

        self.marvelous.set_colorkey(self.marvelous.get_at((0,0)),RLEACCEL)
        self.perfect.set_colorkey(self.perfect.get_at((0,0)),RLEACCEL)
        self.great.set_colorkey(self.great.get_at((0,0)),RLEACCEL)
        self.ok.set_colorkey(self.ok.get_at((0,0)),RLEACCEL)
        self.crappy.set_colorkey(self.crappy.get_at((0,0)),RLEACCEL)
        self.shit.set_colorkey(self.shit.get_at((0,0)),RLEACCEL)
        self.miss.set_colorkey(self.miss.get_at((0,0)),RLEACCEL)

        self.image = self.space
        
    def update(self, listnum, steptimediff, judgetype):
      if steptimediff < 0.5 or (judgetype == ('MISS' or ' ')):
        if   judgetype == "MARVELOUS":       self.image = self.marvelous
        elif judgetype == "PERFECT":         self.image = self.perfect
        elif judgetype == "GREAT":           self.image = self.great
        elif judgetype == "OK":              self.image = self.ok
        elif judgetype == "CRAPPY":          self.image = self.crappy
        elif judgetype == "SHIT":            self.image = self.shit
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

class ScoringDisp(pygame.sprite.Sprite):
    def __init__(self,playernum,playmode):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.playernum = playernum-1
        
        # prerender the baseimage
        self.font = pygame.font.Font(None, 28)
        tx = self.font.size(playmode)[0]+2
        self.basemode = pygame.transform.scale(fontfx.embfade(playmode,28,2,(tx,24),(127,127,127)),(tx,48))
        self.baseimage = pygame.surface.Surface((128,48))
        self.baseimage.blit(self.basemode,(64-(tx/2),0))
        self.oldscore = -1
        self.image = pygame.surface.Surface((160,48))
        self.rect = self.image.get_rect()
        self.rect.bottom = 484
        self.rect.centerx = 160+(self.playernum*320)
        
    def update(self, score):
      if score != self.oldscore:
        self.image.blit(self.baseimage,(0,0))
        scoretext = self.font.render(repr(score),1,(192,192,192))
        self.image.blit(scoretext,(64-(scoretext.get_rect().size[0]/2),13))
        self.image.set_colorkey(self.image.get_at((0,0)),RLEACCEL)
        self.oldscore = score

class TimeDisp(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.font = pygame.font.Font(None, 40)
        self.oldtime = "-1000"
        self.image = pygame.surface.Surface((1,1))
        self.rect = self.image.get_rect()
        self.rect.top = 25
        self.rect.centerx = 320
        self.blahmod = 0
        
    def update(self, time):
      nowtime = repr(time)[:repr(time).index('.')+3]
      if (nowtime != self.oldtime) and (self.blahmod > 3):
        self.image = self.font.render(nowtime,1,(224,224,224))
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
    self.haslyrics = ''
    self.fooblah = fn
    try:
      try:
        print "trying full banner",fn[:-5]+'-full.png'
        self.lilbanner = pygame.image.load(fn[:-5]+'-full.png').convert()
      except:
        print "nogo, trying rotated banner",fn[:-5]+'.png'
        self.lilbanner = pygame.transform.rotate(pygame.image.load(fn[:-5]+'.png').convert(),-45)
    except:
      print "settling for blank banner for",fn
      self.lilbanner = pygame.surface.Surface((1,1))
    self.lilbanner.set_colorkey(self.lilbanner.get_at((0,0)))
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
    self.mixname = 'unspecified mix'
    self.playingbpm = 146.0    # while playing, event handler will use this for arrow control
    self.mixerclock = int(mainconfig['mixerclock'])
    self.lyricdisplay = LyricDispKludge(400, map((lambda x: int(x)), mainconfig['lyriccolor'].split(',')))
    self.transdisplay = LyricDispKludge(428, map((lambda x: int(x)), mainconfig['transcolor'].split(',')))
    little = int(mainconfig["little"])
    coloringmod = 0
    self.totarrows = {}
    self.holdinfo = []
    self.holdref = []
    numholds = 1
    holdlist = []
    releaselist = []
    holdtimes = []
    releasetimes = []
    holding = [0,0,0,0]
    chompNext = None
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
          curTime = float(self.offset) #/1000.0
          curBPM = self.bpm
          difficulty = firstword
          self.totarrows[difficulty] = 0
          modeDict[difficulty] = SongEvent(when=curTime,bpm=curBPM,extra=int(rest[0]))
          chompNext = modeDict,modeDict[difficulty]
        elif len(chompNext) == 2:
          modeDict, tail = chompNext
          if firstword == 'end':
            coloringmod = 0

            # append the hold info for this mode
            self.holdinfo.append( zip(holdlist,holdtimes,releasetimes) )
            self.holdref.append( zip(holdlist,holdtimes) )

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
#              print curTime,":",holding,feetstep,

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
                      if feetstep[checkforholds] & 8:
                        feetstep[checkforholds] ^= 8       # xor the arrow event only
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
        self.haslyrics = '  (LYRICS)'
        curTime = 0.0
        curBPM = self.bpm
        self.lyrics = SongEvent(when=curTime,bpm=curBPM)
        chompNext = None,self.lyrics
      elif firstword == 'song':        self.song = " ".join(rest)
      elif firstword == 'mix':         self.mixname = " ".join(rest)
      elif firstword == 'group':       self.group = " ".join(rest)
      elif firstword == 'bpm':
        self.bpm = float(nextword) 
        if int(mainconfig['onboardaudio']):
          self.bpm = self.bpm * float(48000/44128.0)
        self.playingbpm = self.bpm
      elif firstword in modes.keys():  chompNext=(modes[firstword],)
      elif firstword == 'file':        self.file = " ".join(rest)
      elif firstword == 'bg':          self.bgfile = " ".join(rest)
      elif firstword == 'movie':       self.moviefile = " ".join(rest)
      elif firstword == 'startat':     self.startsec = float(nextword)
      elif firstword == 'endat':       self.endsec = float(nextword)
      elif firstword == 'offset':      
        self.offset = float(-int(nextword)-int(mainconfig['masteroffset']))/1000.0
        if int(mainconfig['onboardaudio']):
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
      # this is so much easier in 2.2
      # self.modeinfodict[m] = dict(self.modeinfo[m])
      self.modeinfodict[m] = {}
      for key,val in self.modeinfo[m]:
        self.modeinfodict[key]=val

  def renderListText(self,totalsongs,j):
    listimage = BlankSprite((640,48))
    listimage.set_colorkey(listimage.get_at((0,0)),RLEACCEL)
    stext = "%s - %s"%(self.group,self.song)
    text = fontfx.shadefade(stext,28,3,(640,32),(63+j*(192/(totalsongs+1)),j*(240/(totalsongs+1)),240-(j*255/(totalsongs+1))))
    text.set_colorkey(text.get_at((0,0)),RLEACCEL)
    listimage.blit(text,(32,0))
    stext = "BPM: %d"%int(round(self.bpm)) + "".join(map(lambda (n,d): "  %s %d"%(n,d),self.modeinfo[playmode])) + self.haslyrics
    text = fontfx.embfade(stext,28,3,(640,32),(63+j*(192/(totalsongs+1)),j*(240/(totalsongs+1)),240-(j*255/(totalsongs+1))))
    text.set_colorkey(text.get_at((0,0)),RLEACCEL)
    listimage.blit(text,(64,24))
    
    titleimage = BlankSprite((640,90))
    text = fontfx.shadefade(self.group,64,3,(640,68),(192,64,64))
    titleimage.blit(text,(8,0))
    text = fontfx.shadefade(self.song,48,3,(640,52),(192,64,192))
    text.set_colorkey(text.get_at((0,0)),RLEACCEL)
    titleimage.blit(text, (32,40))

    self.listimage  = listimage
    listimage.set_colorkey(listimage.get_at((0,0)),RLEACCEL)
    self.titleimage = titleimage

  def discardListText(self):
    self.listimage = None
    self.titleimage = None

  def cache (self):
    # open / read / close
    try:
      open(self.osfile).read()
    except IOError:
      print "file not found"
      self.crapout = 2
#    print "cached"
    
  def init (self):
#    ss = pygame.movie.Movie(self.osfile)
    try:
      pygame.mixer.music.load(self.osfile)
    except pygame.error:
      print "not a supported filetype"
      self.crapout = 1
    if self.startsec > 0.0:
      print "Skipping %f seconds" % self.startsec
#      ss.skip(self.startsec)
    
  def play(self,mode,difficulty,actuallyplay):
#    self.ss.play()
    try:
      if self.crapout == 0 and actuallyplay:
        pygame.mixer.music.play(0, self.startsec)
    except TypeError:
      print "Sorry, pyDDR needs a more up to date Pygame or SDL than you have."
      sys.exit()

    self.curtime = 0.0
    self.tickstart = pygame_time_get_ticks()
    self.head = self.fhead = self.modes[mode][difficulty]

  def kill(self):
#    self.ss.stop()
    pygame.mixer.music.stop()

  def get_time(self):
    if self.mixerclock:
      self.curtime = float(pygame.mixer.music.get_pos())/1000.0 # -self.tickstart causes desync
    else:
      self.curtime = float(pygame_time_get_ticks() - self.tickstart)/1000.0
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
    self.head=head

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
    return events,nevents,time,arrowtime,bpm

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
  list = os.listdir(path)
  for f in list:
    filepath = '%s/%s' % (path, f)
    mode = os.stat(filepath)[ST_MODE]
    if S_ISDIR(mode):
      matches.extend(find(filepath, pattern))
    else:
      if fnmatch.fnmatch(filepath, pattern):
        matches.append(filepath)
  return matches

class fastSong:
  def __init__ (self, fn, path=None):
    self.objectcreationtime = pygame.time.get_ticks()
    # note that I'm only copying DIFFICULTIES because it's the right size..
    self.haslyrics = ''
    self.fooblah = fn

    try:
      try:
        print fn[:-5]+'-full.png?',
        self.lilbanner = pygame.image.load(fn[:-5]+'-full.png').convert()
        self.bannertype = 2
        print "yes"
      except:
        print fn[:-5]+'.png?',
        self.lilbanner = pygame.image.load(fn[:-5]+'.png').convert()
        if (self.lilbanner.get_rect().size[0] / 2) > self.lilbanner.get_rect().size[1]:
          print "yes, rotated banner was fullsize"
          self.bannertype = 2
        else:
          self.lilbanner = pygame.transform.rotate(self.lilbanner,-45)
          self.lilbanner.set_colorkey(self.lilbanner.get_at((0,0)))
          self.bannertype = 1
          print "yes"
    except:
      print "settling for blank banner for",fn
      self.lilbanner = pygame.surface.Surface((1,1))
      self.lilbanner.set_colorkey(self.lilbanner.get_at((0,0)))
      self.bannertype = 0
 
    self.bannercreationtime = pygame.time.get_ticks()
    self.rrrr = self.lilbanner.get_rect()
    self.rrrr.center = (320,300)
    r = screen.blit(self.lilbanner,self.rrrr)
    update_screen(r)
    self.file = None
    self.modes = modes = MODES.copy()
    self.modelist = []
    self.modediff = {}
    self.modeinfo = {}
    self.modeinfodict = {}
    self.path = path
    for key in MODELIST: modes[key]=DIFFICULTIES.copy()
    curTime = 0.0
    curBPM = 0.0
    self.offset = 0.0
    self.isValid = 0
    self.startsec = 0.0
    self.endsec = -1.0
    self.bpm = 146.0
    self.bgfile = ' '
    self.mixname = '---'
    self.playingbpm = 146.0    # while playing, event handler will use this for arrow control
    self.mixerclock = int(mainconfig['mixerclock'])
#    self.lyricdisplay = LyricDispKludge(400)
#    self.transdisplay = LyricDispKludge(428)
    little = int(mainconfig['little'])
    self.totarrows = 0
    chompNext = None
    self.variablecreationtime = pygame.time.get_ticks()
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
          difficulty = firstword
          modeDict[difficulty]  = SongEvent(when=curTime,bpm=curBPM,extra=int(rest[0]))
          chompNext = modeDict,modeDict[difficulty]
        
        elif len(chompNext) == 2:
          modeDict, tail = chompNext
          if firstword == 'end':
            chompNext = None
      elif firstword == 'LYRICS':
        self.haslyrics = '  (LYRICS)'
        chompNext = None, 0
      elif firstword == 'song':        self.song = " ".join(rest)
      elif firstword == 'mix':         self.mixname = " ".join(rest)
      elif firstword == 'group':       self.group = " ".join(rest)
      elif firstword == 'bpm':         self.bpm = float(nextword) 
      elif firstword in modes.keys():  chompNext=(modes[firstword],)
      elif firstword == 'file':        self.file = " ".join(rest)
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
    # setup lists to make it easy and in order for the song selector
    self.modelist = filter(lambda m,modes=modes: modes.has_key(m), MODELIST)
    self.filereadcreationtime = pygame.time.get_ticks()

    if path is None:
      self.path = os.path.dirname(fn)

    if self.file is None:
      self.file = string.join(fn[len(self.path)+1:-5].split("/")[-1:],"")
      for ext in [".ogg",".mp3",".wav",".mid"]:
        if os.path.isfile(os.path.join(self.path,self.file+ext)):
          self.file = self.file+ext
          break

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
      # this is so much easier in 2.2
      # self.modeinfodict[m] = dict(self.modeinfo[m])
      self.modeinfodict[m] = {}
      for key,val in self.modeinfo[m]:
        self.modeinfodict[key]=val

    self.modereadcreationtime = pygame.time.get_ticks()
    
  def renderListText(self,totalsongs,j):
    listimage = BlankSprite((560,48))
    if self.mixname:
      text = fontfx.shadefade(self.mixname,32,2,(128,28),(80,80,80))
      listimage.blit(text,(432,2))
      
#    cmap = (63+j*(192/(totalsongs+1)),j*(240/(totalsongs+1)),240-(j*255/(totalsongs+1)))
    cmap = (224,224,224)

    text = fontfx.shadefade(self.song,20,3,(500,20),cmap)
    text.set_colorkey(text.get_at((0,0)))
    listimage.blit(text,(160,2))
    text = fontfx.shadefade("- "+self.group,18,3,(500,18),cmap)
    text.set_colorkey(text.get_at((0,0)))
    listimage.blit(text,(168,14))
    stext = "%d BPM"%int(round(self.bpm)) + "".join(map(lambda (n,d): "  %s %d"%(n,d),self.modeinfo[playmode])) + self.haslyrics
    text = fontfx.embfade(stext,20,3,(500,20),cmap)
    text.set_colorkey(text.get_at((0,0)))
    listimage.blit(text,(160,30))
    if self.bannertype == 2:
      listimage.blit(pygame.transform.scale(self.lilbanner,(self.lilbanner.get_rect().size[0]/2,self.lilbanner.get_rect().size[1]/2)),(20,4))
    elif self.bannertype == 1:
      listimage.blit(pygame.transform.scale(self.lilbanner,(self.lilbanner.get_rect().size[0]/1.5,self.lilbanner.get_rect().size[1]/1.5)),(3,65-(self.lilbanner.get_rect().size[1]/2)))

    pygame.draw.line(listimage.image,(191,191,191),(4,1),(12,46),2)
    pygame.draw.line(listimage.image,(191,191,191),(544,1),(552,46),2)

    pygame.draw.line(listimage.image,(191,191,191),(4,1),(544,1),2)
    pygame.draw.line(listimage.image,(191,191,191),(12,46),(552,46),2)
    
    titleimage = BlankSprite((640,80))
    colorthinger = pygame.surface.Surface((640,16))
    for i in range(4):
      colorthinger.fill((12*i,12*i,12*i))
      titleimage.blit(colorthinger,(0,16+(16*i)))
    sn = repr(j)+"/"+repr(totalsongs)
    text = fontfx.embfade(sn,20,2,(56,16),(160,160,160))
    titleimage.blit(text, (584,0))
    text = fontfx.shadefade(self.group,60,3,(640,64),(192,64,64))
    text.set_colorkey(text.get_at((0,0)))
    titleimage.blit(text,(8,0))
    text = fontfx.shadefade(self.song,44,3,(640,48),(192,64,192))
    text.set_colorkey(text.get_at((0,0)))
    titleimage.blit(text, (32,36))
    
    self.listimage  = listimage
    listimage.set_colorkey(listimage.get_at((0,0)))
    self.titleimage = titleimage
    
  def discardListText(self):
    self.listimage = None
    self.titleimage = None

  def __nonzero__ (self):
    return self.isValid
    
  def __repr__ (self):
    return '<song song=%r group=%r bpm=%s file=%r>'%(self.song,self.group,repr(self.bpm)[:7],self.file)

class ArrowSet: 
  def __init__ (self, path, prefix='arr', imgtype='png', separator='_'):
    # left, up, right, down
    arrows = {'l': 12, 'd': 12+76, 'u': 12+2*76, 'r': 12+3*76}
    for dir,left in arrows.items():
      for cnum in range(4):
        if cnum == 3:
          casdf = 1
        else:
          casdf = cnum
        arrows[dir+repr(cnum)] = Arrow(self,dir,path,prefix,imgtype,separator,left,casdf)
    # allow access by instance.l or instance.arrows['l']
    for n in arrows.keys(): self.__dict__[n] = arrows[n] 
    self.arrows = arrows
  def __getitem__ (self,item):
    # allow access by instance['l']
    return getattr(self,item)
    
class Arrow:
  def __init__ (self, parent, dir, path, prefix, imgtype, separator,left=0,color=0):
      # reference to ArrowSet
      self.parent=parent
      # direction (short) i.e. 'l'
      self.dir = dir
      # normal, pulse, stepped on, pulse & stepped on, colored, offbeat colored
      states = {'c':None} #, 'p':None, 's':None, 'b':None, 'n':None, 'o':None}
      for state in states.keys():
        fn = os.path.join(path, separator.join([prefix,state,dir,repr(color)]) + '.' + imgtype)
        states[state] = SimpleSprite(fn)
        states[state].rect.left = left
      # allow access by instance.n or instance.states['n']
      for n in states.keys(): self.__dict__[n] = states[n]

class SimpleSprite(pygame.sprite.Sprite):
  def __init__ (self, file, zindex=DEFAULTZINDEX):
    pygame.sprite.Sprite.__init__(self)
    self.zindex=zindex
    image = pygame.image.load(file).convert()
    image.set_colorkey(image.get_at((0,0)))
    self.fn = file
    self.image = image
    self.rect = image.get_rect()

  def draw(self,surf,pos=None,rect=None):
    if rect and pos:
      return surf.blit(self.image,pos,rect)
    elif pos:
      return surf.blit(self.image,pos)
    elif rect:
      return surf.blit(self.image,(0,0),rect)
    else:
      return surf.blit(self.image,self.rect)

  def update(self):
    pass

  def __getattr__(self,attr):
    return getattr(self.image,attr)
    
  def __repr__(self):
    return '<Sprite fn=%r rect=%r>'%(self.fn,self.rect)

class BlankSprite(SimpleSprite):
  def __init__ (self, res, fill=BLACK,zindex=DEFAULTZINDEX):
    pygame.sprite.Sprite.__init__(self)
    self.zindex=zindex
    image = pygame.Surface(res)
    if fill is not None: image.fill(fill)
    self.image = image
    self.rect = image.get_rect()

  def __repr__(self):
    return '<Sprite rect=%r>'%(self.rect)

class CloneSprite(BlankSprite):
  def __init__ (self, spr,zindex=DEFAULTZINDEX):
    pygame.sprite.Sprite.__init__(self)
    self.zindex=zindex
    self.image = spr.convert()
    try:
      self.rect = Rect(spr.rect)
    except:
      self.rect = spr.get_rect()

class TransformSprite(BlankSprite):
  _rotozoom = pygame.transform.rotozoom
  _rotate = pygame.transform.rotate
  _flip = pygame.transform.flip
  _scale = pygame.transform.scale
  def __init__ (self, spr, scale=None, size=None, zindex=DEFAULTZINDEX,hflip=0,vflip=0,angle=None,filter=None):
    pygame.sprite.Sprite.__init__(self)
    self.zindex=zindex
    image = None
    try:
      image = spr.image
    except:
      image = spr
    if scale and not size:      size = map(lambda n,scale=scale: scale*n, spr.rect.size)
    if angle and size:          image = self._rotozoom(image,angle,zoom)
    elif angle:                 image = self._rotate(image,angle)
    elif size:                  image = self._scale(image,size)
    if hflip or vflip:          image = self._flip(image,hflip,vflip)
    self.image = image
    self.rect = self.image.get_rect()

#DCY: Bottom of 640 gives lots of "update rejecting"    
if int(mainconfig['reversescroll']):
  ARROWTOP  = 408
  ARROWBOT  = int(-64 - (float(mainconfig['scrollspeed'])-1)*576)
else:
  ARROWTOP  = 64
  ARROWBOT  = int(576 * float(mainconfig['scrollspeed']))

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
    if int(mainconfig['assist']):
      self.playedsound = None
      if self.dir == 'u':
        self.sample = pygame.mixer.Sound("assist-u.wav")
      elif self.dir == 'd':
        self.sample = pygame.mixer.Sound("assist-d.wav")
      elif self.dir == 'l':
        self.sample = pygame.mixer.Sound("assist-l.wav")
      elif self.dir == 'r':
        self.sample = pygame.mixer.Sound("assist-r.wav")
    else:
      self.playedsound = 1
    self.r = 0
    self.playernum = playernum-1
    self.bimage = self.image
    self.arrowspin = float(mainconfig["arrowspin"])
    self.arrowshrink = float(mainconfig["arrowshrink"])
    self.arrowgrow = float(mainconfig["arrowgrow"])
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
    arrscale = int(float((self.rect.top-64)/416.0)*64)

    if self.arrowshrink:
      self.cimage = pygame.transform.scale(self.bimage, (arrscale,arrscale) )
    if self.arrowgrow:
      self.cimage = pygame.transform.scale(self.bimage, (64-arrscale,64-arrscale) )
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
    self.playernum = playernum-1
    self.curalpha = -1
    self.dir = spr.fn[-7:-6]
    self.playedsound = None
    if int(mainconfig['assist']):
      if self.dir == 'u':
        self.sample = pygame.mixer.Sound("assist-u.wav")
      elif self.dir == 'd':
        self.sample = pygame.mixer.Sound("assist-d.wav")
      elif self.dir == 'l':
        self.sample = pygame.mixer.Sound("assist-l.wav")
      elif self.dir == 'r':
        self.sample = pygame.mixer.Sound("assist-r.wav")
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
    self.arrowshrink = float(mainconfig["arrowshrink"])
    self.arrowgrow = float(mainconfig["arrowgrow"])
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
    if len(lbct)<2:
      onebeat = float(60000.0/curbpm)/1000
      doomtime = self.timef2 - curtime
      beatsleft = float(doomtime / onebeat)
      self.bottom = self.bottom - int( (beatsleft/8.0)*ARROWDIFF )
    else:
      oldbpmsub = [curtime,curbpm]
      bpmbeats = 0
      for bpmcheck in range(len(lbct[-1])-1):
        bpmsub = lbct[bpmcheck+1]
#        print "bpmsub[0]",bpmsub[0],"curtime",curtime
        if bpmsub[0] <= self.timef2:
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
        bpmdoom = self.timef2 - oldbpmsub[0] 
        bpmbeats = float(bpmdoom / onefbeat)
#        print "bpmbeats",bpmbeats
        self.bottom = self.bottom - int(bpmbeats*ARROWDIFF/8.0)
        finaltime = 1

    finaltime = 0
    if len(lbct)<2:
      onebeat = float(60000.0/curbpm)/1000
      doomtime = self.timef1 - curtime
      if doomtime < 0:
        doomtime = 0
      beatsleft = float(doomtime / onebeat) #- 0.5
      self.top = self.top - int( (beatsleft/8.0)*ARROWDIFF )
    else:
      print "holdarrow + bpmchange = weirdstuffmighthappen"
      oldbpmsub = [curtime,curbpm]
      bpmbeats = 0
      for bpmcheck in range(len(lbct[-1])-1):
        bpmsub = lbct[bpmcheck+1]
#        print "bpmsub[0]",bpmsub[0],"curtime",curtime
        if bpmsub[0] <= self.timef1:
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
        bpmdoom = self.timef1 - oldbpmsub[0] 
        bpmbeats = float(bpmdoom / onefbeat) #- 0.5
#        print "bpmbeats",bpmbeats
        self.top = self.top - int(bpmbeats*ARROWDIFF/8.0)
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

    arrscale = int(float((self.rect.top-64)/416.0)*64)

    if self.arrowshrink:
      self.cimage = pygame.transform.scale(self.bimage, (arrscale,arrscale) )
    if self.arrowgrow:
      self.cimage = pygame.transform.scale(self.bimage, (64-arrscale,64-arrscale) )
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
      
# enum would be nice
E_PASS,E_QUIT,E_LEFT,E_RIGHT,E_UP,E_DOWN,E_FULLSCREEN,E_START,E_SCREENSHOT,E_HCENTER,E_VCENTER,E_PGUP,E_PGDN,E_LEFT2,E_RIGHT2,E_UP2,E_DOWN2,E_START2,E_SELECT = range(19)

HAXIS,VAXIS = 0,1
ZERO,NEGATIVE,POSITIVE = 0,1,2

SHIFTPAD     = 0 # 4 bits: joypad 0-15
SHIFTAXIS    = 4 # 2 bits: HAXIS, VAXIS
SHIFTDIR     = 6 # 3 bits: NEGATIVE,ZERO,POSITIVE
SHIFTBUTTON  = 8 # N bits: button0,button1,...buttonN-1

def joyEvent(button=None,axis=None,dir=None,pad=0):
  ev = pad
  # axis is low 2 bits, dir is next two bits, button is rest
  if axis is not None:
    ev |= 1L << (SHIFTAXIS   + axis)
  if dir is not None:
    ev |= 1L << (SHIFTDIR    + dir)
  if button is not None:
    ev |= 1L << (SHIFTBUTTON + button)
  return ev
  
KEYCONFIG = { E_QUIT:       [K_ESCAPE],
              E_LEFT:       [p1l],
              E_RIGHT:      [p1r],
              E_UP:         [p1u],
              E_DOWN:       [p1d],
              E_FULLSCREEN: [K_f],
              E_SCREENSHOT: [K_s],
              E_START:      [13,271],
              E_PGUP:       [K_PAGEUP],
              E_PGDN:       [K_PAGEDOWN],
              E_LEFT2:      [p2l],
              E_RIGHT2:     [p2r],
              E_UP2:        [p2u],
              E_DOWN2:      [p2d],
              E_START2:     [K_2],
              E_SELECT:     [K_r]
            }

EMS2CONFIG= { E_QUIT:       [],
              E_LEFT:       [joyEvent( button=15 )],
              E_RIGHT:      [joyEvent( button=13 )],
              E_UP:         [joyEvent( button=12 )],
              E_DOWN:       [joyEvent( button=14 )],
              E_FULLSCREEN: [],
              E_SCREENSHOT: [],
              E_START:      [joyEvent( button=9 )],
              E_PGUP:       [joyEvent( button=1 )],
              E_PGDN:       [joyEvent( button=3 )],
              E_LEFT2:      [joyEvent( button=31 )],
              E_RIGHT2:     [joyEvent( button=29 )],
              E_UP2:        [joyEvent( button=28 )],
              E_DOWN2:      [joyEvent( button=30 )],
              E_START2:     [joyEvent( button=25)],
              E_SELECT:     [joyEvent( button=8 )],
            }
J2CONFIG  = { E_LEFT2:      [joyEvent( button=int(mainconfig["joy_left"]))],
              E_RIGHT2:     [joyEvent( button=int(mainconfig['joy_right']))],
              E_UP2:        [joyEvent( button=int(mainconfig['joy_up']))],
              E_DOWN2:      [joyEvent( button=int(mainconfig['joy_down']))],
            }
JOYCONFIG = { E_LEFT:       [joyEvent( button=int(mainconfig['joy_left']))],
              E_RIGHT:      [joyEvent( button=int(mainconfig['joy_right']))],
              E_UP:         [joyEvent( button=int(mainconfig['joy_up']))],
              E_DOWN:       [joyEvent( button=int(mainconfig['joy_down']))],
              E_SELECT:     [joyEvent( button=int(mainconfig['joy_select']))],
              E_START:      [joyEvent( button=int(mainconfig['joy_start']))],
              E_PGUP:       [joyEvent( button=int(mainconfig['joy_pgup']))],
              E_PGDN:       [joyEvent( button=int(mainconfig['joy_pgdn']))],
            }

class EventManager:
  def __init__ (self,kConfig=KEYCONFIG,jConfig=JOYCONFIG,pygameevent=pygame.event):
    self.pygameevent = pygameevent
    pygameevent.set_blocked(range(NUMEVENTS))
    pygameevent.set_allowed((KEYUP,KEYDOWN))
    # joystick
    matjoy = self.matjoy = None
    matjoy2 = self.matjoy2 = None
    emsusb2 = self.emsusb2 = None
    try:
      totaljoy = pygame.joystick.get_count()
    except:
      totaljoy = 0
    print totaljoy,"joystick[s] total. ",
    for i in range(totaljoy):
      ddrmat = pygame.joystick.Joystick(i)
      ddrmat.init()
      matbuttons = int(mainconfig['mat_buttons'])
      mataxes = int(mainconfig['mat_axes'])
      if ddrmat.get_numbuttons() == 32 and ((ddrmat.get_numaxes() == 11) or (ddrmat.get_numaxes() == 8)):
        emsusb2 = i
      elif ddrmat.get_numbuttons() == matbuttons and ddrmat.get_numaxes() == mataxes:
        if matjoy is None:
          matjoy = i
        else:
          matjoy2 = i
      ddrmat.quit()
    if emsusb2 is not None:
      ddrmat = pygame.joystick.Joystick(emsusb2)
      ddrmat.init()
      print "EMSUSB2 initialised: js",emsusb2
      self.emsusb2 = emsusb2
      pygameevent.set_allowed((JOYBUTTONUP,JOYBUTTONDOWN))
      self.setupEMS()
    elif (matjoy is not None) or (matjoy2 is not None):
      if matjoy2 is not None:
        ddrmat2 = pygame.joystick.Joystick(matjoy2)
        ddrmat2.init()
        print "DDR mat 2 initialised: js",matjoy2
        self.matjoy2 = matjoy2
        pygameevent.set_allowed((JOYBUTTONUP,JOYBUTTONDOWN))
        self.setupJoy2()
      if matjoy is not None:
        ddrmat = pygame.joystick.Joystick(matjoy)
        ddrmat.init()
        print "DDR mat 1 initialised: js",matjoy
        self.matjoy = matjoy
        pygameevent.set_allowed((JOYBUTTONUP,JOYBUTTONDOWN))
        self.setupJoy(jConfig)
    else:
      print "No DDR mat found! Not initialising joystick"
    self.setupKeys(kConfig)

  def __getattr__(self,attr):
    return getattr(self.pygameevent,attr)

  def setupKeys(self,kConfig=KEYCONFIG):
    keymap = {}
    for event,lst in kConfig.items():
      for key in lst:
        keymap[key]=event
    self.keymap=keymap

  def setupEMS(self,jConfig=EMS2CONFIG):
    joymap = {}
    for event,lst in jConfig.items():
      for joy in lst:
        joymap[joy]=event
    self.emsmap=joymap
    print self.emsmap

  def setupJoy(self,jConfig=JOYCONFIG):
    joymap = {}
    for event,lst in jConfig.items():
      for joy in lst:
        joymap[joy]=event
    self.joymap=joymap

  def setupJoy2(self,jConfig=J2CONFIG):
    joymap = {}
    for event,lst in jConfig.items():
      for joy in lst:
        joymap[joy]=event
    self.joymap2=joymap

  def nextEvent(self,event):
#    print event
    if   event.type == QUIT:          return E_QUIT
    elif event.type == JOYAXISMOTION: return self.joyMove(event.axis,event.value)
    elif event.type == JOYBUTTONDOWN: return self.joyButton(event.joy,event.button)
    elif event.type == JOYBUTTONUP:   return -self.joyButton(event.joy,event.button)
    elif event.type == KEYDOWN:       return self.keyDown(event.key)
    elif event.type == KEYUP:         return -self.keyDown(event.key)
    else:                             return E_PASS

  def joyMove(self,axis,dir):
    if   dir<0: dir = NEGATIVE
    elif dir>0: dir = POSITIVE
    else:       dir = ZERO
    return self.joymap.get(joyEvent(axis=axis,dir=dir),E_PASS)

  def joyButton(self,joy,button):
#    print "joy",joy,"button",button
#    print "this button is", joyEvent(button=button)
#    print "matjoy",self.matjoy,"matjoy2",self.matjoy2,"emsusb2",self.emsusb2
    if joy == self.matjoy:
      return self.joymap.get(joyEvent(button=button),E_PASS)
    if joy == self.matjoy2:
      return self.joymap2.get(joyEvent(button=button),E_PASS)
    if joy == self.emsusb2:
      return self.emsmap.get(joyEvent(button=button),E_PASS)

  def keyDown(self,key):
    return self.keymap.get(key,E_PASS)

  def keyUp(self,key):
    return -self.keymap.get(key,E_PASS)
  
  def poll(self):
    blah = self.nextEvent(self.pygameevent.poll())
#    if blah > 0: 
#      print "pressed",
    if blah < 0:
#      print "released",
      if blah == -2: holdkey.letgo('l')
      if blah == -3: holdkey.letgo('r')
      if blah == -4: holdkey.letgo('u')
      if blah == -5: holdkey.letgo('d')
      if blah == -13: holdkey2.letgo('l')
      if blah == -14: holdkey2.letgo('r')
      if blah == -15: holdkey2.letgo('u')
      if blah == -16: holdkey2.letgo('d')
 #   if blah != E_PASS:
 #     print ['E_PASS','E_QUIT','E_LEFT','E_RIGHT','E_UP','E_DOWN','E_FULLSCREEN','E_START','E_SCREENSHOT','E_HCENTER','E_VCENTER','E_PGUP','E_PGDN','E_LEFT2','E_RIGHT2','E_UP2','E_DOWN2','E_START2','E_SELECT'][blah]
    return blah
    
J_UP,J_DOWN,J_RIGHT,J_LEFT = map(lambda n: 1<<n, range(4))
J_UP2,J_DOWN2,J_RIGHT2,J_LEFT2 = map(lambda n: 1<<n, range(13,17,1))

# print a number as binary, low 16 bits
def sbin16(d,bits=16):
  return sbin32(d,bits)

# print a number as binary, all 32 bits
def sbin32(d,bits=32):
  bin=''
  for n in range(bits):
    bin = str(d&1)+bin
    d>>=1
  return bin

def J_B(n):
  return 1<<(4+n)

JBUTTONS = [[E_START],[E_SCREENSHOT],[E_FULLSCREEN],[E_QUIT]]
class JoyPad:
  def __init__(self,eventManager=None,buttons=JBUTTONS,history=10):
    if eventManager is None: eventManager = EventManager()
    self.eventManager=eventManager
    self.state = 0
    self.bdict = bdict = {E_UP:      J_UP,
                          E_DOWN:    J_DOWN,
                          E_LEFT:    J_LEFT,
                          E_RIGHT:   J_RIGHT,
                          E_UP2:     J_UP2,
                          E_DOWN2:   J_DOWN2,
                          E_LEFT2:   J_LEFT2,
                          E_RIGHT2:  J_RIGHT2}
    for (button,lst) in zip(map(J_B,range(len(buttons))),buttons):
      for event in lst: bdict[event] = button
    self.history = None
    if history:
      self.history = map(None,range(history))

  def poll(self):
    _bd = self.bdict
    _bd_has = _bd.has_key
    _em = self.eventManager
    _st = _stold = self.state
    _em_peek = _em.peek
    _em_poll = _em.poll
    _sh = self.history
    if _em.peek():
#      print _em_peek()
      oevent = event = _em_poll()
#      if   event == E_PASS:     continue
      # handled as a button
      #elif event == E_QUIT:     raise QuitGame("Caught a quit from the JoyPad")
#      event = abs(event)
      _bm = 0 # bitmask
      if   event == E_HCENTER:    _st &= ~(J_LEFT|J_RIGHT)
      elif event == E_VCENTER:    _st &= ~(J_UP|J_DOWN)
      # print event
      if _bd_has(event):        _bm = _bd[event]
      if oevent>0:                _st |= _bm
      else:                       _st &= ~_bm
    delta = _st^_stold
#    if delta == ~0: delta=0
    rval = pygame_time_get_ticks(), _st, delta
    if delta and _sh:
      # record time, state, change
      _sh.append(rval)
      del(_sh[0])
    return rval

# acts like a subclass of Sprite
class SimpleAnim:
  def __init__ (self, path, prefix, separator, imgtype='png', frameNumbers=None, files=None, zindex=DEFAULTZINDEX):
    frames = []
    if files is None:
      if frameNumbers is None:
        files=glob.glob(os.path.join(path,separator.join([prefix,'*.'+imgtype])))
      else:
        files=[]
        for i in frameNumbers: 
          files.append(os.path.join(path,separator.join([prefix,"%d.%s"%(i,imgtype)])))
    self.frames=map(lambda fn,SimpleSprite=SimpleSprite,zindex=zindex: SimpleSprite(fn,zindex=zindex), files)
    self.curframe = 0

  def update(self):
    """swap the groups of old sprite into new sprite"""
    oldspr = self.curframe
    frames = self.frames
    curframe = oldspr+1
    if curframe>=len(frames): curframe=0
    # degenerate case, a 1 frame animation
    if oldspr == curframe: return
    frames[curframe].rect = frames[oldspr].rect
    # only one frames is the "sprite" at any given time
    for n in frames[oldspr].groups: frames[curframe].add(n)
    frames[oldspr].kill()
    self.curframe = curframe

  def __getattr__(self,attr):
    """pretend we are a Sprite by overloading getattr with frames[curframe]"""
    return getattr(self.frames[self.curframe],attr)

#  def __setattr__(self,attr,val):
#    if attr=='rect': setattr(self.frames[self.curframe],attr,val)
#    else: self.__dict__[attr]=val 


class Xanim(SimpleAnim):
  def __init__ (self, path, prefix='x_out', separator='-', imgtype='png', frameNumbers=None, files=None):
    SimpleAnim.__init__(self,path,prefix,separator,imgtype,frameNumbers,files,zindex=XANIMZINDEX)
    

class BarSet:
  def __init__ (self, path, suffix='bar', imgtype='png'):
    bars = {'red':None, 'org':None, 'yel':None, 'grn':None}
    for color in bars.keys():
      fn = os.path.join(path, ''.join([color,suffix,'.',imgtype]))
      bars[color] = SimpleSprite(fn,zindex=BARSZINDEX)
    self.bars = bars
    for n in bars.keys(): self.__dict__[n] = bars[n]


class RenderLayered(pygame.sprite.RenderClear):

  def draw(self,surface):
    spritedict = self.spritedict
    surface_blit = surface.blit
    dirty = self.lostsprites
    dirty_append = dirty.append
    self.lostsprites = []
    sitems=spritedict.items()
    sitems.sort(lambda a,b: cmp(a[0].zindex,b[0].zindex))
    for s,r in sitems:
      newrect = surface_blit(s.image,s.rect)
      if r is 0:
        dirty_append(newrect)
      else:
        dirty_append(newrect.union(r))
      spritedict[s] = newrect
    return dirty

  def ordersprites(self):
    " self.ordersprites() -> overlaplist, cleanlist"
    dirty=[]
    clean=[]
    dirty_append=dirty.append
    clean_append=clean.append
    sprlist = self.sprites
    while len(sprlist):
      sprite1 = sprlist.pop(0)
      spritecollide = sprite.rect.colliderect
      
      

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
    if int(mainconfig["vesacompat"]):
      screen = pygame.display.set_mode((640, 480), 16)
    
    elif int(mainconfig["fullscreen"]):
      if osname == "macosx":
        screen = pygame.display.set_mode((640, 480), FULLSCREEN, 16)
      else:
        screen = pygame.display.set_mode((640, 480), HWSURFACE|DOUBLEBUF|FULLSCREEN, 16)
    
    else:
      screen = pygame.display.set_mode((640, 480), HWSURFACE|DOUBLEBUF, 16)
  except:
    print "Can't get a 16 bit display!" 
    sys.exit()

# so it's currently in one routine. shut up, I'm learning python =]
def main():
  global screen,background,eventManager,currentTheme,playmode
  print "pyDDR, by theGREENzebra (tgz@clickass.org)"
  print "Initialising.."
  # SDL_mixer is retarded when trying to play oggs; doesn't force stereo
  if os.name == 'posix':
    try:
      pygame.mixer.pre_init(44100,-16,2)
    except:
      pygame.mixer.pre_init()
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
  eventManager = EventManager()

  global update_screen
  if (screen.get_flags()&DOUBLEBUF == DOUBLEBUF):
      update_screen = update_screen_doublebuffer
  elif screen.get_flags()&HWSURFACE:
      update_screen = update_display_hardware
  #else it defaults to software update rect

  pygame.mixer.music.load("menu.ogg")
  try:
    pygame.mixer.music.play(4, 0.0)
  except TypeError:
    print "Sorry, pyDDR needs a more up to date Pygame or SDL than you have."
    sys.exit()

  background = BlankSprite(screen.get_size())

  print "Loading Images.."
  currentTheme = Theme(theme)

  playmode = 'SINGLE'
  
  font = pygame.font.Font(None, 32)

  if debugmode:
    print "Entering debug mode. Not loading the song list."
    totalsongs = 1
  else:
    text_fadeon(screen, font, "Looking for songs..", (320, 240))
    print 'Searching for STEP files..'
    # Search recursively for all STEP files
    fileList = find(songdir, '*.step')
    for f in fileList:
      print "file: ", f
    totalsongs = len(fileList)
    fileList.sort()
    # return the list of valid songs
    songs = filter(None,map(fastSong,fileList))
    text_fadeoff(screen, font, "Looking for songs..", (320, 240))

  event = eventManager.poll()

  difWrap = 2*len(DIFFICULTIES)

  if totalsongs < 1:
    print "You don't have any songs, and you need one. Go here: http://clickass.org/~tgz/pyddr/"
    sys.exit()


  text_fadeon(screen, font, "Prerendering....", (320, 240))
  print 'Prerendering'
  if not debugmode:
    # prerender the list texts for songs, speed up song selector
    brect = Rect(220, 250, 190, 5)
    ox = brect.left+4
    pixelbar = pygame.surface.Surface((1,3))
    pixelbar.fill((192,192,192))
    fuxor = 1
    for n in songs:
      x = brect.size[0] * fuxor/float(totalsongs)
      dirty = []
      for i in range(x-ox):
        dirty.append(screen.blit(pixelbar,(brect.left+ox+i,brect.bottom+3)))
      pygame.display.update(dirty)
      ox = x-1
      n.renderListText(totalsongs,fuxor)
      fuxor += 1

  p1combo = ComboDisp(1)
  holdkey = keykludge()
  p2combo = ComboDisp(2)
  holdkey2 = keykludge()
  global p1combo, p2combo, holdkey, holdkey2, sortmode
  text_fadeoff(screen, font, "Prerendering....", (320, 240))

#  pygame.time.delay(500)

  print "pyDDR ready. Entering song selector...."

  domenu(songs)
    
class TextSprite(BlankSprite):
  def __init__(self, font=None, size=32, text='', color=WHITE, bold=None, italic=None, underline=None, antialias=1, bkgcolor=None):
    pygame.sprite.Sprite.__init__(self)
    surf = None
    font = pygame.font.Font(font, size)
    if bold:      font.set_bold(bold)
    if italic:    font.set_italic(italic)
    if underline: font.set_underline(underline)
    if bkgcolor:
      surf = font.render(text,antialias,color,bkgcolor)
      surf.set_colorkey(bkgcolor)
    else:
      surf = font.render(text,antialias,color)
    self.image = surf
    self.rect = surf.get_rect()
      
def domenu(songs):
  global fooblah
  
  class MenuItem:
    # Simplest option switcher - select the next option in the list
    def opt_rotate(self, initial = 0):
      option_name = self.extras["option_name"]
      options = self.extras["options"]
      if not initial:
        current_val = mainconfig[option_name]
        new_val = None
        if current_val == None:
          new_val = options[0]
        else:
          new_val = options[(options.index(current_val) + 1) % len(options)]
        mainconfig[option_name] = new_val
        return new_val
      else:
        return mainconfig[option_name]

    # Slightly more advanced option switcher -
    # the displayed text is the list value, but the option value is
    # the index.
    def opt_rotate_with_index(self, initial = 0):
      option_name = self.extras["option_name"]
      options = self.extras["options"]
      if not initial:
        current_val = mainconfig[option_name]
        new_val = None
        if current_val == None: new_val = 0
        else:
          new_val = str((int(current_val) + 1) % len(options))
          mainconfig[option_name] = new_val
        return options[int(new_val)]
      else:
        return options[int(mainconfig[option_name])]

    # For settings with a range of values - divide into 25 discrete values,
    # cycle through them
    def change(self, sign, initial = 0):
      if type(self.extras) != types.DictionaryType: return None
      option_name = self.extras["option_name"]
      options = self.extras["options"]
      if not initial:
        try:
          delta = (self.extras["max"] - self.extras["min"])
          if type(delta) == types.FloatType:
            delta /= (sign * 15)
          else:
            delta /= (sign * min(delta, 20))
          try:
            val = int(mainconfig[option_name]) + delta
          except ValueError:
            val = float(mainconfig[option_name]) + delta
          val = str(max(self.extras["min"], min(self.extras["max"], val)))
          mainconfig[option_name] = val
          self.add_text = val
          self.render()
          return val
        except KeyError:
          return mainconfig[option_name]
      else:
        return mainconfig[option_name]

    # This is used for lyric & trans colors - it changes the text color
    # of the object and the data value
    def color_text(self, initial = 0):
      options = self.extras["options"]
      option_name = self.extras["option_name"]
      if not initial:
        is_next = False
        current_val = mainconfig[option_name]
        for colors in options:
          if colors[0] == current_val:
            print colors[0], "is current_val"
            is_next = True
          elif is_next:
            print colors[0], "was found next"
            mainconfig[option_name] = colors[0]
            self.add_text = colors[1]
            self.rgb = map((lambda x: int(x)), colors[0].split(","))
            is_next = False
            break
        if is_next: # we were at the end of the list
            mainconfig[option_name] = options[0][0]
            self.add_text = options[0][1]
            self.rgb = map((lambda x: int(x)), options[0][0].split(","))
      else:
        colorval = mainconfig[option_name]
        for colors in options:
          if colors[0] == colorval:
            self.add_text = colors[1]
        if self.add_text == None: # try to track manual changes and DTRT
          self.add_text = "custom"
        self.rgb = map((lambda x: int(x)), colorval.split(","))

      return self.add_text

    def __init__(self, itemname, extras):
      self.itemname = itemname    # actual item name
      self.extras = extras        # actual command/menu/list 
      self.image = pygame.surface.Surface((1,1))
      self.rgb = (224, 224, 224)
      self.add_text = None
      if type(self.extras) == types.DictionaryType:
        self.add_text = self.extras["function"](self, 1)
      else:
        self.add_text = None

    def activate(self):
      if callable(self.extras): # function to execute
        self.extras()
        return None, None
      elif type(self.extras) == types.DictionaryType:
          self.add_text = self.extras["function"](self)
          self.render()
          return None, None
      elif type(self.extras) == types.ListType:
        # Another menu
        return self.itemname, self.extras
      elif type(self.extras) == types.StringType:
        TextCycler(self.extras.split("\n"))
        return None, None
      elif self.extras == None:
        return -1, -1  # "Back"
      print "Error! Unknown menu structure."
      return None, None

    def render(self):
      # pretty box
      self.image = pygame.surface.Surface((192,40))
      for i in range(192):
        pygame.draw.line(self.image,(192-i,192-i,192-i),(i,0),(i,47))
        pygame.draw.line(self.image,(i,i,i),(i,0),(i,1))
        pygame.draw.line(self.image,(i,i,i),(i,46),(i,47))
      for i in range(2):
        pygame.draw.line(self.image,(192,192,192),(190+i,0),(190+i,47))
        pygame.draw.line(self.image,(0,0,0),(i,0),(i,47))
      # menu text
      if self.add_text == None:
        f = pygame.font.Font(None,32)
        itemtext = f.render(self.itemname,1, self.rgb)
        self.image.blit(itemtext, (96-(f.size(self.itemname)[0]/2), 8))
      else:
        f1 = pygame.font.Font(None, 26)
        f2 = pygame.font.Font(None, 20)
        itemtext = f1.render(self.itemname, 1, self.rgb)
        subtext = f2.render(self.add_text, 1, self.rgb)
        self.image.blit(itemtext ,(96-(f1.size(self.itemname)[0]/2), 4))
        self.image.blit(subtext,(96-(f2.size(self.add_text)[0]/2), 22))

  class Menu:
    def __init__(self, menuitemlist):
      self.itemlist = copy.copy(menuitemlist)
      self.items = []
      for i in menuitemlist:
        curitem = MenuItem(i[0], i[1])
        self.items.append(curitem)
      for i in self.items:
        i.render()

  class TextCycler:
    def __init__(self, strings):
      pos = 0
      print len(strings)
      self.image = pygame.surface.Surface((640, 480))
      last_ev = None

      self.image.fill((0,0,0))
      f = pygame.font.Font(None, 36)
      mstring = strings[pos].strip()
      text = f.render(mstring, 1, (224, 224, 224))
      self.image.blit(text, ((640 - f.size(mstring)[0])/2, 240))
      offset = 40
      for i in range(28, 0, -4):
        f = pygame.font.Font(None, i)
        mstring = strings[pos - (32 - i) / 4].strip()
        text = f.render(mstring, 1, (6*i, 6*i, 6*i))
        self.image.blit(text, ((640-f.size(mstring)[0])/2, 245 - offset))
        mstring = strings[(pos + (32 - i) / 4) % len(strings)].strip()
        text = f.render(mstring, 1, (6*i, 6*i, 6*i))
        self.image.blit(text, ((640-f.size(mstring)[0])/2, 240 + offset))
        offset += i
      screen.fill((0,0,0))
      screen.blit(self.image, (0, 0))
      pygame.display.flip()

      force_scroll = 0
      while True:
        force_scroll += 1
        e = pygame.event.poll()
        if e.type == KEYUP:
          last_ev = None
        elif e.type == KEYDOWN or last_ev or force_scroll == 30:
          key = None
          if last_ev:
            key = last_ev
            last_ev = key
          elif force_scroll == 30:
            key = p1d
          else:
            key = e.key
            last_ev = key
          screen.fill((0,0,0))
          force_scroll = 0

          if key == p1u or key == p2u:
            pos = pos - 1
            if pos == -1: pos = len(strings) - 1

          elif key == p1d or key == p2d:
            pos = (pos + 1) % len(strings)

          elif key == K_ESCAPE or key == K_RETURN:
            break

          self.image.fill((0,0,0))
          f = pygame.font.Font(None, 36)
          mstring = strings[pos].strip()
          try:
            print mstring
            text = f.render(mstring, 1, (224, 224, 224))
          except:
            text = f.render(' ', 1, (224, 224, 224))
          self.image.blit(text, ((640-(f.size(mstring)[0]))/2, 240))
          offset = 36
          for i in range(28, 0, -4):
            f = pygame.font.Font(None, i)
            mstring = strings[pos - (32 - i) / 4].strip()
            text = f.render(mstring, 1, (6*i, 6*i, 6*i))
            self.image.blit(text, ((640-(f.size(mstring)[0]))/2, 245 - offset))
            mstring = strings[(pos + (32 - i) / 4) % len(strings)].strip()
            text = f.render(mstring, 1, (6*i, 6*i, 6*i))
            self.image.blit(text, ((640-(f.size(mstring)[0]))/2,
                                     240 + offset))
            offset += i
          screen.fill((0,0,0))
          screen.blit(self.image, (0, 0))
          pygame.display.flip()

        pygame.time.delay(500)

  # Hey, did you know at one point, Boliva was so overrun with rats that
  # they got the Pope to declare rats fish, so they could eat them every
  # Friday?

  SetDisplayMode(mainconfig)

  # Make structures appropriate for the menu
  def onoff_opt(name):
    return { "function" : MenuItem.opt_rotate_with_index,
             "option_name" : name,
             "options" : ['off', 'on'] }

  def list_opt(name, list):
    return { "function" : MenuItem.opt_rotate,
             "option_name" : name,
             "options" : list }

  def list_index_opt(name, list):
    return { "function" : MenuItem.opt_rotate_with_index,
             "option_name" : name,
             "options" : list }

  def range_opt(name, max, min = 0):
    return { "min" : min, 
             "max" : max,
             "options" : [],
             "option_name" : name,
             "function" : (lambda x, y=0 : MenuItem.change(x, 1, y)) }

  help_strings = """\
  pyDDR is a simple game. There's that mat (look down)
  and there's your feet. On the mat are four arrows,
  (up, down, left, and right), which is where you place
  your feet. Stepping on those is like pressing the
  arrows on the keyboard. There's also the start button
  which is like enter. Got it? Good. That's all the
  controls there are.
  ---
  Now, you're going to want to start an actual game. From
  the main menu, select New Game, then Single. A huge
  list of songs will come up - scroll through the list
  using up and down until you find one you like. In the
  bottom left there's going to be a number of bars. The
  more bars, the harder this song is. You can use left
  and right to select different difficulty levels. Once
  you hear a song you like, hit enter (or start) to
  start the game.
  ---
  Now there's a bunch of arrows scrolling up the screen.
  When they reach the top (which is also going to be
  on-beat with the music), step on that arrow. Keep
  doing this until the song's over. That's the whole
  game."""

  game_opts = ['Game Options',
               [("Autofail", onoff_opt("killsongonfail")),
                ("Arrow Speed",  range_opt("scrollspeed", 4.0, 1.0)),
                ("Reverse", onoff_opt("reversescroll")),
                ("Little", list_index_opt("little",
                                          ["show all notes", "no 16ths",
                                           "no 8ths", "no 8ths or 16ths"])),
                ("Hidden", list_index_opt("hidden", ["none", "hide one",
                                                     "hide two", "hide three"])),
                ("Sudden", list_index_opt("sudden", ["none", "hide one",
                                                     "hide two", "hide three"])),
                ("Top Arrows", onoff_opt("showtoparrows")),
                ("Arrows Shrink", onoff_opt("arrowshrink")),
                ("Arrows Grow", onoff_opt("arrowgrow")),
                ("Arrows Spin", onoff_opt("arrowspin")),
                ("Back", None)
                ]
               ]

  lyric_colors = [('0,244,244', 'cyan'),
                  ('0,244,122', 'aqua'),
                  ('244,244,122', 'yellow'),
                  ('244,244,244', 'white'),
                  ('244,122,122', 'red'),
                  ('244,122,244', 'purple'),
                  ('244,170,0', 'orange')]

  lyr_opts = ['Lyric Options',
              [('Show Lyrics', onoff_opt("showlyrics")),
               ('Lyric Color',
                { 'function': MenuItem.color_text,
                  'option_name': 'lyriccolor',
                  'options': lyric_colors }),
               ('Translation Color',
                { 'function': MenuItem.color_text,
                  'option_name': 'transcolor',
                  'options': lyric_colors }),
               ("Back", None)
               ]]

  def fullscreen_toggle():
    mainconfig["fullscreen"] = int(mainconfig["fullscreen"]) ^ 1
    if mainconfig["fullscreen"] == 1:
      if osname == "macosx":
        screen = pygame.display.set_mode((640, 480), FULLSCREEN, 16)
      else:
        screen = pygame.display.set_mode((640, 480),
                                         HWSURFACE|DOUBLEBUF|FULLSCREEN, 16)
    else:
      screen = pygame.display.set_mode((640, 480),
                                       HWSURFACE|DOUBLEBUF, 16)

  gr_opts = ['Graphic Options',
             [('Fullscreen', fullscreen_toggle),
              ('Arrow Theme', list_opt('gfxtheme', ['classic', 'bryan'])),
              ('Backgrounds', onoff_opt("showbackground")),
              ('BG Brightness', range_opt("bgbrightness", 255)),
              ('Exploding',
               list_index_opt("explodestyle",
                              ['none', 'rotate', 'scale', 'rotate & scale'])),
              ('FPS Counter', onoff_opt("fpsdisplay")),
              ('Show Combo', onoff_opt("showcombo")),
              ('Back', None)
              ]]


  mainmenu = [['PLAY GAME',
              [('SINGLE', (lambda : songSelect(songs, 1) )),
               ('VERSUS', (lambda : songSelect(songs, 2) )),
               ('DOUBLE', (lambda : sys.stdout.write("double\n"))),
               ('NONSTOP', (lambda : sys.stdout.write("nonstop\n"))),
               ('UNISON', (lambda : sys.stdout.write("unison\n"))),
               ('ONI', (lambda : sys.stdout.write("oni\n"))),
               ('Back', None)
               ]],
              ['OPTIONS',
               [game_opts, gr_opts, lyr_opts,
#                ("Preview Songs", onoff_opt("previewmusic")),
                ("Sort By", list_index_opt("sortmode",
                                           ["file", "song", "group", "bpm",
                                            "difficulty", "mix"])),
                ("Save Changes",
                 (lambda : mainconfig.write(os.path.join(rscdir, "pyddr.cfg")))),
                ("Back", None)
                ]],
              ('HELP', help_strings),
              ('CREDITS', (lambda : sys.stdout.write("credits strings\n"))),
              ('EXIT GAME', sys.exit)
             ]

  blah = Menu(mainmenu)
  lastmenu = []
  lasttext = []
  footopscreen = fontfx.TextZoomer("MAIN MENU",127,63,255)
  fooblah = ' '
  curitem = topitem = 0
  z = 8
  zd = -1

  while 1:
    k = pygame.event.poll()
    if k.type == KEYDOWN:
      if (k.key == p1d or k.key == p2d) and (curitem < len(blah.items)-1):
        curitem += 1
        if curitem >= topitem+7: 
          topitem += 1
      elif (k.key == p1u or k.key == p2u) and (curitem > 0):
        curitem -= 1
        if curitem < topitem: 
          topitem = curitem

      elif k.key == K_ESCAPE:
        if lastmenu == []:
          sys.exit()
        else:
          blah = Menu(lastmenu[-1:][0])
          lastmenu = lastmenu[:-1]
          footopscreen.changetext(lasttext[-1:][0])
          lasttext = lasttext[:-1]
          curitem=topitem=0

      elif k.key == p1l or k.key == p2l:
        blah.items[curitem].change(-1)
      elif k.key == p1r or k.key == p2r:
        blah.items[curitem].change(1)

      elif k.key == K_RETURN:
        zoomtext, newblah = blah.items[curitem].activate()
        if zoomtext == -1 and newblah == -1: # back
          blah = Menu(lastmenu[-1:][0])
          lastmenu = lastmenu[:-1]
          footopscreen.changetext(lasttext[-1:][0])
          lasttext = lasttext[:-1]
          curitem=topitem=0
        elif newblah:
          lastmenu.append(blah.itemlist)
          lasttext.append(footopscreen.zoomtext)
          blah = Menu(newblah)
          footopscreen.changetext(zoomtext)
          topitem = curitem = 0

    #blanx0r      
    screen.fill((0,0,0))

    # flashy header
    footopscreen.iterate()
    screen.blit(footopscreen.tempsurface,(0,0))

    # zooming text thinger for menuselect
    z += zd
    if (z > 12) or (z < 0):  zd *= -1

    for i in range(7):
      if i+topitem < len(blah.items):
        if i+topitem == curitem:
          screen.blit(pygame.transform.scale(blah.items[topitem+i].image,(200-z,48-(z/2))),(220+(z/2),76+(z/4)+i*48))
        else:
          screen.blit(blah.items[topitem+i].image,(224,80+i*48))

    pygame.display.flip()
    pygame.time.wait(10)

def blatantplug():
  xiphlogo = pygame.image.load("xifish.png").convert()
  pygamelogo = pygame.image.load("pygamelogo.png").convert()
  oddlogo = pygame.image.load("oddlogos.png").convert()
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
    
  pygame.mixer.music.load("plugmusic.ogg")
  pygame.mixer.music.play(0,14.75)
  pygame.mixer.music.set_volume(0)
  
  for i in range(26):
    screen.fill((i*8,i*8,i*8))
    pygame.display.flip()
    pygame.mixer.music.set_volume(i/2.0)
    pygame.time.delay(16)
    
  pygame.time.delay(450)

  screen.blit(pygamelogo,pygamelogorect)
  screen.blit(oddlogo,oddlogorect)
  screen.blit(xiphlogo,xiphlogorect)
  pygame.display.flip()

  pygame.time.delay(450)
  
  tfont = pygame.font.Font(None,48)
  plugtext = ["You have been playing:","pyDDR","by:","Brendan Becker","which is available at:","http://clickass.org"," ","Say hi to him if you like it!"," ","it was made possible by:","Python, SDL,  Pygame,  and Xiph.org"]
  for i in plugtext:
    mrtext = tfont.render(i,1,(plugtext.index(i)*8,plugtext.index(i)*8,plugtext.index(i)*8))
    mrtextrect = mrtext.get_rect()
    mrtextrect.centerx = 320
    mrtextrect.top = plugtext.index(i)*43
    screen.blit(mrtext,mrtextrect)
    pygame.display.flip()
    pygame.time.delay(45)

  pygame.time.delay(2250)

  for i in range(26):
    pygame.mixer.music.set_volume((26-i)/2.0)
    pygame.time.delay(4)
    

def songSelect(songs, players):
  global screen,background,eventManager,currentTheme,playmode,fooblah
  pygame.mixer.music.fadeout(500)
  totalredraw = 1

  if fooblah == " ":
    oldfoo = 0  
  else:
    oldfoo = 1  #so the song selector doesn't keep it on the same song and we can save it from the menus
    
  while 1:
    if totalredraw:
      totalredraw = 0
      # let's calm the impatient crowd
      font = pygame.font.Font(None,40)
      niftyscreenclear = pygame.surface.Surface((640,8))
      niftyscreenclear.fill((0,0,0))
      start = pygame.time.get_ticks()
      ticktime = 500 / 30
      for i in range(31):
        r1 = screen.blit(niftyscreenclear,(0,8*i))
        r2 = screen.blit(niftyscreenclear,(0,480-(8*i)))
        update_screen((r1, r2))
        pygame.time.delay(ticktime*i - (pygame.time.get_ticks() - start))

      realdiff = realdiff2 = -1
      songidx = scrolloff = s = difficulty = difficulty2 = 0
      helpfiles = ["keyboard-ik.png","mat-updn.png","keyboard-s.png","keyboard-jl.png","mat-leftright.png","keyboard-scroll.png","mat-scroll.png","random.png","start.png"]
      oldhelp = CloneSprite(pygame.surface.Surface((1,1)))
      oldhelp.set_colorkey(oldhelp.get_at((0,0)))
      oldhelp.set_alpha(0)
      curhelp = CloneSprite(oldhelp)
      helptime = pygame.time.get_ticks()
      fontdisp = dozoom = 1
      idir = -8
      i = 192
      sortmode = int(mainconfig["sortmode"])
      s = 1
      # filter out songs that don't support the current mode (e.g. 'SINGLE')
      songs = filter(lambda song,mode=playmode: song.modes.has_key(mode),songs)
      totalsongs = len(songs)
    #  fuxor = 1
    #  for n in songs: 
    #    n.renderListText(totalsongs,fuxor)
    #    fuxor += 1
      dirtyBar=dirtyBar2=songSelectDirty=None
      dif=numbars=-1
      dif2=numbars2=-1
      background.fill((48,48,48))
      background.draw(screen)
      pygame.display.flip()
      dirtyRect=None
      eraseRects=[]
      fEraseRects=[]
      lastidx = None
      sprList = []

      # need bkgcolor or else it will use per-pixel alpha
      arrowTextMax      = TextSprite(size=32*2, bkgcolor=BLACK, text='>')
      songSelectTextMax = TextSprite(size=47*2, bkgcolor=BLACK, text='SONG SELECT')
      prevsong = songs[0]
      previewMusic = int(mainconfig['previewmusic'])
      sortmode -= 1
      songChanged = 1

      print "fooblah (%s)"%repr(fooblah)
      print "oldfoo (%s)"%repr(oldfoo)

    if oldfoo:
      newlist = []
      for sorti in songs:
        newlist.append(sorti.fooblah)
      songidx = newlist.index(fooblah)
      print "songidx set to", songidx, "because stepfile was",fooblah
      songChanged = 1
      oldfoo = 0
      
    boink = 0
    pygame.time.wait(1)
    dirtyRects=[]
    dirtyRects2=[]
    for n in eraseRects: dirtyRects.append(background.draw(screen,n,n))
    eraseRects=[]
    currentSong = songs[songidx]
    diffList = currentSong.modediff[playmode]

    # If preview music option is set, switch songs when the song is changed
    if previewMusic:
      if songChanged:
        songChanged = 0
        songswitchedat = pygame.time.get_ticks()
        try:
          pygame.mixer.music.stop()
          pygame.mixer.music.load(currentSong.osfile)
          # Just an arbitrary start position, an attempt to pick up the chorus or
          # the most recognizable part of the song.
          previewStart = 45
          pygame.mixer.music.set_volume(1.0)
          pygame.mixer.music.play(0, currentSong.startsec + previewStart)
          pygame.mixer.music.set_volume(0.0)
        except pygame.error:
          print "had a problem previewing", currentSong.osfile
      timesince = (pygame.time.get_ticks() - songswitchedat)/1000.0
      if timesince <= 1.0:
        pygame.mixer.music.set_volume(timesince)
      if 9.0 <= timesince <= 10.0:
        pygame.mixer.music.set_volume(10.0-timesince)
      if timesince > 10.0:
        pygame.mixer.music.set_volume(0)
        pygame.mixer.music.stop()
    else:
      pygame.mixer.music.load("menu.ogg")
      try:
        pygame.mixer.music.play(4, 0.0)
      except TypeError:
        print "Sorry, pyDDR needs a more up to date Pygame or SDL than you have."
        sys.exit()
  
    event = eventManager.poll()
    if  event == E_QUIT:
      pygame.mixer.music.fadeout(1000)
      pygame.time.delay(1000)
      pygame.mixer.music.stop()
      pygame.mixer.music.load("menu.ogg")
      pygame.mixer.music.play(4, 0.0)
      pygame.mixer.music.set_volume(1.0)
      fooblah = currentSong.fooblah
      break
    elif event < 0:                                  pass # key up
    elif event == E_PASS:                            pass
    elif event == E_FULLSCREEN:
      pygame.display.toggle_fullscreen()
      mainconfig["fullscreen"] = int(mainconfig["fullscreen"]) ^ 1
    elif event == E_SCREENSHOT:                      s = 1
    elif (event == E_LEFT):    difficulty -= 1
    elif (event == E_RIGHT):   difficulty += 1
    elif (event == E_LEFT2):   difficulty2 -= 1
    elif (event == E_RIGHT2):  difficulty2 += 1
    elif (event == E_UP) or (event == E_UP2):
      prevsong = songs[songidx]
      songChanged = 1
      if songidx>0:
        songidx -= 1
        scrolloff = -60
        fontdisp = 1
        sod = 0
      else:
        songidx = totalsongs-1
        scrolloff = 60
        fontdisp = 1
        sod = 0
    elif (event == E_DOWN) or (event == E_DOWN2):
      prevsong = songs[songidx]
      songChanged = 1
      if songidx<(totalsongs-1):
        songidx += 1
        scrolloff = 60
        fontdisp = 1
        sod = 0
      else:
        songidx = 0
        scrolloff = -60
        fontdisp = 1
        sod = 0
    elif event == E_PGUP:
      prevsong = songs[songidx]
      songChanged = 1
      if songidx-5 > 0:
        songidx -= 5
        scrolloff = -60
        fontdisp = 1
        sod = 0
      else:
        songidx = 0
        scrolloff = 60
        fontdisp = 1
        sod = 0
    elif event == E_PGDN:
      prevsong = songs[songidx]
      songChanged = 1
      if songidx<(totalsongs-5):
        songidx += 5
        scrolloff = 60
        fontdisp = 1
        sod = 0
      else:
        songidx = totalsongs-1
        scrolloff = -60
        fontdisp = 1
        sod = 0
      '''
      print "fastsong total creation time was", songs[songidx].modereadcreationtime - songs[songidx].objectcreationtime
      print "      to make the banner it took", songs[songidx].bannercreationtime - songs[songidx].objectcreationtime
      print "     to define variables it took", songs[songidx].variablecreationtime - songs[songidx].bannercreationtime
      print "        to read the file it took", songs[songidx].filereadcreationtime - songs[songidx].variablecreationtime
      print "     to filter the modes it took", songs[songidx].modereadcreationtime - songs[songidx].filereadcreationtime
      '''
    elif (event == E_START2):
      players = 2
    elif (event == E_SELECT):
      newidx = int(random.random()*len(songs))
      if newidx < songidx:
        scrolloff = 60
      else:
        scrolloff = -60
      prevsong = songs[songidx]
      songidx = newidx
      songChanged = 1
      fontdisp = 1
      sod = 0
    elif event == E_START or ((event == E_START2) and (players==2)):
      pygame.mixer.music.fadeout(1000)
      annc.say('menu')
      background.blit(screen,(0,0))
      for n in range(63):
        background.set_alpha(255-(n*4))
        screen.fill(BLACK)
        background.draw(screen)
        pygame.display.flip()
        pygame.time.wait(1)
        if (eventManager.poll() == E_QUIT): 
          print "song was cancelled!"
          break
      background.set_alpha()
      screen.fill(BLACK)
      try:
        while annc.chan.get_busy():
          pass
      except:
        pass

      biggerdifflist = []
      biggerdifflist.append(diffList[difficulty])
      if players == 2:
        biggerdifflist.append(diffList[difficulty2])

      fooblah = currentSong.fooblah
      mrsong = Song(fooblah)
      pygame.mixer.quit()
      oldfoo = 1
      dance(mrsong,players,biggerdifflist)
      #blatantplug()

      totalredraw = 1
#      return currentSong,biggerdifflist

    if not totalredraw:
      # No difficulty selected.
      if difficulty<0: difficulty=len(diffList)-1
      if difficulty2<0: difficulty2=len(diffList)-1

      # User really wants to be on a different difficulty.
      # We had switched because the previous song didn't have the one the user wants.
      if realdiff != -1 and realdiff < len(diffList):
         difficulty=realdiff
         realdiff=-1
      if realdiff2 != -1 and realdiff2 < len(diffList):
         difficulty2=realdiff2
         realdiff2=-1

      # This song doesn't have the currently selected difficulty.
      if difficulty>=len(diffList): 
         realdiff=difficulty # Save it...
         difficulty=0 # And set to whatever the first one it has is.
      if difficulty2>=len(diffList): 
         realdiff2=difficulty2 # Save it...
         difficulty2=0 # And set to whatever the first one it has is.
      if dozoom:
        fontdisp=1
        dz = 0

      dz+=dozoom*16

      if fontdisp==1:
        if dz>255: 
          dozoom = 0
          dz=255
        for m in fEraseRects: dirtyRects.append(background.draw(screen,m,m))
        fEraseRects=[]
        screen.set_clip((0,0,640,388))
        clip=screen.get_clip()
        if lastidx!=songidx:
          lastidx = songidx
          sprList = []
          for j in range(7):
            idx = songidx-3+j
            if idx<0 or idx>=totalsongs:
              continue
            spr = CloneSprite(songs[idx].listimage)
            mra = 255-(abs(3-j)*91)
            if mra > 255:
              mra = 255
            spr.set_alpha(mra)
            spr.orig = 32+60*j
            if j != 3:
              sprList.append(spr)
        for spr in sprList:
          spr.rect.top = spr.orig+scrolloff+4
          spr.rect.left = 40
          ro=spr.draw(screen)
          if ro:
            dirtyRects.append(ro)
            fEraseRects.append(ro)
        screen.set_clip((0,0,640,480))

        currentSong.titleimage.set_alpha()
        dirtyRects.append(currentSong.titleimage.draw(screen))

      # currently selected song flasher thingy
      spr = CloneSprite(songs[songidx].listimage)
      mra = 192+(i/4)
      if mra > 255:
        mra = 255
      spr.set_alpha(mra)
      spr.rect = (40,212+scrolloff+4)
      ro=spr.draw(screen)
      if ro:
        dirtyRects.append(ro)
        fEraseRects.append(ro)

      if fontdisp==1:
        if (scrolloff<=2) and (scrolloff>=-2):
          scrolloff = 0
          fontdisp = 0
          sod = -1
        if sod > -1:
          sod += 1
        if scrolloff:
          scrolloff = scrolloff/sod 
        if sod == 2:
          sod = 0

      i += idir
      if i < 64:
        idir = 8
      if i > 240:
        idir = -8
      ii = 256-i

      if oldhelp.get_alpha() > 8:
        oldhelp.set_alpha(oldhelp.get_alpha()-8)
      if curhelp.get_alpha() < 244:
        curhelp.set_alpha(curhelp.get_alpha()+8)

      eraseRects.append(oldhelp.rect)
      eraseRects.append(curhelp.rect)
      dirtyRects.append(oldhelp.draw(screen))
      dirtyRects.append(curhelp.draw(screen))

      if helptime+4000 < pygame.time.get_ticks():
        helptime = pygame.time.get_ticks()
        oldhelp = CloneSprite(curhelp)
        curhelp = CloneSprite(pygame.image.load(os.path.join("menuhelp",helpfiles[0])).convert())
        helpfiles.append(helpfiles.pop(0))
        curhelp.rect.left = 128
        curhelp.rect.top = 400
        oldhelp.set_alpha(255)
        curhelp.set_alpha(0)

      scale = (0.5+float(i)/240.0)/2
      arrow = TransformSprite(arrowTextMax,scale=scale)
      arrow.set_alpha(scale*255)
      arrow.rect.right = 32
      arrow.rect.centery = screen.get_rect().centery
      eraseRects.append(arrow.rect)
      dirtyRects.append(arrow.draw(screen))

      arrow = TransformSprite(arrow,hflip=1)
      arrow.set_alpha(scale*255)
      arrow.rect.left = 608
      arrow.rect.centery = screen.get_rect().centery
      eraseRects.append(arrow.rect)
      dirtyRects.append(arrow.draw(screen))

      try:
        sortimg = TextSprite(size=20, bkgcolor=BLACK, text=string.upper(sortbytext))
        sortimg.rect.centerx = 320
        sortimg.rect.top = 388
        sortimg.set_alpha(192)
        eraseRects.append(sortimg.rect)
        dirtyRects.append(sortimg.draw(screen))
      except:
        pass

      select = TransformSprite(songSelectTextMax,scale=scale/1.5)
      select.set_alpha(scale*127)
      select.rect.centerx = 320
      select.rect.bottom = 482
      eraseRects.append(select.rect)
      dirtyRects.append(select.draw(screen))

      ldif=dif
      lnumbars=numbars
      dif=DIFFICULTYLIST.index(diffList[difficulty])
      numbars=currentSong.modeinfo[playmode][difficulty][1]
      if ldif!=dif or lnumbars!=numbars or dz>0:
        if dirtyBar: 
          dirtyRects.append(background.draw(screen,dirtyBar,dirtyBar))
        color = ((0,255,0),(255,128,0),(255,0,0))[dif]
        text = fontfx.embfade(DIFFICULTYLIST[dif],28,3,(96,32),color)
        text2 = fontfx.embfade(DIFFICULTYLIST[dif],28,3,(96,32),color)
        text2.set_colorkey((0,0,0))
        text.fill((48,48,48))
        text.blit(text2,(0,0))
        if dz>0: text.set_alpha(dz*20)
        dirtyRects.append(screen.blit(text, (8,420) ))
        kr = range(8)
        bars = currentTheme.bars
        for j in range(numbars):
          sj = 6+j*10
          for k in range(6):
            b=[bars.grn,bars.org,bars.red][dif]
            if dz>0:
              b.set_alpha(dz*16)
            else:
              b.set_alpha()
            dirtyRects.append(b.draw(screen,(sj+k,448)))
        dirtyBar = ([8,448],[8+12*10,32])

      if players == 2:
        ldif2=dif2
        lnumbars2=numbars2
        dif2=DIFFICULTYLIST.index(diffList[difficulty2])
        numbars2=currentSong.modeinfo[playmode][difficulty2][1]
        if ldif2!=dif2 or lnumbars2!=numbars2 or dz>0:
          if dirtyBar2: 
            dirtyRects.append(background.draw(screen,dirtyBar2,dirtyBar2))
          color = ((0,255,0),(255,128,0),(255,0,0))[dif2]
          text = fontfx.embfade(DIFFICULTYLIST[dif2],28,3,(96,32),color)
          text2 = fontfx.embfade(DIFFICULTYLIST[dif2],28,3,(96,32),color)
          text2.set_colorkey((0,0,0))
          text.fill((48,48,48))
          text.blit(text2,(0,0))
          if dz>0: text.set_alpha(dz*20)
          dirtyRects.append(screen.blit(text, (560,420) ))
          kr = range(8)
          bars = currentTheme.bars
          for j in range(numbars2):
            sj = 6+j*10
            for k in range(6):
              b=[bars.grn,bars.org,bars.red][dif2]
              if dz>0:
                b.set_alpha(dz*16)
              else:
                b.set_alpha()
              dirtyRects.append(b.draw(screen,(640-(sj+k),448)))
          dirtyBar2 = ([544,448],[640,32])

      pygame.time.delay(8)
      pygame.display.update(dirtyRects)

      if s:        # sort songs
        # 0 - alpha by step file
        # 1 - alpha by songname
        # 2 - alpha by groupname
        # 3 - ascending by bpm
        # 4 - ascending by difficulty
        # 5 - ascending by mix

        dozoom = 1
        lastidx = None

        newlist = []

        sortmode += 1
        if sortmode > 5 or sortmode < 0:
          sortmode = 0
        sortbytext = "sorted by "
        if sortmode == 0:
          sortbytext+= "filename"
          for sorti in songs:
            newlist.append(sorti.fooblah)
        if sortmode == 1:
          sortbytext+= "songname"
          for sorti in songs:
            newlist.append(sorti.song)
        if sortmode == 2:
          sortbytext+= "groupname"
          for sorti in songs:
            newlist.append(sorti.group)
        if sortmode == 3:
          sortbytext+= "bpm"
          for sorti in songs:
            newlist.append(sorti.bpm)
        if sortmode == 4:
          sortbytext+= "difficulty"
          for sorti in songs:
            newlist.append(sorti.modeinfo[playmode][difficulty][1])
        if sortmode == 5:
          sortbytext+= "mix"
          for sorti in songs:
            newlist.append(sorti.mixname)

        if int(mainconfig["sortpersist"]) == 1:
          mainconfig["sortmode"] = sortmode

        print sortbytext

        blah = zip(newlist,songs)
        blah.sort()
        songs = map(lambda x:x[1], blah)
        songidx = songs.index(currentSong)
        s = 0

def dance(song,players,difficulty):
  global screen,background,eventManager,currentTheme,playmode

  if players == 2:
    song2 = copy.copy(song)

  pygame.mixer.init()

  #JBUTTONS = [[E_START],[E_SCREENSHOT],[E_FULLSCREEN],[E_QUIT]]
  #            J_B(0)    J_B(1)         J_B(2)         J_B(3)
  
  G_START, G_SCREENSHOT, G_FULLSCREEN, G_QUIT = map(J_B,range(4))
  
  joypad = JoyPad(eventManager=eventManager)
  # render group, almost[?] every sprite that gets rendered
  rgroup = RenderLayered()
  # text group, EG. judgings and combos
  tgroup = RenderLayered()  
  # special group for top arrows
  sgroup = RenderLayered()
  # special group for arrowfx
  fgroup = RenderLayered()
  # moving arrows group
  agroup = RenderLayered()
  agroup2 = RenderLayered()

  # lyric display group
  lgroup = RenderLayered()

  # background group
  bgroup = RenderLayered()

  # dancer group
  dgroup = RenderLayered()

  if song.moviefile != ' ':
    backmovie = BGmovie(os.path.join(songdir,song.moviefile))
  else:
    backmovie = BGmovie(None)
    
  if song.bgfile != ' ':
    backimage = BGimage(os.path.join(songdir,song.bgfile))
    bifn = os.path.join(songdir,song.bgfile)
  else:
    try:
      bifn = song.fooblah[:-5] + '-bg.png'
      backimage = BGimage(bifn)
    except pygame.error:
      bifn = 'bg.png'
      backimage = BGimage('bg.png')

  if int(mainconfig['showbackground']) > 0:
    if song.moviefile == ' ':
      bgkludge = pygame.transform.scale(pygame.image.load(bifn),(640,480)).convert()
      bgkludge.set_alpha(int(mainconfig['bgbrightness']), RLEACCEL)
      background.image = pygame.surface.Surface((640,480))
      background.image.blit(bgkludge,(0,0))
      backimage.add(bgroup)
    else:
      background.fill(BLACK)
#      backmovie.add(bgroup)
  else:
    background.fill(BLACK)

  suddenval = float(mainconfig['sudden'])

  if int(64.0*float(mainconfig['hidden'])): hidden = 1
  else: hidden = 0
  
  hiddenval = float(mainconfig['hidden'])
  
  # so the current combos get displayed
  global p1combo
  global holdkey
  p1list0 = JudgingDisp(1)
  p1list1 = JudgingDisp(1)
  p1list2 = JudgingDisp(1)
  p1score = ScoringDisp(1,difficulty[0])
  lifebar = LifeBarDisp(1)
  holdtext = HoldJudgeDisp(1)

  holdtext.add(tgroup)
  lifebar.add(tgroup)  
  p1score.add(tgroup)
  
  if players == 2:
    p2list0 = JudgingDisp(2)
    p2list1 = JudgingDisp(2)
    p2list2 = JudgingDisp(2)
    p2score = ScoringDisp(2,difficulty[1])
    lifebar2 = LifeBarDisp(2)
    holdtext2 = HoldJudgeDisp(2)

    holdtext2.add(tgroup)
    lifebar2.add(tgroup)  
    p2score.add(tgroup)
  
  fpstext = fpsDisp()

#  dancer = DancerAnim(200,400)
#  dancer.add(dgroup)
  
  colortype = int(mainconfig['arrowcolors'])
  if colortype == 0:
    colortype = 1

  if int(mainconfig['fpsdisplay']):
    fpstext.add(tgroup)
  if int(mainconfig['showlyrics']):
    song.lyricdisplay.add(lgroup)
    song.transdisplay.add(lgroup)

  showcombo = int(mainconfig['showcombo'])

  if int(mainconfig['totaljudgings']) > 0:
    p1list0.add(tgroup)
  if int(mainconfig['totaljudgings']) > 1:
    p1list1.add(tgroup)
  if int(mainconfig['totaljudgings']) > 2:
    p1list2.add(tgroup)

  if players == 2:
    if int(mainconfig['totaljudgings']) > 0:
      p2list0.add(tgroup)
    if int(mainconfig['totaljudgings']) > 1:
      p2list1.add(tgroup)
    if int(mainconfig['totaljudgings']) > 2:
      p2list2.add(tgroup)

  bg = pygame.Surface(screen.get_size())
  bg.fill((0,0,0))

  # FLASHY SONG ZOOM
  for j in range(8):
    screen.blit(bg, (0,0))
    
    font = pygame.font.Font(None, ((8-j)*32)-14)
    backtext = font.render("pyDDR", 1, (16-j*2, 16-j*2, 16-j*2))
    backtextpos = backtext.get_rect()
    backtextpos.centerx = 320
    backtextpos.centery = 240
    screen.blit(backtext, backtextpos)

    pygame.display.flip()

  songtext = zztext(song.song,480,12)
  grptext = zztext(song.group,160,12)
  timewatch = TimeDisp()

  songtext.plunk()
  grptext.plunk()

  tgroup.add(timewatch)
  tgroup.add(songtext)
  tgroup.add(grptext)

  bgroup.draw(screen)

  blackspot,blkbar,blacktext = map(BlankSprite,((64,64),(3,24),(240,56)))

  marvelous=perfect=great=ok=crappy=shit=0
  life,oldlife = 25.0,0.0
  totalmiss=bestcombo=combo=failed=0
  oldet=0
  fps=0
  tempholding = [-1,-1,-1,-1]
  tempholding2 = [-1,-1,-1,-1]
  i,j,k=1,0,0
  screenshot=fontdisp=0
  
  song.cache()
  if song.crapout == 0:
    song.init()

  if song.crapout:
    font = None
    text = None
    font = pygame.font.Font(None, 192)
    text = font.render('ERROR!', 1, (48,48,48))
    textpos = text.get_rect()
    textpos.centerx = 320
    textpos.centery = 240
    screen.blit(text, textpos)

    font = None
    text = None
    font = pygame.font.Font(None, 32)

    if song.crapout == 1:
      text = font.render("The type of music file this song is in isn't recognised", 1, (224,224,224))
    if song.crapout == 2:
      text = font.render("The music file ("+song.file+") for this song wasn't found", 1, (224,224,224))

    text.set_colorkey(text.get_at((0,0)))
    textpos = text.get_rect()
    textpos.centerx = 320
    textpos.centery = 216
    screen.blit(text, textpos)

    text = font.render("Press ENTER", 1, (160,160,160))
    text.set_colorkey(text.get_at((0,0)))
    textpos = text.get_rect()
    textpos.centerx = 320
    textpos.centery = 264
    screen.blit(text, textpos)

    pygame.display.flip()

    while 1:
      event = pygame.event.poll()
      if (event.type == KEYDOWN and (event.key==13 or event.key==271)) or (event.type==JOYBUTTONDOWN and event.button==9):
        break


  tick=brokecombo=drawmiss=0   
  stepj = " "
  beatnum = bar = arroff = 0
  pulsechange = 1
  screenshot = 0

  arrowSet = currentTheme.arrows

#  for n in ['l','d','u','r']:
#    c=CloneSprite(arrowSet[n].n)
#    c.rect.top=64
#    c.add(rgroup)

#  print "playmode: %r difficulty %r modes %r" % (playmode,difficulty,song.modes)
#  print "Total arrows are %d " % song.totarrows[difficulty]
  song.play(playmode, difficulty[0],1)

  # second instance of song created JUST to manage player 2's arrows/etc, that's it
  if players == 2:
    song2.play(playmode, difficulty[1],0)

  if int(mainconfig['assist']):
    pygame.mixer.music.set_volume(0.6)
  else:
    pygame.mixer.music.set_volume(1.0)

  holds = len(song.holdref[song.modediff[playmode].index(difficulty[0])])
  if players == 2:
    holds2 = len(song.holdref[song.modediff[playmode].index(difficulty[1])])
  difflist = song.modediff[playmode]
  diffnum = difflist.index(difficulty[0])
  dajudge = Judge(song.bpm, holds, song.modeinfo[playmode][diffnum][1],
                  song.totarrows[difficulty[0]],difficulty[0])
  if players == 2:
    diffnum2 = difflist.index(difficulty[1])
    dajudge2 = Judge(song.bpm, holds2, song.modeinfo[playmode][diffnum2][1],
                     song.totarrows[difficulty[1]],difficulty[1])

  extbox = Blinky(song.bpm)
#  extbox.add(tgroup)

  toparr1_l = TopArrow(song.bpm,'l',ARROWTOP,1)
  toparr1_d = TopArrow(song.bpm,'d',ARROWTOP,1)
  toparr1_u = TopArrow(song.bpm,'u',ARROWTOP,1)
  toparr1_r = TopArrow(song.bpm,'r',ARROWTOP,1)

  toparrfx1_l = ArrowFX(song.bpm,'l',ARROWTOP,1)
  toparrfx1_d = ArrowFX(song.bpm,'d',ARROWTOP,1)
  toparrfx1_u = ArrowFX(song.bpm,'u',ARROWTOP,1)
  toparrfx1_r = ArrowFX(song.bpm,'r',ARROWTOP,1)

  if players == 2:
    toparr2_l = TopArrow(song.bpm,'l',ARROWTOP,2)
    toparr2_d = TopArrow(song.bpm,'d',ARROWTOP,2)
    toparr2_u = TopArrow(song.bpm,'u',ARROWTOP,2)
    toparr2_r = TopArrow(song.bpm,'r',ARROWTOP,2)
 
    toparrfx2_l = ArrowFX(song.bpm,'l',ARROWTOP,2)
    toparrfx2_d = ArrowFX(song.bpm,'d',ARROWTOP,2)
    toparrfx2_u = ArrowFX(song.bpm,'u',ARROWTOP,2)
    toparrfx2_r = ArrowFX(song.bpm,'r',ARROWTOP,2)

  if int(mainconfig['explodestyle']) > -1:
    toparrfx1_l.add(fgroup)
    toparrfx1_d.add(fgroup)
    toparrfx1_u.add(fgroup)
    toparrfx1_r.add(fgroup)

    if players == 2:
      toparrfx2_l.add(fgroup)
      toparrfx2_d.add(fgroup)
      toparrfx2_u.add(fgroup)
      toparrfx2_r.add(fgroup)

  if int(mainconfig['showtoparrows']):
    toparr1_l.add(sgroup)
    toparr1_d.add(sgroup)
    toparr1_u.add(sgroup)
    toparr1_r.add(sgroup)

    if players == 2:
      toparr2_l.add(sgroup)
      toparr2_d.add(sgroup)
      toparr2_u.add(sgroup)
      toparr2_r.add(sgroup)
  
  oldbpm = song.playingbpm
  bpmchanged = 0
  
  lastt=0
  while 1:
    #grab an event
    ee = song.get_events()
    if int(mainconfig['killsongonfail']) and lifebar.failed:
      song.kill()
    if ee is not None: 
#      print ee
      events,nevents,curtime,arrowtime,bpm = ee
    else:
      if song.isOver():
        break

    if players == 2:
      ee2 = song2.get_events()
      if ee2 is not None: 
        events2,nevents2,curtime2,arrowtime2,bpm2 = ee2
    
    # ticks is current ticks for joy history, state is joypad state, delta is change in joy state
    ticks, state, delta = joypad.poll()
    # nstate is the set of bits that were just turned on
    nstate = state&delta

#    print "nstate", nstate, "  state", state, "  delta",delta

    keys = 0

    if delta:
#      print state
      key = []
      
      if nstate&G_START:
        if holdkey.checkstate('r'):
          print "holding right plus start quits. pyDDR now exiting."
          sys.exit()
        elif holdkey.checkstate('l'):
          break
        else:
          pass
      
      if state&G_QUIT:       break
      if nstate&G_FULLSCREEN: 
        pygame.display.toggle_fullscreen()
      if nstate&G_SCREENSHOT: 
        screenshot = 1
      if nstate&J_LEFT:
        key.append('l1')
        toparr1_l.stepped(1,curtime+(song.offset*1000))
        keys += 1
      if nstate&J_RIGHT:
        key.append('r1')
        toparr1_r.stepped(1,curtime+(song.offset*1000))
        keys += 1
      if nstate&J_UP:
        key.append('u1')
        toparr1_u.stepped(1,curtime+(song.offset*1000))
        keys += 1
      if nstate&J_DOWN:
        key.append('d1')
        toparr1_d.stepped(1,curtime+(song.offset*1000))
        keys += 1
      if players == 2:
        if nstate&J_LEFT2:
          key.append('l2')
          toparr2_l.stepped(1,curtime+(song.offset*1000))
          keys += 1
        if nstate&J_RIGHT2:
          key.append('r2')
          toparr2_r.stepped(1,curtime+(song.offset*1000))
          keys += 1
        if nstate&J_UP2:
          key.append('u2')
          toparr2_u.stepped(1,curtime+(song.offset*1000))
          keys += 1
        if nstate&J_DOWN2:
          key.append('d2')
          toparr2_d.stepped(1,curtime+(song.offset*1000))
          keys += 1

    fxdir = fxtext = fxdir2 = fxtext2 = ' '
    fxtime = fxtime2 = 0.0
            
    if keys:
      for checkkey in range(keys):
        if key[checkkey][1] == '1':
          holdkey.pressed(key[checkkey][0])
          fxtext, fxdir, fxtime = dajudge.handle_key(key[checkkey][0], curtime)
        if players == 2 and (key[checkkey][1] == '2'):
          holdkey2.pressed(key[checkkey][0])
          fxtext2, fxdir2, fxtime2 = dajudge2.handle_key(key[checkkey][0], curtime)

    directions = ['l','d','u','r']
    for checkhold in directions:
      if checkhold == 'l':
        toparrfx1_l.holding(0)
      if checkhold == 'd':
        toparrfx1_d.holding(0)
      if checkhold == 'u':
        toparrfx1_u.holding(0)
      if checkhold == 'r':
        toparrfx1_r.holding(0)
      currenthold = holdkey.shouldhold(checkhold,curtime,song.holdinfo[song.modediff[playmode].index(difficulty[0])],song.playingbpm)
      if currenthold is not None:
        if holdkey.checkstate(checkhold):
          if dajudge.holdsub[tempholding[directions.index(checkhold)]] != -1:
            if checkhold == 'l':
              toparrfx1_l.holding(1)
            if checkhold == 'd':
              toparrfx1_d.holding(1)
            if checkhold == 'u':
              toparrfx1_u.holding(1)
            if checkhold == 'r':
              toparrfx1_r.holding(1)
          tempholding[directions.index(checkhold)] = currenthold
        else:
          dajudge.botchedhold(currenthold)
          holdtext.fillin(curtime,directions.index(checkhold),"NG")
      else:
        if tempholding[directions.index(checkhold)] > -1:
          if dajudge.holdsub[tempholding[directions.index(checkhold)]] != -1:
            tempholding[directions.index(checkhold)] = -1
            holdtext.fillin(curtime,directions.index(checkhold),"OK")

    if players == 2:
      for checkhold in directions:
        if checkhold == 'l':
          toparrfx2_l.holding(0)
        if checkhold == 'd':
          toparrfx2_d.holding(0)
        if checkhold == 'u':
          toparrfx2_u.holding(0)
        if checkhold == 'r':
          toparrfx2_r.holding(0)
        currenthold = holdkey2.shouldhold(checkhold,curtime,song.holdinfo[song.modediff[playmode].index(difficulty[1])],song.playingbpm)
        if currenthold is not None:
          if holdkey2.checkstate(checkhold):
            if dajudge2.holdsub[tempholding2[directions.index(checkhold)]] != -1:
              if checkhold == 'l':
                toparrfx2_l.holding(1)
              if checkhold == 'd':
                toparrfx2_d.holding(1)
              if checkhold == 'u':
                toparrfx2_u.holding(1)
              if checkhold == 'r':
                toparrfx2_r.holding(1)
            tempholding2[directions.index(checkhold)] = currenthold
          else:
            dajudge2.botchedhold(currenthold)
            holdtext2.fillin(curtime,directions.index(checkhold),"NG")
        else:
          if tempholding2[directions.index(checkhold)] > -1:
            if dajudge2.holdsub[tempholding2[directions.index(checkhold)]] != -1:
              tempholding2[directions.index(checkhold)] = -1
              holdtext2.fillin(curtime,directions.index(checkhold),"OK")

    if ee is not None:
      # handle events that are happening now
      for ev in events:
#        print "current event: %r"%ev
        if ev.extra == 'CHBPM':
          if (bpm != dajudge.getbpm()):
            dajudge.changingbpm(ev.bpm)
            if players == 2:
              dajudge2.changingbpm(ev.bpm)
        if ev.extra == 'TSTOP':
          pygame.time.wait(ev.bpm)
        if ev.feet:
          for (dir,num) in zip(['l','d','u','r'],ev.feet):
            if num & 8:
              dajudge.handle_arrow(dir, curtime, ev.when)

    if players == 2:
      if ee2 is not None:
        for ev in events2:
          if ev.feet:
            for (dir,num) in zip(['l','d','u','r'],ev.feet):
              if num & 8:
                dajudge2.handle_arrow(dir, curtime, ev.when)
              
    # handle only new arrows
    for ev in nevents:
#        print "future event: %r"%ev
      if ev.extra == 'CHBPM':
        song.lastbpmchangetime.append([ev.when,ev.bpm])
        print [ev.when,ev.bpm],"was added to the bpm changelist"
      if ev.feet:
        for (dir,num) in zip(directions,ev.feet):
          if num & 8:
            if not (num & 128):
              ArrowSprite(arrowSet[dir+repr(int(ev.color)%colortype)].c,curtime,ev.when,ev.bpm,1).add([agroup,rgroup])

          if num & 128:
            diffnum = song.modediff[playmode].index(difficulty[0])
            holdindex = song.holdref[diffnum].index((directions.index(dir),ev.when))
            HoldArrowSprite(arrowSet[dir+repr(int(ev.color)%colortype)].c,curtime,song.holdinfo[diffnum][holdindex],ev.bpm,song.lastbpmchangetime[0],1).add([agroup,rgroup])

    if players == 2:
      for ev in nevents2:
        if ev.feet:
          for (dir,num) in zip(directions,ev.feet):
            if num & 8:
              if not (num & 128):
                ArrowSprite(arrowSet[dir+repr(int(ev.color)%colortype)].c,curtime,ev.when,ev.bpm,2).add([agroup2,rgroup])

            if num & 128:
              diffnum = song.modediff[playmode].index(difficulty[1])
              holdindex = song.holdref[diffnum].index((directions.index(dir),ev.when))
              HoldArrowSprite(arrowSet[dir+repr(int(ev.color)%colortype)].c,curtime,song.holdinfo[diffnum][holdindex],ev.bpm,song.lastbpmchangetime[0],2).add([agroup2,rgroup])

    if len(song.lastbpmchangetime)>1:
      if (curtime >= song.lastbpmchangetime[1][0]):
        nbpm = song.lastbpmchangetime[1][1]
        print "BPM tried to change from ",oldbpm, " to ", nbpm, " at ",curtime,"..",
        if song.lastbpmchangetime[1][1] is not None:
          if int(mainconfig['showtoparrows']):
            toparr1_l.remove(sgroup)
            toparr1_d.remove(sgroup)
            toparr1_u.remove(sgroup)
            toparr1_r.remove(sgroup)

          toparr1_l = TopArrow(nbpm,'l',ARROWTOP,1)
          toparr1_d = TopArrow(nbpm,'d',ARROWTOP,1)
          toparr1_u = TopArrow(nbpm,'u',ARROWTOP,1)
          toparr1_r = TopArrow(nbpm,'r',ARROWTOP,1)

          if int(mainconfig['showtoparrows']):
            toparr1_l.add(sgroup)
            toparr1_d.add(sgroup)
            toparr1_u.add(sgroup)
            toparr1_r.add(sgroup)

          # PLAYER 2
          if players == 2:
            if int(mainconfig['showtoparrows']):
              toparr2_l.remove(sgroup)
              toparr2_d.remove(sgroup)
              toparr2_u.remove(sgroup)
              toparr2_r.remove(sgroup)

            toparr2_l = TopArrow(nbpm,'l',ARROWTOP,2)
            toparr2_d = TopArrow(nbpm,'d',ARROWTOP,2)
            toparr2_u = TopArrow(nbpm,'u',ARROWTOP,2)
            toparr2_r = TopArrow(nbpm,'r',ARROWTOP,2)

            if int(mainconfig['showtoparrows']):
              toparr2_l.add(sgroup)
              toparr2_d.add(sgroup)
              toparr2_u.add(sgroup)
              toparr2_r.add(sgroup)

          dajudge.changebpm(nbpm)
          if players == 2:
            dajudge2.changebpm(nbpm)
          oldbpm = nbpm
          print "succeeded."
        else:
          print "failed."
        song.lastbpmchangetime = song.lastbpmchangetime[1:]
        print "lastbpmchangetime is now",song.lastbpmchangetime
        bpmchanged = 0
        
    if fxtext != ' ':
      if (fxtext == 'MARVELOUS') or (fxtext == 'PERFECT') or (fxtext == 'GREAT'):
        for checkspr in agroup.sprites():
          try:  #because holds and other sprites will cause this to break
            if (checkspr.timef == fxtime) and (checkspr.dir == fxdir):
              checkspr.kill()  #they hit this arrow, kill it
          except:
            nothing = None  #dummy
        if fxdir == 'l':
          toparrfx1_l.stepped(curtime,fxtext)
        if fxdir == 'd':
          toparrfx1_d.stepped(curtime,fxtext)
        if fxdir == 'u':
          toparrfx1_u.stepped(curtime,fxtext)
        if fxdir == 'r':
          toparrfx1_r.stepped(curtime,fxtext)
    if fxtext2 != ' ':
      if (fxtext2 == 'MARVELOUS') or (fxtext2 == 'PERFECT') or (fxtext2 == 'GREAT'):
        for checkspr in agroup2.sprites():
          try:  #because holds and other sprites will cause this to break
            if (checkspr.timef == fxtime2) and (checkspr.dir == fxdir2):
              checkspr.kill()  #they hit this arrow, kill it
          except:
            nothing = None  #dummy
        if fxdir2 == 'l':
          toparrfx2_l.stepped(curtime,fxtext2)
        if fxdir2 == 'd':
          toparrfx2_d.stepped(curtime,fxtext2)
        if fxdir2 == 'u':
          toparrfx2_u.stepped(curtime,fxtext2)
        if fxdir2 == 'r':
          toparrfx2_r.stepped(curtime,fxtext2)
    
    dajudge.expire_arrows(curtime)
    for spr in agroup.sprites():
      spr.update(curtime,dajudge.getbpm(),song.lastbpmchangetime,hiddenval,suddenval)

    if players == 2:
      dajudge2.expire_arrows(curtime)
      for spr in agroup2.sprites():
        spr.update(curtime,dajudge2.getbpm(),song.lastbpmchangetime,hiddenval,suddenval)

    extbox.update(curtime+(song.offset*1000.0))

    # update the top arrows
    toparr1_l.update(curtime+(song.offset*1000.0))
    toparr1_d.update(curtime+(song.offset*1000.0))
    toparr1_u.update(curtime+(song.offset*1000.0))
    toparr1_r.update(curtime+(song.offset*1000.0))
    
    toparrfx1_l.update(curtime,dajudge.combo)
    toparrfx1_d.update(curtime,dajudge.combo)
    toparrfx1_u.update(curtime,dajudge.combo)
    toparrfx1_r.update(curtime,dajudge.combo)

    if players == 2:
      toparr2_l.update(curtime+(song.offset*1000.0))
      toparr2_d.update(curtime+(song.offset*1000.0))
      toparr2_u.update(curtime+(song.offset*1000.0))
      toparr2_r.update(curtime+(song.offset*1000.0))

      toparrfx2_l.update(curtime,dajudge2.combo)
      toparrfx2_d.update(curtime,dajudge2.combo)
      toparrfx2_u.update(curtime,dajudge2.combo)
      toparrfx2_r.update(curtime,dajudge2.combo)
    
    song.lyricdisplay.update(curtime)
    song.transdisplay.update(curtime)

    # make sure the combo displayed at the bottom is current and the correct size
    p1combo.update(dajudge.combo,curtime-dajudge.steppedtime)
    p1score.update(dajudge.score)
    p1list0.update(0, curtime-dajudge.steppedtime, dajudge.recentsteps[0])
    p1list1.update(1, curtime-dajudge.steppedtime, dajudge.recentsteps[1])
    p1list2.update(2, curtime-dajudge.steppedtime, dajudge.recentsteps[2])
    lifebar.update(dajudge)
    holdtext.update(curtime)
    if players == 2:
      p2combo.update(dajudge2.combo,curtime-dajudge2.steppedtime)
      p2score.update(dajudge2.score)
      p2list0.update(0, curtime-dajudge2.steppedtime, dajudge2.recentsteps[0])
      p2list1.update(1, curtime-dajudge2.steppedtime, dajudge2.recentsteps[1])
      p2list2.update(2, curtime-dajudge2.steppedtime, dajudge2.recentsteps[2])
      lifebar2.update(dajudge2)
      holdtext2.update(curtime)

    fpstext.update(curtime)
    timewatch.update(curtime)

#    dancer.update()
    backimage.update()
    backmovie.update(curtime)

    if backmovie.filename:
      if backmovie.changed or (fpstext.fpsavg > 30):
        backmovie.resetchange()
        backmovie.image.set_alpha(int(mainconfig['bgbrightness']), RLEACCEL)
        background.fill(BLACK)
        screen.blit(background.image,(0,0))
        screen.blit(backmovie.image,(0,0))

    songtext.update()
    grptext.update()

    # more than one display.update will cause flicker
#    bgroup.draw(screen)
    sgroup.draw(screen)
    dgroup.draw(screen)
#    rgroup.draw(screen)
    agroup.draw(screen)
    agroup2.draw(screen)
    fgroup.draw(screen)
    tgroup.draw(screen)
    lgroup.draw(screen)
    if showcombo:
      p1combo.draw(screen)
      if players == 2:
        p2combo.draw(screen)

    pygame.display.update()

    if screenshot:
      pygame.image.save(pygame.transform.scale(screen, (640,480)), "screenshot.bmp")
      screenshot = 0

    trippy = 1

    if not backmovie.filename:
      if showcombo:
        p1combo.clear(screen, background.image)
        if players == 2:
          p2combo.clear(screen, background.image)
      lgroup.clear(screen,background.image)
      tgroup.clear(screen,background.image)
      fgroup.clear(screen,background.image)
  #    rgroup.clear(screen,background.image)
      agroup.clear(screen,background.image)
      agroup2.clear(screen,background.image)
      dgroup.clear(screen,background.image)
      sgroup.clear(screen,background.image)

#    time.sleep(0.0066667)
#    time.sleep(0.0096066)

  # GRADES
  if int(mainconfig['grading']):

    grade = None
    if players == 2:
      grade = GradingScreen([dajudge, dajudge2]).make_gradescreen(screen)
    else:
      grade = GradingScreen([dajudge]).make_gradescreen(screen)

    if not grade:
      song.kill()
      return

    print "LPS for this song was %d tops, %d on average, %d at worst." % (
      fpstext.highest, fpstext.fpsavg(), fpstext.lowest)

    idir = -4
    i = 192
    font = pygame.font.Font(None, 32)
    while 1:
      if i < 32:
        idir = 4
      elif i > 224:
        idir = -4

      i += idir
      event = eventManager.poll()
      if (event == E_QUIT) or (event == E_START):
        break
      elif event == E_FULLSCREEN:  #f
        print "fullscreen toggle"
        pygame.display.toggle_fullscreen()
      elif event == E_SCREENSHOT: #s
        print "writing next frame to screenshot.bmp"
        screenshot = 1
          
      gradetext = font.render("Press ESC/ENTER/START",1, (i,128,128) )
      gradetextpos = gradetext.get_rect()
      gradetextpos.centerx = screen.get_rect().centerx
      gradetextpos.bottom = screen.get_rect().bottom - 16
      r = screen.blit(gradetext,gradetextpos)
      update_screen(r)
      pygame.time.wait(1)     # don't peg the CPU on the grading screen

      if screenshot:
        pygame.image.save(pygame.transform.scale(screen, (640,480)),
                          "screenshot.bmp")
        screenshot = 0
  song.kill()
# "end"

if __name__ == '__main__': main()
