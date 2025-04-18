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
    ORBIT_DRAWER_QUEUE_NAME,
    RESTRICTED_ZONE_STORAGE_QUEUE_NAME,
    RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
)
from src.satellite_control_system.restricted_zone import RestrictedZone


class RestrictedZonesStorage(BaseCustomProcess):
    """Хранилище запрещенных зон (зеленый домен)"""

    log_prefix = "[ZONES]"
    event_source_name = RESTRICTED_ZONE_STORAGE_QUEUE_NAME
    events_q_name = event_source_name

    def __init__(self, queues_dir, log_level=DEFAULT_LOG_LEVEL):
        super().__init__(
            log_prefix=RestrictedZonesStorage.log_prefix,
            queues_dir=queues_dir,
            events_q_name=RestrictedZonesStorage.events_q_name,
            event_source_name=RestrictedZonesStorage.event_source_name,
            log_level=log_level,
        )
        self._zones = {}
        self._log_message(LOG_INFO, "Хранилище запрещенных зон создано")

    def _check_events_q(self):
        """Обработка запросов"""
        while True:
            try:
                event = self._events_q.get_nowait()
                if not isinstance(event, Event):
                    continue

                # Проверка источника запроса
                if event.source != RESTRICTED_ZONES_MANAGER_QUEUE_NAME:
                    self._log_message(LOG_ERROR, f"Отклонен запрос от {event.source}")
                    continue

                match event.operation:
                    case "add_restricted_zone":
                        # Добавление зоны
                        zone_id, lat1, lon1, lat2, lon2 = event.parameters

                        # Проверка существования зоны
                        if zone_id in self._zones:
                            self._log_message(
                                LOG_INFO, f"Зона id={zone_id} уже существует"
                            )
                            continue

                        try:
                            # Создание зоны
                            zone = RestrictedZone(lat1, lon1, lat2, lon2)
                            self._zones[zone_id] = zone
                            self._log_message(
                                LOG_INFO,
                                f"Добавлена зона id={zone_id}, lat1={lat1:.3f}, lon1={lon1:.3f}, lat2={lat2:.3f}, lon2={lon2:.3f}",
                            )

                            # Отрисовка зоны
                            drawer_q = self._queues_dir.get_queue(
                                ORBIT_DRAWER_QUEUE_NAME
                            )
                            drawer_q.put(
                                Event(
                                    source=self.event_source_name,
                                    destination=ORBIT_DRAWER_QUEUE_NAME,
                                    operation="draw_restricted_zone",
                                    parameters=zone,
                                )
                            )

                            # Уведомление об успехе
                            manager_q = self._queues_dir.get_queue(
                                RESTRICTED_ZONES_MANAGER_QUEUE_NAME
                            )
                            manager_q.put(
                                Event(
                                    source=self.event_source_name,
                                    destination=RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
                                    operation="zone_operation_result",
                                    parameters=("add", zone_id, True),
                                )
                            )

                        except Exception as e:
                            self._log_message(LOG_ERROR, f"Ошибка: {e}")

                    case "remove_restricted_zone":
                        # Удаление зоны
                        zone_id = event.parameters

                        if zone_id not in self._zones:
                            self._log_message(
                                LOG_ERROR, f"Зона id={zone_id} не найдена"
                            )
                            continue

                        zone = self._zones[zone_id]
                        del self._zones[zone_id]

                        # Обновление отображения
                        drawer_q = self._queues_dir.get_queue(ORBIT_DRAWER_QUEUE_NAME)
                        drawer_q.put(
                            Event(
                                source=self.event_source_name,
                                destination=ORBIT_DRAWER_QUEUE_NAME,
                                operation="remove_restricted_zone",
                                parameters=zone,
                            )
                        )

                        # Уведомление об успехе
                        manager_q = self._queues_dir.get_queue(
                            RESTRICTED_ZONES_MANAGER_QUEUE_NAME
                        )
                        manager_q.put(
                            Event(
                                source=self.event_source_name,
                                destination=RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
                                operation="zone_operation_result",
                                parameters=("remove", zone_id, True),
                            )
                        )

                    case "get_all_zones":
                        # Отправка списка зон
                        zones_list = list(self._zones.values())
                        manager_q = self._queues_dir.get_queue(
                            RESTRICTED_ZONES_MANAGER_QUEUE_NAME
                        )
                        manager_q.put(
                            Event(
                                source=self.event_source_name,
                                destination=RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
                                operation="all_zones_data",
                                parameters=zones_list,
                            )
                        )

            except Empty:
                break

    def run(self):
        self._log_message(LOG_INFO, "Хранилище зон ограничений запущено")
        while not self._quit:
            self._check_events_q()
            self._check_control_q()
