#! /usr/bin/env python

# pyDDR - DDR clone written in Python
# I know the dependencies suck, but in terms of programming so do I.
# SONG SELECTOR

#import psyco
#psyco.jit()
#from psyco.classes import *

import pygame, pygame.surface, pygame.font, pygame.image, pygame.mixer, pygame.movie, pygame.sprite
import os, time, sys, glob, random, fnmatch
import pygame.surfarray
import pygame.transform
import types, operator
import fontfx
from pygame.locals import *
from Numeric import *
from stat import *

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
  
_pixels3d   = pygame.surfarray.pixels3d
_blit_array = pygame.surfarray.blit_array

#def (surf,color):
#  size = surf.rect.width*surf.rect.height
#  surf=surf.image
#  narray=_pixels3d(surf).astype(Float32)
#  reshape(narray,[size,3])
#  narray*=array(color).astype(Float32)
#  _blit_array(surf,narray.astype(Int8))

class ConfigFile:
  def __init__(self, filename, autoupdate = 1):
    self.filename = filename
    self.config = {}
    self.cursec = "__main__"
    self.autoupdate = autoupdate
    csec = "__main__"
    self.config[csec] = {}
    f = open(filename,"r")
    l = f.readlines()
    f.close()
    for cl in l:
      if cl[0] == '[':
        csec = cl[1:cl.find(']')]
        self.config[csec] = {}
        if self.cursec == "__main__": self.cursec = csec
      elif cl.isspace() or len(cl) == 0 or cl[0] == '#': pass
      else:
        self.config[csec][cl[0:cl.find(' ')]] = cl[cl.find(' ')+1:].strip()
  def get_section(self, section):
    return self.config[section]
  def get_sections(self):
    return self.config.keys()
  def get_keys(self, section):
    return self.config[section].keys()
  def get_value(self, key, section = None, default = None):
    if section == None: section = self.cursec
    try:
      return self.config[section][key]
    except KeyError:
      return default
  def set_value(self, key, value, section=None):
    if section == None: section = self.cursec
    self.config[section][key] = value
    if self.autoupdate: self.write()
    return value
  def select_section(self, section):
    self.cursec = section
    try:
      self.config.keys().index(section)
    except ValueError:
      self.config[section] = {}
  def write(self):
    f = open(self.filename, "w")
    for k in self.config.keys():
      f.write("[%s]\n" % k)
      for k2 in self.config[k].keys():
        f.write("%s %s" % (k2, self.config[k][k2]))
      f.write("\n")
    f.close()

#MAIN CONFIG FILE
mainconfig = ConfigFile('pyddr.cfg')

class Announcer:
  def __init__(self, config):
    self.config = config
    self.path = os.path.join(os.path.split(self.config.filename)[:-1])[0]
    ann = self.config.get_section("announcer")
    self.name = ann["name"]
    self.author = ann["author"]
    self.rev = ann["rev"]
    self.date = ann["date"]
    self.saytime = -1000000
  def __play(self, filename):
#    os.system("playmus %s &" % os.path.join(self.path,filename))
    if (pygame.time.get_ticks() - self.saytime > 6000):
      self.snd = pygame.mixer.Sound(os.path.join(self.path,filename))
      self.chan = self.snd.play()
    self.saytime = pygame.time.get_ticks()
  def say_file(self, filename):
    self.__play(filename)
  def saywait(self, sections, mood=(1,100)):
    self.say(sections,mood)
    try:
      while self.chan.get_busy():
        pass
    except:
      pass
  def say(self, sections, mood=(1,100)):
    # sections can be either a string or a sequence of strings.
    # mood can be either a number from 1-100, or a 2-tuple of numbers, which
    # will be treated as a range.
    secdata = {}
    try:
      sections.isalnum()
    except AttributeError:
      for x in sections:
        secdata.update(self.config.get_section(x))
    else:
      # we have only one section to read.
      secdata = self.config.get_section(sections)
    try:
      mood[0]
    except TypeError:
      # it's a single number, not a range.
      mood = (mood, mood)
    possible = []
    for x in secdata.keys():
      cm = int(secdata[x])
      if cm >= mood[0] and cm <= mood[1]:
        possible.append(x)
    if len(possible):
      self.__play(possible[random.randrange(len(possible))])
      
DefaultThemeDir = os.path.join('themes','gfx')
theme = mainconfig.get_value('gfxtheme',default='bryan')
songdir = mainconfig.get_value('songdir',default='.')
anncname = mainconfig.get_value('djtheme',default='none')
annc_cf = ConfigFile(os.path.join('themes','dj',anncname,'djtheme.cfg'))
annc = Announcer(annc_cf)

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
MODELIST = ['SINGLE','COUPLE']
MODES = emptyDictFromList(MODELIST)
BEATS = {'sixty':0.25,'twtfr':1.0/3.0,'steps':1.0,'tripl':4.0/3.0,'eight':2.0,'qurtr':4.0,'halfn':8.0,'whole':16.0} 

def toRealTime(bpm,steps):
  if bpm != 0:
    return steps*0.25*60.0/bpm
  else:
    return steps*0.25*60.0/146

class BGimage(pygame.sprite.Sprite):
  def __init__ (self, filename):
    pygame.sprite.Sprite.__init__(self)        #call Sprite initializer
    self.image = pygame.transform.scale(pygame.image.load(filename),(640,480)).convert()
    self.image.set_alpha(int(mainconfig.get_value('bgbrightness',default='127')), RLEACCEL)
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
        self.oldframe = copy.copy(curframe)

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
  def __init__ (self, bpm, holds):
    self.steps = {}
    self.tick = toRealTime(bpm, 1)
    self.perfect = self.great = self.ok = self.crap = self.shit = self.miss = 0
    self.combo = self.bestcombo = self.broke = 0
    self.steppedtime = -1000
    self.recentsteps = [' ',' ',' ']
#    self.table = string.maketrans("", "")
    self.early = self.late = self.ontime = 0
    self.totalcombos = 1
    self.bpm = bpm
    self.holdsub = []
    for i in range(holds):
      self.holdsub.append(0)
    
  def changebpm(self, bpm):
    self.tick = toRealTime(bpm, 1)
    self.bpm = copy.copy(bpm)
        
  def getbpm(self):
    return self.bpm
    
  def botchedhold(self,whichone):
    self.holdsub[whichone] = -1
    
  def handle_key(self, dir, curtime):
    times = self.steps.keys()
    time = round(curtime / (self.tick / 6))
    done = 0
    early = late = ontime = 0
    off = -1
    for i in range(-11, 12):
      if time+i in times:
        if dir in self.steps[time+i]:
          off = i
          if off > 3: self.early += 1
          elif off < -3: self.late += 1
          else: self.ontime += 1
          done = 1
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

        if off < 4:
          self.perfect += 1
          text = "PERFECT"
          anncrange = (80, 100)
        else:
          self.great += 1
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

    return text, dir, time

  def trytime(self, dir, time):
    return time in self.times and dir in self.steps[time]

  def expire_arrows(self, time):
    curtick = round((time - 2*self.tick) / (self.tick / 6))
    self.times = self.steps.keys()
    self.times.sort()
    for k in xrange(24):
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
  
  def handle_arrow(self, key, time):
    tick_6 = self.tick / 6
    curtick = round((time + 2*self.tick) / tick_6)
    self.times = self.steps.keys()
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
      
