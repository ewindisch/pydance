# These parse various file formats describing steps.
# Please read docs/dance-spec.txt

import colors, audio, games, stepfilters

from lyrics import Lyrics
from util import toRealTime
from constants import *

# FIXME: This can probably be replaced by something smaller, like a tuple.
class SongEvent(object):
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

class Steps(object):
  def __init__(self, song, difficulty, player, pid, lyrics, playmode):
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

    holdlist = []
    holdtimes = []
    holdbeats = []
    releaselist = []
    releasetimes = []
    releasebeats = []
    self.numholds = 1
    holding = [0] * len(games.GAMES[playmode].dirs)
    coloring_mod = 0
    cur_time = float(self.offset)
    last_event_was_freeze = False
    cur_beat = 0
    cur_bpm = self.bpm
    self.speed = player.speed

    # If this is too small, arrows don't appear fast enough. If it's
    # too large, many arrows queue up and pydance slows down.
    # 104 == (480 (screen height) - 64 (space on top)) / 4 (pixels per beat)
    self.nbeat_offset = 104.0 / player.speed
    self.lastbpmchangetime = []
    self.events = [SongEvent(when = cur_time, bpm = cur_bpm, beat = cur_beat,
                             extra = song.difficulty[playmode][difficulty])]

    self.event_idx = 0
    self.nevent_idx = 0

    if playmode in song.steps:
      song_steps = song.steps[playmode][difficulty]
      if playmode in games.COUPLE: song_steps = song_steps[pid]
      # Copy the steps so transformations don't affect both players.
      song_steps = [list(s) for s in song_steps]
    else:
      song_steps = stepfilters.generate_mode(song, difficulty, playmode, pid)

    song_steps = stepfilters.compress(song_steps)

    if player.transform:
      stepfilters.rotate(song_steps, player.transform, playmode)

    if player.size: stepfilters.size(song_steps, player.size)
    if player.jumps != 1: stepfilters.jumps(song_steps, player.jumps)
    if not player.holds: stepfilters.remove_holds(song_steps, player.holds)

    if not player.secret_kind: stepfilters.remove_secret(song_steps)

    for words in song_steps:

      if words[0] == 'W':
        cur_time += float(words[1])
        cur_beat += cur_bpm * float(words[1]) / 60
        last_event_was_freeze = False
      elif words[0] == 'R':
        self.ready = cur_time
        last_event_was_freeze = False
        coloring_mod = 0
      elif isinstance(words[0], float):
        # Don't create arrow events with no arrows
        arrowcount = 0
        for i in words[1:]: arrowcount += int(i)

        if arrowcount != 0:
          feetstep = words[1:]

          if last_event_was_freeze:
            time_to_add = last_event_was_freeze
            last_event_was_freeze = False
          else: time_to_add = cur_time

          # Check for holds
          for hold in range(len(feetstep)):
            if feetstep[hold] & 2 and holding[hold] == 0:
              holdtimes.insert(self.numholds, time_to_add)
              holdbeats.insert(self.numholds, cur_beat)
              holdlist.insert(self.numholds, hold)
              releasetimes.append(None)
              releasebeats.append(None)
              releaselist.append(None)
              holding[hold] = self.numholds
              self.numholds += 1

            elif (feetstep[hold] and holding[hold]):
              releasetimes[holding[hold] - 1] = time_to_add
              releasebeats[holding[hold] - 1] = cur_beat
              releaselist[holding[hold] - 1] = hold
              feetstep[hold] = 0
              holding[hold] = 0
              
          self.events.append(SongEvent(when = time_to_add, bpm = cur_bpm,
                                       feet = feetstep, extra = words[0],
                                       beat = cur_beat,
                                       color = coloring_mod % 4))

          for arrowadder in feetstep:
            if arrowadder & 1 and not arrowadder & 4:
              self.totalarrows += 1

        # Even if there are no steps in the event, we don't want to
        # propogate the freeze.
        else: last_event_was_freeze = False


        beat = words[0]

        cur_time += toRealTime(cur_bpm, beat)
        cur_beat += beat
        coloring_mod += beat

        if int(coloring_mod + 0.0001) > int(coloring_mod):
          coloring_mod = float(int(coloring_mod + 0.0001))
        if int(cur_beat + 0.0001) > int(cur_beat):
          cur_beat = float(int(cur_beat + 0.0001))

      elif words[0] == "D":
        last_event_was_freeze = False
        cur_time += toRealTime(cur_bpm, 4.0 * words[1])
        cur_beat += 4.0 * words[1]
        coloring_mod += 4 * words[1]

      elif words[0] == "B":
        cur_bpm = words[1]
        last_event_was_freeze = False
        self.lastbpmchangetime.append([cur_time, cur_bpm])

      elif words[0] == "S":
        # We can treat stops as a BPM change to zero with a wait.
        last_event_was_freeze = cur_time
        self.lastbpmchangetime.append([cur_time, 1e-127]) # This is zero
        cur_time += float(words[1])
        self.lastbpmchangetime.append([cur_time, cur_bpm])

      elif words[0] == "L" and lyrics:
        lyrics.addlyric(cur_time - 0.4, words[1], words[2])

    self.length = cur_time + toRealTime(cur_bpm, 8.0)

    self.holdinfo = zip(holdlist, holdtimes, releasetimes)
    self.holdref = zip(holdlist, holdtimes)
    self.holdbeats = zip(holdbeats, releasebeats)

    if self.ready == None:
      if len(self.events) > 1:
        self.ready = self.events[1].when - toRealTime(self.events[1].bpm, 16)
      else: self.ready = 0.0

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

class SongData(object):
  def __init__(self, song, config):
    if song.info["background"]: self.background = song.info["background"]
    else: self.background = os.path.join(image_path, "bg.png")

    for key in ("movie", "filename", "title", "artist", "startat", "endat"):
      self.__dict__[key] = song.info[key]

    self.soffset = song.info["gap"] * 1000

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
