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
    SECURITY_MONITOR_QUEUE_NAME,
    RESTRICTED_ZONE_STORAGE_QUEUE_NAME,
    RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
    CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
    ORBIT_DRAWER_QUEUE_NAME,
)


class RestrictedZonesManager(BaseCustomProcess):
    """Модуль работы с запрещенными зонами"""

    log_prefix = "[ZONES_MGR]"
    event_source_name = RESTRICTED_ZONES_MANAGER_QUEUE_NAME
    events_q_name = event_source_name

    def __init__(self, queues_dir, log_level=DEFAULT_LOG_LEVEL):
        super().__init__(
            log_prefix=RestrictedZonesManager.log_prefix,
            queues_dir=queues_dir,
            events_q_name=RestrictedZonesManager.events_q_name,
            event_source_name=RestrictedZonesManager.event_source_name,
            log_level=log_level,
        )
        self._zones_cache = []
        self._checked_points = {}
        self._log_message(LOG_INFO, "Модуль работы с запрещенными зонами создан")
        self._request_zones_list()

    def _request_zones_list(self):
        """Запрос списка зон из хранилища"""
        q: Queue = self._queues_dir.get_queue(SECURITY_MONITOR_QUEUE_NAME)
        q.put(
            Event(
                source=self.event_source_name,
                destination=RESTRICTED_ZONE_STORAGE_QUEUE_NAME,
                operation="get_all_zones",
                parameters=None,
            )
        )

    def _check_point_in_zones(self, lat, lon):
        """Проверка, находится ли точка в запрещенных зонах"""
        point_key = (lat, lon)
        if point_key in self._checked_points:
            return self._checked_points[point_key]

        for zone in self._zones_cache:
            if (
                zone.lat_bot_left <= lat <= zone.lat_top_right
                and zone.lon_bot_left <= lon <= zone.lon_top_right
            ):
                self._log_message(
                    LOG_INFO,
                    f"Точка ({lat:.3f},{lon:.3f}) в запрещенной зоне: {zone.lat_bot_left:.3f},{zone.lon_bot_left:.3f} - {zone.lat_top_right:.3f},{zone.lon_top_right:.3f}",
                )

                # Сохраняем и возвращаем результат
                self._checked_points[point_key] = True
                return True

        # Если не нашли совпадений
        self._log_message(
            LOG_DEBUG,
            f"Точка ({lat},{lon}) НЕ в запрещенной зоне. Проверено {len(self._zones_cache)} зон",
        )

        # Сохраняем в кэш и возвращаем результат
        self._checked_points[point_key] = False
        return False

    def _update_central_system(self):
        """Отправка обновления о зонах в центральную систему"""
        try:
            q: Queue = self._queues_dir.get_queue(SECURITY_MONITOR_QUEUE_NAME)
            q.put(
                Event(
                    source=self.event_source_name,
                    destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
                    operation="zones_update",
                    parameters=self._zones_cache,
                )
            )
            self._log_message(
                LOG_INFO,
                f"Отправлено обновление зон в центральную систему: {len(self._zones_cache)} зон",
            )
        except Exception as e:
            self._log_message(
                LOG_ERROR, f"Ошибка при отправке обновления в центральную систему: {e}"
            )

    def _check_events_q(self):
        """Обработка запросов"""
        while True:
            try:
                event = self._events_q.get_nowait()
                if not isinstance(event, Event):
                    continue

                match event.operation:
                    case "add_zone_request":
                        # Запрос на добавление зоны
                        zone_id, lat1, lon1, lat2, lon2 = event.parameters
                        self._log_message(
                            LOG_INFO,
                            f"Запрос на добавление зоны: id={zone_id}, координаты={lat1:.3f},{lon1:.3f} - {lat2:.3f},{lon2:.3f}",
                        )

                        self._checked_points = {}

                        q: Queue = self._queues_dir.get_queue(
                            SECURITY_MONITOR_QUEUE_NAME
                        )
                        q.put(
                            Event(
                                source=self.event_source_name,
                                destination=RESTRICTED_ZONE_STORAGE_QUEUE_NAME,
                                operation="add_restricted_zone",
                                parameters=(zone_id, lat1, lon1, lat2, lon2),
                            )
                        )

                    case "draw_zone":
                        zone_id, zone = event.parameters
                        self._log_message(
                            LOG_INFO,
                            f"Запрос на отрисовку зоны: id={zone_id}",
                        )

                        q: Queue = self._queues_dir.get_queue(
                            SECURITY_MONITOR_QUEUE_NAME
                        )
                        q.put(
                            Event(
                                source=self.event_source_name,
                                destination=ORBIT_DRAWER_QUEUE_NAME,
                                operation="draw_restricted_zone",
                                parameters=zone,
                            )
                        )

                    case "remove_zone_request":
                        # Запрос на удаление зоны
                        zone_id = event.parameters

                        # Сбрасываем кэш проверенных точек при изменении зон
                        self._checked_points = {}

                        q: Queue = self._queues_dir.get_queue(
                            SECURITY_MONITOR_QUEUE_NAME
                        )
                        q.put(
                            Event(
                                source=self.event_source_name,
                                destination=RESTRICTED_ZONE_STORAGE_QUEUE_NAME,
                                operation="remove_restricted_zone",
                                parameters=zone_id,
                            )
                        )

                    case "check_point":
                        # Проверка точки на нахождение в запрещенных зонах
                        lat, lon = event.parameters
                        self._log_message(
                            LOG_INFO, f"Запрос на проверку точки: {lat:.3f}, {lon:.3f}"
                        )

                        # Проверяем, попадает ли точка в запрещенную зону
                        is_restricted = self._check_point_in_zones(lat, lon)

                        # Отправка результата проверки в центральную систему
                        q: Queue = self._queues_dir.get_queue(
                            SECURITY_MONITOR_QUEUE_NAME
                        )
                        q.put(
                            Event(
                                source=self.event_source_name,
                                destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
                                operation="point_check_result",
                                parameters=(lat, lon, is_restricted),
                            )
                        )

                        self._log_message(
                            LOG_INFO,
                            f"Результат проверки точки ({lat:.3f},{lon:.3f}): {'ЗАПРЕЩЕНА' if is_restricted else 'разрешена'}",
                        )

                    case "all_zones_data":
                        # Обновление зон
                        self._zones_cache = event.parameters
                        # Сбрасываем проверенные точки при обновлении зон
                        self._checked_points = {}

                        self._log_message(
                            LOG_INFO, f"Получен список из {len(self._zones_cache)} зон"
                        )

                        # Отправляем обновленные данные в центральную систему
                        self._update_central_system()

                        for i, zone in enumerate(self._zones_cache):
                            self._log_message(
                                LOG_DEBUG,
                                f"Зона {i}: {zone.lat_bot_left:.3f},{zone.lon_bot_left:.3f} - {zone.lat_top_right:.3f},{zone.lon_top_right:.3f}",
                            )

                    case "zone_operation_result":
                        # Обновление списка зон после изменения
                        operation, zone_id, success = event.parameters
                        self._log_message(
                            LOG_INFO,
                            f"Результат операции {operation} для зоны {zone_id}: {'успешно' if success else 'ошибка'}",
                        )
                        # Запрашиваем актуальный список зон
                        self._request_zones_list()

            except Empty:
                break
            except Exception as e:
                self._log_message(LOG_ERROR, f"Ошибка при обработке запроса: {e}")

    def run(self):
        self._log_message(LOG_INFO, "Модуль работы с запрещенными зонами запущен")
        while not self._quit:
            self._check_events_q()
            self._check_control_q()
