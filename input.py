# Event handler design
# --------------------
# The event handler's job is to process the stuff coming from the
# system event handler (pygame.event probably), and turn the various
# inputs into values that matter, e.g. K_LEFT and a joystick left
# should generate (0, E_LEFT). Events are stored as a tuple of
# (inputtype, value) and returned as (playerno, event).

# In addition, we have to track some degree of local state, for hold
# arrows. This only matters for direction arrows, but do it for
# everything anyway.

import pygame
from constants import *

# Basic keyboard configuration
KEYCONFIG = {
  K_ESCAPE: E_QUIT,
  K_f: E_FULLSCREEN,
  K_s: E_SCREENSHOT,
  K_PAGEUP: E_PGUP,
  K_PAGEDOWN: E_PGDN,
  K_BACKSPACE: E_UNMARK,
  K_TAB: E_SELECT,
  K_DELETE: E_CLEAR,
  K_RETURN: E_START,
  K_UP: E_UP,
  K_DOWN: E_DOWN,
  K_LEFT: E_LEFT,
  K_RIGHT: E_RIGHT,
  }

NUM_KEYS = {
  K_KP7: E_UPLEFT,
  K_KP8: E_UP,
  K_KP9: E_UPRIGHT,
  K_KP4: E_LEFT,
  K_KP5: E_CENTER,
  K_KP6: E_RIGHT,
  K_KP1: E_DOWNLEFT,
  K_KP2: E_DOWN,
  K_KP3: E_DOWNRIGHT,
  K_RETURN: E_START,
  K_KP_ENTER: E_START,
  K_KP0: E_SELECT,
  }

QWERTY_KEYS = {
  K_u: E_UPLEFT,
  K_i: E_UP,
  K_o: E_UPRIGHT,
  K_j: E_LEFT,
  K_k: E_CENTER,
  K_l: E_RIGHT,
  K_m: E_DOWNLEFT,
  K_COMMA: E_DOWN,
  K_PERIOD: E_DOWNRIGHT,
  K_7: E_SELECT,
  K_9: E_START,
  }

DVORAK_KEYS = {
  K_g: E_UPLEFT,
  K_c: E_UP,
  K_r: E_UPRIGHT,
  K_h: E_LEFT,
  K_t: E_CENTER,
  K_n: E_RIGHT,
  K_m: E_DOWNLEFT,
  K_w: E_DOWN,
  K_v: E_DOWNRIGHT,
  K_7: E_SELECT,
  K_9: E_START,
  }

# 16 buttons, 4 axis
# The EMSUSB2, one adapter, two joysticks - +16 to get p2, uses this too
# Apparently, there are two possible start buttons, 9 and 11?

# L1: 4, L2: 6, R1: 7, R2: 5
# Left: 15, Up: 12, Right: 13, Down: 14
# Square: 3, Tri: 0, Circle: 1, X: 2
# Select: 8, start: 9
# Left analog: 10, Right analog: 11

A4B16 = { 0: E_MARK, 1: E_PGUP, 2: E_UNMARK, 3: E_PGDN, 8: E_SELECT, 9:
          E_START, 15: E_LEFT, 13: E_RIGHT, 12: E_UP, 14: E_DOWN,
          11: E_START, 5: E_CENTER }


# 6 axis, 12 button joystick (BNS parallel adapter)
A6B12 = { 1: E_PGUP, 3: E_PGDN, 8: E_SELECT, 4: E_LEFT, 5: E_RIGHT,
          6: E_DOWN, 7: E_UP, 9: E_START }

# Gravis Gamepad Pro USB
# 0: Square, 1: X, 2: O, 3: Triangle
# 4: L1, 5: R1, 6: L2, 7: R2
# 8: Select, 9: Start
A2B10 = { 0: E_LEFT, 1: E_DOWN, 2: E_RIGHT, 3: E_UP,
         5: E_PGUP, 7: E_PGDN, 8: E_SELECT, 9: E_START}
  
# This is some sort of natively USB mat, I guess...
# FIXME: I don't think it works.
A2B8 = { E_UP: 4, E_DOWN: 6, E_LEFT: 5, E_RIGHT: 7,
         E_START: 2, E_MARK: 3, E_PGUP: 0, E_PGDN: 1 }

# X-Box controller with X-Box Linux
A14B10 = { E_UP: 4, E_DOWN: 0, E_LEFT: 3, E_RIGHT: 1, E_START: 6,
           E_QUIT: 9, }

MATS = { (6, 12): A6B12,
         (14, 10): A14B10,
         (2, 10): A2B10,
         (2, 8): A2B8 }

