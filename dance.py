import pygame
from constants import *

from util import toRealTime
from player import Player
from announcer import Announcer

from pygame.sprite import RenderUpdates

import fontfx, gradescreen, steps, audio, fileparsers, games, error, colors

import random, sys, os, copy

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

class FPSDisp(pygame.sprite.Sprite):
  def __init__(self):
    pygame.sprite.Sprite.__init__(self)
    self.oldtime = -10000000
    self.image = pygame.surface.Surface((1,1))
    self.clock = pygame.time.Clock()
    self.cycles = 0
    self.totalcount = 0

  def fps(self):
    return self.totalcount / self.cycles

  def update(self, time):
    self.clock.tick()

    self.totalcount += loops
    self.cycles += 1

    loops = int(self.clock.get_fps())
    if (time - self.oldtime) > 1:
      text = repr(loops) + " fps"
      self.image = FONTS[16].render(text, True, [160, 160, 160])
      self.rect = self.image.get_rect()
      self.image.set_colorkey(self.image.get_at([0, 0]), RLEACCEL)
      self.rect.bottom = 480
      self.rect.right = 640
      self.oldtime = time

class Blinky(pygame.sprite.Sprite):
  def __init__ (self, bpm):
    pygame.sprite.Sprite.__init__(self)
    self.tick = toRealTime(bpm, 0.5)
    self.frame = 0
    self.oldframe = -100
    self.topimg = []
    
    im = pygame.surface.Surface([48, 40])
    im.fill([1, 1, 1])
    self.topimg.append(im.convert())
    self.topimg.append(im.convert())

    im.fill([255, 255, 255])
    for i in range(2):          
      self.topimg.append(im.convert())

    self.image = self.topimg[3]
    self.rect = self.image.get_rect()
    self.rect.top = 440
    self.rect.left = 592

  def update(self, time):
    self.frame = int(time / self.tick) % 8
    if self.frame > 3: self.frame = 3

    if self.frame != self.oldframe:
      self.image = self.topimg[self.frame]
      self.oldframe = self.frame

class TimeDisp(pygame.sprite.Sprite):
  def __init__(self):
    pygame.sprite.Sprite.__init__(self)
    self.oldtime = "-1000"
    self.image = pygame.surface.Surface((1,1))
    self.rect = self.image.get_rect()
    self.rect.top = 0
    self.rect.centerx = 320
    self.blahmod = 0
        
  def update(self, time):
    nowtime = repr(time)[:repr(time).index('.')+3]
    if (nowtime != self.oldtime) and (self.blahmod > 1):
      self.image = FONTS[40].render(nowtime,1,(224,224,224))
      self.image.set_colorkey(self.image.get_at((0,0)), RLEACCEL)
      self.oldtime = nowtime
      self.rect = self.image.get_rect()
      self.rect.top = 0
      self.rect.centerx = 320
      self.blahmod = 0
    else:
      self.blahmod += 1

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

def play(screen, playlist, configs, songconf, playmode):
  numplayers = len(configs)

  game = games.GAMES[playmode]

  first = True

  players = []
  for playerID in range(numplayers):
    plr = Player(playerID, configs[playerID], songconf, game)
    players.append(plr)

  for songfn, diff in playlist:
    try: current_song = fileparsers.SongItem(songfn)
    except None:
      error.ErrorMessage(screen, ["There was an error loading",
                                  os.path.split(songfn)[1]])
      continue
      
    pygame.mixer.quit()
    prevscr = pygame.transform.scale(screen, (640,480))
    songdata = steps.SongData(current_song, songconf)

    for pid in range(len(players)):
      players[pid].set_song(current_song, diff[pid], songdata.lyricdisplay)

    print "Playing", songfn
    print songdata.title.encode("ascii", "replace"), "by", songdata.artist.encode("ascii", "replace")

    try:
      if dance(screen, songdata, players, prevscr, first, game):
        break # Failed
      first = False
    except None:
      error.ErrorMessage(screen, ["There was an error playing",
                                  os.path.split(songfn)[0]])
      first = True

  if mainconfig['grading']:
    grade = gradescreen.GradingScreen(players)
    background = pygame.transform.scale(screen, (640,480))
    if grade.make_gradescreen(screen, background):
      grade.make_waitscreen(screen)

