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
    SATELITE_QUEUE_NAME,
)


class OrbitMonitoring(BaseCustomProcess):
    """Модуль мониторинга орбиты - отслеживает текущее состояние орбиты"""

    log_prefix = "[ORBIT_MON]"
    event_source_name = ORBIT_MONITORING_QUEUE_NAME
    events_q_name = event_source_name

    def __init__(self, queues_dir, log_level=DEFAULT_LOG_LEVEL):
        super().__init__(
            log_prefix=OrbitMonitoring.log_prefix,
            queues_dir=queues_dir,
            events_q_name=OrbitMonitoring.events_q_name,
            event_source_name=OrbitMonitoring.event_source_name,
            log_level=log_level,
        )
        # Текущие параметры орбиты - инициализируем начальными значениями
        self._current_orbit = {
            "altitude": 1000e3,  # Начальное значение высоты
            "inclination": None,
            "raan": None,
        }
        self._log_message(LOG_INFO, "Модуль мониторинга орбиты создан")

        # Запрашиваем актуальные параметры орбиты при старте
        self._request_orbit_params()

    def _request_orbit_params(self):
        """Запрос текущих параметров орбиты у спутника"""
        try:
            satellite_q = self._queues_dir.get_queue(SATELITE_QUEUE_NAME)
            satellite_q.put(
                Event(
                    source=self.event_source_name,
                    destination=SATELITE_QUEUE_NAME,
                    operation="get_orbit_params",
                    parameters=None,
                )
            )
            self._log_message(LOG_INFO, "Запрошены текущие параметры орбиты")
        except Exception as e:
            self._log_message(LOG_ERROR, f"Ошибка при запросе параметров орбиты: {e}")

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
                        orbit_control_q = self._queues_dir.get_queue(
                            ORBIT_CONTROL_QUEUE_NAME
                        )
                        orbit_control_q.put(
                            Event(
                                source=self.event_source_name,
                                destination=ORBIT_CONTROL_QUEUE_NAME,
                                operation="check_orbit_change",
                                parameters=(
                                    new_altitude,
                                    new_inclination,
                                    new_raan,
                                    self._current_orbit["altitude"],
                                    self._current_orbit["inclination"],
                                    self._current_orbit["raan"],
                                ),
                            )
                        )
                        self._log_message(
                            LOG_INFO,
                            f"Параметры переданы в систему контроля орбиты. "
                            f"Текущая высота: {self._current_orbit['altitude']/1000:.1f}км",
                        )

                    # Для обработки ответа от спутника используем правильное имя операции
                    case "update_orbit_data":
                        # Получены параметры орбиты от спутника
                        altitude, inclination, raan = event.parameters

                        old_altitude = self._current_orbit["altitude"]
                        self._current_orbit = {
                            "altitude": altitude,
                            "inclination": inclination,
                            "raan": raan,
                        }

                        self._log_message(
                            LOG_INFO,
                            f"Получены параметры орбиты от спутника: высота={altitude/1000:.1f}км, "
                            f"наклонение={inclination:.3f}, RAAN={raan:.3f}",
                        )

                        # Если это первое получение или изменение орбиты, уведомляем ЦСУ
                        if old_altitude is None or old_altitude != altitude:
                            central_q = self._queues_dir.get_queue(
                                CENTRAL_CONTROL_SYSTEM_QUEUE_NAME
                            )
                            central_q.put(
                                Event(
                                    source=self.event_source_name,
                                    destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
                                    operation="orbit_changed",
                                    parameters=(altitude, inclination, raan),
                                )
                            )
                            self._log_message(
                                LOG_INFO,
                                "Отправлено уведомление об обновлении орбиты в ЦСУ",
                            )

                    # Альтернативное имя операции, которое может прийти от спутника
                    case "post_orbit_params":
                        # Получены параметры орбиты от спутника
                        altitude, inclination, raan = event.parameters

                        old_altitude = self._current_orbit["altitude"]
                        self._current_orbit = {
                            "altitude": altitude,
                            "inclination": inclination,
                            "raan": raan,
                        }

                        self._log_message(
                            LOG_INFO,
                            f"Получены параметры орбиты от спутника (post): высота={altitude/1000:.1f}км, "
                            f"наклонение={inclination:.3f}, RAAN={raan:.3f}",
                        )

                        # Уведомляем ЦСУ об изменении орбиты
                        central_q = self._queues_dir.get_queue(
                            CENTRAL_CONTROL_SYSTEM_QUEUE_NAME
                        )
                        central_q.put(
                            Event(
                                source=self.event_source_name,
                                destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
                                operation="orbit_changed",
                                parameters=(altitude, inclination, raan),
                            )
                        )

                    # Еще одно возможное имя операции для ответа от спутника
                    case "current_orbit":
                        # Получены параметры орбиты от спутника
                        altitude, inclination, raan = event.parameters

                        old_altitude = self._current_orbit["altitude"]
                        self._current_orbit = {
                            "altitude": altitude,
                            "inclination": inclination,
                            "raan": raan,
                        }

                        self._log_message(
                            LOG_INFO,
                            f"Получены текущие параметры орбиты от спутника: высота={altitude/1000:.1f}км, "
                            f"наклонение={inclination:.3f}, RAAN={raan:.3f}",
                        )

            except Empty:
                break
            except Exception as e:
                self._log_message(LOG_ERROR, f"Ошибка при обработке запроса: {e}")

    def run(self):
        self._log_message(LOG_INFO, "Модуль мониторинга орбиты запущен")

        # Запрашиваем параметры орбиты сразу при запуске
        self._request_orbit_params()

        while not self._quit:
            self._check_events_q()
            self._check_control_q()
