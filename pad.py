# A basic 11 button dance pad abstraction

from constants import *
import pygame, os
import cPickle as pickle
from pygame.locals import *

(PASS, QUIT, UP, UPLEFT, LEFT, DOWNLEFT, DOWN, DOWNRIGHT,
 RIGHT, UPRIGHT, CENTER, START, SELECT) = range(13)

NAMES = ["", "quit", "up", "up-left", "left", "down-left", "down",
         "down-right", "right", "up-right", "center", "start", "select"]

# Events for the transition
# FIXME: REMOVE THESE
FULLSCREEN = -100
SORT = SCREENSHOT = -200
CLEAR = -300
MARK = UPLEFT
UNMARK = DOWNLEFT
PGUP = UPRIGHT
PGDN = DOWNRIGHT

KEYS = {
  K_ESCAPE: QUIT,
  }

KEY1 = {
  K_KP7: UPLEFT,
  K_KP8: UP,
  K_KP9: UPRIGHT,
  K_KP4: LEFT,
  K_KP5: CENTER,
  K_KP6: RIGHT,
  K_KP1: DOWNLEFT,
  K_KP2: DOWN,
  K_KP3: DOWNRIGHT,
  K_RETURN: START,
  K_KP_ENTER: START,
  K_KP0: SELECT,
}

KEY2 = {
  K_u: UPLEFT,
  K_i: UP,
  K_o: UPRIGHT,
  K_j: LEFT,
  K_k: CENTER,
  K_l: RIGHT,
  K_m: DOWNLEFT,
  K_COMMA: DOWN,
  K_PERIOD: DOWNRIGHT,
  K_7: SELECT,
  K_9: START,
  }

# 16 buttons, 4 axis
# The EMSUSB2 is one adapter, two joysticks - +16 to get p2, uses this
# too. Apparently, there are two possible start buttons, 9 and 11?

# L1: 4, L2: 6, R1: 7, R2: 5
# Left: 15, Up: 12, Right: 13, Down: 14
# Square: 3, Tri: 0, Circle: 1, X: 2
# Select: 8, start: 9
# Left analog: 10, Right analog: 11

A4B16 = { 0: DOWNLEFT, 1: UPRIGHT, 2: UPLEFT, 3: DOWNRIGHT, 5: CENTER,
          8: SELECT, 9: START, 11: START, 12: UP, 13: RIGHT, 14: DOWN,
          15: LEFT }

# Buy n Shop parallel adapter
A6B12 = { 1: UPRIGHT, 3: UPLEFT, 8: SELECT, 4: LEFT, 5: RIGHT,
          6: DOWN, 7: UP, 9: START }

# Gravis Gamepad Pro USB - Uses axes for directions.
# 0: Square, 1: X, 2: O, 3: Triangle
# 4: L1, 5: R1, 6: L2, 7: R2
# 8: Select, 9: Start
A2B10 = { 0: LEFT, 1: DOWN, 2: RIGHT, 3: UP, 5: UPRIGHT, 7: DOWNRIGHT,
          8: SELECT, 9: START }
  
# This is some sort of natively USB mat
A2B8 = { 4: UP, 6: DOWN,  5: LEFT, 7: RIGHT, 2: START,
         3: DOWNLEFT, 0: UPRIGHT, 1: DOWNRIGHT }

# X-Box controller with X-Box Linux
A14B10 = { 4: UP, 0: DOWN, 3: LEFT, 1: RIGHT,  6: START, 9: QUIT }

MATS = { (6, 12): A6B12, (14, 10): A14B10, (2, 10): A2B10, (2, 8): A2B8 }

