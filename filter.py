import queue
import datetime

class Filter():
    def __init__(self):
        self._users_timers = {}
        self._rules = {
            ### maxsize, time in minutes
            'photo': (15, 60),
            'video': (10, 60),
            'quick_voice': (10, 10),
            'sticker': (20, 60)
        }

    def _append_user(self, id: str) -> None:
        if not id in self._users_timers:
            self._users_timers[id] = {
                tp: queue.Queue(maxsize=self._rules[tp][0]) for tp in self._rules
            }

    def check_type(self, id: str, tp: str) -> bool:
        self._append_user(id)
        now_date = datetime.datetime.now()
        if self._users_timers[id][tp].full():
            first_date = self._users_timers[id][tp].queue[0]
            diff = (now_date - first_date).total_seconds() / 60.0
            if diff <= self._rules[tp][1]:
                self._users_timers[id][tp].get()
                self._users_timers[id][tp].put(now_date)
                return True
            return False 
        else:
            self._users_timers[id][tp].put(now_date)
            return True