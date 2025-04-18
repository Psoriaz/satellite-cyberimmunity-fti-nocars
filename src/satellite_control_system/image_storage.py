from src.system.custom_process import BaseCustomProcess
from src.system.event_types import Event

#Написал для тестов
class ImageStorage(BaseCustomProcess):
    def __init__(self, queues_dir, log_level):
        super().__init__(
            log_prefix="[ImageStorage]",
            queues_dir=queues_dir,
            events_q_name="image_storage",
            event_source_name="image_storage",
            log_level=log_level
        )

    def run(self):
        self._log_message(0, "Хранилище изображений запущено")
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
        # Пока просто логируем получение событий
