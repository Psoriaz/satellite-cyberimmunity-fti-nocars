from src.system.custom_process import BaseCustomProcess
from src.system.event_types import Event
from src.system.config import LOG_DEBUG, LOG_ERROR, LOG_INFO, DEFAULT_LOG_LEVEL
from src.system.queues_dir import QueuesDirectory

class SecurityMonitor(BaseCustomProcess):
    """ Монитор безопасности """

    log_prefix = "[SecurityMonitor]"
    event_source_name = "security_monitor"
    events_q_name = event_source_name

    def __init__(self, queues_dir: QueuesDirectory, log_level: int = DEFAULT_LOG_LEVEL):
        super().__init__(
            log_prefix=SecurityMonitor.log_prefix,
            queues_dir=queues_dir,
            events_q_name=SecurityMonitor.event_source_name,
            event_source_name=SecurityMonitor.event_source_name,
            log_level=log_level
        )
        self._log_message(LOG_INFO, "Монитор безопасности запущен")

    def run(self):
        while not self._quit:
            try:
                self._check_events_q()
                self._check_control_q()
            except Exception as e:
                self._log_message(LOG_ERROR, f"Ошибка в SecurityMonitor: {e}")

    def _check_events_q(self):
        while True:
            try:
                event: Event = self._events_q.get_nowait()

                if not isinstance(event, Event):
                    return

                self._handle_event(event)
            except Exception:
                break

    def _handle_event(self, event: Event):
        """Проверяем разрешённые операции"""
        self._log_message(LOG_INFO, f"Монитор получил событие: {event.operation}")

        if event.operation == "request_photo":
            # Маршрутизируем запрос фото в optics_control
            try:
                optics_q = self._queues_dir.get_queue("optics_control")
                optics_q.put(Event(
                    source=self._event_source_name,
                    destination="optics_control",
                    operation="request_photo",
                    parameters=None
                ))
                self._log_message(LOG_INFO, "Перенаправили запрос съёмки в optics_control")
            except KeyError:
                self._log_message(LOG_ERROR, "Очередь optics_control не найдена!")

        else:
            self._log_message(LOG_ERROR, f"Неизвестная или запрещённая операция: {event.operation}")
