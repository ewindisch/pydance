import pygame, announcer, colors, fontfx

from constants import *

# FIXME - This whole thing needs reworking/documentation

class GradingScreen(object):
  def __init__(self, players):
    self.players = players

    for player in players:
      if player == None: continue
      print "Player %d:" % (player.pid + 1)
    
      grade = player.grade.grade(player.failed)
      totalsteps = player.stats.arrow_count

      steps = (grade, player.difficulty, player.stats.arrow_count,
               player.stats.maxcombo)

      steptypes = (player.stats["V"], player.stats["P"], player.stats["G"],
                   player.stats["O"], player.stats["B"], player.stats["M"],
                   player.stats.good_holds, player.stats.hold_count)
      print "GRADE: %s (%s) - total steps: %d best combo %d" % steps
      print "V: %d P: %d G: %d O: %d B: %d M: %d - %d/%d holds" % steptypes
      print
 
  def make_gradescreen(self, screen, background):
    player = self.players[0]

    if player is None: return None

    totalsteps = player.stats.arrow_count

    if totalsteps == 0: return None

    # dim screen
    for n in range(31):
      background.set_alpha(255-(n*4))
      screen.fill(colors.BLACK)
      screen.blit(background, (0, 0))
      pygame.display.flip()
      pygame.time.wait(1)

    grading = fontfx.sinkblur("GRADING",64,4,(224,72),(64,64,255))
    grading.set_colorkey(grading.get_at((0,0)))
    screen.blit(grading, (320-grading.get_rect().centerx,-8) )
    pygame.display.update()

    rows = ["MARVELOUS", "PERFECT", "GREAT", "OK", "BOO",
            "MISS", "early", "late", " ", "TOTAL", " ", "MAX COMBO",
            "HOLDS", " ", "SCORE"]

    for j in range(4):
      for i in range(len(rows)):
        fc = ((j*32)+96-(i*8))
        if fc < 0: fc=0
        gradetext = fontfx.shadefade(rows[i],28,j,(224,32), (fc,fc,fc))
        gradetext.set_colorkey(gradetext.get_at((0,0)))
        gradetextpos = gradetext.get_rect()
        gradetextpos.right = 32 + screen.get_rect().centerx + 8-j
        gradetextpos.top = 64 + (i*24) + 8-j
        r = screen.blit(gradetext, (320-FONTS[28].size(rows[i])[0]/2,
                                64 + (i*24) + 8-j))
        pygame.display.update(r)
      pygame.time.wait(100)

    for player in self.players:
      grade = player.grade.grade(player.failed)
      for i in range(4):
        font = pygame.font.Font(None, 100-(i*2))
        gradetext = font.render(grade, 1, (48 + i*16, 48 + i*16, 48 + i*16))
        gradetext.set_colorkey(gradetext.get_at((0,0)))
        r = screen.blit(gradetext, (200 + 250 * player.pid - (font.size(grade))[0]/2, 150))
        pygame.display.update(r)
        pygame.time.delay(48)

      totalsteps = player.stats.arrow_count

      rows = [player.stats[k] for k in ["V", "P", "G", "O", "B", "M"]]
      rows += [player.stats.early, player.stats.late]

      for j in range(4):
        for i in range(len(rows)):
          fc = ((j*32)+96-(i*8))
          if fc < 0: fc=0
          text = "%d (%d%%)" % (rows[i], 100 * rows[i] / totalsteps)
          gradetext = fontfx.shadefade(text,28,j,(FONTS[28].size(text)[0]+8,32), (fc,fc,fc))
          gradetext.set_colorkey(gradetext.get_at((0,0)))
          graderect = gradetext.get_rect()
          graderect.top = 72 + (i*24) - j
          if player.pid == 0:
            graderect.left = 40
          elif player.pid == 1:
            graderect.right = 600
          r = screen.blit(gradetext, graderect)
          pygame.display.update(r)
        pygame.time.wait(100)

      # Total
      for j in range(4):
        gradetext = fontfx.shadefade(str(totalsteps),28,j,(FONTS[28].size(str(totalsteps))[0]+8,32), (fc,fc,fc))
        gradetext.set_colorkey(gradetext.get_at((0,0)))
        graderect = gradetext.get_rect()
        graderect.top = 288-j
        if player.pid == 0:
          graderect.left = 40
        elif player.pid == 1:
          graderect.right = 600
        r = screen.blit(gradetext, graderect)
        pygame.display.update(r)
      pygame.time.wait(100)

      # Combo
      for j in range(4):
        text = "%d (%d%%)" % (player.stats.maxcombo,
                              player.stats.maxcombo * 100 / totalsteps)
        gradetext = fontfx.shadefade(text,28,j,(FONTS[28].size(text)[0]+8,32), (fc,fc,fc))
        gradetext.set_colorkey(gradetext.get_at((0,0)))
        graderect = gradetext.get_rect()
        graderect.top = 336-j
        if player.pid == 0:
          graderect.left = 40
        elif player.pid == 1:
          graderect.right = 600
        r = screen.blit(gradetext, graderect)
        pygame.display.update(r)
      pygame.time.wait(100)

      # Holds
      for j in range(4):
        text = "%d / %d" % (player.stats.good_holds, player.stats.hold_count)
        gradetext = fontfx.shadefade(text,28,j,(FONTS[28].size(text)[0]+8,32), (fc,fc,fc))
        gradetext.set_colorkey(gradetext.get_at((0,0)))
        graderect = gradetext.get_rect()
        graderect.top = 360-j
        if player.pid == 0:
          graderect.left = 40
        elif player.pid == 1:
          graderect.right = 600
        r = screen.blit(gradetext, graderect)
        pygame.display.update(r)
      pygame.time.wait(100)

      # Score
      # Pete's suggestion, make it more readable by adding commas.
      orig_score = str(int(player.score.score))
      score = ""
      while len(orig_score) > 3:
        score = orig_score[-3:] + "," + score
        orig_score = orig_score[:-3]
      score = (orig_score + "," + score)[:-1]
      for j in range(4):
        gradetext = fontfx.shadefade(str(score), 28, j,
                                     (FONTS[28].size(str(score))[0]+8,32),
                                     (fc,fc,fc))
        gradetext.set_colorkey(gradetext.get_at((0,0)))
        graderect = gradetext.get_rect()
        graderect.top = 412-j
        if player.pid == 0:
          graderect.left = 40
        elif player.pid == 1:
          graderect.right = 600
        r = screen.blit(gradetext, graderect)
        pygame.display.update(r)
      pygame.time.wait(100)

    background.set_alpha()

    return 1
    
  def make_waitscreen(self, screen):
    idir = -4
    i = 192
    screenshot = 0
    while 1:
      if i < 32:        idir =  4
      elif i > 224:     idir = -4

      i += idir
      ev = event.poll()
      if (ev[1] == E_QUIT) or (ev[1] == E_START):
        break
      elif ev[1] == E_FULLSCREEN:
        pygame.display.toggle_fullscreen()
        mainconfig["fullscreen"] ^= 1
      elif ev[1] == E_SCREENSHOT:
        print "writing next frame to", os.path.join(rc_path, "screenshot.bmp")
        screenshot = 1
          
      gradetext = FONTS[32].render("Press ESC/ENTER/START",1, (i,128,128) )
      gradetextpos = gradetext.get_rect()
      gradetextpos.centerx = screen.get_rect().centerx
      gradetextpos.bottom = screen.get_rect().bottom - 16
      r = screen.blit(gradetext,gradetextpos)
      pygame.display.update(r)
      pygame.time.wait(40)     # don't peg the CPU on the grading screen

      if screenshot:
        pygame.image.save(pygame.transform.scale(screen, (640,480)),
                          os.path.join(rc_path, "screenshot.bmp"))
        screenshot = 0

    return
