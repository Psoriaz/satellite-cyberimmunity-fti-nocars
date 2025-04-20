from multiprocessing import Queue
from queue import Empty
from src.system.custom_process import BaseCustomProcess
from src.system.queues_dir import QueuesDirectory
from src.system.event_types import Event
from src.system.config import (
    LOG_DEBUG,
    LOG_ERROR,
    LOG_INFO,
    DEFAULT_LOG_LEVEL,
    OPTICS_CONTROL_QUEUE_NAME,
    ORBIT_DRAWER_QUEUE_NAME,
    CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
    SECURITY_MONITOR_QUEUE_NAME,
)


class OpticsControl(BaseCustomProcess):
    """Модуль контроля оптики"""

    log_prefix = "[OPTIC]"
    event_source_name = OPTICS_CONTROL_QUEUE_NAME
    events_q_name = event_source_name

    def __init__(self, queues_dir, log_level=DEFAULT_LOG_LEVEL):
        super().__init__(
            log_prefix=OpticsControl.log_prefix,
            queues_dir=queues_dir,
            events_q_name=OpticsControl.event_source_name,
            event_source_name=OpticsControl.event_source_name,
            log_level=log_level,
        )

        self._zones_cache = []
        self._pending_photos = {}
        self._log_message(LOG_INFO, "Модуль управления оптикой создан")

    def _check_point_in_zones(self, lat, lon):
        """Проверка, находится ли точка в запрещенных зонах"""
        for zone in self._zones_cache:
            if (
                zone.lat_bot_left <= lat <= zone.lat_top_right
                and zone.lon_bot_left <= lon <= zone.lon_top_right
            ):
                self._log_message(
                    LOG_INFO,
                    f"Точка ({lat:.3f},{lon:.3f}) в запрещенной зоне",
                )
                return True

        self._log_message(
            LOG_DEBUG,
            f"Точка ({lat:.3f},{lon:.3f}) НЕ в запрещенной зоне",
        )
        return False

    def _check_events_q(self):
        """Обработка запросов"""
        while True:
            try:
                event = self._events_q.get_nowait()
                if not isinstance(event, Event):
                    continue

                match event.operation:
                    case "zones_update":
                        self._zones_cache = event.parameters
                        self._log_message(
                            LOG_INFO,
                            f"Получено обновление зон от ЦСУ: {len(self._zones_cache)} зон",
                        )

                    case "camera_update":
                        lat, lon = event.parameters
                        self._log_message(
                            LOG_INFO,
                            f"Получены координаты спутника: {lat:.3f}, {lon:.3f}",
                        )

                        # Проверяем координаты
                        is_restricted = self._check_point_in_zones(lat, lon)
                        self._pending_photos[(lat, lon)] = is_restricted

                        self._log_message(
                            LOG_INFO,
                            f"Результат локальной проверки ({lat:.3f},{lon:.3f}): {'ЗАПРЕЩЕНО' if is_restricted else 'разрешено'}",
                        )

                    case "post_photo":
                        lat, lon = event.parameters
                        self._log_message(
                            LOG_INFO,
                            f"Получен снимок с координатами: {lat:.3f}, {lon:.3f}",
                        )

                        # Проверяем координаты снимка
                        if (lat, lon) not in self._pending_photos:
                            # Если координаты не проверены, проверяем сейчас
                            is_restricted = self._check_point_in_zones(lat, lon)
                        else:
                            is_restricted = self._pending_photos[(lat, lon)]

                        if is_restricted:
                            self._log_message(
                                LOG_ERROR,
                                f"СНИМОК ЗАБЛОКИРОВАН - координаты в запрещенной зоне: {lat:.3f}, {lon:.3f}",
                            )

                            # Уведомляем ЦСУ о блокировке снимка
                            q: Queue = self._queues_dir.get_queue(
                                SECURITY_MONITOR_QUEUE_NAME
                            )
                            q.put(
                                Event(
                                    source=self.event_source_name,
                                    destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
                                    operation="photo_processed",
                                    parameters=(
                                        lat,
                                        lon,
                                        True,  # снимок запрещен
                                    ),
                                )
                            )
                        else:
                            # Снимок разрешен - отправляем на отрисовку и уведомляем ЦСУ
                            self._log_message(
                                LOG_INFO,
                                f"Снимок разрешен, отправка на отрисовку: {lat:.3f}, {lon:.3f}",
                            )

                            q: Queue = self._queues_dir.get_queue(
                                SECURITY_MONITOR_QUEUE_NAME
                            )
                            q.put(
                                Event(
                                    source=self.event_source_name,
                                    destination=ORBIT_DRAWER_QUEUE_NAME,
                                    operation="update_photo_map",
                                    parameters=(lat, lon),
                                )
                            )

                            # Уведомляем ЦСУ об успешной обработке снимка
                            q: Queue = self._queues_dir.get_queue(
                                SECURITY_MONITOR_QUEUE_NAME
                            )
                            q.put(
                                Event(
                                    source=self.event_source_name,
                                    destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
                                    operation="photo_processed",
                                    parameters=(
                                        lat,
                                        lon,
                                        False,  # снимок разрешен
                                    ),
                                )
                            )

                        # Очищаем данные о проверке
                        if (lat, lon) in self._pending_photos:
                            del self._pending_photos[(lat, lon)]

            except Empty:
                break
            except Exception as e:
                self._log_message(LOG_ERROR, f"Ошибка при обработке события: {e}")

    def run(self):
        self._log_message(LOG_INFO, "Модуль управления оптикой активен")
        while not self._quit:
            self._check_events_q()
            self._check_control_q()