def dance(screen, song, players, prevscr, ready_go, game):
  songFailed = False

  pygame.mixer.init()

  # text group, EG. judgings and combos
  tgroup =  RenderUpdates()  
  
  # lyric display group
  lgroup = RenderUpdates()

  if song.movie != None:
    backmovie = BGmovie(song.movie)
    background.fill(colors.BLACK)
  else:
    backmovie = BGmovie(None)
    
  background = pygame.Surface((640, 480))
  background.fill(colors.BLACK)

  ready_go_time = 100
  for player in players: ready_go_time = min(player.ready, ready_go_time)
  rgs = ReadyGoSprite(ready_go_time)
  if ready_go: tgroup.add(rgs)

  if mainconfig['showbackground'] > 0:
    if backmovie.filename == None:
      bgkludge = pygame.image.load(song.background).convert()
      bgkrect = bgkludge.get_rect()
      if (bgkrect.size[0] == 320) and (bgkrect.size[1] == 240):
        bgkludge = pygame.transform.scale2x(bgkludge)
      else:
        bgkludge = pygame.transform.scale(bgkludge,(640,480))
      bgkludge.set_alpha(mainconfig['bgbrightness'], RLEACCEL)
      
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

      background.blit(bgkludge, (0, 0))
    else:
      background.fill(colors.BLACK)
      screen.fill(colors.BLACK)
      pygame.display.flip()
  else:
    background.fill(colors.BLACK)
    screen.fill(colors.BLACK)
    pygame.display.flip()

  # Store these values so we don't look them up during the main loop
  strobe = mainconfig["strobe"]
  if strobe:
    extbox = Blinky(song.bpm)
    extbox.add(tgroup)

  fpsdisplay = mainconfig["fpsdisplay"]
  if fpsdisplay:
    fpstext = FPSDisp()
    timewatch = TimeDisp()
    tgroup.add([fpstext, timewatch])

  if mainconfig['showlyrics']:
    lgroup.add(song.lyricdisplay.channels.values())

  songtext = fontfx.zztext(song.title, 480,12)
  grptext = fontfx.zztext(song.artist, 160,12)

  songtext.zin()
  grptext.zin()

  tgroup.add((songtext, grptext))

  song.init()

  if song.crapout != 0:
    error.ErrorMessage(screen, ["The audio file for this song", song.filename,
                               "could not be found."])
    return False # The player didn't fail.

  screenshot = 0

  if mainconfig['assist']: audio.set_volume(0.6)
  else: audio.set_volume(1.0)

  song.play()
  for plr in players: plr.start_song()

  autofail = mainconfig['autofail']

  while 1:
    if autofail:
      songFailed = True
      for plr in players:
        if not plr.lifebar.gameover:
          songFailed = False
          break
      if songFailed:
        song.kill()

    for plr in players: plr.get_next_events(song)

    if song.is_over(): break
    else: curtime = audio.get_pos()/1000.0

    key = []

    ev = event.poll()

    for i in range(len(players)):
      if (event.states[(i, E_START)] and event.states[(i, E_SELECT)]):
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
      elif ev[1] == E_MARK: key.append((ev[0], 'w'))
      elif ev[1] == E_UNMARK: key.append((ev[0], 'k'))
      elif ev[1] == E_RIGHT: key.append((ev[0], 'r'))
      elif ev[1] == E_PGUP: key.append((ev[0], 'z'))
      elif ev[1] == E_PGDN: key.append((ev[0], 'g'))
      elif ev[1] == E_UP: key.append((ev[0], 'u'))
      elif ev[1] == E_DOWN: key.append((ev[0], 'd'))
      elif ev[1] == E_CENTER: key.append((ev[0], 'c'))

      ev = event.poll()

    if ev[1] == E_QUIT: return False
  
    for ev in key:
      if game.double: pid = ev[0] / 2
      else: pid = ev[0]
      
      if pid < len(players): players[pid].handle_key(ev, curtime)

    rectlist = []

    for plr in players: rectlist.extend(plr.game_loop(curtime, screen))

    if strobe: extbox.update(curtime + song.soffset)

    song.lyricdisplay.update(curtime)

    if backmovie.filename:
      backmovie.update(curtime)
      if backmovie.changed or (fpstext.fpsavg > 30):
        backmovie.resetchange()
        screen.blit(backmovie.image,(0,0))

    songtext.update()
    grptext.update()
    rgs.update(curtime)

    if fpsdisplay:
      fpstext.update(curtime)
      timewatch.update(curtime)

    rectlist.extend(tgroup.draw(screen))
    rectlist.extend(lgroup.draw(screen))

    if not backmovie.filename: pygame.display.update(rectlist)
    else: pygame.display.update()

    if screenshot:
      pygame.image.save(pygame.transform.scale(screen, (640,480)),
                        os.path.join(rc_path, "screenshot.bmp"))
      screenshot = 0

    if not backmovie.filename:
      lgroup.clear(screen,background)
      tgroup.clear(screen,background)
      for plr in players: plr.clear_sprites(screen, background)

    if ((curtime > players[0].length - 1) and
        (songtext.zdir == 0) and (songtext.zoom > 0)):
      songtext.zout()
      grptext.zout()

  print "Average FPS for this song was %d." % fpstext.fps()
  return songFailed
