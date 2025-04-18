from src.system.custom_process import BaseCustomProcess
from src.system.event_types import Event
from src.system.config import LOG_INFO, LOG_ERROR, LOG_DEBUG, DEFAULT_LOG_LEVEL
from src.system.queues_dir import QueuesDirectory

class ImageStorage(BaseCustomProcess):
    """ Модуль хранения полученных снимков """
    log_prefix = "[ImageStorage]"
    event_source_name = "image_storage"
    events_q_name = event_source_name

    def __init__(self, queues_dir: QueuesDirectory, log_level: int = DEFAULT_LOG_LEVEL):
        super().__init__(
            log_prefix=ImageStorage.log_prefix,
            queues_dir=queues_dir,
            events_q_name=ImageStorage.event_source_name,
            event_source_name=ImageStorage.event_source_name,
            log_level=log_level
        )

        self._log_message(LOG_INFO, "Хранилище изображений создано")

        # Список всех снимков [(lat, lon, timestamp)]
        self.photos = []

    def run(self):
        self._log_message(LOG_INFO, "Хранилище изображений активно")
        while not self._quit:
            try:
                self._check_events_q()
                self._check_control_q()
            except Exception as e:
                self._log_message(LOG_ERROR, f"Ошибка в модуле хранения изображений: {e}")

    def _check_events_q(self):
        """Проверяем события"""
        while True:
            try:
                event: Event = self._events_q.get_nowait()

                if not isinstance(event, Event):
                    return

                self._handle_event(event)
            except Exception:
                break

    def _handle_event(self, event: Event):
        """Обрабатываем полученные события"""
        if event.operation == "save_photo":
            self._save_photo(event.parameters)
        elif event.operation == "get_all_photos":
            self._send_photos_list(event.source)
        else:
            self._log_message(LOG_ERROR, f"Неизвестная операция: {event.operation}")

    def _save_photo(self, photo_info):
        """Сохраняем новый снимок"""
        if not isinstance(photo_info, tuple) or len(photo_info) != 3:
            self._log_message(LOG_ERROR, f"Неверный формат фото данных: {photo_info}")
            return

        self.photos.append(photo_info)
        lat, lon, timestamp = photo_info
        self._log_message(LOG_INFO, f"Фото сохранено: lat={lat}, lon={lon}, time={timestamp}")

    def _send_photos_list(self, requester_queue_name):
        """Отправляем список всех снимков по запросу"""
        try:
            requester_q = self._queues_dir.get_queue(requester_queue_name)
            requester_q.put(Event(
                source=self._event_source_name,
                destination=requester_queue_name,
                operation="photos_list",
                parameters=self.photos
            ))
            self._log_message(LOG_INFO, f"Отправлен список снимков в {requester_queue_name}")
        except KeyError:
            self._log_message(LOG_ERROR, f"Очередь для отправки списка фото '{requester_queue_name}' не найдена. Выведем список в консоль:")
            self._log_message(LOG_INFO, f"Список фото: {self.photos}")

