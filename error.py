# Put up a pretty error message.

from interface import *
from constants import mainconfig
import fontfx
import ui
from fonttheme import FontTheme

# EricW - OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
import Image

class ErrorMessage(InterfaceWindow):
  def __init__(self, screen, lines):
    #screen.fill((0, 0, 0))
    bg = pygame.image.load(os.path.join(image_path, "bg.png"))
    bg.set_alpha(128)
    screen.blit(bg, (0, 0))
    text = FONTS[60].render("ERROR!", 1, (0, 0, 0))
    text_rect = text.get_rect()
    text_rect.center = (320, 30)
    screen.blit(text, text_rect)

    for i in range(len(lines)):
      text = FONTS[32].render(lines[i], 1, (244, 244, 244))
      text_rect = text.get_rect()
      text_rect.center = (320, 36 * (i + 3))
      screen.blit(text, text_rect)

    text = FONTS[32].render("Press Enter/Start/Esc", 1, (160, 160, 160))
    text.set_colorkey(text.get_at((0, 0)))
    textpos = text.get_rect()
    textpos.center = (320, 440)
    screen.blit(text, textpos)

    img=pygame.image.tostring(screen, "RGB", 1)
    glDrawPixels (screen.get_size()[0], screen.get_size()[1], GL_RGB, GL_UNSIGNED_BYTE, img);

    glEnable (GL_LIGHTING)
    glEnable (GL_LIGHT0)
    quad=gluNewQuadric()
    gluSphere (quad, .5, 50, 50)
    glDisable (GL_LIGHTING)

    pygame.display.flip()
    ev = (0, E_PASS)
    while ev[1] != E_START and ev[1] != E_QUIT:
      pygame.time.wait(50)
      ev = event.poll()
