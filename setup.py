#!/usr/bin/env python
# Set up the appropriate pyDDR installation makefiles.

import os, sys

# Check for the presence of appropriate Python and Pygame versions.
def sanity_check():
  print "Checking for appropriate libraries."
  sys.stdout.write("Checking Python version... ")
  if sys.version_info[0] < 2 and sys.version_info[1] < 2:
    print "Versions of Python less than 2.2 are not supported by pyDDR."
    print "Visit http://www.python.org to upgrade."
    sys.exit(1)
  else: print "2.2.x or greater"

  try:
    sys.stdout.write("Checking for Pygame... ")
    import pygame
    ver = pygame.version.ver.split(".")
    if int(ver[0]) == 1 and int(ver[1]) < 5 and int(ver[2]) < 5:
      print "You have pygame, but a version less than 1.5.5."
      print "Visit http://www.pygame.org to upgrade."
      sys.exit(1)
    else:
      print pygame.version.ver
  except ImportError:
    print "You don't seem to have pygame installed."
    print "Visit http://www.pygame.org to install it."

def detect_real_os():
  sys.stdout.write("Detecting your operating system... ")
  if os.name == "win32":
    print "Windows"
    return "win32"
  elif os.name == "posix":
    sys.stdout.write("POSIX - ")
    if os.path.islink("/System/Library/CoreServices/WindowServer"):
      print "MacOS X"
      return "macosx"
    elif os.environ.has_key("HOME") and os.path.isdir("/etc"):
      print "UNIX-like"
      return "posix"
    else:
      print "Unknown!"
      print "I'm all confused as to your OS. pyDDR will run pretending that you're"
      print "UNIX, but you'll have to force this setup step if you really want to."
      sys.exit(1)
  else:
    print "Unknown"
    print "Your platform isn't supported at all by pyDDR (yet)."
    sys.exit(1)

sanity_check()
osname = detect_real_os()

print

if os.path.isfile("pyddr." + osname + ".cfg"):
  fin = open("pyddr." + osname + ".cfg")
  fout = open("pyddr.cfg", "w")
  for line in fin: fout.write(line)
  fout.close()
  fin.close()

if os.path.isfile("Makefile." + osname):
  fin = open("Makefile." + osname)
  fout = open("Makefile", "w")
  for line in fin: fout.write(line)
  fout.close()
  fin.close()  

if osname == "win32":
  print "Configuration for Win32 systems complete. No installation is needed."
  print "Make sure your pyddr.cfg file points to your song directory."
elif osname == "macosx":
  print "This OSs support is not yet integrated into this program."
elif osname == "posix":
  print "Configuration for UNIX-like systems complete. 'make install' should"
  print "properly install pyDDR, by default into /usr/local. You can override"
  print "this by setting $PREFIX. You can also set $DESTDIR, which will be"
  print "prepended to all installation paths."

  if os.path.exists("/vmlinuz"):
    print "\nLinux users may wish to examine the joystick driver in ddrmat/, too."

