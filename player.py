class Player:
  def __init__(self, pid, score, lifebar,  holdtext, arrowgroup,
               combos, holdkey, song, difficulty, mode = "SINGLE"):
    self.pid = pid
    self.score = score
    self.lifebar = lifebar
    self.holdtext = holdtext
    self.arrow_group = arrowgroup
    self.judging_list = []
    self.tempholding = [-1, -1, -1, -1]
    self.combos = combos
    self.holdkey = holdkey
    self.song = song
    self.difficulty = difficulty
    self.holds = None
    self.toparr = {}
    self.toparrfx = {}
    self.evt = None
    self.fx_data = []

  def get_events(self):
    self.evt = self.song.get_events()
