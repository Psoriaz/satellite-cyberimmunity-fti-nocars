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
    ORBIT_MONITORING_QUEUE_NAME,
    ORBIT_CONTROL_QUEUE_NAME,
    CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
    SECURITY_MONITOR_QUEUE_NAME,
)
import numpy as np


class OrbitMonitoring(BaseCustomProcess):
    """Модуль мониторинга орбиты - отслеживает текущее состояние орбиты"""

    log_prefix = "[ORBIT_MON]"
    event_source_name = ORBIT_MONITORING_QUEUE_NAME
    events_q_name = event_source_name

    def __init__(
        self,
        queues_dir,
        log_level=DEFAULT_LOG_LEVEL,
        initial_altitude=1000e3,
        initial_inclination=np.pi / 3,
        initial_raan=0,
    ):
        super().__init__(
            log_prefix=OrbitMonitoring.log_prefix,
            queues_dir=queues_dir,
            events_q_name=OrbitMonitoring.events_q_name,
            event_source_name=OrbitMonitoring.event_source_name,
            log_level=log_level,
        )
        self._current_orbit = {
            "altitude": initial_altitude,
            "inclination": initial_inclination,
            "raan": initial_raan,
        }
        self._log_message(LOG_INFO, "Модуль мониторинга орбиты создан")
        self._log_message(
            LOG_INFO,
            f"Начальные параметры орбиты: высота={initial_altitude/1000:.1f}км, "
            f"наклонение={initial_inclination:.3f}, RAAN={initial_raan:.3f}",
        )

    def _check_events_q(self):
        """Обработка запросов"""
        while True:
            try:
                event = self._events_q.get_nowait()
                if not isinstance(event, Event):
                    continue

                match event.operation:
                    case "check_orbit_params":
                        # Запрос на проверку параметров орбиты от ЦСУ
                        new_altitude, new_inclination, new_raan = event.parameters
                        self._log_message(
                            LOG_INFO,
                            f"Запрос на проверку параметров орбиты: высота={new_altitude/1000:.1f}км, "
                            f"наклонение={new_inclination:.3f}, RAAN={new_raan:.3f}",
                        )

                        # Проверка текущего состояния орбиты
                        if self._current_orbit["altitude"] is None:
                            self._log_message(
                                LOG_ERROR,
                                "Текущие параметры орбиты неизвестны, используем начальные",
                            )

                        # Передаем запрос в систему контроля орбиты с текущими параметрами
                        q: Queue = self._queues_dir.get_queue(
                            SECURITY_MONITOR_QUEUE_NAME
                        )
                        q.put(
                            Event(
                                source=self.event_source_name,
                                destination=ORBIT_CONTROL_QUEUE_NAME,
                                operation="check_orbit_change",
                                parameters=(
                                    new_altitude,
                                    new_inclination,
                                    self._current_orbit["altitude"],
                                    self._current_orbit["inclination"],
                                ),
                            )
                        )
                        self._log_message(
                            LOG_INFO,
                            f"Параметры переданы в систему контроля орбиты. "
                            f"Текущая высота: {self._current_orbit['altitude']/1000:.1f}км",
                        )

            except Empty:
                break
            except Exception as e:
                self._log_message(LOG_ERROR, f"Ошибка при обработке запроса: {e}")

    def run(self):
        self._log_message(LOG_INFO, "Модуль мониторинга орбиты запущен")

        while not self._quit:
            self._check_events_q()
            self._check_control_q()
