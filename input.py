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
  K_r: E_SELECT,
  K_PAGEUP: E_PGUP,
  K_PAGEDOWN: E_PGDN,
  K_m: E_MARK
}

# 6 axis, 12 button joystick (BNS parallel adapter)
A6B12 = { 1: E_PGUP, 3: E_PGDN, 8: E_SELECT, 4: E_LEFT, 5: E_RIGHT,
          6: E_DOWN, 7: E_UP, 9: E_START }

# 16 buttons, 4 axis
# The EMSUSB2, one adapter, two joysticks - +16 to get p2, uses this too
A4B16 = { 0: E_MARK, 1: E_PGUP, 3: E_PGDN, 8: E_SELECT, 9: E_START,
          15: E_LEFT, 13: E_RIGHT, 12: E_UP, 14: E_DOWN }

class EventManager:
  def __init__(self, handler = pygame.event):
    self.handler = handler
    self.handler.set_blocked(range(NUMEVENTS))
    self.handler.set_allowed((KEYUP, KEYDOWN))
    self.states = {} # States of buttons
    # Tuples of events, key is tuple: (from, event)
    # Types are "kb" or "jsX" where X is a joystick number.
    self.events = {}

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
      elif ddrmat.get_numbuttons() == 12 and ddrmat.get_numaxes() == 6:
        if mat == None: mat = i
        elif mat2 == None: mat2 = i
      else:
        print "You have a joystick attached, but it doesn't seem to be a DDR mat."
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
        
    elif mat != None:
      ddrmat = pygame.joystick.Joystick(mat)
      ddrmat.init()
      data = {}
      if ddrmat.get_numbuttons() == 16:
        self.mergeEvents(A4B16, 0, "js" + str(mat))
      elif ddrmat.get_numbuttons() == 12:
        self.mergeEvents(A6B12, 0, "js" + str(mat))
      print "DDR mat 1 initialized: js", mat
      self.handler.set_allowed((JOYBUTTONUP, JOYBUTTONDOWN))
      if mat2 != None:
        ddrmat = pygame.joystick.Joystick(mat2)
        ddrmat.init()
        if ddrmat.get_numbuttons() == 16:
          self.mergeEvents(A4B16, 1, "js" + str(mat2))
        elif ddrmat.get_numbuttons() == 12:
          self.mergeEvents(A6B12, 1, "js" + str(mat2))
        print "DDR mat 2 initialized: js", mat2
    else:
      print "No DDR mats found. Not initializing joystick support."
    self.setupKeys()

  def setupKeys(self):
    keys = [{K_RETURN: E_START}, {K_2: E_START}]
    dirs = (E_UP, E_DOWN, E_LEFT, E_RIGHT)
  
    # Keymap settings. The 'r' varieties are just swapped.
    if mainconfig["keyboard"] == "qwerty":
      keys[0][K_i], keys[0][K_k], keys[0][K_j], keys[0][K_l] = dirs
      keys[1][K_UP], keys[1][K_DOWN], keys[1][K_LEFT], keys[1][K_RIGHT] = dirs
    elif mainconfig["keyboard"] == "rqwerty":
      keys[0][K_UP], keys[0][K_DOWN], keys[0][K_LEFT], keys[0][K_RIGHT] = dirs
      keys[1][K_i], keys[1][K_k], keys[1][K_j], keys[1][K_l] = dirs
    elif mainconfig["keyboard"] == "dvorak":
      keys[0][K_c], keys[0][K_t], keys[0][K_h], keys[0][K_n] = dirs
      keys[1][K_UP], keys[1][K_DOWN], keys[1][K_LEFT], keys[1][K_RIGHT] = dirs
    elif mainconfig["keyboard"] == "rdvorak":
      keys[0][K_UP], keys[0][K_DOWN], keys[0][K_LEFT], keys[0][K_RIGHT] = dirs
      keys[1][K_c], keys[1][K_t], keys[1][K_h], keys[1][K_n] = dirs
    else:
      print "Error! Unknown keyboard type", mainconfig["keyboard"]
      sys.exit(1)

    for i in range(len(keys)):
      self.mergeEvents(keys[i], i, "kb")
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

  # Poll the event handler and normalize the result.
  def poll(self):
    ev = self.handler.poll()
    t = ''
    v = 0
    if ev.type == QUIT: return E_QUIT
    elif ev.type == JOYBUTTONDOWN or ev.type == JOYBUTTONUP:
      t = "js" + str(ev.joy)
      v = ev.button
    elif ev.type == KEYDOWN or ev.type == KEYUP:
      t = "kb"
      v = ev.key
    else:
      return (0, E_PASS)
    
    v = self.events.get((t, v))
    if v != None:
      if ev.type == JOYBUTTONUP or ev.type == KEYUP:
        self.states[v] = min(self.states[v] - 1, 0)
        v = (v[0], -v[1])
      elif ev.type == JOYBUTTONDOWN or ev.type == KEYDOWN:
        self.states[v] += 1
    else:
      v = (0, E_PASS)

    return v
