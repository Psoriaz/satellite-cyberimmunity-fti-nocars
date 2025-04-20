from multiprocessing import Queue
from queue import Empty
import time
from src.system.custom_process import BaseCustomProcess
from src.system.queues_dir import QueuesDirectory
from src.system.event_types import Event
from src.system.config import (
    LOG_DEBUG,
    LOG_ERROR,
    LOG_INFO,
    DEFAULT_LOG_LEVEL,
    IMAGE_STORAGE_QUEUE_NAME,
    CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
    SECURITY_MONITOR_QUEUE_NAME,
)


class ImageStorage(BaseCustomProcess):
    """
    Хранилище изображений - сохраняет и предоставляет доступ к снимкам
    'Изображения' представляют собой кортеж в виде (lat, lon, timestamp)
    """

    log_prefix = "[IMG_STOR]"
    event_source_name = IMAGE_STORAGE_QUEUE_NAME
    events_q_name = event_source_name

    def __init__(self, queues_dir, log_level=DEFAULT_LOG_LEVEL):
        super().__init__(
            log_prefix=ImageStorage.log_prefix,
            queues_dir=queues_dir,
            events_q_name=ImageStorage.events_q_name,
            event_source_name=ImageStorage.event_source_name,
            log_level=log_level,
        )
        # Хранилище изображений
        self._images = {}
        self._log_message(LOG_INFO, "Хранилище изображений создано")

    def _check_events_q(self):
        """Обработка запросов"""
        while True:
            try:
                event = self._events_q.get_nowait()
                if not isinstance(event, Event):
                    continue

                match event.operation:
                    case "save_image":
                        # Получен снимок для сохранения
                        if len(event.parameters) >= 2:
                            lat, lon = event.parameters[0], event.parameters[1]
                            # Если есть timestamp, используем его, иначе текущее время
                            timestamp = (
                                event.parameters[2]
                                if len(event.parameters) > 2
                                else time.time()
                            )

                            # Сохраняем изображение
                            image_key = (lat, lon)
                            self._images[image_key] = {
                                "timestamp": timestamp,
                                "source": event.source,
                            }

                            self._log_message(
                                LOG_INFO,
                                f"Сохранено изображение с координатами ({lat:.3f},{lon:.3f}), timestamp={timestamp}",
                            )

                            # Уведомляем ЦСУ о сохранении снимка
                            q: Queue = self._queues_dir.get_queue(
                                SECURITY_MONITOR_QUEUE_NAME
                            )
                            q.put(
                                Event(
                                    source=self.event_source_name,
                                    destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
                                    operation="image_saved",
                                    parameters=(lat, lon, timestamp),
                                )
                            )
                        else:
                            self._log_message(
                                LOG_ERROR,
                                f"Недостаточно параметров для сохранения изображения: {event.parameters}",
                            )

                    case "get_all_images":
                        # Запрос на получение всех сохраненных изображений
                        images_list = []
                        for (lat, lon), data in self._images.items():
                            images_list.append((lat, lon, data["timestamp"]))

                        self._log_message(
                            LOG_INFO,
                            f"Запрошен список всех изображений ({len(images_list)} шт.)",
                        )
                        self._log_message(
                            LOG_INFO,
                            f"Полученные изображения: {images_list}",
                        )

            except Empty:
                break
            except Exception as e:
                self._log_message(LOG_ERROR, f"Ошибка при обработке запроса: {e}")

    def run(self):
        self._log_message(LOG_INFO, "Хранилище изображений запущено")
        while not self._quit:
            self._check_events_q()
            self._check_control_q()
