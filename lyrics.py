from constants import *

import colors

class LyricChannel(pygame.sprite.Sprite):
  def __init__(self, top, color):
      pygame.sprite.Sprite.__init__(self)
      self.lyrics = []
      self.times = []
      self.prender = []
      self.lasttime = -1000
 
      self.image = pygame.surface.Surface((1,1))
 
      self.oldlyric = -1
      self.oldalp = 0
      self.color = color
      self.darkcolor = colors.darken_div(color)
      self.topimg = top

      self.rect = self.image.get_rect()
      self.rect.top = self.topimg
      self.rect.centerx = 320
       
  def addlyric(self, time, lyric):
    self.lyrics.append(lyric)
    self.times.append(time)
 
    image1 = FONTS[32].render(lyric,1,self.darkcolor)
    image2 = FONTS[32].render(lyric,1,self.color)
    rimage = pygame.Surface(image1.get_size(), 0, 16)
    rimage.fill((64,64,64))
    rimage.blit(image1,(-2,-2))
    rimage.blit(image1,(2,2))
    rimage.blit(image2,(0,0))
    rimage.set_colorkey(rimage.get_at((0,0)))
    image = rimage.convert()
 
    self.prender.append(image)

  def update(self, curtime):
    self.currentlyric = -1
    timediff = curtime - self.lasttime
    for i in self.times:
      if curtime >= i:
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

class Lyrics:
  def __init__(self, clrs):
    self.channels = {}
    self.colors = clrs
    
  def addlyric(self, time, chan, lyric):
    if not self.channels.has_key(chan):
      color = self.colors[chan % len(self.colors)]
      self.channels[chan] = LyricChannel(480 - (chan + 1) * 32, color)
    self.channels[chan].addlyric(time - 0.4, lyric)

  def update(self, curtime):
    for i in self.channels.values(): i.update(curtime)
