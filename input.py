# Event handler design
# --------------------
# The event handler's job is to process the stuff coming from the
# system event handler (pygame.event probably), and turn the various
# inputs into values that matter, e.g. K_LEFT and a joystick left
# should generate E_LEFT1.

# Keep a hash of tuples of (eventtype, eventval), with the values
# being the event to return.

# In addition, we have to track some degree of local state, for hold
# arrows. This only matters for direction arrows, but do it for
# everything anyway.


import pygame
from constants import *

E_PASS,E_QUIT,E_LEFT1,E_RIGHT1,E_UP1,E_DOWN1,E_FULLSCREEN,E_START1,E_SCREENSHOT,E_HCENTER,E_VCENTER,E_PGUP,E_PGDN,E_LEFT2,E_RIGHT2,E_UP2,E_DOWN2,E_START2,E_SELECT = range(19)

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

EMSUSB2 = {
  15: E_LEFT1,
  13: E_RIGHT1,
  12: E_UP1,
  14: E_DOWN1,
  9: E_START1,
  1: E_PGUP,
  3: E_PGDN,
  31: E_LEFT2,
  29: E_RIGHT2,
  28: E_UP2,
  30: E_DOWN2,
  25: E_START2,
  8: E_SELECT
  }

class EventManager:
  def __init__(self, config, handler = pygame.event):
    self.handler = handler
    self.handler.set_blocked(range(NUMEVENTS))
    self.handler.set_allowed((KEYUP, KEYDOWN))
    self.states = {}
    self.events = {}
  
    mat = mat2 = emsusb2 = None
    try:
      totaljoy = pygame.joystick.get_count()
    except:
      totaljoy = 0
    print totaljoy, "joystick[s] found in total."
    for i in range(totaljoy):
      ddrmat = pygame.joystick.Joystick(i)
      ddrmat.init()
      if ddrmat.get_numbuttons() == 32 and (ddrmat.get_numaxes() == 11 or
                                            ddrmat.get_numaxes() == 8):
        emsusb2 = i
      elif (ddrmat.get_numbuttons() == config['mat_buttons'] and
            ddrmat.get_numaxes() == config['mat_axes']):
        if mat == None: mat = i
        else: mat2 = i
      ddrmat.quit()
    if emsusb2 != None:
      ddrmat = pygame.joystick.Joystick(emsusb2)
      ddrmat.init()
      print "EMSUSB2 adapter initialized: js", emsusb2
      self.handler.set_allowed((JOYBUTTONUP, JOYBUTTONDOWN))
      self.mergeEvents(EMSUSB2, "js" + str(emsusb2))
    elif mat != None:
      p1jconf = { config["joy_left"]: E_LEFT1,
                  config["joy_right"]: E_RIGHT1,
                  config["joy_up"]: E_UP1,
                  config["joy_down"]: E_DOWN1,
                  config["joy_start"]: E_START1
                 }
      jconf = { config["joy_select"]: E_SELECT,
                config["joy_pgup"]: E_PGUP,
                config["joy_pgdown"]: E_PGDN
                }

      ddrmat = pygame.joystick.Joystick(mat)
      ddrmat.init()
      self.mergeEvents(p1jconf, "js" + str(mat))
      print "DDR mat 1 initialized: js", mat
      self.handler.set_allowed((JOYBUTTONUP, JOYBUTTONDOWN))
      if mat2 != None:
        p2jconf = { config["joy_left"]: E_LEFT2,
                    config["joy_right"]: E_RIGHT2,
                    config["joy_up"]: E_UP2,
                    config["joy_down"]: E_DOWN2,
                    config["joy_start"]: E_START2
                    }
        ddrmat2 = pygame.joystick.Joystick(mat2)
        ddrmat2.init()
        self.mergeEvents(jconf, "js" + str(mat2))
        self.mergeEvents(p2jconf, "js" + str(mat2))
        print "DDR mat 2 initialized: js", mat2
    else:
      print "No DDR mats found. Not initializing joystick support."
    self.setupKeys(config)

  def setupKeys(self, config):
    keys = {}
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
    
    print "Retreiving event", t, v
    v = self.events.get((t, v))
    if v:
      if ev.type == JOYBUTTONUP or ev.type == KEYUP:
        self.states[v] -= 1
        v = -v
      elif ev.type == JOYBUTTONDOWN or ev.type == KEYDOWN:
        self.states[v] += 1
    else: v = E_PASS

    print "Event is : ", v
    print "States:"
    for s in self.states: print "state : ", s, " : value : ", self.states[s]
    return v
