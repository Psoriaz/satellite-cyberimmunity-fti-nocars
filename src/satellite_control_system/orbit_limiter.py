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
    ORBIT_LIMITER_QUEUE_NAME,
    ORBIT_CONTROL_QUEUE_NAME,
    SECURITY_MONITOR_QUEUE_NAME,
)


class OrbitLimiter(BaseCustomProcess):
    """Модуль ограничений орбиты - устанавливает допустимые пределы параметров орбиты"""

    log_prefix = "[ORBIT_LIM]"
    event_source_name = ORBIT_LIMITER_QUEUE_NAME
    events_q_name = event_source_name

    def __init__(self, queues_dir, log_level=DEFAULT_LOG_LEVEL):
        super().__init__(
            log_prefix=OrbitLimiter.log_prefix,
            queues_dir=queues_dir,
            events_q_name=OrbitLimiter.events_q_name,
            event_source_name=OrbitLimiter.event_source_name,
            log_level=log_level,
        )
        # Устанавливаем ограничения орбиты по умолчанию
        self._orbit_limits = {
            "min_altitude": 300e3,  # Минимальная высота 300 км
            "max_altitude": 1500e3,  # Максимальная высота 1500 км
            "min_inclination": 0.0,  # Минимальное наклонение 0 радиан
            "max_inclination": 3.14,  # Максимальное наклонение pi радиан
            "max_delta_altitude": 200e3,  # Максимальное изменение высоты за раз
            "max_delta_inclination": 0.5,  # Максимальное изменение наклонения за раз
        }

        self._send_limits_to_control()

        self._log_message(LOG_INFO, "Модуль ограничений орбиты создан")

    def _send_limits_to_control(self):
        """Отправка ограничений в систему контроля орбиты"""
        try:
            q: Queue = self._queues_dir.get_queue(SECURITY_MONITOR_QUEUE_NAME)
            q.put(
                Event(
                    source=self.event_source_name,
                    destination=ORBIT_CONTROL_QUEUE_NAME,
                    operation="set_orbit_limits",
                    parameters=self._orbit_limits,
                )
            )
            self._log_message(
                LOG_INFO,
                f"Ограничения орбиты отправлены в систему контроля: "
                f"высота={self._orbit_limits['min_altitude']/1000:.1f}-{self._orbit_limits['max_altitude']/1000:.1f}км, "
                f"наклонение={self._orbit_limits['min_inclination']:.2f}-{self._orbit_limits['max_inclination']:.2f}",
            )
        except Exception as e:
            self._log_message(LOG_ERROR, f"Ошибка при отправке ограничений: {e}")

    def run(self):
        self._log_message(LOG_INFO, "Модуль ограничений орбиты запущен")
        while not self._quit:
            self._check_events_q()
            self._check_control_q()
