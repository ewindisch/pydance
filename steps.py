from lyrics import Lyrics
from constants import *

import colors

BEATS = { 'x': 0.25, 't': 0.5, 'f': 2.0/3.0,
          's': 1.0, 'w': 4.0/3.0, 'e': 2.0,
          'q': 4.0, 'h': 8.0, 'o': 16.0 }

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
               lyrics = None): # FIXME - New lyrics system
    self.playmode = playmode
    self.difficulty = difficulty
    self.feet = song.difficulty[playmode][difficulty]
    self.length = 0.0
    self.offset = float(song.info["gap"] +
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
    self.lastbpmchangetime = []
    self.events = SongEvent(when = cur_time, bpm = cur_bpm,
                            extra = song.difficulty[playmode][difficulty])

    tail = self.events

    for words in song.steps[playmode][difficulty]:

#     if firstword == "atsec":
#       cur_time = float(nextword)
#       cur_time = float(nextword)
      if words[0] == 'W':
        cur_time += float(words[1])
      elif words[0] == 'R':
        tail.next = SongEvent(when=cur_time,bpm=cur_bpm,extra='READY')
        coloring_mod = 0
        tail = tail.next
      elif words[0] in BEATS.keys():
        cando = True
        if ((little == 1 and (coloring_mod % 4 == 1 or
                              coloring_mod % 4 == 3)) or
            (little == 2 and (coloring_mod % 4 == 2)) or
            (little == 3 and (coloring_mod % 4 != 0))): cando = False

        # Don't create arrow events with no arrows
        arrowcount = 0
        for i in words[1:]: arrowcount += int(i)

        if cando and arrowcount != 0:
          feetstep = words[1:]
          # Check for jumps on this note
          arrowcount = 0
          for jump in range(len(feetstep)):
            if (feetstep[jump] & 1 and arrowcount != 0 and
                mainconfig['badknees'] and holding[jump] == 0):
              feetstep[jump] == 0
            arrowcount += 1

          # Check for holds
          for hold in range(len(feetstep)):
            if feetstep[hold] & 2 and holding[hold] == 0:
              holdtimes.insert(self.numholds, cur_time)
              holdlist.insert(self.numholds, hold)
              releasetimes.append(None)
              releaselist.append(None)
              holding[hold] = self.numholds
              self.numholds += 1

            elif ((feetstep[hold] & 2 or feetstep[hold] & 1) and
                  holding[hold]):
              releasetimes[holding[hold] - 1] = cur_time
              releaselist[holding[hold] - 1] = hold
              feetstep[hold] = 0 # broken stepfile, junk the event
              holding[hold] = 0

          tail.next = SongEvent(when = cur_time, bpm = cur_bpm,
                                feet = feetstep, extra = words[0],
                                color = coloring_mod % 4)

          for arrowadder in feetstep:
            if arrowadder & 1:
              self.totalarrows += 1

          tail = tail.next

        cur_time += toRealTime(cur_bpm, BEATS[words[0]])

        coloring_mod += BEATS[words[0]]

      elif words[0] == "D":
        cur_time += toRealTime(cur_bpm, BEATS['q'] * words[1])
        coloring_mod += 4 * words[1]

      elif words[0] == "B":
        cur_bpm = words[1]
        self.lastbpmchangetime.append([cur_time, cur_bpm])

      elif words[0] == "S":
        cur_time += words[1]
        tail = tail.next

      elif words[0] == "L" and lyrics:
        lyrics.addlyric(cur_time - 0.4, words[2], words[1])

    self.length = cur_time + toRealTime(cur_bpm, BEATS['h'])

    self.holdinfo = zip(holdlist, holdtimes, releasetimes)
    self.holdref = zip(holdlist, holdtimes)

  def play(self):
    self.curtime = 0.0
    self.tickstart = pygame.time.get_ticks()
    self.head = self.fhead = self.events
    self.playingbpm = self.bpm

  def get_events(self):
    # FIXME These optimizations probably are useless
    events, nevents = [], []
    time = self.curtime = float(pygame.mixer.music.get_pos())/1000.0
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
    if song.info["background"]: self.background = song.info["background"]
    else: self.background = os.path.join(image_path, "bg.png")

    for key in ("movie", "filename", "title", "artist", "startat", "endat"):
      self.__dict__[key] = song.info[key]

    self.crapout = 0

    clrs = [colors.color[c] for c in mainconfig["lyriccolor"].split("/")]
    clrs.reverse()
    self.lyricdisplay = Lyrics(clrs)

    atsec = 0
    for lyr in song.lyrics:
      self.lyricdisplay.addlyric(*lyr)

  def init(self):
    try: pygame.mixer.music.load(self.filename)
    except pygame.error:
      print "Not a supported file type:", self.filename
      self.crapout = 1
    if self.startat > 0:
      print "Skipping %f seconds." % self.startat
      
  def play(self):
    pygame.mixer.music.play(0, self.startat)

  def kill(self):
    pygame.mixer.music.stop()

  def is_over(self):
    if not pygame.mixer.music.get_busy(): return True
    elif self.endat and pygame.mixer.music.get_pos() > self.endat * 1000:
      pygame.mixer.music.stop()
      return True
    else: return False
