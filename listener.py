# This is the base class for most of the active objects in the game.

# It basically says that the object should do nothing on all the
# events it might get.

class Listener(object):
  def __init__(self):
    raise NotImplementedError("This class should never be instantiated.")

  # This is received when a hold is sucessfully completed ("OK").
  def ok_hold(self): pass

  # Received when a hold is broken ("NG") for the first time.
  def broke_hold(self): pass

  # Received when an arrow is stepped on or missed.
  # combo is the current combo count. rating is V (marvelous), P
  # (perfect), G (great), O (okay), B (boo), or M (miss).
  # Note that since Combo objects are Listeners, the order Listeners
  # are called in *does* matter in that case.
  def stepped(self, curtime, rating, combo): pass

  # Received when a new song is started. difficulty is the name as a
  # string; count is the number of arrows in the song; feet is the
  # song rating.
  def set_song(self, difficulty, count, feet): pass

  # Received when the BPM of the song changes. The new BPM is given.
  def change_bpm(self, bpm): pass
