from src.system.custom_process import BaseCustomProcess
from src.system.event_types import Event
from src.satellite_control_system.restricted_zone import RestrictedZone

class RestrictedZonesStorage(BaseCustomProcess):
    def __init__(self, queues_dir, log_level):
        super().__init__(
            log_prefix="[RestrictedZonesStorage]",
            queues_dir=queues_dir,
            events_q_name="restricted_zone_storage",
            event_source_name="restricted_zone_storage",
            log_level=log_level
        )
        self.zones = []

    def run(self):
        self._log_message(0, "Хранилище запрещённых зон запущено")
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
        if event.operation == "set_restricted_zone":
            zone = event.parameters
            if isinstance(zone, RestrictedZone):
                self.zones.append(zone)
                self._log_message(0, f"Добавлена запрещённая зона: {zone}")
            else:
                self._log_message(2, "Ошибка: параметр не является RestrictedZone")