class EventManager(object):
  def __init__(self, handler = pygame.event):
    self.handler = handler
    self.handler.set_blocked(range(NUMEVENTS))
    self.handler.set_allowed((KEYUP, KEYDOWN, ACTIVEEVENT, VIDEOEXPOSE))
    self.states = {} # States of buttons
    # Tuples of events, key is tuple: (from, event)
    # Types are "kb" or "jsX" where X is a joystick number.
    self.events = {}
    self.set_repeat()

    # These store the joystick numbers of the device
    mat = mat2 = emsusb2 = None
    try: totaljoy = pygame.joystick.get_count()
    except: totaljoy = 0
    print totaljoy, "joystick[s] found in total."
    for i in range(totaljoy):
      ddrmat = pygame.joystick.Joystick(i)
      ddrmat.init()
      if ddrmat.get_numbuttons() == 32:
        emsusb2 = i
      elif ddrmat.get_numbuttons() == 16 and ddrmat.get_numaxes() == 4:
        if mat == None: mat = i
        else: # A 4/16 should be P1 if available, overriding 6/12.
          mat2 = mat
          mat = i
      elif MATS.get((ddrmat.get_numaxes(), ddrmat.get_numbuttons())):
        if mat == None: mat = i
        elif mat2 == None: mat2 = i
      else:
        print "You have a joystick attached, but it doesn't seem to be a mat."
        print "It has", ddrmat.get_numbuttons(), "buttons and", ddrmat.get_numaxes(), "axes."
      ddrmat.quit()
    if emsusb2 != None: # EMSUSB2, if found, is the only device we'll use.
      ddrmat = pygame.joystick.Joystick(emsusb2)
      ddrmat.init()
      print "EMSUSB2 adapter initialized: js", emsusb2
      self.handler.set_allowed((JOYBUTTONUP, JOYBUTTONDOWN))

      emsp2 = {} # Player two's keys on the EMSUSB
      for key in A4B16: emsp2[key + 16] = A4B16[key]

      self.mergeEvents(A4B16, 0, "js" + str(emsusb2))
      self.mergeEvents(emsp2, 1, "js" + str(emsusb2))
    # FIXME We can clean this up a lot
    elif mat != None:
      ddrmat = pygame.joystick.Joystick(mat)
      ddrmat.init()
      data = {}
      if ddrmat.get_numbuttons() == 16:
        self.mergeEvents(A4B16, 0, "js" + str(mat))
      elif MATS.get(ddrmat.get_numaxes(), ddrmat.get_numbuttons()):
        self.mergeEvents(MATS[(ddrmat.get_numaxes(), ddrmat.get_numbuttons())],
                         0, "js" + str(mat))
      print "Mat 1 initialized: js", mat
      self.handler.set_allowed((JOYBUTTONUP, JOYBUTTONDOWN))
      if mat2 != None:
        ddrmat = pygame.joystick.Joystick(mat2)
        ddrmat.init()
        if ddrmat.get_numbuttons() == 16:
          self.mergeEvents(A4B16, 1, "js" + str(mat2))
        elif MATS.get(ddrmat.get_numaxes(), ddrmat.get_numbuttons()):
          self.mergeEvents(MATS[(ddrmat.get_numaxes(),
                                 ddrmat.get_numbuttons())], 0, "js" + str(mat))
        print "Mat 2 initialized: js", mat2
    else:
      print "No mats found. Not initializing joystick support."
    self.setupKeys()

  def setupKeys(self):
    dirs = (E_UP, E_DOWN, E_LEFT, E_RIGHT)
  
    # Keymap settings. The 'r' varieties are just swapped.
    if mainconfig["keyboard"] == "qwerty": keys = [QWERTY_KEYS, NUM_KEYS]
    elif mainconfig["keyboard"] == "rqwerty": keys = [NUM_KEYS, QWERTY_KEYS]
    elif mainconfig["keyboard"] == "dvorak": keys = [DVORAK_KEYS, NUM_KEYS]
    elif mainconfig["keyboard"] == "rdvorak": keys = [NUM_KEYS, DVORAK_KEYS]
    else:
      print "Error! Unknown keyboard type", mainconfig["keyboard"]
      sys.exit(1)

    keys[1][K_KP_PLUS] = E_START

    for i in range(len(keys)): self.mergeEvents(keys[i], i, "kb")
    self.mergeEvents(KEYCONFIG, 0, "kb")

  def mergeEvents(self, events, player, type):
    for key in events:
      self.events[(type, key)] = (player, events[key])
      if not self.states.has_key((player, events[key])):
        self.states[(player, events[key])] = 0

  # Clear waiting events and reset key states.
  # This could be bad, so don't call it.
  def clear(self):
    self.handler.clear()
    for key in self.states: self.states[key] = 0

  def set_repeat(self, *args):
    if len(args) == 0:
      self.repeat = False
      self.rate = False
      self.last_press = (None, None)
      self.last_repeat = 0
      pygame.key.set_repeat()
    elif len(args) == 2:
      self.repeat = True
      self.rate = args
      self.last_press = ((0, E_PASS), 0)
      self.last_repeat = 0
      pygame.key.set_repeat(*args)

  # Poll the event handler and normalize the result.
  def poll(self):
    ev = self.handler.poll()
    t = ''
    v = 0
    if ev.type == QUIT: return (0, E_QUIT)
    elif ev.type == JOYBUTTONDOWN or ev.type == JOYBUTTONUP:
      t = "js" + str(ev.joy)
      v = ev.button
    elif ev.type == KEYDOWN or ev.type == KEYUP:
      t = "kb"
      v = ev.key
    elif (self.repeat and self.last_press[0][1] and
          self.last_press[1] + self.rate[0] < pygame.time.get_ticks() and
          self.last_repeat + self.rate[1] < pygame.time.get_ticks() and
          self.states[self.last_press[0]] == True):
      self.last_repeat = pygame.time.get_ticks()
      return self.last_press[0]      
    else:
      return (0, E_PASS)
    
    v = self.events.get((t, v), (0, E_PASS))
    if ev.type == JOYBUTTONUP or ev.type == KEYUP:
      self.states[v] = False
      v = (v[0], -v[1])
    elif ev.type == JOYBUTTONDOWN or ev.type == KEYDOWN:
      self.states[v] = True
      self.last_press = (v, pygame.time.get_ticks())

    return v

  def wait(self, delay = 10):
    ev = (0, E_PASS)
    while ev[1] == E_PASS:
      ev = self.poll()
      pygame.time.wait(delay)
    return ev

  def empty(self):
    ev = (0, E_QUIT)
    while ev[1] != E_PASS: ev = self.poll()
