from src.system.custom_process import BaseCustomProcess
from src.system.event_types import Event

class OrbitLimiter(BaseCustomProcess):
    def __init__(self, queues_dir, log_level):
        super().__init__(
            log_prefix="[OrbitLimiter]",
            queues_dir=queues_dir,
            events_q_name="orbit_limiter",
            event_source_name="orbit_limiter",
            log_level=log_level
        )

    def run(self):
        self._log_message(0, "Ограничитель орбиты запущен")
        while not self._quit:
            self._check_events_q()
            self._check_control_q()

    def _check_events_q(self):
        try:
            event = self._events_q.get_nowait()
            if isinstance(event, Event):
                self._handle_event(event)
        except:
            pass

    def _handle_event(self, event):
        if event.operation == "change_orbit":
            altitude, raan, inclination = event.parameters

            if 0 < inclination < 3.14:
                self._log_message(0, f"Допустимый наклон орбиты: {inclination} рад")
                self._forward_event("orbit_control", event)
            else:
                self._log_message(2, f"Недопустимый наклон орбиты: {inclination} рад")

    def _forward_event(self, destination, event):
        new_event = Event(
            source=self._event_source_name,
            destination=destination,
            operation=event.operation,
            parameters=event.parameters
        )
        self._queues_dir.get_queue(destination).put(new_event)
