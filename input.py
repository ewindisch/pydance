# Event handler design
# --------------------
# The event handler's job is to process the stuff coming from the
# system event handler (pygame.event probably), and turn the various
# inputs into values that matter, e.g. K_LEFT and a joystick left
# should generate E_LEFT1.

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
  K_RETURN: E_START1,
  K_2: E_START2
}

# 4 axis, 16 button joystick (common type)
A4B16 = { }
A4B16_1 = { }
A4B16_2 = { }

# 6 axis, 12 button joystick (BNS parallel adapter)
A6B12 = { 1: E_PGUP, 3: E_PGDN, 8: E_SELECT }
A6B12_1 = { 4: E_LEFT1, 5: E_RIGHT1, 6: E_DOWN1, 7: E_UP1, 9: E_START1 }
A6B12_2 = { 4: E_LEFT2, 5: E_RIGHT2, 6: E_DOWN2, 7: E_UP2, 9: E_START2 }

# EMSUSB2, one adapter, two joysticks
EMSUSB2 = {
  1: E_PGUP, 3: E_PGDN, 8: E_SELECT,
  17: E_PGUP, 20: E_PGDN, 24: E_SELECT,
  15: E_LEFT1, 13: E_RIGHT1, 12: E_UP1, 14: E_DOWN1, 9: E_START1,
  31: E_LEFT2, 29: E_RIGHT2, 28: E_UP2, 30: E_DOWN2, 25: E_START2
  }

class EventManager:
  def __init__(self, config, handler = pygame.event):
    self.handler = handler
    self.handler.set_blocked(range(NUMEVENTS))
    self.handler.set_allowed((KEYUP, KEYDOWN))
    self.states = {} # States of buttons
    # Tuples of events, key is tuple: (from, val), value is one of E_*.
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
      if ddrmat.get_numbuttons() == 32 and (ddrmat.get_numaxes() == 11 or
                                            ddrmat.get_numaxes() == 8):
        emsusb2 = i
      elif ddrmat.get_numbuttons() == 16 and ddrmat.get_numaxes() == 4:
        if mat == None: mat = i
        else: # A 4/16 should be P1 if available, overriding 6/12.
          mat2 = mat
          mat =i
      elif ddrmat.get_numbuttons() == 12 and ddrmat.get_numaxes() == 6:
        if mat == None: mat = i
        elif mat2 == None: mat2 = i
      ddrmat.quit()
    if emsusb2 != None: # EMSUSB2, if found, is the only device we'll use.
      ddrmat = pygame.joystick.Joystick(emsusb2)
      ddrmat.init()
      print "EMSUSB2 adapter initialized: js", emsusb2
      self.handler.set_allowed((JOYBUTTONUP, JOYBUTTONDOWN))
      self.mergeEvents(EMSUSB2, "js" + str(emsusb2))
    elif mat != None:
      ddrmat = pygame.joystick.Joystick(mat)
      ddrmat.init()
      data = {}
      if ddrmat.get_numbuttons() == 16:
        self.mergeEvents(A4B16, "js" + str(mat))
        self.mergeEvents(A4B16_1, "js" + str(mat))
      elif ddrmat.get_numbuttons() == 12:
        self.mergeEvents(A6B12, "js" + str(mat))
        self.mergeEvents(A6B12_1, "js" + str(mat))
      print "DDR mat 1 initialized: js", mat
      self.handler.set_allowed((JOYBUTTONUP, JOYBUTTONDOWN))
      if mat2 != None:
        ddrmat = pygame.joystick.Joystick(mat2)
        ddrmat.init()
        if ddrmat.get_numbuttons() == 16:
          self.mergeEvents(A4B16, "js" + str(mat2))
          self.mergeEvents(A4B16_2, "js" + str(mat2))
        elif ddrmat.get_numbuttons() == 12:
          self.mergeEvents(A6B12, "js" + str(mat2))
          self.mergeEvents(A6B12_2, "js" + str(mat2))
        print "DDR mat 2 initialized: js", mat2
    else:
      print "No DDR mats found. Not initializing joystick support."
    self.setupKeys(config)

  def setupKeys(self, config):
    keys = {}
    # Keymap settings. The 'r' varieties are just swapped.
    if config["keyboard"] == "qwerty":
      keys[K_i], keys[K_k], keys[K_j], keys[K_l] = E_UP1, E_DOWN1, E_LEFT1, E_RIGHT1
      keys[K_UP], keys[K_DOWN], keys[K_LEFT], keys[K_RIGHT] = E_UP2, E_DOWN2, E_LEFT2, E_RIGHT2
    elif config["keyboard"] == "rqwerty":
      keys[K_UP], keys[K_DOWN], keys[K_LEFT], keys[K_RIGHT] = E_UP1, E_DOWN1, E_LEFT1, E_RIGHT1
      keys[K_i], keys[K_k], keys[K_j], keys[K_l] = E_UP2, E_DOWN2, E_LEFT2, E_RIGHT2
    elif config["keyboard"] == "dvorak":
      keys[K_c], keys[K_t], keys[K_h], keys[K_n] = E_UP1, E_DOWN1, E_LEFT1, E_RIGHT1
      keys[K_UP], keys[K_DOWN], keys[K_LEFT], keys[K_RIGHT] = E_UP2, E_DOWN2, E_LEFT2, E_RIGHT2
    elif config["keyboard"] == "rdvorak":
      keys[K_UP], keys[K_DOWN], keys[K_LEFT], keys[K_RIGHT] = E_UP1, E_DOWN1, E_LEFT1, E_RIGHT1
      keys[K_c], keys[K_t], keys[K_h], keys[K_n] = E_UP2, E_DOWN2, E_LEFT2, E_RIGHT2
    else: print "Error! Unknown keyboard type", config["keyboard"]

    # Custom bindings for player keys.
    if config["p1_keys"]:
      ks = eval(config["p1_keys"])
      keys[ks[0]], keys[ks[1]], keys[ks[2]], keys[ks[3]] = E_UP1, E_DOWN1, E_LEFT1, E_RIGHT1
    if config["p2_keys"]:
      ks = eval(config["p2_keys"])
      keys[ks[0]], keys[ks[1]], keys[ks[2]], keys[ks[3]] = E_UP2, E_DOWN2, E_LEFT1, E_RIGHT1

    self.mergeEvents(keys, "kb")
    self.mergeEvents(KEYCONFIG, "kb")

  def mergeEvents(self, events, type):
    for key in events:
      print "adding event", type, key
      self.events[(type, key)] = events[key]
      if not self.states.has_key(events[key]):
        self.states[events[key]] = 0

  # Clear waiting events and reset key states.
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
      return
    
    v = self.events.get((t, v))
    if v:
      if ev.type == JOYBUTTONUP or ev.type == KEYUP:
        self.states[v] -= 1
        v = -v
      elif ev.type == JOYBUTTONDOWN or ev.type == KEYDOWN:
        self.states[v] += 1
    else: v = E_PASS

    return v
