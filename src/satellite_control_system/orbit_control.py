from multiprocessing import Queue
from queue import Empty
from src.system.custom_process import BaseCustomProcess
from src.system.queues_dir import QueuesDirectory
from src.system.event_types import Event
from src.system.config import (
    LOG_ERROR,
    LOG_INFO,
    DEFAULT_LOG_LEVEL,
    ORBIT_CONTROL_QUEUE_NAME,
    CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
    SECURITY_MONITOR_QUEUE_NAME,
)


class OrbitControl(BaseCustomProcess):
    """Система контроля орбиты - проверяет и исполняет запросы на изменение орбиты"""

    log_prefix = "[ORBIT_CTRL]"
    event_source_name = ORBIT_CONTROL_QUEUE_NAME
    events_q_name = event_source_name

    def __init__(self, queues_dir, log_level=DEFAULT_LOG_LEVEL):
        super().__init__(
            log_prefix=OrbitControl.log_prefix,
            queues_dir=queues_dir,
            events_q_name=OrbitControl.events_q_name,
            event_source_name=OrbitControl.event_source_name,
            log_level=log_level,
        )
        self._orbit_limits = {}
        self._log_message(LOG_INFO, "Система контроля орбиты создана")

    def _check_orbit_parameters(
        self,
        new_altitude,
        new_inclination,
        current_altitude=None,
        current_inclination=None,
    ):
        """Проверка параметров орбиты на соответствие ограничениям"""
        violations = []

        # Проверка высоты
        if new_altitude < self._orbit_limits["min_altitude"]:
            violations.append(
                f"Высота орбиты {new_altitude/1000:.1f}км меньше минимально допустимой {self._orbit_limits['min_altitude']/1000:.1f}км"
            )

        if new_altitude > self._orbit_limits["max_altitude"]:
            violations.append(
                f"Высота орбиты {new_altitude/1000:.1f}км больше максимально допустимой {self._orbit_limits['max_altitude']/1000:.1f}км"
            )

        # Проверка наклонения
        if new_inclination < self._orbit_limits["min_inclination"]:
            violations.append(
                f"Наклонение орбиты {new_inclination:.3f} меньше минимально допустимого {self._orbit_limits['min_inclination']:.3f}"
            )

        if new_inclination > self._orbit_limits["max_inclination"]:
            violations.append(
                f"Наклонение орбиты {new_inclination:.3f} больше максимально допустимого {self._orbit_limits['max_inclination']:.3f}"
            )

        # Проверка изменения параметров относительно текущих (если известны)
        if current_altitude is not None and "max_delta_altitude" in self._orbit_limits:
            delta_altitude = abs(new_altitude - current_altitude)
            if delta_altitude > self._orbit_limits["max_delta_altitude"]:
                violations.append(
                    f"Изменение высоты {delta_altitude/1000:.1f}км превышает допустимое {self._orbit_limits['max_delta_altitude']/1000:.1f}км"
                )

        if (
            current_inclination is not None
            and "max_delta_inclination" in self._orbit_limits
        ):
            delta_inclination = abs(new_inclination - current_inclination)
            if delta_inclination > self._orbit_limits["max_delta_inclination"]:
                violations.append(
                    f"Изменение наклонения {delta_inclination:.3f} превышает допустимое {self._orbit_limits['max_delta_inclination']:.3f}"
                )

        return violations

    def _check_events_q(self):
        """Обработка запросов"""
        while True:
            try:
                event = self._events_q.get_nowait()
                if not isinstance(event, Event):
                    continue

                match event.operation:
                    case "set_orbit_limits":
                        # Установка ограничений орбиты от модуля ограничителя
                        self._orbit_limits = event.parameters
                        self._log_message(
                            LOG_INFO,
                            f"Установлены новые ограничения орбиты: "
                            f"высота={self._orbit_limits['min_altitude']/1000:.1f}-{self._orbit_limits['max_altitude']/1000:.1f}км",
                        )

                    case "check_orbit_change":
                        # Проверка запроса на изменение орбиты
                        params = event.parameters
                        new_altitude, new_inclination, new_raan = params[0:3]
                        current_params = params[3:6]

                        self._log_message(
                            LOG_INFO,
                            f"Проверка запроса на изменение орбиты: высота={new_altitude/1000:.1f}км, "
                            f"наклонение={new_inclination:.3f}, RAAN={new_raan:.3f}",
                        )

                        # Проверка параметров на соответствие ограничениям
                        violations = self._check_orbit_parameters(
                            new_altitude, new_inclination, new_raan, *current_params
                        )

                        if violations:
                            # Есть нарушения ограничений - отклоняем запрос
                            self._log_message(
                                LOG_ERROR, "Запрос на изменение орбиты отклонен:"
                            )
                            for violation in violations:
                                self._log_message(LOG_ERROR, f"- {violation}")

                            # Уведомляем ЦСУ об отклонении запроса
                            q: Queue = self._queues_dir.get_queue(
                                SECURITY_MONITOR_QUEUE_NAME
                            )
                            q.put(
                                Event(
                                    source=self.event_source_name,
                                    destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
                                    operation="orbit_change_rejected",
                                    parameters=violations,
                                )
                            )
                        else:
                            # Ограничения соблюдены - разрешаем изменение орбиты
                            self._log_message(
                                LOG_INFO,
                                "Запрос на изменение орбиты соответствует ограничениям, отправляем в ЦСУ",
                            )

                            # Уведомляем ЦСУ об одобрении запроса
                            q: Queue = self._queues_dir.get_queue(
                                SECURITY_MONITOR_QUEUE_NAME
                            )
                            q.put(
                                Event(
                                    source=self.event_source_name,
                                    destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
                                    operation="orbit_change_approved",
                                    parameters=(
                                        new_altitude,
                                        new_inclination,
                                        new_raan,
                                    ),
                                )
                            )

            except Empty:
                break
            except Exception as e:
                self._log_message(LOG_ERROR, f"Ошибка при обработке запроса: {e}")

    def run(self):
        self._log_message(LOG_INFO, "Система контроля орбиты запущена")
        while not self._quit:
            self._check_events_q()
            self._check_control_q()
