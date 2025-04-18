from multiprocessing import Queue
from queue import Empty

from src.system.custom_process import BaseCustomProcess
from src.system.event_types import Event
from src.system.config import LOG_DEBUG, LOG_INFO, LOG_ERROR, DEFAULT_LOG_LEVEL

class OrbitMonitor(BaseCustomProcess):
    def __init__(self, queues_dir, log_level=DEFAULT_LOG_LEVEL):
        super().__init__(
            log_prefix="[OrbitMonitor]",
            queues_dir=queues_dir,
            events_q_name="orbit_monitor",
            event_source_name="orbit_monitor",
            log_level=log_level
        )
        self._log_message(LOG_INFO, "Монитор орбиты создан")

    def run(self):
        self._log_message(LOG_INFO, "Монитор орбиты запущен")
        while not self._quit:
            self._check_events_q()
            self._check_control_q()

    def _check_control_q(self):
        try:
            request = self._control_q.get_nowait()
            self._log_message(LOG_DEBUG, f"проверяем запрос {request}")
            if hasattr(request, 'operation') and request.operation == 'stop':
                self._quit = True
        except Empty:
            pass

    def _check_events_q(self):
        try:
            event = self._events_q.get_nowait()
            if isinstance(event, Event):
                self._handle_event(event)
        except Empty:
            pass

    def _handle_event(self, event):
        if event.operation == "change_orbit":
            altitude, raan, inclination = event.parameters

            # Проверка допустимости высоты орбиты
            if 300e3 <= altitude <= 2000e3:
                self._log_message(LOG_INFO, f"Допустимая орбита: {altitude} м")
                self._forward_event("orbit_limiter", event)
            else:
                self._log_message(LOG_ERROR, f"Ошибка орбиты: высота {altitude} м вне допустимого диапазона")

    def _forward_event(self, destination, event):
        new_event = Event(
            source=self._event_source_name,
            destination=destination,
            operation=event.operation,
            parameters=event.parameters
        )
        self._queues_dir.get_queue(destination).put(new_event)
