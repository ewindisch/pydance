import pygame
from constants import *

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
font32 = pygame.font.Font(None, 32)
font26 = pygame.font.Font(None, 26)
font20 = pygame.font.Font(None, 20)

class MenuItem:

  def __init__(self, callbacks, *args):
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
    self.text = "A Button"
    self.render()
    self.activate("initial")

  # Call an appropriate callback function, for the event given.
  # The function can return up to three arguments - the new
  # text to display on the button, the new subtext to display, and
  # the RGB value of the text.

  # Event IDs are those in constants.py.
  def activate(self, ev_id):
    if callable(self.callbacks.get(ev_id)):
      text, subtext, rgb = self.callbacks(ev_id)(*args)
      if text: self.text = text
      if subtext: self.subtext = subtext
      if rgb: self.rgb = rgb
      self.render()

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
        self.items.append(MenuItem(i[0], i[1]))
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
  def display(handler): # Input handler
    screen.fill((0,0,0))
    top_offset = 80
    curitem = 0
    topitem = 0
    zoom = 8
    zoomdelta = - 1
    ev = E_PASS
    while ev != E_QUIT:
      ev = handler.poll()

      # Scroll down through the menu
      if ev == E_DOWN1 or ev == E_DOWN2:
        if type(self.items[curitem]) == MenuItem:
          self.items[curitem].activate("unselect")
        curitem += 1
        if curitem == len(self.items): # Loop at the bottom
          curitem = 0
          topitem = 0
        elif curitem >= topitem + 7: # Advance the menu if necessary
          topitem += 1
        if type(self.items[curitem]) == MenuItem:
          self.items[curitem].activate("select")

      # Same as above, but up
      elif ev == E_UP1 or ev == E_UP2:
        if type(self.items[curitem]) == MenuItem:
          self.items[curitem].activate("unselect")
        curitem -= 1
        if curitem < 0:
          curitem = len(self.items) - 1
          topitem = max(0, curitem - 6)
        elif curitem < topitem:
          topitem = curitem
        if type(self.items[curitem]) == MenuItem:
          self.items[curitem].activate("select")

      # Otherwise, if the event actually happened, pass it on to the button.
      elif ev != E_PASS:
        if type(self.items[curitem]) == MenuItem:
          self.items[curitem].activate(ev)
        elif ev == E_START1 or ev == E_START2:
          # Except if we're not a button and the event was START, go to
          # the new menu.
          self.items[curitem].display(handler)
          screen.fill((0,0,0)) # Reset buffer.

      # Draw the buttons to the screen
      for i in range(7):
        if i + topitem < len(self.items):
          img = self.items[topitem + i].image
          if i + topitem == curitem:
            zoom += zoomdelta
            if zoom > 12 or zoom < 0: zoomdelta *= -1
            screen.blit(pygame.transform.scale(img, (200 - z, 48 - z / 2)),
                        (220 + z/2, 76 + z/4 + i*48))
          else:
            screen.blit(img, (224, top_offset+i*48))

      pygame.display.flip()
      pygame.time.wait(10)
