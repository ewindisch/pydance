#!/usr/bin/env python
# Convert any 

import sys, os, getopt, fnmatch, time

pyddr_path = sys.argv[0]
if os.name == "posix":
  sys.path.append(os.path.split(os.path.realpath(pyddr_path))[0])
else: sys.path.append(os.path.split(os.path.abspath(pyddr_path))[0])

VERSION = "0.1"
FORMATS = ('*.step', '*.dance', '*.dwi')

import fileparsers

def convert(arg, delete):
  if not os.path.exists(arg):
    sys.stderr.write("no such filename: " + arg + "\n")
  elif os.path.isdir(arg):
    for file in os.listdir(arg): convert(os.path.join(arg, file), delete)
  else:
    matched = False
    for format in FORMATS:
      if fnmatch.fnmatch(arg, format): matched = True
    if not matched: return

    cwd = os.getcwd()
    dir, name = os.path.split(arg)
    if dir == "": dir = "."
    os.chdir(dir)
    try:
      newname = name[:name.rindex(".")] + ".dance"
      print "Converting", name, "to", newname

      song = fileparsers.SongItem(name)
      dir = os.path.realpath(".")
      for k in ("banner", "background", "filename", "movie"):
        if song.info[k]: song.info[k] = song.info[k].replace(dir + os.sep, '')
      song.write(newname)

      if delete: os.unlink(name)
    except:
      sys.stderr.write("Error converting " + name + "\n")
    os.chdir(cwd)

def usage(exitcode = 0):
  print "any2dance", VERSION, "- convert other formats to .dance"
  print "Usage:", sys.argv[0], "oldfile.ext"
  sys.exit(exitcode)

def main():

  delete = False

  try: opts, args = getopt.getopt(sys.argv[1:], "vh",
                                  ["version", "help", "delete"])
  except getopt.GetoptError: usage(1)

  for o, a in opts:
    if o in ("--help", "-h"):
      usage()
    elif o in ("-v", "--version"):
      sys.stderr.write("any2dance version " + VERSION + "\n")
      sys.exit()
    elif o in ("--delete",):
      print "WARNING: Files will be deleted after conversion. You have 5 seconds to exit."
      time.sleep(5)
      delete = True

  if len(args) == 0: usage(2)

  for arg in args: convert(arg, delete)

if __name__ == '__main__': main()
