# This module wraps pygame.mixer.music and pymad, using pymad for MP3s
# when it can (since SMPEG is a piece of shit).

from constants import mainconfig
import pygame, thread

# There has got to be a better way to do this, right? Someone? Python gurus?
state = { "busy": False,
          "mf": None,
          "killed": False,
          "lasttime": 0,
          "currenttime": 0 }

def load(fn):
  if mainconfig["usemad"] and fn[-3:].lower() == "mp3":
    try:
      import mad, ao # Make sure we have both available
      if state["mf"]: state["killed"] = True
      while state["mf"]: pass
      state["mf"] = mad.MadFile(fn)
    except ImportError:
      pygame.mixer.music.load(fn)
  else:
    pygame.mixer.music.load(fn)

def play_thread():
  import ao
  state["killed"] = False
  mf = state["mf"]
  dev = ao.AudioDevice('oss', bits = 16, rate = mf.samplerate())
  state["busy"] = True
  while not state["killed"]:
    state["lasttime"] = pygame.time.get_ticks()
    state["currenttime"] = state["mf"].current_time() - 400
    buffy = mf.read()
    if buffy is None: break
    dev.play(buffy, len(buffy))
  pygame.time.wait(500) # for the last buffered sound
  state["lasttime"] = 0
  state["mf"] = None
  dev = None
  state["busy"] = False

def play(loops, startat):
  while get_busy(): pass
  if state["mf"]: thread.start_new_thread(play_thread, ())
  else: pygame.mixer.music.play(loops, startat)

def get_busy():
  if state["mf"]: return state["busy"]
  else: return pygame.mixer.music.get_busy()

def get_pos():
  if state["mf"]:
    time = state["currenttime"]
    if state["lasttime"]: time += (pygame.time.get_ticks() - state["lasttime"])
    return time
  else: return pygame.mixer.music.get_pos()

def stop():
  if state["mf"]: state["killed"] = True
  else: pygame.mixer.music.stop()
  
def fadeout(time):
  if state["mf"]: stop()
  else: pygame.mixer.music.fadeout(time)

def set_volume(vol):
  if state["mf"]:
    if vol == 0: stop()
  else: pygame.mixer.music.set_volume(vol)