class zztext(pygame.sprite.Sprite):
    def __init__(self,text,x,y):
      pygame.sprite.Sprite.__init__(self) #call Sprite initializer
      self.x = copy.copy(x)
      self.y = copy.copy(y)
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
    def __init__(self,topnum,progx,progy):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.trect = 296+(int(mainconfig.get_value('totaljudgings',default=1))*24)
        self.sticky = int(mainconfig.get_value('stickycombo',default=1))
        self.lowcombo = int(mainconfig.get_value('lowestcombo',default=4))

        self.space = pygame.surface.Surface((1,1))
        self.space.fill((0,0,0))

        self.baseimage = self.space
        self.image = self.baseimage
        self.font = pygame.font.Font(None,48)

        self.rect = self.image.get_rect()
        self.image.set_colorkey(self.image.get_at((0,0)))
        self.rect.top = self.trect
        self.rect.centerx = 160

        pixelbar = pygame.surface.Surface((1,3))
        pixelbar.fill((192,192,192))
        
        self.prerender = []

        for i in range(topnum):
          if (i % 5) == 0:
            screen.blit(pixelbar, (progx+(i/5),progy))
            pygame.display.flip()
          text = repr(i) + "x COMBO"
          image1 = self.font.render(text,1,(16,16,16))
          image2 = self.font.render(text,1,(224,224,224))
          self.rimage = self.font.render(text,1,(224,224,224))
          self.rimage.blit(image1,(-2,2))
          self.rimage.blit(image1,(2,-2))
          self.rimage.blit(image2,(0,0))
          self.rimage.set_colorkey(self.rimage.get_at((0,0)))

          self.prerender.append(self.rimage)

    def update(self, xcombo, steptimediff):
      if (steptimediff < 0.36) or self.sticky:
        if (xcombo >= self.lowcombo):
          self.baseimage = self.prerender[xcombo]
        else:
          self.baseimage = self.space

        if steptimediff > 0.2:                steptimediff = 0.2
        self.image = pygame.transform.rotozoom(self.baseimage, 0, 1-(steptimediff*2))

        self.rect = self.image.get_rect()
        self.rect.top = self.trect
        self.rect.centerx = 160

