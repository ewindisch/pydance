# These parse various file formats describing steps.
# Please read docs/fileparsers.txt and docs/dance-spec.txt

import colors, audio, random, copy

from lyrics import Lyrics
from util import toRealTime
from constants import *

BEATS = { 'x': 0.25, 't': 0.5, 'u': 1.0/3.0, 'f': 2.0/3.0,
          's': 1.0, 'w': 4.0/3.0, 'e': 2.0,
          'q': 4.0, 'h': 8.0, 'o': 16.0, 'n': 1/12.0 }

# 0 - Normal
# 1 - Mirror
# 2 - Left
# 3 - Right
# -1 - Shuffle (calculated elsewhere)
STEP_MAPPINGS = {
  "SINGLE": [[0, 1, 2, 3], [3, 2, 1, 0], [1, 3, 0, 2], [2, 0, 3, 1]],
  "COUPLE": [[0, 1, 2, 3], [3, 2, 1, 0], [1, 3, 0, 2], [2, 0, 3, 1]],
  }

# FIXME: This can probably be replaced by something smaller, like a tuple.

class SongEvent:
  def __init__ (self, bpm, when=0.0, beat = 0, feet=None, next=None,
                extra=None, color=None):
    self.bpm  = bpm
    self.when = when
    self.feet = feet
    self.extra = extra
    self.color = color
    self.beat = beat

  def __repr__(self):
    rest = []
    if self.feet: rest.append('feet=%r'%self.feet)
    if self.extra: rest.append('extra=%r'%self.extra)
    if self.extra: rest.append('color=%r'%self.color)
    return '<SongEvent when=%r bpm=%r %s>' % (self.when,self.bpm,
                                                ' '.join(rest))

# Step objects, made from SongItem objects

COUPLE_MODES = ["COUPLE"]