class Pad(object):

  (PASS, QUIT, UP, UPLEFT, LEFT, DOWNLEFT, DOWN, DOWNRIGHT,
   RIGHT, UPRIGHT, CENTER, START, SELECT) = range(13)

  # Events for the transition
  # FIXME: REMOVE THESE
  FULLSCREEN = -100
  SORT = SCREENSHOT = -200
  CLEAR = -300000000000
  MARK = UPLEFT
  UNMARK = DOWNLEFT
  PGUP = UPRIGHT
  PGDN = DOWNRIGHT

  def __init__(self, handler = pygame.event):
    self.handler = handler
    self.handler.set_blocked(range(NUMEVENTS))
    self.handler.set_allowed((KEYUP, KEYDOWN, JOYBUTTONUP, JOYBUTTONDOWN))

    self.joysticks = []

    self.states = {}
    self.events = {}

    mat = mat2 = emsusb2 = None

    try: totaljoy = pygame.joystick.get_count()
    except: totaljoy = 0

    print totaljoy, "joystick(s) found."

    # Initialize all the joysticks, print diagnostics.
    for i in range(totaljoy):
      m = pygame.joystick.Joystick(i)
      m.init()
      args = (i, m.get_numaxes(), m.get_numbuttons())
      print "Joystick %d initialized: %d axes, %d buttons." % args

      if args[2] == 32: emsusb2 = i
      elif mat == None and (args[1], args[2]) in MATS: mat = i
      elif mat2 == None and (args[1], args[2]) in MATS: mat2 = i

    self.merge_events(-1, -1, KEYS)
    self.merge_events(0, -1, KEY1)
    self.merge_events(1, -1, KEY2)

    loaded_input = False
    if os.path.exists(os.path.join(rc_path, "input.cfg")):
      try:
        fn = os.path.join(rc_path, "input.cfg")
        self.events = pickle.load(file(fn, "r"))
        for ev in self.events.values(): self.states[ev] = False
        loaded_input = True
      except:
        print "E: Unable to load input configuration file."

    if loaded_input:
      print "Loaded input configuration."
    elif emsusb2 != None:
      self.merge_events(0, emsusb2, A4B16) 
      self.merge_events(1, emsusb2, dict([(k + 16, v) for (k, v) in A4B16.items()]))
      print "EMSUSB2 found. Using preset EMSUSB2 config."
    elif mat != None:
      joy = pygame.joystick.Joystick(mat)
      but, axes = joy.get_numaxes(), joy.get_numbuttons()
      print "Initializing player 1 using js%d." % mat
      self.merge_events(0, mat, MAT[(but, axes)])

      if mat2:
        joy = pygame.joystick.Joystick(mat2)
        but, axes = joy.get_numaxes(), joy.get_numbuttons()
        print "Initializing player 2 using js%d." % mat2
        self.merge_events(1, mat2, MAT[(but, axes)])
    elif totaljoy > 0:
      print "No known joysticks found! If you want to use yours,"
      print "you'll have to map its button manually once to use it."

  def add_event(self, device, key, pid, event):
    self.events[(device, key)] = (pid, event)
    self.states[(pid, event)] = False

  def merge_events(self, pid, device, events):
    for key, event in events.items():
      self.add_event(device, key, pid, event)

  def device_key_for(self, keyboard, pid, event):
    for (device, key), (p, e) in self.events.items():
      if p == pid and e == event:
        if keyboard and device == -1: return pygame.key.name(key)
        elif not keyboard and device != -1: return "js%d:%d" % (device, key)
    return "n/a"

  def delete_events(self, pid):
    for k, v in self.events.items():
      if v[0] == pid: del(self.events[k])
      self.states[v] == False

  # Poll the event handler and normalize the result. If we don't know
  # about the event but the device is the keyboard, return (-2, key).
  # Otherwise, return pass.
  def poll(self):
    ev = self.handler.poll()
    t = ''
    v = 0
    if ev.type == JOYBUTTONDOWN or ev.type == JOYBUTTONUP:
      t, v = ev.joy, ev.button
    elif ev.type == KEYDOWN or ev.type == KEYUP:
      t, v = -1, ev.key
    else:
      return (-2, PASS)

    if ev.type == KEYDOWN or ev.type == KEYUP: default = (-2, ev.key)
    else: default = (-2, PASS)

    ret = self.events.get((t, v), default)

    if ev.type == JOYBUTTONUP or ev.type == KEYUP:
      self.states[ret] = False
      ret = (ret[0], -ret[1])
    elif ev.type == JOYBUTTONDOWN or ev.type == KEYDOWN:
      self.states[ret] = True

    return ret

  def wait(self, delay = 20):
    ev = (-1, PASS)
    while ev[1] == PASS:
      ev = self.poll()
      pygame.time.wait(delay)
    return ev

  def empty(self):
    ev = (0, E_QUIT)
    while ev[1] != E_PASS: ev = self.poll()

  def write(self, fn):
    pickle.dump(self.events, file(fn, "w"))

  def set_repeat(*args): pass

pad = Pad()

class PadConfig(object):

  bg = pygame.image.load(os.path.join(image_path, "bg.png"))

  xys = {UP: [160, 100],
         UPLEFT: [100, 100],
         LEFT: [100, 250],
         DOWNLEFT: [100, 400],
         DOWN: [160, 400],
         DOWNRIGHT: [220, 400],
         RIGHT: [220, 250],
         UPRIGHT: [220, 100],
         CENTER: [160, 250],
         SELECT: [106, 25],
         START: [212, 25]
         }

  directions = range(2, 13)

  def __init__(self, screen):
    self.screen = screen

    ev = pygame.event.poll()
    while ev.type != KEYDOWN or ev.key != K_ESCAPE:
      self.render()
      ev = pygame.event.poll()
      pygame.display.update()
      pygame.time.delay(10)

  def render(self):
    self.screen.blit(PadConfig.bg, [0, 0])
    for i in range(2):
      for d in PadConfig.directions:
        x, y = PadConfig.xys[d]

        t_name = FONTS[16].render(NAMES[d], 1, [0, 0, 0])
        r_name = t_name.get_rect()
        r_name.center = (x + 320 * i, y)

        text = pad.device_key_for(True, i, d)
        t_key = FONTS[16].render(text, 1, [0, 0, 0])
        r_key = t_key.get_rect()
        r_key.center = (x + 320 * i, y + 16)

        text = pad.device_key_for(False, i ,d)
        t_but = FONTS[16].render(text, 1, [0, 0, 0])
        r_but = t_but.get_rect()
        r_but.center = (x + 320 * i, y + 32)

        self.screen.blit(t_name, r_name)
        self.screen.blit(t_key, r_key)
        self.screen.blit(t_but, r_but)
