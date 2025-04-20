from multiprocessing import Queue
from queue import Empty
from src.system.custom_process import BaseCustomProcess
from src.system.queues_dir import QueuesDirectory
from src.system.event_types import Event
from src.system.config import (
    LOG_DEBUG,
    LOG_ERROR,
    LOG_INFO,
    SECURITY_MONITOR_QUEUE_NAME,
    DEFAULT_LOG_LEVEL,
    CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
    OPTICS_CONTROL_QUEUE_NAME,
    RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
    CAMERA_QUEUE_NAME,
    ORBIT_MONITORING_QUEUE_NAME,
    IMAGE_STORAGE_QUEUE_NAME,
    SATELITE_QUEUE_NAME,
)
import time


class CentralControlSystem(BaseCustomProcess):
    """Центральная система управления - единая точка взаимодействия между доменами"""

    log_prefix = "[CENTRAL]"
    event_source_name = CENTRAL_CONTROL_SYSTEM_QUEUE_NAME
    events_q_name = event_source_name

    def __init__(self, queues_dir, log_level=DEFAULT_LOG_LEVEL):
        super().__init__(
            log_prefix=CentralControlSystem.log_prefix,
            queues_dir=queues_dir,
            events_q_name=CentralControlSystem.events_q_name,
            event_source_name=CentralControlSystem.event_source_name,
            log_level=log_level,
        )
        self._restricted_zones_cache = []
        self._log_message(LOG_INFO, "Центральная система управления создана")

    def _check_events_q(self):
        """Обработка запросов от других модулей"""
        while True:
            try:
                event = self._events_q.get_nowait()
                if not isinstance(event, Event):
                    continue

                match event.operation:
                    # Обработка команд от клиента
                    case "request_photo":
                        self._log_message(
                            LOG_INFO, "Получен запрос на фотографирование"
                        )
                        # Перенаправляем запрос в камеру
                        q: Queue = self._queues_dir.get_queue(
                            SECURITY_MONITOR_QUEUE_NAME
                        )
                        q.put(
                            Event(
                                source=self.event_source_name,
                                destination=CAMERA_QUEUE_NAME,
                                operation="request_photo",
                                parameters=None,
                            )
                        )

                    case "add_zone_request":
                        self._log_message(
                            LOG_INFO, "Получен запрос на добавление запрещенной зоны"
                        )
                        # Перенаправляем запрос в менеджер зон
                        q: Queue = self._queues_dir.get_queue(
                            SECURITY_MONITOR_QUEUE_NAME
                        )
                        q.put(
                            Event(
                                source=self.event_source_name,
                                destination=RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
                                operation="add_zone_request",
                                parameters=event.parameters,
                            )
                        )

                    case "remove_zone_request":
                        self._log_message(
                            LOG_INFO, "Получен запрос на удаление запрещенной зоны"
                        )
                        # Перенаправляем запрос в менеджер зон
                        q: Queue = self._queues_dir.get_queue(
                            SECURITY_MONITOR_QUEUE_NAME
                        )
                        q.put(
                            Event(
                                source=self.event_source_name,
                                destination=RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
                                operation="remove_zone_request",
                                parameters=event.parameters,
                            )
                        )

                    case "change_orbit":
                        self._log_message(
                            LOG_INFO, "Получен запрос на изменение орбиты"
                        )
                        # Перенаправляем запрос в модуль мониторинга орбиты
                        q: Queue = self._queues_dir.get_queue(
                            SECURITY_MONITOR_QUEUE_NAME
                        )
                        q.put(
                            Event(
                                source=self.event_source_name,
                                destination=ORBIT_MONITORING_QUEUE_NAME,
                                operation="check_orbit_params",
                                parameters=event.parameters,
                            )
                        )
                        self._log_message(
                            LOG_INFO,
                            "Запрос на изменение орбиты передан в модуль мониторинга орбиты",
                        )

                    case "zones_update":
                        self._zones_cache = event.parameters
                        self._log_message(
                            LOG_INFO,
                            f"Получено обновление запрещенных зон: {len(self._zones_cache)} зон",
                        )

                        # Передаем информацию в модуль оптики
                        q: Queue = self._queues_dir.get_queue(
                            SECURITY_MONITOR_QUEUE_NAME
                        )
                        q.put(
                            Event(
                                source=self.event_source_name,
                                destination=OPTICS_CONTROL_QUEUE_NAME,
                                operation="zones_update",
                                parameters=self._zones_cache,
                            )
                        )

                    # Сообщения от камеры - проверяем координаты и передаем в оптику
                    case "camera_update":
                        lat, lon = event.parameters
                        self._log_message(
                            LOG_INFO, f"Получены координаты от камеры: {lat}, {lon}"
                        )

                        # Передаем координаты в модуль оптики для проверки и обработки
                        q: Queue = self._queues_dir.get_queue(
                            SECURITY_MONITOR_QUEUE_NAME
                        )
                        q.put(
                            Event(
                                source=self.event_source_name,
                                destination=OPTICS_CONTROL_QUEUE_NAME,
                                operation="camera_update",
                                parameters=(lat, lon),
                            )
                        )

                    case "post_photo":
                        lat, lon = event.parameters
                        self._log_message(
                            LOG_INFO, f"Получена фотография от камеры: {lat}, {lon}"
                        )

                        # Передаем в модуль оптики
                        q: Queue = self._queues_dir.get_queue(
                            SECURITY_MONITOR_QUEUE_NAME
                        )
                        q.put(
                            Event(
                                source=self.event_source_name,
                                destination=OPTICS_CONTROL_QUEUE_NAME,
                                operation="post_photo",
                                parameters=(lat, lon),
                            )
                        )

                    case "orbit_change_approved":
                        # Получено одобрение изменения орбиты
                        altitude, inclination, raan = event.parameters
                        self._log_message(
                            LOG_INFO,
                            f"Получено одобрение изменения орбиты: высота={altitude/1000:.1f}км, "
                            f"наклонение={inclination:.3f}, RAAN={raan:.3f}",
                        )
                        q: Queue = self._queues_dir.get_queue(
                            SECURITY_MONITOR_QUEUE_NAME
                        )
                        q.put(
                            Event(
                                source=self.event_source_name,
                                destination=SATELITE_QUEUE_NAME,
                                operation="change_orbit",
                                parameters=(altitude, inclination, raan),
                            )
                        )

                    case "orbit_change_rejected":
                        # Получен отказ в изменении орбиты
                        violations = event.parameters
                        self._log_message(
                            LOG_ERROR,
                            f"Запрос на изменение орбиты отклонен из-за нарушений ограничений:",
                        )
                        for violation in violations:
                            self._log_message(LOG_ERROR, f"- {violation}")

                    case "orbit_changed":
                        # Получено уведомление об изменении орбиты
                        altitude, inclination, raan = event.parameters
                        self._log_message(
                            LOG_INFO,
                            f"Орбита изменена: высота={altitude/1000:.1f}км, "
                            f"наклонение={inclination:.3f}, RAAN={raan:.3f}",
                        )

                    case "photo_processed":
                        # Изображение обработано оптическим модулем
                        lat, lon, is_restricted = event.parameters

                        # Если изображение не в запрещенной зоне, сохраняем его
                        if not is_restricted:
                            self._log_message(
                                LOG_INFO,
                                f"Снимок разрешен, отправляем на сохранение: ({lat:.3f},{lon:.3f})",
                            )
                            # Отправляем в хранилище изображений
                            q: Queue = self._queues_dir.get_queue(
                                IMAGE_STORAGE_QUEUE_NAME
                            )
                            q.put(
                                Event(
                                    source=self.event_source_name,
                                    destination=IMAGE_STORAGE_QUEUE_NAME,
                                    operation="save_image",
                                    parameters=(lat, lon, time.time()),
                                )
                            )
                        else:
                            self._log_message(
                                LOG_ERROR,
                                f"Снимок заблокирован - находится в запрещенной зоне: ({lat:.3f},{lon:.3f})",
                            )

                    case "image_saved":
                        # Получено уведомление о сохранении изображения
                        lat, lon, timestamp = event.parameters
                        self._log_message(
                            LOG_INFO,
                            f"Изображение успешно сохранено: ({lat:.3f},{lon:.3f}), время={timestamp}",
                        )

                    case "get_all_images":
                        self._log_message(
                            LOG_INFO, "Получен запрос на получение всех изображений"
                        )
                        q: Queue = self._queues_dir.get_queue(
                            SECURITY_MONITOR_QUEUE_NAME
                        )
                        q.put(
                            Event(
                                source=self.event_source_name,
                                destination=IMAGE_STORAGE_QUEUE_NAME,
                                operation="get_all_images",
                                parameters=None,
                            )
                        )

                    case _:
                        self._log_message(
                            LOG_DEBUG,
                            f"Получено событие: {event.operation} от {event.source}",
                        )

            except Empty:
                break
            except Exception as e:
                self._log_message(LOG_ERROR, f"Ошибка при обработке события: {e}")

    def run(self):
        self._log_message(LOG_INFO, "Центральная система управления запущена")
        while not self._quit:
            self._check_events_q()
            self._check_control_q()
