# Put up a pretty error message.

from interface import *
from constants import mainconfig
import fontfx
import ui

# FIXME: We should word-wrap text so we don't have to pass in a list.

class ErrorMessage(InterfaceWindow):
  def __init__(self, screen, lines):
    InterfaceWindow.__init__(self, screen, "error-bg.png")
    text = fontfx.shadow("Error!", 60, [255, 255, 255], offset = 2)
    text_rect = text.get_rect()
    text_rect.center = (320, 50)
    screen.blit(text, text_rect)

    for i in range(len(lines)):
      text = fontfx.shadow(lines[i], 32, [200, 200, 200])
      text_rect = text.get_rect()
      text_rect.center = [320, 36 * (i + 3)]
      screen.blit(text, text_rect)

    text = fontfx.shadow("Press Enter/Start/Escape", 32, [160, 160, 160])
    textpos = text.get_rect()
    textpos.center = [320, 440]
    screen.blit(text, textpos)

    pygame.display.update()
    ui.ui.empty()
    pid, ev = ui.ui.poll()

    while ev not in [ui.START, ui.CONFIRM, ui.QUIT]:
      if ev == ui.FULLSCREEN:
        pygame.display.toggle_fullscreen()
        mainconfig["fullscreen"] ^= 1
      pid, ev = ui.ui.wait()