class Steps:
  def __init__(self, song, difficulty, player, lyrics, playmode):
    self.playmode = playmode
    self.difficulty = difficulty
    self.feet = song.difficulty[playmode][difficulty]
    self.length = 0.0
    self.offset = -(song.info["gap"] + mainconfig['masteroffset']) / 1000.0
    self.soffset = self.offset * 1000
    self.bpm = song.info["bpm"]

    if mainconfig['onboardaudio']:
      self.offset = int(self.offset * 48000.0/44128.0)
      self.bpm = self.bpm * 48000.0/44128.0

    self.lastbpmchangetime = []
    self.totalarrows = 0
    self.ready = None

    if player.arrows == -1:
      self.mapping = copy.copy(STEP_MAPPINGS[playmode][0])
      random.shuffle(self.mapping)
    else: self.mapping = STEP_MAPPINGS[playmode][player.arrows]

    holdlist = []
    holdtimes = []
    releaselist = []
    releasetimes = []
    self.numholds = 1
    holding = [0, 0, 0, 0]
    little = player.little
    coloring_mod = 0
    cur_time = float(self.offset)
    cur_beat = 0
    cur_bpm = self.bpm
    self.speed = player.speed
    # If too small, arrows don't appear fast enough
    if player.accel: self.nbeat_offset = 104 / player.speed
    else:  self.nbeat_offset = 64 / player.speed
    self.lastbpmchangetime = []
    self.events = [SongEvent(when = cur_time, bpm = cur_bpm, beat = cur_beat,
                             extra = song.difficulty[playmode][difficulty])]

    self.event_idx = 0
    self.nevent_idx = 0

    song_steps = song.steps[playmode][difficulty]
    if playmode in COUPLE_MODES: song_steps = song_steps[player.pid]

    for words in song_steps:

      if words[0] == 'W':
        cur_time += float(words[1])
        cur_beat += cur_bpm * float(words[1]) / 60
      elif words[0] == 'R':
        self.ready = cur_time
        coloring_mod = 0
      elif words[0] in BEATS or isinstance(words[0], int):
        
        cando = True # FIXME: Do little correctly for 24th etc notes
        if ((little == 1 and (coloring_mod % 4 == 1 or
                              coloring_mod % 4 == 3)) or
            (little == 2 and (coloring_mod % 4 == 2)) or
            (little == 3 and (coloring_mod % 4 != 0))): cando = False

        # Don't create arrow events with no arrows
        arrowcount = 0
        for i in words[1:]: arrowcount += int(i)

        if cando and arrowcount != 0:
          origsteps = words[1:]
          feetstep = copy.copy(origsteps)
          for i in range(len(origsteps)):
            feetstep[self.mapping[i]] = origsteps[i]
          # Check for jumps on this note
          arrowcount = 0
          for jump in range(len(feetstep)):
            if (feetstep[jump] & 1):
              if (arrowcount != 0 and not player.jumps and
                  holding[jump] == 0):
                feetstep[jump] = 0
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

          self.events.append(SongEvent(when = cur_time, bpm = cur_bpm,
                                       feet = feetstep, extra = words[0],
                                       beat = cur_beat,
                                       color = coloring_mod % 4))

          for arrowadder in feetstep:
            if arrowadder & 1:
              self.totalarrows += 1

        if words[0] in BEATS: beat = BEATS[words[0]]
        else: beat = 16.0 / words[0]

        cur_time += toRealTime(cur_bpm, beat)
        cur_beat += beat
        coloring_mod += beat

        if int(coloring_mod + 0.0001) > int(coloring_mod):
          coloring_mod = float(int(coloring_mod + 0.0001))
        if int(cur_beat + 0.0001) > int(cur_beat):
          cur_beat = float(int(cur_beat + 0.0001))

      elif words[0] == "D":
        cur_time += toRealTime(cur_bpm, BEATS['q'] * words[1])
        cur_beat += BEATS['q'] * words[1]
        coloring_mod += 4 * words[1]

      elif words[0] == "B":
        cur_bpm = words[1]
        self.lastbpmchangetime.append([cur_time, cur_bpm])

      elif words[0] == "S":
        # We can treat stops as a BPM change to zero with a wait.
        self.lastbpmchangetime.append([cur_time, 1e-127]) # This is zero
        cur_time += float(words[1])
        self.lastbpmchangetime.append([cur_time, cur_bpm])

      elif words[0] == "L" and lyrics:
        lyrics.addlyric(cur_time - 0.4, words[1], words[2])

    self.length = cur_time + toRealTime(cur_bpm, BEATS['o'])

    self.holdinfo = zip(holdlist, holdtimes, releasetimes)
    self.holdref = zip(holdlist, holdtimes)

    if self.ready == None:
      self.ready = self.events[1].when - toRealTime(self.events[1].bpm, 16)

  def play(self):
    self.curtime = 0.0
    self.event_idx = self.nevent_idx = 0
    self.playingbpm = self.bpm

  def get_events(self):
    events, nevents = [], []
    idx = self.event_idx
    nidx = self.nevent_idx
    time = self.curtime = float(audio.get_pos())/1000.0
    while (idx < len(self.events) and
           self.events[idx].when <= time + 2 * toRealTime(self.events[idx].bpm, 1)):
      events.append(self.events[idx])
      idx += 1
    bpm = self.playingbpm
    self.event_idx = idx

    if idx < len(self.events) and nidx < len(self.events):
      nbeat = self.events[idx].beat + self.nbeat_offset
      while (nidx < len(self.events) and self.events[nidx].beat <= nbeat):
        self.playingbpm = self.events[nidx].bpm
        nevents.append(self.events[nidx])
        nidx += 1
      self.nevent_idx = nidx
    return events, nevents, time, bpm

# Player-indep data generated from SongItem.

class SongData:
  def __init__(self, song, config):
    if song.info["background"]: self.background = song.info["background"]
    else: self.background = os.path.join(image_path, "bg.png")

    for key in ("movie", "filename", "title", "artist", "startat", "endat"):
      self.__dict__[key] = song.info[key]

    self.crapout = 0

    self.__dict__.update(config)

    clrs = [colors.color[c] for c in mainconfig["lyriccolor"].split("/")]
    clrs.reverse()
    self.lyricdisplay = Lyrics(clrs)

    atsec = 0
    for lyr in song.lyrics:
      self.lyricdisplay.addlyric(*lyr)

  def init(self):
    try: audio.load(self.filename)
    except:
      print "Not a supported file type:", self.filename
      self.crapout = 1
    if self.startat > 0:
      print "Skipping %f seconds." % self.startat

  def play(self):
    audio.play(0, self.startat)

  def kill(self):
    audio.stop()

  def is_over(self):
    if not audio.get_busy(): return True
    elif self.endat and audio.get_pos() > self.endat * 1000:
      audio.stop()
      return True
    else: return False
