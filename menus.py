import pygame
from constants import *
from fontfx import TextZoomer

DARK_GRAY = (244, 244, 244)
BUTTON_SIZE = (192, 40)

# Default button style - gray gradient with a light outline
button_bg = pygame.surface.Surface(BUTTON_SIZE)
for i in range(192):
  pygame.draw.line(button_bg, (192-i, 192-i, 192-i), (i, 0), (i, 47))
  pygame.draw.line(button_bg, (i, i, i), (i, 0), (i, 1))
  pygame.draw.line(button_bg, (i, i, i), (i, 46), (i, 47))
for i in range(2):
  pygame.draw.line(button_bg, (192, 192, 192), (190+i, 0), (190+i, 47))
  pygame.draw.line(button_bg, (0, 0, 0), (i, 0), (i, 47))

# Commonly used fonts
pygame.font.init()
font32 = pygame.font.Font(None, 32)
font26 = pygame.font.Font(None, 26)
font20 = pygame.font.Font(None, 20)

class MenuItem:

  def __init__(self, text, callbacks, args):
    # Dict of callbacks by keycodes, also "initial", "select", "unselect"

    # This looks something like:
    # MenuItem({ 'initial': do_setup, E_START1: do_change,
    #            E_START2: do_change }, (configdata, mystrings))
    # When the button is pressed, do_change(configdata, mystrings) will be
    # called.
    self.callbacks = callbacks
    self.args = args
    self.bg = button_bg
    self.rgb = DARK_GRAY
    self.subtext = None
    self.text = text
    self.render()
    self.activate("initial")

  # Call an appropriate callback function, for the event given.
  # The function can return up to three arguments - the new
  # text to display on the button, the new subtext to display, and
  # the RGB value of the text.

  # Event IDs are those in constants.py.
  def activate(self, ev_id):
    if ev_id == E_START1 or ev_id == E_START2: ev_id = E_START
    if ev_id == E_LEFT1 or ev_id == E_LEFT2: ev_id = E_LEFT
    if ev_id == E_RIGHT1 or ev_id == E_RIGHT2: ev_id = E_RIGHT
    if self.callbacks == None:
      if ev_id == E_START:
        return E_QUIT # This is a back button
      else: return E_PASS # Shouldn't happen
    if callable(self.callbacks.get(ev_id)):
      text, subtext, rgb = self.callbacks[ev_id](*self.args)
      if text: self.text = text
      if subtext: self.subtext = subtext
      if rgb: self.rgb = rgb
      self.render()
      return E_PASS
    else: return E_PASS

  # Render the image. If subtext is present, the main text gets smaller.
  def render(self):
    self.image = pygame.surface.Surface(BUTTON_SIZE)
    self.image.blit(self.bg, (0,0))
    if self.subtext == None:
      text = font32.render(self.text, 1, self.rgb)
      self.image.blit(text, (96 - (font32.size(self.text)[0] / 2), 8))
    else:
      text = font26.render(self.text, 1, self.rgb)
      subtext = font20.render(self.subtext, 1, self.rgb)
      self.image.blit(text, (96 - (font26.size(self.text)[0] / 2), 4))
      self.image.blit(subtext, (96 - (font20.size(self.subtext)[0] / 2), 22))

class Menu:

  # Menus are defined based on a tree of tuples (submenus) ending
  # in a list (the final item). The first item of the tuple is
  # a string of text which gets displayed.
  def __init__(self, name, itemlist):
    self.items = []
    self.text = name
    self.rgb = DARK_GRAY
    self.bg = button_bg
    self.render()
    for i in itemlist:
      if type(i) == type([]): # Menuitems are lists
        self.items.append(MenuItem(i[0], i[1], i[2]))
        self.items[-1].activate("initial")
      elif type(i) == type((0,0)): # New submenus are tuples
        self.items.append(Menu(i[0], i[1:]))

  # Menu rendering is tons easier, since it never changes.
  def render(self):
    self.image = pygame.surface.Surface((192, 40))
    self.image.blit(self.bg, (0,0))
    text = font32.render(self.text, 1, self.rgb)
    self.image.blit(text, (96 - (font32.size(self.text)[0] / 2), 8))

  # Render and start navigating the menu.
  # Postcondition: Screen buffer is in an unknown state!
  def display(self, screen):
    screen.fill((0,0,0))
    top_offset = 80
    curitem = 0
    topitem = 0
    toprotater = TextZoomer(self.text, 127, 63, 255)
    zoom = 8
    zoomdelta = - 1
    time_to_zoom = 0

    ev = E_PASS
    while ev != E_QUIT:
      ev = event.poll()

      # Scroll down through the menu
      if ev == E_DOWN1 or ev == E_DOWN2:
        try: self.items[curitem].activate("deselect")
        except AttributeError: pass
        curitem += 1
        if curitem == len(self.items): # Loop at the bottom
          curitem = 0
          topitem = 0
        elif curitem >= topitem + 7: # Advance the menu if necessary
          topitem += 1
        try: self.items[curitem].activate("select")
        except AttributeError: pass

      # Same as above, but up
      elif ev == E_UP1 or ev == E_UP2:
        try: self.items[curitem].activate("deselect")
        except AttributeError: pass
        curitem -= 1
        if curitem < 0:
          curitem = len(self.items) - 1
          topitem = max(0, curitem - 6)
        elif curitem < topitem:
          topitem = curitem
        try: self.items[curitem].activate("select")
        except AttributeError: pass

      # Otherwise, if the event actually happened, pass it on to the button.
      elif ev != E_PASS and ev != E_QUIT:
        try:
          self.items[curitem].activate(ev)
        except AttributeError:
          if ev == E_START1 or ev == E_START2:
            # Except if we're not a button and the event was START, go to
            # the new menu.
            self.items[curitem].display(screen)
            screen.fill((0,0,0)) # Reset buffer.

      zoom += zoomdelta
      if zoom > 12 or zoom < 0: zoomdelta *= -1

      # Draw the buttons to the screen
      screen.fill((0,0,0))
      toprotater.iterate()
      screen.blit(toprotater.tempsurface, (0,0))
      for i in range(7):
        if i + topitem < len(self.items):
          img = self.items[topitem + i].image
          if i + topitem == curitem:
            screen.blit(pygame.transform.scale(img, (200-zoom, 48-zoom/2)),
                        (220 + zoom/2, 76 + zoom/4 + i*48))
          else:
            screen.blit(img, (224, top_offset+i*48))

      pygame.display.flip()
      
      pygame.time.wait(20)
