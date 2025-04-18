from src.system.custom_process import BaseCustomProcess
from src.system.event_types import Event

class OrbitMonitor(BaseCustomProcess):
    def __init__(self, queues_dir, log_level):
        super().__init__(
            log_prefix="[OrbitMonitor]",
            queues_dir=queues_dir,
            events_q_name="orbit_monitor",
            event_source_name="orbit_monitor",
            log_level=log_level
        )

    def run(self):
        self._log_message(0, "Монитор орбиты запущен")
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

            if 300e3 <= altitude <= 2000e3:
                self._log_message(0, f"Допустимая орбита: {altitude} м")
                self._forward_event("orbit_limiter", event)
            else:
                self._log_message(2, f"Ошибка орбиты: высота {altitude} м вне допустимого диапазона")

    def _forward_event(self, destination, event):
        new_event = Event(
            source=self._event_source_name,
            destination=destination,
            operation=event.operation,
            parameters=event.parameters
        )
        self._queues_dir.get_queue(destination).put(new_event)
