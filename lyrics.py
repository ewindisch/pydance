from constants import *

import colors

class LyricDisp(pygame.sprite.Sprite):
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
    
