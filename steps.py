from lyrics import LyricDisp
from constants import *

import colors

BEATS = { 'sixty': 0.25, 'thrty': 0.5, 'twtfr': 2.0/3.0,
          'steps': 1.0, 'tripl': 4.0/3.0, 'eight': 2.0,
          'qurtr': 4.0, 'halfn': 8.0, 'whole': 16.0 }

class SongEvent:
  def __init__ (self, bpm, when=0.0, feet=None, next=None,
                extra=None, color=None):
    self.bpm  = bpm
    self.when = when
    self.feet = feet
    self.next = next
    self.extra = extra
    self.color = color

  def __repr__(self):
    rest = []
    if self.feet: rest.append('feet=%r'%self.feet)
    if self.extra: rest.append('extra=%r'%self.extra)
    if self.extra: rest.append('color=%r'%self.color)
    return '<SongEvent when=%r bpm=%r %s>' % (self.when,self.bpm,
                                                ' '.join(rest))

# Step objects, made from SongItem objects

#FIXME Why are we using a linked list? We should be using a python list
class Steps:
  def __init__(self, song, difficulty, playmode="SINGLE",
               lyrics = None, trans = None): # FIXME - New lyrics system
    self.playmode = playmode
    self.difficulty = difficulty
    self.feet = song.difficulty[playmode][difficulty]
    self.length = 0.0
    self.offset = float(song.info["offset"] +
                        mainconfig['masteroffset']) / -1000.0

    if mainconfig['onboardaudio']:
      self.offset = self.offset * float(48000/44128.0)

    self.bpm = song.info["bpm"]
    self.lastbpmchangetime = [[0.0, self.bpm]]
    self.totalarrows = 0

    holdlist = []
    holdtimes = []
    releaselist = []
    releasetimes = []
    self.numholds = 1
    holding = [0, 0, 0, 0]
    little = mainconfig["little"]
    coloring_mod = 0
    cur_time = float(self.offset)
    cur_bpm = self.bpm
    self.events = SongEvent(when = cur_time, bpm = cur_bpm,
                            extra = song.difficulty[playmode][difficulty])

    tail = self.events

    for line in song.steps[playmode][difficulty]:
      fsplit = line.split()
      firstword = fsplit[0]
      if len(fsplit) > 1: nextword, rest = fsplit[1], fsplit[1:]
      else: nextword, rest = None, None

      if firstword == "end":
        if self.length < cur_time + toRealTime(cur_bpm, BEATS['halfn']):
          self.length = cur_time + toRealTime(cur_bpm, BEATS['halfn'])
          coloring_mod = 0
          break
      elif firstword == "atsec":
        cur_time = float(nextword)
        cur_time = float(nextword)
        tail.next = SongEvent(when=cur_time,bpm=cur_bpm,extra='ATSEC')
        tail = tail.next
      elif firstword == 'waits':
        cur_time += float(nextword)
        tail.next = SongEvent(when=cur_time,bpm=cur_bpm,extra='WAITS')
        tail = tail.next
      elif firstword == 'ready':
        tail.next = SongEvent(when=cur_time,bpm=cur_bpm,extra='READY')
        coloring_mod = 0
        tail = tail.next
      elif firstword in BEATS.keys():
        cando = True
        if ((little == 1 and (coloring_mod % 4 == 1 or
                              coloring_mod % 4 == 3)) or
            (little == 2 and (coloring_mod % 4 == 2)) or
            (little == 3 and (coloring_mod % 4 != 0))): cando = False

        # Don't create arrow events with no arrows
        arrowcount = 0
        for i in rest: arrowcount += int(i)

        if cando and arrowcount != 0:
          feetstep = [int(x, 16) for x in rest]

          # Check for jumps on this note
          arrowcount = 0
          for jump in range(len(feetstep)):
            if (feetstep[jump] & 8 and arrowcount != 0 and
                mainconfig['badknees'] and holding[jump] == 0):
              feetstep[jump] == 0
            arrowcount += 1

          # Check for holds
          for hold in range(len(feetstep)):
            didnothold = True
            if feetstep[hold] & 128 and holding[hold] == 0:
              holdtimes.insert(self.numholds, cur_time)
              holdlist.insert(self.numholds, hold)
              holding[hold] = self.numholds
              self.numholds += 1
              didnothold = False

            elif ((feetstep[hold] & 128 or feetstep[hold] & 8) and
                  holding[hold] and didnothold):
              releasetimes.insert(holding[hold], cur_time)
              releaselist.insert(holding[hold], hold)
              feetstep[hold] = 0 # broken stepfile, junk the event
              holding[hold] = 0

          tail.next = SongEvent(when = cur_time, bpm = cur_bpm,
                                feet = feetstep, extra = firstword,
                                color = coloring_mod % 4)

          for arrowadder in feetstep:
            if arrowadder & 8:
              self.totalarrows += 1

          tail = tail.next

        cur_time += toRealTime(cur_bpm, BEATS[firstword])

        coloring_mod += BEATS[firstword]

      elif firstword == "delay":
        cur_time += toRealTime(cur_bpm,
                               BEATS['qurtr'] * float(nextword))
        coloring_mod += 4 * float(nextword)
        tail.next = SongEvent(when = cur_time, bpm = cur_bpm, extra = "DELAY")
        tail = tail.next

      elif firstword == "chbpm":
        cur_bpm = float(nextword)
        tail.next = SongEvent(when = cur_time, bpm = cur_bpm,
                              extra = "CHBPM")
        tail = tail.next

      elif firstword == "tstop":
        tail.next = SongEvent(when = cu_time, bpm = cur_bpm,
                              extra = "TSTOP")
        cur_time += float(nextword) / 1000
        tail = tail.next

      elif firstword == "lyric" and lyrics:
        lyrics.addlyric(cur_time - 0.4, rest)
        tail.next = SongEvent(when = cur_time, bpm = cur_bpm,
                              extra = ("LYRIC", rest))
        tail = tail.next

      elif firstword == 'trans' and trans:
        trans.addlyric(cur_time - 0.4, rest)
        tail.next = SongEvent(when=cur_time,bpm=cur_bpm,extra=('TRANS',rest))
        tail = tail.next

    self.holdinfo = zip(holdlist, holdtimes, releasetimes)
    self.holdref = zip(holdlist, holdtimes)

  def play(self):
    self.curtime = 0.0
    self.tickstart = pygame.time.get_ticks()
    self.head = self.fhead = self.events
    self.playingbpm = self.bpm

  def get_time(self):
    self.curtime = float(pygame.mixer.music.get_pos())/1000.0
    return self.curtime

  def get_events(self):
    # FIXME These optimizations probably are useless
    events, nevents = [], []
    time = self.get_time()
    head = self.head
    fhead = self.fhead
    arrowtime = None
    bpm = None
    events_append, nevents_append = events.append, nevents.append
    while (head and head.when <= (time + 2 * toRealTime(head.bpm, 1))):
      events_append(head)
      head = head.next
    self.head = head

    if head and fhead:
      bpm = self.playingbpm
      arrowtime = 512.0 / bpm
      ntime = time + arrowtime * 1.5
      while fhead and fhead.when <= ntime:
        self.playingbpm = fhead.bpm
        nevents_append(fhead)
        fhead = fhead.next
      self.fhead = fhead
    return events, nevents, time, bpm

