# utils/timer.py
import threading, time

class PomodoroTimer:
    def __init__(self, on_tick=None, on_phase=None, on_done=None):
        self._lock = threading.Lock()
        self._t = None
        self._stop = False
        self._paused = False
        self._on_tick = on_tick   # (remaining_secs, phase) -> None
        self._on_phase = on_phase # (phase) -> None  # "work" | "break"
        self._on_done = on_done   # () -> None
        self._remaining = 0
        self._phase = "idle"

    def start(self, work_min=25, break_min=5, cycles=1):
        with self._lock:
            if self.is_running(): return False
            self._stop = False
            self._paused = False
            self._t = threading.Thread(target=self._run, args=(work_min*60, break_min*60, cycles), daemon=True)
            self._t.start()
            return True

    def _run(self, work_s, break_s, cycles):
        for c in range(cycles):
            if not self._countdown(work_s, "work"):  return
            if c < cycles-1:
                if not self._countdown(break_s, "break"): return
        if self._on_done: self._on_done()

    def _countdown(self, seconds, phase):
        self._phase = phase
        if self._on_phase: self._on_phase(phase)
        self._remaining = seconds
        while self._remaining > 0:
            if self._stop: self._phase = "idle"; return False
            if not self._paused:
                self._remaining -= 1
                if self._on_tick: self._on_tick(self._remaining, self._phase)
            time.sleep(1)
        return True

    def pause(self):  self._paused = True
    def resume(self): self._paused = False
    def stop(self):
        self._stop = True
    def is_running(self): return self._t is not None and self._t.is_alive()
    def status(self): return dict(phase=self._phase, remaining=self._remaining, running=self.is_running(), paused=self._paused)
    def remaining(self): return self._remaining
    def phase(self): return self._phase
