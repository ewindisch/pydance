# A generic configuration file parser

import os

class Config:
  def __init__(self, data = None):
    self.user = {}
    self.master = {}
    if data != None: self.update(data, True)

  def update(self, data, master = False):
    if master:
      for k in data: self.master[k] = data[k]
    else:
      for k in data: self.user[k] = data[k]
        
  def __getitem__(self, key):
    if self.user.has_key(key): return self.user[key]
    elif self.master.has_key(key): return self.master[key]
    else: return None
  
  def __setitem__(self, key, value, master = False):
    if master: self.master[key] = value
    else: self.user[key] = value

  def __delitem__(self, key):
    if self.master.has_key(key): del(self.master[key])
    if self.user.has_key(key): del(self.user[key])

  def load(self, filename, master = False, shouldExist = False):
    d = None
    if master: d = self.master
    else: d = self.user

    if not os.path.isfile(filename) and not shouldExist: return

    fi = open(filename, "r")
    for line in fi:
      if line.isspace() or len(line) == 0 or line[0] == '#': pass
      else: d[line[0:line.find(' ')]] = line[line.find(' ')+1:].strip()

    fi.close()

  def write(self, filename):
    fi = open(filename, "w")
    keys = self.user.keys()
    keys.sort()
    for key in keys:
      if not self.master.has_key(key) or self.master[key] != self.user[key]:
        fi.write("%s %s\n" % (key, self.user[key]))
    fi.close()