# The other half of the old 'Song' object, which is player-indep data

class SongData:
  def __init__(self, song):
    if song.info.has_key("bg"): self.background = song.info["bg"]
    else: self.background = os.path.join(image_path, "bg.png")

    if song.info.has_key("movie"): self.movie = song.info["movie"]
    else: self.movie = None

    self.song_file = song.info["file"]

    self.title, self.artist = song.info["song"], song.info["group"]

    if song.info.has_key("startat"): self.start = float(song.info["startat"])
    else: self.start = 0.0
    if song.info.has_key("endat"): self.end = float(song.info["endat"])
    else: self.end = None

    self.crapout = 0

    self.lyricdisplay = LyricDisp(400,
                                  colors.color[mainconfig['lyriccolor']])
    self.transdisplay = LyricDisp(428,
                                  colors.color[mainconfig['transcolor']])
    atsec = 0
    for lyr in song.lyrics:
      lsplit = lyr.split()
      if lsplit[0] == "atsec": atsec = float(lsplit[1])
      elif lsplit[0] == "lyric":
        self.lyricdisplay.addlyric(atsec - 0.4, lsplit[1:])
      elif lsplit[0] == "trans":
        self.transdisplay.addlyric(atsec - 0.4, lsplit[1:])

  def init(self):
    try: pygame.mixer.music.load(self.song_file)
    except pygame.error:
      print "Not a supported file type:", self.song_file
      self.crapout = 1
    if self.start > 0:
      print "Skipping %f seconds." % self.start
      
  def play(self):
    pygame.mixer.music.play(0, self.start)

  def kill(self):
    pygame.mixer.music.stop()

  def is_over(self):
    if not pygame.mixer.music.get_busy(): return True
    elif self.end and pygame.mixer.music.get_pos() > self.end * 1000:
      pygame.mixer.music.stop()
      return True
    else: return False