class HoldJudgeDisp(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer

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
        self.rect.left = 48

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
          self.slotold[i] = copy.copy(self.slotnow[i])
          
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
        self.lasttime = copy.copy(i)

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
        self.oldalp = copy.copy(alp)

    self.oldlyric = copy.copy(self.currentlyric)
      
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
          self.highest = copy.copy(self.loops)
        if (self.loops < self.lowest) and len(self.fpses)>2:
          self.lowest = copy.copy(self.loops)

        self.fpses.append(self.loops)
        self.oldtime = copy.copy(time)
        self.loops = 0

class TopArrow(pygame.sprite.Sprite):
  def __init__ (self, bpm, direction, ypos):
    pygame.sprite.Sprite.__init__(self)        #call Sprite initializer
    self.presstime = -1
    self.steps = {}
    self.tick = toRealTime(bpm, 1);
    self.frame = 0
    self.oldframe = -1
    self.state = 'n'
    self.filepref = 'arr_'
    self.adder = 0
    self.direction = direction
    self.topimg = []
    self.ypos = ypos

    for i in range(8):
      if i < 4:        ftemp = 'n_'
      else:            ftemp = 's_'
      fn = os.path.join('themes','gfx',theme,'arr_') + ftemp + self.direction + '_' + repr(i) + '.png'
      self.topimg.append(pygame.image.load(fn))
      self.topimg[i].set_colorkey(self.topimg[i].get_at((0,0)),RLEACCEL)

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

      self.rect = self.image.get_rect()
      self.image.set_colorkey(self.image.get_at((0,0)))
      self.rect.top = self.ypos
      if self.direction == 'l':        self.rect.left = 12
      if self.direction == 'd':        self.rect.left = 88
      if self.direction == 'u':        self.rect.left = 164
      if self.direction == 'r':        self.rect.left = 240

    self.oldframe = copy.copy(self.frame)

class ArrowFX(pygame.sprite.Sprite):
  def __init__ (self, bpm, direction, ypos):
    pygame.sprite.Sprite.__init__(self)        #call Sprite initializer
    self.presstime = -1000000
    self.tick = toRealTime(bpm, 1);
    self.centery = ypos + 32
    self.centerx = {'l':44, 'd':120, 'u':196, 'r':272}[direction]

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

    style = int(mainconfig.get_value('explodestyle', default='3'))
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
    if tinttype == 'GREAT':
      tinter.fill((0,255,0))
    tinter.set_alpha(127)
    self.tintimg.blit(tinter,(0,0))
    self.tintimg.set_colorkey(self.tintimg.get_at((0,0)))
    self.tintimg = self.tintimg.convert() #_alpha() #rotozoom wants _alpha 
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
          scale = 1.0 + (steptimediff * 4.0)
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

class LifeBarDisp(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.oldlife = self.failed = 0
        self.life = 25
        self.image = pygame.Surface((204,28))
        self.blkbar = pygame.Surface((3,24))
        self.grade = None
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
        self.rect.left = 58

    def failed(self):
       return self.failed
       
    def update(self, judges):
      tstmp = judges.perfect + judges.great + judges.ok + judges.crap + judges.shit + judges.miss
      if tstmp: 
        self.life += judges.combo*8 / tstmp
        self.life += judges.bestcombo*8 / tstmp

      self.life = 25
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
        for j in xrange(50-self.life):
          self.image.blit(self.blkbar, ((2+int(self.life+j)*4), 2) )
        for j in xrange(self.life):
          barpos = int(self.life-j-1)
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

      self.oldlife = copy.copy(self.life)

class JudgingDisp(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer

        self.total = int(mainconfig.get_value('totaljudgings',default=1))
        self.sticky = int(mainconfig.get_value('stickyjudge',default=1))
        self.needsupdate = 1
        self.stepped = 0
        self.oldzoom = -1
        
        # prerender the text for judging for a little speed boost
        font = pygame.font.Font(None, 48)
        tx = font.size("PERFECT")[0]+4
        self.perfect = fontfx.shadefade("PERFECT",48,4,(tx,40),(224,224, 32))
        tx = font.size("GREAT")[0]+4
        self.great   = fontfx.shadefade("GREAT"  ,48,4,(tx,40),( 32,224, 32))
        tx = font.size("OK")[0]+4
        self.ok      = fontfx.shadefade("OK"     ,48,4,(tx,40),( 32, 32,224))
        tx = font.size("CRAPPY")[0]+4
        self.crappy  = fontfx.shadefade("CRAPPY" ,48,4,(tx,40),(128, 32,128))
        tx = font.size("ACK")[0]+4
        self.shit    = fontfx.shadefade("ACK"    ,48,4,(tx,40),( 96, 64, 32))
        tx = font.size("MISS")[0]+4
        self.miss    = fontfx.shadefade("MISS"   ,48,4,(tx,40),(224, 32, 32))
        self.space   = font.render( " ",       1, (  0,   0,   0) )

        self.perfect.set_colorkey(self.perfect.get_at((0,0)),RLEACCEL)
        self.great.set_colorkey(self.great.get_at((0,0)),RLEACCEL)
        self.ok.set_colorkey(self.ok.get_at((0,0)),RLEACCEL)
        self.crappy.set_colorkey(self.crappy.get_at((0,0)),RLEACCEL)
        self.shit.set_colorkey(self.shit.get_at((0,0)),RLEACCEL)
        self.miss.set_colorkey(self.miss.get_at((0,0)),RLEACCEL)

        self.image = self.space
        
    def update(self, listnum, steptimediff, judgetype):
      if steptimediff < 0.5 or (judgetype == ('MISS' or ' ')):
        if judgetype == " ":               self.image = self.space
        if judgetype == "PERFECT":         self.image = self.perfect
        if judgetype == "GREAT":           self.image = self.great
        if judgetype == "OK":              self.image = self.ok
        if judgetype == "CRAPPY":          self.image = self.crappy
        if judgetype == "SHIT":            self.image = self.shit
        if judgetype == "MISS":            self.image = self.miss

        zoomzoom = steptimediff

        if zoomzoom != self.oldzoom:
          if (steptimediff > 0.36) and (self.sticky == 0) and self.stepped:
            self.image = self.space
            self.needsupdate = 1
            self.stepped = 0
          if listnum == 0:
            if steptimediff > 0.2:                zoomzoom = 0.2
            self.image = pygame.transform.rotozoom(self.image, 0, 1-(zoomzoom*2))
            self.needsupdate = 1
            self.stepped = 1
          else:
            self.image = pygame.transform.rotozoom(self.image, 0, 0.6)
            self.needsupdate = 1

      if self.needsupdate:
        self.rect = self.image.get_rect()
        self.image.set_colorkey(self.image.get_at((0,0)))
        self.rect.bottom = 320+(listnum*24)
        self.rect.centerx = 160
        self.needsupdate = 0

class Song:
  def __init__ (self, fn, path=None):
    # note that I'm only copying DIFFICULTIES because it's the right size..
    self.haslyrics = ''
    self.fooblah = fn
    try:
      self.lilbanner = pygame.transform.rotate(pygame.image.load(fn[:-5]+'.png').convert(),-45)
    except:
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
    self.lastbpmchangetime = [[0.0,copy.copy(self.bpm)]]
    self.bgfile = ' '
    self.file = None
    self.moviefile = ' '
    self.mixname = 'unspecified mix'
    self.playingbpm = 146.0    # while playing, event handler will use this for arrow control
    self.mixerclock = int(mainconfig.get_value('mixerclock',default='0'))
    self.lyricdisplay = LyricDispKludge(400, map((lambda x: int(x)), mainconfig.get_value('lyriccolor',default='0,224,244').split(',')))
    self.transdisplay = LyricDispKludge(428, map((lambda x: int(x)), mainconfig.get_value('transcolor',default='0,224,122').split(',')))
    little = int(mainconfig.get_value('little',default='0'))
    coloringmod = 0
    self.totarrows = 0
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
              chompNext = modeDict, tail.next
              self.totarrows += 1
            curTime += toRealTime(curBPM,BEATS[firstword])
            coloringmod += BEATS[firstword]
          elif firstword == 'delay':
            curTime += toRealTime(curBPM,BEATS['qurtr']*int(nextword))
            coloringmod += (4*int(nextword))
            tail.next = SongEvent(when=curTime,bpm=curBPM,extra="DELAY")
            chompNext = modeDict, tail.next
          elif firstword == 'chbpm':
            curBPM = float(nextword)
            tail.next = SongEvent(when=curTime,bpm=curBPM,extra="CHBPM")
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
        if int(mainconfig.get_value('onboardaudio',default='0')):
          self.bpm = self.bpm * float(48000/44128.0)
        self.playingbpm = copy.copy(self.bpm)
      elif firstword in modes.keys():  chompNext=(modes[firstword],)
      elif firstword == 'file':        self.file = " ".join(rest)
      elif firstword == 'bg':          self.bgfile = " ".join(rest)
      elif firstword == 'movie':       self.moviefile = " ".join(rest)
      elif firstword == 'startat':     self.startsec = float(nextword)
      elif firstword == 'endat':       self.endsec = float(nextword)
      elif firstword == 'offset':      
        self.offset = float(-int(nextword)-int(mainconfig.get_value('masteroffset',default='0')))/1000.0
        if int(mainconfig.get_value('onboardaudio',default='0')):
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
    
  def play(self,mode,difficulty):
#    self.ss.play()
    try:
      if self.crapout == 0:
        pygame.mixer.music.play(0, self.startsec)
    except TypeError:
      raise QuitGame("Sorry, pyDDR needs at least pygame 1.4.9")
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
    return '<song song=%r group=%r bpm=%r file=%r>'%(self.song,self.group,self.bpm,self.file)

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
      self.lilbanner = pygame.transform.rotate(pygame.image.load(fn[:-5]+'.png').convert(),-45)
    except:
      self.lilbanner = pygame.surface.Surface((1,1))
    self.bannercreationtime = pygame.time.get_ticks()
    self.lilbanner.set_colorkey(self.lilbanner.get_at((0,0)))
    self.rrrr = self.lilbanner.get_rect()
    self.rrrr.center = (320,300)
    screen.blit(self.lilbanner,self.rrrr)
    pygame.display.flip()
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
    self.mixname = 'unspecified mix'
    self.playingbpm = 146.0    # while playing, event handler will use this for arrow control
    self.mixerclock = int(mainconfig.get_value('mixerclock',default='0'))
#    self.lyricdisplay = LyricDispKludge(400)
#    self.transdisplay = LyricDispKludge(428)
    little = int(mainconfig.get_value('little',default='0'))
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
    listimage = BlankSprite((640,48))
    stext = "%s - %s"%(self.group,self.song)
    cmap = (63+j*(192/(totalsongs+1)),j*(240/(totalsongs+1)),240-(j*255/(totalsongs+1)))
    text = fontfx.shadefade(stext,28,3,(640,32),cmap)
    listimage.blit(text,(32,0))
    stext = "BPM: %d"%int(round(self.bpm)) + "".join(map(lambda (n,d): "  %s %d"%(n,d),self.modeinfo[playmode])) + self.haslyrics
    text = fontfx.embfade(stext,28,3,(640,32),cmap)
    listimage.blit(text,(64,24))
    
    titleimage = BlankSprite((640,90))
    text = fontfx.shadefade(self.group,64,3,(640,68),(192,64,64))
    titleimage.blit(text,(8,0))
    text = fontfx.shadefade(self.song,48,3,(640,52),(192,64,192))
    text.set_colorkey(text.get_at((0,0)))
    titleimage.blit(text, (32,40))
    sn = repr(j)+"/"+repr(totalsongs)
#    print sn
    text = fontfx.embfade(sn,20,2,(56,16),(160,160,160))
    text.set_colorkey(text.get_at((0,0)))
    titleimage.blit(text, (584,0))
    
    self.listimage  = listimage
    listimage.set_colorkey(listimage.get_at((0,0)))
    self.titleimage = titleimage
    
  def discardListText(self):
    self.listimage = None
    self.titleimage = None

  def __nonzero__ (self):
    return self.isValid
    
  def __repr__ (self):
    return '<song song=%r group=%r bpm=%r file=%r>'%(self.song,self.group,self.bpm,self.file)

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
if int(mainconfig.get_value('reversescroll',default='0')):
  ARROWTOP  = 408
  ARROWBOT  = int(-64 - (float(mainconfig.get_value('scrollspeed',default='1'))-1)*576)
else:
  ARROWTOP  = 64
  ARROWBOT  = int(576 * float(mainconfig.get_value('scrollspeed',default='1')))

ARROWDIFF = float(ARROWTOP-ARROWBOT)

class ArrowSprite(CloneSprite):
  def __init__ (self, spr, curtime, endtime, bpm, zindex=ARROWZINDEX):
    CloneSprite.__init__(self,spr,zindex=zindex)
    self.timeo = curtime
    self.timef = endtime
    self.life  = endtime-curtime
    self.bpm = bpm
    self.curalpha = -1
    self.r = 0
    self.bimage = self.image
    self.arrowspin = float(mainconfig.get_value("arrowspin",default="0"))
    self.arrowshrink = float(mainconfig.get_value("arrowshrink",default="0"))
    self.arrowgrow = float(mainconfig.get_value("arrowgrow",default="0"))
    self.centerx = copy.copy(self.rect.centerx)
    
  def update (self,curtime,curbpm,lbct,hidden,sudden):
    if curtime>self.timef: # +(0.5*(60000/float(curbpm)))
      self.kill()
      return
      
    self.rect = self.image.get_rect()
    self.rect.centerx = self.centerx

    self.top = copy.copy(ARROWTOP)
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
          oldbpmsub = copy.copy(bpmsub)
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
    self.rect.top = copy.copy(self.top)
    
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
      alp = 255-(hiddenzone-self.rect.top)*8
    if self.rect.top > hiddenzone:
      if self.rect.top < suddenzone:
        alp = (suddenzone-self.rect.top)*8
    if alp < 0:      alp = 0
    if alp > 255:    alp = 255
    if alp != self.curalpha:
      self.image.set_alpha(alp)

class HoldArrowSprite(CloneSprite):
  def __init__ (self, spr, curtime, times, bpm, lastbpmtime, zindex=ARROWZINDEX):
    CloneSprite.__init__(self,spr,zindex=zindex)
    self.timeo = curtime
    self.timef1 = times[1]
    self.timef2 = times[2]
    self.life  = times[2]-curtime
    self.bpm = bpm
    self.lastbpmtime = lastbpmtime
    self.curalpha = -1
    self.r = 0
    self.oimage = pygame.surface.Surface((64,32))
    self.oimage.blit(self.image,(0,-32))
    self.oimage.set_colorkey(self.oimage.get_at((0,0)))
    self.oimage2 = pygame.surface.Surface((64,32))
    self.oimage2.blit(self.image,(0,0))
    self.oimage2.set_colorkey(self.oimage.get_at((0,0)))
    self.bimage = pygame.surface.Surface((64,1))
    self.bimage.blit(self.image,(0,-31))
    self.arrowspin = float(mainconfig.get_value("arrowspin",default="0"))
    self.arrowshrink = float(mainconfig.get_value("arrowshrink",default="0"))
    self.arrowgrow = float(mainconfig.get_value("arrowgrow",default="0"))
    self.centerx = copy.copy(self.rect.centerx)
    
  def update (self,curtime,curbpm,lbct,hidden,sudden):
    if curtime > self.timef2:
      self.kill()
      return
      
    self.rect = self.image.get_rect()
    self.rect.centerx = self.centerx

    self.top = copy.copy(ARROWTOP)
    self.bottom = copy.copy(ARROWTOP) #+ int(ARROWDIFF/8.0)

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
          oldbpmsub = copy.copy(bpmsub)
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
          oldbpmsub = copy.copy(bpmsub)
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
    self.rect.bottom = copy.copy(self.bottom)
 
    if self.top > 480:
      self.top = 480
    if self.top < 64:
      self.top = 64
    self.rect.top = copy.copy(self.top)
    
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
      alp = 255-(hiddenzone-self.rect.top)*8
    if self.rect.top > hiddenzone:
      if self.rect.top < suddenzone:
        alp = (suddenzone-self.rect.top)*8
    if alp < 0:      alp = 0
    if alp > 255:    alp = 255
    if alp != self.curalpha:
      self.image.set_alpha(alp)
  
#    print "alpha ",alp
      
# enum would be nice
E_PASS,E_QUIT,E_LEFT,E_RIGHT,E_UP,E_DOWN,E_FULLSCREEN,E_START,E_SCREENSHOT,E_HCENTER,E_VCENTER,E_PGUP,E_PGDN = range(13)

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
    ev |= 1 << (SHIFTAXIS   + axis)
  if dir is not None:
    ev |= 1 << (SHIFTDIR    + dir)
  if button is not None:
    ev |= 1 << (SHIFTBUTTON + button)
  return ev
  
KEYCONFIG = { E_QUIT:       [K_ESCAPE],
              E_LEFT:       [260,K_LEFT],
              E_RIGHT:      [262,K_RIGHT],
              E_UP:         [264,K_UP],
              E_DOWN:       [258,K_DOWN],
              E_FULLSCREEN: [102],
              E_SCREENSHOT: [115],
              E_START:      [13,271],
              E_PGUP:       [K_PAGEUP],
              E_PGDN:       [K_PAGEDOWN],
            }

JOYCONFIG = { E_LEFT:       [joyEvent(axis=HAXIS,dir=NEGATIVE),joyEvent( button=int(mainconfig.get_value('joy_left',default='4')) )],
              E_RIGHT:      [joyEvent(axis=HAXIS,dir=POSITIVE),joyEvent( button=int(mainconfig.get_value('joy_right',default='5')) )],
              E_UP:         [joyEvent(axis=VAXIS,dir=NEGATIVE),joyEvent( button=int(mainconfig.get_value('joy_up',default='7')) )],
              E_DOWN:       [joyEvent(axis=VAXIS,dir=POSITIVE),joyEvent( button=int(mainconfig.get_value('joy_down',default='6')) )],
              E_START:      [joyEvent( button=int(mainconfig.get_value('joy_start',default='9')) )],
              E_PGUP:       [joyEvent(axis=VAXIS,dir=NEGATIVE),joyEvent( button=int(mainconfig.get_value('joy_pgup',default='1')) )],
              E_PGDN:       [joyEvent(axis=VAXIS,dir=POSITIVE),joyEvent( button=int(mainconfig.get_value('joy_pgdn',default='3')) )],
            }

class EventManager:
  def __init__ (self,kConfig=KEYCONFIG,jConfig=JOYCONFIG,pygameevent=pygame.event):
    self.pygameevent = pygameevent
    pygameevent.set_blocked(range(NUMEVENTS))
    pygameevent.set_allowed((KEYUP,KEYDOWN))
    # joystick
    matjoy = None
    try:
      totaljoy = pygame.joystick.get_count()
    except:
      totaljoy = 0
    print totaljoy,"joystick[s] total. ",
    for i in xrange(totaljoy):
      ddrmat = pygame.joystick.Joystick(i)
      ddrmat.init()
      matbuttons = int(mainconfig.get_value('mat_buttons',default='12'))
      mataxes = int(mainconfig.get_value('mat_axes',default='6'))
      if ddrmat.get_numbuttons() == matbuttons and ddrmat.get_numaxes() == mataxes:
        matjoy = copy.copy(i)
      ddrmat.quit()
    if matjoy is not None:
      ddrmat = pygame.joystick.Joystick(matjoy)
      ddrmat.init()
      print "DDR mat initialised: js",matjoy
      pygameevent.set_allowed((JOYBUTTONUP,JOYBUTTONDOWN))
    else:
      print "No DDR mat found! Not initialising joystick"
    self.setupKeys(kConfig)
    self.setupJoy(jConfig)

  def __getattr__(self,attr):
    return getattr(self.pygameevent,attr)

  def setupKeys(self,kConfig=KEYCONFIG):
    keymap = {}
    for event,lst in kConfig.items():
      for key in lst:
        keymap[key]=event
    self.keymap=keymap

  def setupJoy(self,jConfig=JOYCONFIG):
    joymap = {}
    for event,lst in jConfig.items():
      for joy in lst:
        joymap[joy]=event
    self.joymap=joymap

  def nextEvent(self,event):
    if   event.type == QUIT:          return E_QUIT
    elif event.type == JOYAXISMOTION: return self.joyMove(event.axis,event.value)
    elif event.type == JOYBUTTONDOWN: return self.joyButton(event.button)
    elif event.type == JOYBUTTONUP:   return -self.joyButton(event.button)
    elif event.type == KEYDOWN:       return self.keyDown(event.key)
    elif event.type == KEYUP:         return -self.keyDown(event.key)
    else:                             return E_PASS

  def joyMove(self,axis,dir):
    if   dir<0: dir = NEGATIVE
    elif dir>0: dir = POSITIVE
    else:       dir = ZERO
    return self.joymap.get(joyEvent(axis=axis,dir=dir),E_PASS)

  def joyButton(self,button):
    return self.joymap.get(joyEvent(button=button),E_PASS)

  def keyDown(self,key):
    return self.keymap.get(key,E_PASS)

  def keyUp(self,key):
    return -self.keymap.get(key,E_PASS)
  
  def poll(self):
    blah = self.nextEvent(self.pygameevent.poll())
    if blah < 0:
      if blah == -2: holdkey.letgo('l')
      if blah == -3: holdkey.letgo('r')
      if blah == -4: holdkey.letgo('u')
      if blah == -5: holdkey.letgo('d')
    return blah
    
J_UP,J_DOWN,J_RIGHT,J_LEFT = map(lambda n: 1<<n, range(4))

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
                          E_RIGHT:   J_RIGHT}
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
      # print event ********
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
      
      


# so it's currently in one routine. shut up, I'm learning python =]
def main():
  global screen,background,eventManager,currentTheme,playmode
  print "pyDDR, by theGREENzebra (tgz@clickass.org)"
  print "Initialising.."
  # set up the screen and all that other stuff
  pygame.init()
  # SDL_mixer is retarded when trying to play oggs; doesn't force stereo
  pygame.mixer.quit()
  pygame.mixer.init(44100,-16,2)

  # DEBUG MODE - user just wants to test a step file
  debugmode = 0
  if len(sys.argv) > 1:
    debugmode = 1
    stepspecd = sys.argv[1]
    if stepspecd[-5:] != ".step":
      stepspecd += ".step"
    stepspecd = os.path.join(songdir,stepspecd)
    if len(sys.argv) > 2:
      difficulty = string.upper(sys.argv[2])
    else:
      difficulty = 'BASIC'

  pygame.mixer.music.load("loading.ogg")
  try:
    pygame.mixer.music.play(4, 0.0)
  except TypeError:
    raise QuitGame("Sorry, pyDDR needs at least pygame 1.4.9")

  try:
    if int(mainconfig.get_value("vesacompat",default='0')):
      screen = pygame.display.set_mode((640, 480), 16)
    elif int(mainconfig.get_value("fullscreen",default='0')):
      screen = pygame.display.set_mode((640, 480), HWSURFACE|DOUBLEBUF|FULLSCREEN, 16)
    else:
      screen = pygame.display.set_mode((640, 480), HWSURFACE|DOUBLEBUF, 16)
  except:
    raise "Can't get a 16 bit display!" 
  pygame.display.set_caption('pyDDR')
  pygame.mouse.set_visible(0)
  eventManager = EventManager()

  background = BlankSprite(screen.get_size())

  print "Loading Images.."
  currentTheme = Theme(theme)

  playmode = 'SINGLE'
  
  font = pygame.font.Font(None, 32)

  if debugmode:
    print "Entering debug mode. Not loading the song list."
    totalsongs = 1
  else:
    for i in xrange(31):
      text = font.render("Looking for songs..",1,(i*8,i*8,i*8))
      trect = text.get_rect()
      trect.centerx = 320
      trect.centery = 240
      screen.blit(text,trect)
      pygame.display.flip()

    print 'Searching for STEP files..'
    # Search recursively for all STEP files
    fileList = find(songdir, '*.step')
    for f in fileList:
      print "file: ", f
    totalsongs = len(fileList)
    fileList.sort()
    # return the list of valid songs
    songs = filter(None,map(fastSong,fileList))

    for i in xrange(31):
      a = (31-i)*8
      text = font.render("Looking for songs..",1,(a,a,a))
      trect = text.get_rect()
      trect.centerx = 320
      trect.centery = 240
      screen.blit(text,trect)
      pygame.display.flip()

  event = eventManager.poll()

  difWrap = 2*len(DIFFICULTIES)

  if totalsongs < 1:
    raise QuitGame("No songs? Download one: http://clickass.org/~tgz/pyddr/")

  for i in xrange(31):
    text = font.render("Prerendering....",1,(i*8,i*8,i*8))
    trect = text.get_rect()
    trect.centerx = 320
    trect.centery = 240
    screen.blit(text,trect)
    pygame.display.flip()

  if not debugmode:
    # prerender the list texts for songs, speed up song selector
    ox = copy.copy(trect.left)
    pixelbar = pygame.surface.Surface((1,3))
    pixelbar.fill((192,192,192))
    fuxor = 1
    for n in songs:
      x = trect.size[0] * fuxor/float(totalsongs)
      for i in range(x-ox):
        screen.blit(pixelbar,(trect.left+ox+i,trect.bottom+3))
      pygame.display.flip()
      ox = copy.copy(x)-1
      n.renderListText(totalsongs,fuxor)
      fuxor += 1

  global p1combo, holdkey, sortmode
  print "Prerendering.."
  p1combo = ComboDisp(768,trect.left,trect.bottom+6)
  holdkey = keykludge()
  
  for i in xrange(31):
    a = (31-i)*8
    text = font.render("Prerendering....",1,(a,a,a))
    trect = text.get_rect()
    trect.centerx = 320
    trect.centery = 240
    screen.blit(text,trect)
    pygame.display.flip()

  pygame.mixer.music.fadeout(500)
#  pygame.time.delay(500)

  stfile = ' '
  sortmode = int(mainconfig.get_value("sortmode",default='0'))-1

  print "pyDDR ready. Entering song selector...."

  while 1:    # this loop runs while music is playing only
    if debugmode != 1:
      print "stfile is ",stfile
      song,difficulty = songSelect(songs,stfile)
    try:
      if debugmode:
        stfile = stepspecd
      else:
        stfile = song.fooblah
      song = Song(stfile)
      dance(song,difficulty)
      if debugmode:
        print "Ending game, debug mode finished."
        break
    except QuitGame:
      pass
    song = difficulty = None
    sortmode -= 1
    
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
      
def songSelect(songs,fooblah):
  global screen,background,eventManager,currentTheme,playmode,sortmode

  # let's calm the impatient crowd
  font = pygame.font.Font(None,40)
  niftyscreenclear = pygame.surface.Surface((640,8))
  niftyscreenclear.fill((0,0,0))

  for i in xrange(31):
    screen.blit(niftyscreenclear,(0,8*i))
    screen.blit(niftyscreenclear,(0,480-(8*i)))
    pygame.display.flip()

  songidx = scrolloff = s = difficulty = 0
  fontdisp = dozoom = 1
  idir = -8
  i = 192
  # do we have a default sorting mode? should it persist?
  if int(mainconfig.get_value("sortpersist",default='1')):
    print "keeping persistent sortmode"
  else:
    sortmode = int(mainconfig.get_value("sortmode",default='0'))-1
  s = 1
  # filter out songs that don't support the current mode (e.g. 'SINGLE')
  songs = filter(lambda song,mode=playmode: song.modes.has_key(mode),songs)
  totalsongs = len(songs)
#  fuxor = 1
#  for n in songs: 
#    n.renderListText(totalsongs,fuxor)
#    fuxor += 1
  dirtyBar=songSelectDirty=None
  dif=numbars=-1
  background.fill(BLACK)
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
  previewMusic = int(mainconfig.get_value('previewmusic', default='1'))
  songChanged = 1
  while 1:
    boink = 0
    time.sleep(0.01)
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
#      print timesince, pygame.mixer.music.get_volume()
      if timesince <= 1.0:
        pygame.mixer.music.set_volume(timesince)
      if 9.0 <= timesince <= 10.0:
        pygame.mixer.music.set_volume(10.0-timesince)
      if timesince > 10.0:
        pygame.mixer.music.set_volume(0)
    else:
      pygame.mixer.music.load("menu.ogg")
      try:
        pygame.mixer.music.play(4, 0.0)
      except TypeError:
        raise QuitGame("Sorry, pyDDR needs at least pygame 1.4.9")
  
    event = eventManager.poll()
    if   event == E_QUIT:       
      pygame.mixer.music.fadeout(1000)
      raise QuitGame("Quit from songSelect")
    elif event < 0:             pass # key up
    elif event == E_PASS:       pass
    elif event == E_FULLSCREEN: pygame.display.toggle_fullscreen()
    elif event == E_SCREENSHOT: s = 1
    elif event == E_LEFT:       difficulty -= 1
    elif event == E_RIGHT:      difficulty += 1
    elif event == E_UP:
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
    elif event == E_DOWN:
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
    elif event == E_START:
      pygame.mixer.music.fadeout(1000)
      annc.saywait('menu')
      background.blit(screen,(0,0))
      for n in range(20):
        background.set_alpha(255/(2*n+1))
        screen.fill(BLACK)
        background.draw(screen)
#        pygame.display.flip()
        if (eventManager.poll() == E_QUIT): raise QuitGame("Quit right before playing?") # be nice..
      background.set_alpha()
      screen.fill(BLACK)
#      pygame.display.flip()
# free some RAM

#      for n in songs: n.discardListText()
      return currentSong,diffList[difficulty]
    
    if difficulty<0: difficulty=len(diffList)-1
    if difficulty>=len(diffList): difficulty=0
    
    if dozoom:
      fontdisp=1
      dozoom+=1
      if dozoom<17:
        if dirtyRect:
          background.fill(BLACK,dirtyRect)
          screen.fill(BLACK,dirtyRect)
        j=dozoom
        font = pygame.font.Font(None, (j+1)*16)
        backtext = None
        backtext = font.render("pyDDR", 1, (j, j, j))
        backtextpos = backtext.get_rect()
        backtextpos.center = screen.get_rect().center
        screen.blit(backtext, backtextpos)
        dirtyRect=backtextpos
        dirtyRects.append(dirtyRect)
      elif dozoom<(17+8):
        background.fill(BLACK,dirtyRect)
        screen.fill(BLACK,dirtyRect)
        j=dozoom-17
        dirtyRects.append(dirtyRect)
        font = pygame.font.Font(None, 256-(j*2))
        backtext = font.render("pyDDR", 1, (16, 16, 16))
        backtextpos = backtext.get_rect()
        backtextpos.center = screen.get_rect().center
        screen.blit(backtext, backtextpos)
        dirtyRect=backtextpos
      else:
        dozoom = 0
      background.blit(backtext,backtextpos)

    dz=dozoom*12
    
    #pygame.display.flip()    
    if fontdisp==1:
      if dz>255: dz=255
      for m in fEraseRects: dirtyRects.append(background.draw(screen,m,m))
      fEraseRects=[]
      if (scrolloff<=2) and (scrolloff>=-2):
        scrolloff = 0
        fontdisp = 0
        sod = -1
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
          spr.orig = 32+60*j
          sprList.append(spr)
      for spr in sprList:
        spr.rect.top = spr.orig+scrolloff
        ro=spr.draw(screen)
        if ro:
          dirtyRects.append(ro)
          fEraseRects.append(ro)
      screen.set_clip((0,0,640,480))
      if sod > -1:
        sod += 1
      if scrolloff:
        scrolloff = scrolloff/sod 
      if sod == 2:
        sod = 0
      if dz>0:
        currentSong.titleimage.set_alpha(dz)
      else:
        currentSong.titleimage.set_alpha()
      dirtyRects.append(currentSong.titleimage.draw(screen))

    i += idir
    if i < 64:
      idir = 8
    if i > 240:
      idir = -8
    ii = 256-i

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

    prevsong.lilbanner.set_alpha(abs(scrolloff*4))
    currentSong.lilbanner.set_alpha(255-abs(scrolloff*4))
    bannerrect = currentSong.lilbanner.get_rect()
    bannerrect.center = (320,440)
    screen.blit(prevsong.lilbanner,bannerrect)
    screen.blit(currentSong.lilbanner,bannerrect)

    if scrolloff:
      select = TransformSprite(songSelectTextMax,scale=1)
      select.set_alpha(0)
      select.rect.center = (screen.get_rect().centerx,440)
      eraseRects.append(select.rect)
      dirtyRects.append(select.draw(screen))

    select = TransformSprite(songSelectTextMax,scale=scale)
    select.set_alpha(scale*127)
    select.rect.center = (screen.get_rect().centerx,440)
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
      if dz>0: text.set_alpha(dz)
      dirtyRects.append(screen.blit(text, (8,420) ))
      kr = range(8)
      bars = currentTheme.bars
      for j in range(numbars):
        sj = 6+j*10
        for k in range(6):
          b=[bars.grn,bars.org,bars.red][dif]
          if dz>0:
            b.set_alpha(dz)
          else:
            b.set_alpha()
          dirtyRects.append(b.draw(screen,(sj+k,448)))
      dirtyBar = ([8,448],[8+12*10,32])

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
      if sortmode > 5:
        sortmode = 0

      if sortmode == 0:
        print "sorting by filename"
        for sorti in songs:
          newlist.append(sorti.fooblah)
      if sortmode == 1:
        print "sorting by songname"
        for sorti in songs:
          newlist.append(sorti.song)
      if sortmode == 2:
        print "sorting by groupname"
        for sorti in songs:
          newlist.append(sorti.group)
      if sortmode == 3:
        print "sorting by bpm"
        for sorti in songs:
          newlist.append(sorti.bpm)
      if sortmode == 4:
        print "sorting by difficulty"
        for sorti in songs:
          newlist.append(sorti.modeinfo[playmode][difficulty][1])
      if sortmode == 5:
        print "sorting by mix"
        for sorti in songs:
          newlist.append(sorti.mixname)
      blah = zip(newlist,songs)
      blah.sort()
      songs = map(lambda x:x[1], blah)
      songidx = songs.index(currentSong)
      
      s = 0

    if fooblah != ' ':
      newlist = []
      for sorti in songs:
        newlist.append(sorti.fooblah)
      songidx = newlist.index(fooblah)
      print "songidx set to", songidx, "because stepfile was",fooblah
      songChanged = 1
      fooblah = ' '

def dance(song,difficulty):
  global screen,background,eventManager,currentTheme,playmode

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
  agroup = pygame.sprite.Group()

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

  if int(mainconfig.get_value('showbackground',default='1')) > 0:
    if song.moviefile == ' ':
      bgkludge = pygame.transform.scale(pygame.image.load(bifn),(640,480)).convert()
      bgkludge.set_alpha(int(mainconfig.get_value('bgbrightness',default='127')), RLEACCEL)
      background.image = pygame.surface.Surface((640,480))
      background.image.blit(bgkludge,(0,0))
      backimage.add(bgroup)
    else:
      background.fill(BLACK)
#      backmovie.add(bgroup)
  else:
    background.fill(BLACK)

  suddenval = float(mainconfig.get_value('sudden',default='0'))

  if int(64.0*float(mainconfig.get_value('hidden',default='0'))):    hidden = 1
  else:                                                              hidden = 0
  
  hiddenval = float(mainconfig.get_value('hidden',default='0'))
  
  # so the current combos get displayed
  global p1combo
  global holdkey
  p1list0 = JudgingDisp()
  p1list1 = JudgingDisp()
  p1list2 = JudgingDisp()
  lifebar = LifeBarDisp()
  fpstext = fpsDisp()
  holdtext = HoldJudgeDisp()

  holdtext.add(tgroup)
  lifebar.add(tgroup)  
  
#  dancer = DancerAnim(200,400)
#  dancer.add(dgroup)
  
  colortype = int(mainconfig.get_value('arrowcolors',default=4))
  if colortype == 0:
    colortype = 1

  if int(mainconfig.get_value('fpsdisplay',default=1)):
    fpstext.add(tgroup)
  if int(mainconfig.get_value('showlyrics',default=1)):
    song.lyricdisplay.add(lgroup)
    song.transdisplay.add(lgroup)
    
  if int(mainconfig.get_value('showcombo',default=1)):
    p1combo.add(tgroup)

  if int(mainconfig.get_value('totaljudgings',default='1')) > 0:
    p1list0.add(tgroup)
  if int(mainconfig.get_value('totaljudgings',default='1')) > 1:
    p1list1.add(tgroup)
  if int(mainconfig.get_value('totaljudgings',default='1')) > 2:
    p1list2.add(tgroup)

  bg = pygame.Surface(screen.get_size())
  bg.fill((0,0,0))

  # FLASHY SONG ZOOM
  for j in xrange(8):
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
  songtext.plunk()
  grptext.plunk()
  tgroup.add(songtext)
  tgroup.add(grptext)

  bgroup.draw(screen)

  blackspot,blkbar,blacktext = map(BlankSprite,((64,64),(3,24),(240,56)))

  perfect=great=ok=crappy=shit=0
  life,oldlife = 25.0,0.0
  totalmiss=bestcombo=combo=failed=0
  oldet=0
  fps=0
  tempholding = [-1,-1,-1,-1]
  i,j,k=1,0,0
  screenshot=fontdisp=0
  
#  pygame.mixer.init()
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
  song.play(playmode,difficulty)
  pygame.mixer.music.set_volume(1.0)
  
  holds = len(song.holdref[song.modediff[playmode].index(difficulty)])
  dajudge = Judge(song.bpm, holds)

  toparr_l = TopArrow(song.bpm,'l',ARROWTOP)
  toparr_d = TopArrow(song.bpm,'d',ARROWTOP)
  toparr_u = TopArrow(song.bpm,'u',ARROWTOP)
  toparr_r = TopArrow(song.bpm,'r',ARROWTOP)

  toparrfx_l = ArrowFX(song.bpm,'l',ARROWTOP)
  toparrfx_d = ArrowFX(song.bpm,'d',ARROWTOP)
  toparrfx_u = ArrowFX(song.bpm,'u',ARROWTOP)
  toparrfx_r = ArrowFX(song.bpm,'r',ARROWTOP)

  if int(mainconfig.get_value('explodestyle',default='3'))>-1:
    toparrfx_l.add(fgroup)
    toparrfx_d.add(fgroup)
    toparrfx_u.add(fgroup)
    toparrfx_r.add(fgroup)

  if int(mainconfig.get_value('showtoparrows',default='1')):
    toparr_l.add(sgroup)
    toparr_d.add(sgroup)
    toparr_u.add(sgroup)
    toparr_r.add(sgroup)
  
  oldbpm = song.playingbpm
  bpmchanged = 0
  
  lastt=0
  while 1:
    #grab an event
    ee = song.get_events()
    if int(mainconfig.get_value('killsongonfail',default='0')) and lifebar.failed:
      song.kill()
    if ee is not None: 
#      print ee
      events,nevents,curtime,arrowtime,bpm = ee
    else:
      if song.isOver():
        break

    # ticks is current ticks for joy history, state is joypad state, delta is change in joy state
    ticks, state, delta = joypad.poll()
    # nstate is the set of bits that were just turned on
    nstate = state&delta
    key = 0

#    print "nstate", nstate, "  state", state, "  delta",delta

    keys = 0

    if delta:
      key = []
      if state&G_START:      pass
      if state&G_QUIT:       break
      if nstate&G_FULLSCREEN: 
        pygame.display.toggle_fullscreen()
      if nstate&G_SCREENSHOT: 
        screenshot = 1
      if nstate&J_LEFT:
        key.append('l')
        toparr_l.stepped(1,curtime+(song.offset*1000))
        keys += 1
      if nstate&J_RIGHT:
        key.append('r')
        toparr_r.stepped(1,curtime+(song.offset*1000))
        keys += 1
      if nstate&J_UP:
        key.append('u')
        toparr_u.stepped(1,curtime+(song.offset*1000))
        keys += 1
      if nstate&J_DOWN:
        key.append('d')
        toparr_d.stepped(1,curtime+(song.offset*1000))
        keys += 1

    fxdir = fxtext = ' '
            
    if keys:
      for checkkey in xrange(keys):
        holdkey.pressed(key[checkkey])
        fxtext, fxdir, fxtime = dajudge.handle_key(key[checkkey], curtime)

    directions = ['l','d','u','r']
    for checkhold in directions:
      if checkhold == 'l':
        toparrfx_l.holding(0)
      if checkhold == 'd':
        toparrfx_d.holding(0)
      if checkhold == 'u':
        toparrfx_u.holding(0)
      if checkhold == 'r':
        toparrfx_r.holding(0)
      currenthold = holdkey.shouldhold(checkhold,curtime,song.holdinfo[song.modediff[playmode].index(difficulty)],song.playingbpm)
      if currenthold is not None:
        if holdkey.checkstate(checkhold):
          if dajudge.holdsub[tempholding[directions.index(checkhold)]] != -1:
            if checkhold == 'l':
              toparrfx_l.holding(1)
            if checkhold == 'd':
              toparrfx_d.holding(1)
            if checkhold == 'u':
              toparrfx_u.holding(1)
            if checkhold == 'r':
              toparrfx_r.holding(1)
          tempholding[directions.index(checkhold)] = currenthold
        else:
          dajudge.botchedhold(currenthold)
          holdtext.fillin(curtime,directions.index(checkhold),"NG")
      else:
        if tempholding[directions.index(checkhold)] > -1:
          if dajudge.holdsub[tempholding[directions.index(checkhold)]] != -1:
            tempholding[directions.index(checkhold)] = -1
            holdtext.fillin(curtime,directions.index(checkhold),"OK")

    if ee is not None:
      # handle events that are happening now
      for ev in events:
#        print "current event: %r"%ev
        if ev.extra == 'CHBPM':
          if (bpm != dajudge.getbpm()):            bpmchanged = 1
#        print ev.bpm, "at", ev.when
        if ev.feet:
          for (dir,num) in zip(['l','d','u','r'],ev.feet):
            if num & 8:
              dajudge.handle_arrow(dir, curtime)
              
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
                ArrowSprite(arrowSet[dir+repr(int(ev.color)%colortype)].c,curtime,ev.when,ev.bpm).add([agroup,rgroup])
                
            if num & 128:
              diffnum = song.modediff[playmode].index(difficulty)
              holdindex = song.holdref[diffnum].index((directions.index(dir),ev.when))
              HoldArrowSprite(arrowSet[dir+repr(int(ev.color)%colortype)].c,curtime,song.holdinfo[diffnum][holdindex],ev.bpm,song.lastbpmchangetime[0]).add([agroup,rgroup])

    if len(song.lastbpmchangetime)>1:
      if (curtime >= song.lastbpmchangetime[1][0]):
        nbpm = song.lastbpmchangetime[1][1]
        print "BPM tried to change from ",oldbpm, " to ", nbpm, " at ",curtime,"..",
        if song.lastbpmchangetime[1][1] is not None:
          if int(mainconfig.get_value('showtoparrows',default='1')):
            toparrfx_l.remove(fgroup)
            toparrfx_d.remove(fgroup)
            toparrfx_u.remove(fgroup)
            toparrfx_r.remove(fgroup)

            toparr_l.remove(sgroup)
            toparr_d.remove(sgroup)
            toparr_u.remove(sgroup)
            toparr_r.remove(sgroup)

          toparr_l = TopArrow(nbpm,'l',ARROWTOP)
          toparr_d = TopArrow(nbpm,'d',ARROWTOP)
          toparr_u = TopArrow(nbpm,'u',ARROWTOP)
          toparr_r = TopArrow(nbpm,'r',ARROWTOP)

          toparrfx_l = ArrowFX(nbpm,'l',ARROWTOP)
          toparrfx_d = ArrowFX(nbpm,'d',ARROWTOP)
          toparrfx_u = ArrowFX(nbpm,'u',ARROWTOP)
          toparrfx_r = ArrowFX(nbpm,'r',ARROWTOP)

          if int(mainconfig.get_value('explodestyle',default='3'))>-1:
            toparrfx_l.add(fgroup)
            toparrfx_d.add(fgroup)
            toparrfx_u.add(fgroup)
            toparrfx_r.add(fgroup)

          if int(mainconfig.get_value('showtoparrows',default='1')):
            toparr_l.add(sgroup)
            toparr_d.add(sgroup)
            toparr_u.add(sgroup)
            toparr_r.add(sgroup)

          dajudge.changebpm(nbpm)
          oldbpm = copy.copy(nbpm)
          print "succeeded."
        else:
          print "failed."
        song.lastbpmchangetime = song.lastbpmchangetime[1:]
        print "lastbpmchangetime is now",song.lastbpmchangetime
        bpmchanged = 0
    
    if fxtext != ' ':
#      print "FX on ", fxdir, ' ', fxtext
      if (fxtext == 'PERFECT') or (fxtext == 'GREAT'):
        for checkspr in range(len(agroup.sprites())):
          dummy = 1
        if fxdir == 'l':
          toparrfx_l.stepped(curtime,fxtext)
        if fxdir == 'd':
          toparrfx_d.stepped(curtime,fxtext)
        if fxdir == 'u':
          toparrfx_u.stepped(curtime,fxtext)
        if fxdir == 'r':
          toparrfx_r.stepped(curtime,fxtext)
    
    dajudge.expire_arrows(curtime)
    
    for spr in agroup.sprites():
      spr.update(curtime,dajudge.getbpm(),song.lastbpmchangetime,hiddenval,suddenval)

    # update the top arrows
    toparr_l.update(curtime+(song.offset*1000.0))
    toparr_d.update(curtime+(song.offset*1000.0))
    toparr_u.update(curtime+(song.offset*1000.0))
    toparr_r.update(curtime+(song.offset*1000.0))
    
    toparrfx_l.update(curtime)
    toparrfx_d.update(curtime)
    toparrfx_u.update(curtime)
    toparrfx_r.update(curtime)
    
    song.lyricdisplay.update(curtime)
    song.transdisplay.update(curtime)

    # make sure the combo displayed at the bottom is current and the correct size
    p1combo.update(dajudge.combo,curtime-dajudge.steppedtime)
    p1list0.update(0, curtime-dajudge.steppedtime, dajudge.recentsteps[0])
    p1list1.update(1, curtime-dajudge.steppedtime, dajudge.recentsteps[1])
    p1list2.update(2, curtime-dajudge.steppedtime, dajudge.recentsteps[2])
    lifebar.update(dajudge)
    holdtext.update(curtime)
    fpstext.update(curtime)

#    dancer.update()
    backimage.update()
    backmovie.update(curtime)

    if backmovie.filename:
      if backmovie.changed:
        backmovie.resetchange()
        backmovie.image.set_alpha(int(mainconfig.get_value('bgbrightness',default='127')), RLEACCEL)
        background.fill(BLACK)
        screen.blit(background.image,(0,0))
        screen.blit(backmovie.image,(0,0))

    songtext.update()
    grptext.update()

    # more than one display.update will cause flicker
#    bgroup.draw(screen)
    sgroup.draw(screen)
    dgroup.draw(screen)
    rgroup.draw(screen)
    fgroup.draw(screen)
    tgroup.draw(screen)
    lgroup.draw(screen)
    pygame.display.update()

    if screenshot:
      pygame.image.save(pygame.transform.scale(screen, (640,480)), "screenshot.bmp")
      screenshot = 0
      
    lgroup.clear(screen,background.image)
    tgroup.clear(screen,background.image)
    fgroup.clear(screen,background.image)
    rgroup.clear(screen,background.image)
    dgroup.clear(screen,background.image)
    sgroup.clear(screen,background.image)

#    time.sleep(0.0066667)
#    time.sleep(0.0096066)

  for i in xrange(16):
    bg = pygame.Surface(screen.get_size())
    bg.fill(((15-i)*16,(15-i)*16,(15-i)*16))
    screen.blit(bg, (0,0))
    pygame.display.flip()

# GRADES - THIS NEEDS TO BE IN A FUNCTION OR HANDLED BY THE CLASS EVENTUALLY
  if int(mainconfig.get_value('grading',default='1')):
    totalsteps = dajudge.perfect + dajudge.great + dajudge.ok + dajudge.crap + dajudge.shit + dajudge.miss

    # do NOT put these in descending order or you'll get a D/E every time no matter how well you do =]
    if totalsteps:
      perfectpct = dajudge.perfect*100.0 / totalsteps
      greatpct = dajudge.great*100.0 / totalsteps
      okpct = dajudge.ok*100.0 / totalsteps
      crappypct = dajudge.crap*100.0 / totalsteps
      shitpct = dajudge.shit*100.0 / totalsteps
      misspct = dajudge.miss*100.0 / totalsteps

      #pick a grade
      grade = 'doh!'
      if (dajudge.perfect + dajudge.great >= totalsteps*0.2) and (misspct <= 8) and (shitpct <= 16) and (crappypct <= 24) and (okpct <= 32):
        grade = 'D'
      if (dajudge.perfect + dajudge.great >= totalsteps*0.4) and (misspct <= 6) and (shitpct <= 12) and (crappypct <= 18) and (okpct <= 24):
        grade = 'C'
      if (dajudge.perfect + dajudge.great >= totalsteps*0.6) and (misspct <= 4) and (shitpct <= 8) and (crappypct <= 12) and (okpct <= 16):
        grade = 'B'
      if (dajudge.perfect + dajudge.great >= totalsteps*0.8) and (misspct <= 2) and (shitpct <= 4) and (crappypct <= 6) and (okpct <= 8):
        grade = 'A'
      if (dajudge.perfect < dajudge.great) and (dajudge.perfect + dajudge.great == totalsteps):
        grade = 'S'
      if (dajudge.perfect >= dajudge.great) and (dajudge.perfect + dajudge.great == totalsteps):
        grade = 'SS'
      if (perfectpct >= 92) and (greatpct <= 8) and (dajudge.perfect + dajudge.great == totalsteps):
        grade = 'SSS'
      if dajudge.perfect == totalsteps:
        grade = '!!!!'

      gotholds = len(dajudge.holdsub)
      for i in range(len(dajudge.holdsub)):
        gotholds += dajudge.holdsub[i]

      print "GRADE:",grade,"- total steps:",totalsteps," best combo:",dajudge.bestcombo,"current combo:",dajudge.combo
      print "Mode:",difficulty,"  P:",dajudge.perfect," G:",dajudge.great," O:",dajudge.ok," C:",dajudge.crap," S:",dajudge.shit," M:",dajudge.miss," - ",gotholds,"/",len(dajudge.holdsub),"holds"
      print "LPS for this song was",fpstext.highest,"tops,",fpstext.fpsavg(),"on average,",fpstext.lowest,"at worst."
      
      for i in xrange(4):
        font = pygame.font.Font(None, 448-(i*8))
        gradetext = font.render(grade,1, (48-(i*4),48-(i*4),48-(i*4)) )
        gradetext.set_colorkey(gradetext.get_at((0,0)))
        gradetextpos = gradetext.get_rect()
        gradetextpos.centerx = screen.get_rect().centerx
        gradetextpos.centery = screen.get_rect().centery
        screen.blit(gradetext,gradetextpos)
        pygame.time.delay(48)
        pygame.display.flip()

      grading = fontfx.sinkblur("GRADING",64,4,(224,72),(64,64,255))
      screen.blit(grading, (320-grading.get_rect().centerx,4) )

      gnumbaby = "blah"
      font = pygame.font.Font(None, 28)
      for j in xrange(4):
        for i in xrange(14):
          if i == 0:
            gtextbaby = "PERFECT"
            gnumbaby = repr(dajudge.perfect)
            gpctbaby = '%.1f'%perfectpct
          if i == 1:
            gtextbaby = "GREAT"
            gnumbaby = repr(dajudge.great)
            gpctbaby = '%.1f'%greatpct
          if i == 2:
            gtextbaby = "OK"
            gnumbaby = repr(dajudge.ok)
            gpctbaby = '%.1f'%okpct
          if i == 3:
            gtextbaby = "CRAPPY"
            gnumbaby = repr(dajudge.crap)
            gpctbaby = '%.1f'%crappypct
          if i == 4:
            gtextbaby = "ACK"
            gnumbaby = repr(dajudge.shit)
            gpctbaby = '%.1f'%shitpct
          if i == 5:
            gtextbaby = "MISS"
            gnumbaby = repr(dajudge.miss)
            gpctbaby = '%.1f'%misspct
          if i == 6:
            gtextbaby = "TOTAL"
            gnumbaby = repr(totalsteps)
            gpctbaby = "------"
          if i == 7:
            gtextbaby = "MAX COMBO"
            gnumbaby = repr(dajudge.bestcombo)
            bestcombopct = dajudge.bestcombo*100.0/totalsteps
            gpctbaby = '%.1f'%bestcombopct
          if i == 8:
            gtextbaby = "CURRENT COMBO"
            gnumbaby = repr(dajudge.combo)
            combopct = dajudge.combo*100.0/totalsteps
            gpctbaby = '%.1f'%combopct
          if i == 9:
            gtextbaby = "TOTAL COMBOS"
            gnumbaby = repr(dajudge.totalcombos)
            gpctbaby = "------"
          if i == 10:
            if len(dajudge.holdsub):
              gtextbaby = "HOLDS/FREEZES"
              gnumbaby = repr(gotholds)+"/"+repr(len(dajudge.holdsub))
              holdpct = gotholds*100.0/len(dajudge.holdsub)
              gpctbaby = '%.1f'%holdpct
            else:
              gtextbaby = " "
              gnumbaby = " "
              gpctbaby = " "
          if i == 11:
            gtextbaby = "early steps"
            gnumbaby = repr(dajudge.early)
            combopct = dajudge.early*100.0/totalsteps
            gpctbaby = '%.1f'%combopct
          if i == 12:
            gtextbaby = "ontime steps"
            gnumbaby = repr(dajudge.ontime)
            combopct = dajudge.ontime*100.0/totalsteps
            gpctbaby = '%.1f'%combopct
          if i == 13:
            gtextbaby = "late steps"
            gnumbaby = repr(dajudge.late)
            combopct = dajudge.late*100.0/totalsteps
            gpctbaby = '%.1f'%combopct

          gpctbaby += "%"

          fc = ((j*32)+96-(i*8))
          if fc<0:    fc=0
          gradetext = fontfx.shadefade(gtextbaby,28,j,(224,32),(fc,fc,fc))
          gradetext.set_colorkey(gradetext.get_at((0,0)))
          gradetextpos = gradetext.get_rect()
          gradetextpos.right = 32 + screen.get_rect().centerx + 8-j
          gradetextpos.top = 64 + (i*25) + 8-j
          screen.blit(gradetext,gradetextpos)

          gradetext = font.render(gnumbaby,1, (fc,fc,fc) )
          gradetextpos = gradetext.get_rect()
          gradetextpos.right = 64 + screen.get_rect().centerx + 8-j
          gradetextpos.top = 64 + (i*25) + 8-j
          screen.blit(gradetext,gradetextpos)

          gradetext = font.render(gpctbaby,1, (fc,fc,fc) )
          gradetextpos = gradetext.get_rect()
          gradetextpos.right = 160 + screen.get_rect().centerx + 8-j
          gradetextpos.top = 64 + (i*25) + 8-j
          screen.blit(gradetext,gradetextpos)

          pygame.display.flip()

      idir = -4
      i = 192
      font = pygame.font.Font(None, 32)
      while 1:
        if i < 32:
          idir = 4
        if i > 224:
          idir = -4

        i += idir
        event = eventManager.poll()
        if (event == E_QUIT) or (event == E_START):
          break
        if event == E_FULLSCREEN:  #f
          print "fullscreen toggle"
          pygame.display.toggle_fullscreen()
        if event == E_SCREENSHOT: #s
          print "writing next frame to screenshot.bmp"
          screenshot = 1
          
        gradetext = font.render("Press ESC/ENTER/START",1, (i,128,128) )
        gradetextpos = gradetext.get_rect()
        gradetextpos.centerx = screen.get_rect().centerx
        gradetextpos.bottom = screen.get_rect().bottom - 16
        screen.blit(gradetext,gradetextpos)
        pygame.display.flip()
        time.sleep(0.0001) # don't peg the CPU on the grading screen

        if screenshot:
          pygame.image.save(pygame.transform.scale(screen, (640,480)), "screenshot.bmp")
          screenshot = 0
  song.kill()
# "end"

if __name__ == '__main__': main()
