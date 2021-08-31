FRAME_TIMER_ID_YELLOW_BUTTON= 1
FRAME_TIMER_ID_RED_BUTTON= 2

frame_timers = []

def frame_timer_tick():
    global frame_timers
    for timer in frame_timers:
        timer.tick()

def frame_timer_del_all():
    global frame_timers
    frame_timers = []
    
class FrameTimer():
    def __init__(self, frames, callback_fn, id=None, unique=False):
        global frame_timers
        self.frames_left = frames
        self.callback_fn = callback_fn
        self.id = id
        if id and unique:
            #  This timer is supposed to be unique.  Delete any existing matching ones
            frame_timers = [timer for timer in frame_timers if not timer.id == id]
        frame_timers.append(self)

    # Must be called every frame of the game
    def tick(self):
        global frame_timers
        self.frames_left -= 1
        if self.frames_left <= 0:
            frame_timers.remove(self)
            self.callback_fn(self.id)

