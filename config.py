# A generic configuration file parser

import os

# master vs user:
# the 'user' hash (~/.foorc) overrides the master hash (/etc/foorc),
# if a value is present in the user hash.

# When writing out, only things *not* equal to the master hash (or only
# in the master hash) are written back out. 

class Config:
  # Start a config file, based off a hash - this hash is always a master set
  def __init__(self, data = None):
    self.user = {}
    self.master = {}
    if data != None: self.update(data, True)

  # Update with a dict object, instead of a file.
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

  # Update the config data with a 'key value' filename.
  # If shouldExist is true, raise exceptions if the file doesn't exist.
  # Otherwise, we silently ignore it.
  def load(self, filename, master = False, shouldExist = False):
    d = None
    if master: d = self.master
    else: d = self.user

    if not os.path.isfile(filename) and not shouldExist: return

    fi = open(filename, "r")
    for line in fi:
      if line.isspace() or len(line) == 0 or line[0] == '#': pass # comment
      else:
        key = line[0:line.find(' ')]
        val = line[line.find(' ') + 1:].strip()
        # Try to cast the input to a nicer type
        try: d[key] = int(val)
        except ValueError:
          try: d[key] = float(val)
          except ValueError: d[key] = val

    fi.close()

  # Write the filename back out to disk.
  def write(self, filename):
    fi = open(filename, "w")
    keys = self.user.keys()
    keys.sort()
    for key in keys:
      if not self.master.has_key(key) or self.master[key] != self.user[key]:
        fi.write("%s %s\n" % (key, self.user[key]))
    fi.close()
