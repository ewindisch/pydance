#!/usr/bin/python
# Shrink the size of PyDDR step files
# By Joe Wreschnig <piman@debian.org>

import sys, re, getopt

VERSION = "0.9"

def usage():
  print "stepshrink " + VERSION + " - shrink PyDDR step files"
  print "Usage: " + sys.argv[0] + " [-o output] stepfile"
  print "  --output, -o    Filename to output to (default stdout)"


def main():

  output_file = None

  try:
    opts, args = getopt.getopt(sys.argv[1:], "o:vh",
                               ["output", "version", "help"])
  except getopt.GetoptError:
    usage()
    sys.exit(2)

  for o, a in opts:
    if o in ("--help", "-h"):
      usage()
      sys.exit()
    elif o in ("-v", "--version"):
      print "stepshrink version " + VERSION
      sys.exit()
    elif o in ("-o", "--output"): output_file = a

  if len(args) == 0:
    usage()
    sys.exit(2)

  outfile = sys.stdout
  lines = []
  lines2 = []

  infile = open(args[0])
  lines = infile.readlines()
  infile.close()

  lines = lyrics_and_delay(lines)

  types = ("sixty", "thrty", "steps", "eight", "qurtr", "halfn", "whole")
  for i in range(0,len(types) - 1):
    lines = remove_empty_types(types[i], types[i+1], lines)

  lines = remove_empty_types("twtfr", "tripl", lines)

  lines = delays_to_wholes(lines)
  lines = consecutive_delays(lines)

  if output_file != None: outfile = open(output_file, "w")
  for line in lines: outfile.write(line + "\n")
  if output_file != None: outfile.close()

def lyrics_and_delay(lines):
  e_eight = re.compile("^\s*eight\s+00\s+00\s+00\s+00")
  atsec = re.compile("^\s*atsec\s+(\d+)\.(\d*)")
  version = re.compile("^\s*version\s+\d+.\d+")
  btm = re.compile("^\s*[BTM]")
  lyr = re.compile("^\s*L")
  i = 0

  lines2 = []
  stage = 0
  for line in lines:
    if stage == 0:
      if version.match(line):
        stage = 3
        line = "version 0.6" # thrty support requires this
      lines2.append(line.strip())
      
    elif stage == 1:
      # Incredible precision isn't really necessary for lyrics...
      if line == "end": stage = 3
      res = atsec.match(line)
      if res: line = "atsec %s.%s" % (res.group(1), res.group(2)[0:2])
      lines2.append(line.strip())

    elif stage == 2:
      if not e_eight.match(line):
        if i % 2 == 1: lines2.append("eight 00 00 00 00")
        if i > 1: lines2.append("delay %d" % (i/2))
        lines2.append(line.strip())
        stage = 3
        i = 0
      else:
        i += 1

    else:
      if btm.match(line): stage = 2
      elif lyr.match(line): stage = 1
      lines2.append(line.strip())

  return lines2

def remove_empty_types(type, double_type, lines):
  lines2 = []
  emp = re.compile("^\s*%s\s+00\s+00\s+00\s+00" % type)
  ne = re.compile("^\s*%s\s+(\d\d)\s+(\d\d)\s+(\d\d)\s+(\d\d)" % type)
  for line in lines:
    if emp.match(line) and ne.match(lines2[-1]):
      res = ne.match(lines2[-1])
      lines2[-1] = "%s %s %s %s %s" % (double_type, res.group(1),
                                       res.group(2), res.group(3),
                                       res.group(4))
    else: lines2.append(line)
  return lines2

def delays_to_wholes(lines):
  lines2 = []
  delay = re.compile("^\s*delay\s+(\d+)")
  qurtr = re.compile("^\s*qurtr\s+(\d\d)\s+(\d\d)\s+(\d\d)\s+(\d\d)")

  for line in lines:
    res = delay.match(line)
    if len(lines2) != 0: res2 = qurtr.match(lines2[-1])
    else: res2 = None
    if res and res2 and int(res.group(1)) > 0:
      lines2.pop()
      i = int(res.group(1))
      if i >= 3:
        lines2.append("whole %s %s %s %s" % res2.groups((1,2,3,4)))
        lines2.append("delay %d" % (i - 3))
      elif i >= 1:
        lines2.append("halfn %s %s %s %s" % res2.groups((1,2,3,4)))
        lines2.append("delay %d" % (i - 1))
    else: lines2.append(line)
  return lines2

def consecutive_delays(lines):
  lines2 = []
  delay = re.compile("^\s*delay\s+(\d+)")

  for line in lines:
    res = delay.match(line)
    if len(lines2) != 0: res2 = delay.match(lines2[-1])
    if res and res2:
      i = int(res.group(1))
      j = int(res.group(2))
      if i + j == 0: lines2.pop()
      else: lines2[-1] = "delay %d" % (i + j)
    elif not res or res.group(1) != "0": lines2.append(line)
  return lines2

if __name__ == '__main__':
  main()
