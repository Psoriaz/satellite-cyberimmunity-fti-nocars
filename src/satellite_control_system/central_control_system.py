from src.system.custom_process import BaseCustomProcess
from src.system.event_types import Event

class CentralControlSystem(BaseCustomProcess):
    def __init__(self, queues_dir, log_level):
        super().__init__(
            log_prefix="[CentralControlSystem]",
            queues_dir=queues_dir,
            events_q_name="central_control_system",
            event_source_name="central_control_system",
            log_level=log_level
        )

    def run(self):
        self._log_message(0, "Центральная система управления запущена")
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
        self._log_message(0, f"Получено событие: {event.operation}")

        if event.operation == "change_orbit":
            self._forward_event("orbit_monitor", event)

        elif event.operation == "set_restricted_zone":
            self._forward_event("restricted_zone_storage", event)

        elif event.operation == "request_photo":
            self._forward_event("security_monitor", event)

        else:
            self._log_message(1, f"Неизвестная операция: {event.operation}")

    def _forward_event(self, destination, event):
        new_event = Event(
            source=self._event_source_name,
            destination=destination,
            operation=event.operation,
            parameters=event.parameters
        )
        self._queues_dir.get_queue(destination).put(new_event)
        self._log_message(0, f"Переслал событие {event.operation} в {destination}")
