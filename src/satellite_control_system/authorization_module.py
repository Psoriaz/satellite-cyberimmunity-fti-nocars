from multiprocessing import Queue
from queue import Empty
from src.system.custom_process import BaseCustomProcess
from src.system.event_types import Event
from src.system.config import (
    LOG_INFO,
    LOG_ERROR,
    DEFAULT_LOG_LEVEL,
    SECURITY_MONITOR_QUEUE_NAME,
    AUTHORIZATION_MODULE_QUEUE_NAME,
    CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
)


class AuthorizationModule(BaseCustomProcess):
    """
    Модуль авторизации клиента.
    Проверяет разрешение на выполнение операций и перенаправляет события в ЦСУ.
    """

    log_prefix = "[AUTH]"
    event_source_name = AUTHORIZATION_MODULE_QUEUE_NAME
    events_q_name = event_source_name

    def __init__(self, queues_dir, log_level=DEFAULT_LOG_LEVEL):
        super().__init__(
            log_prefix=AuthorizationModule.log_prefix,
            queues_dir=queues_dir,
            events_q_name=AuthorizationModule.events_q_name,
            event_source_name=AuthorizationModule.event_source_name,
            log_level=log_level,
        )
        self._authorized_clients = {
            "client": {"request_photo"},
            "client_trusted": {"request_photo", "change_orbit"},
            "admin": {
                "request_photo",
                "change_orbit",
                "add_zone_request",
                "remove_zone_request",
                "get_all_images",
            },
        }
        self._log_message(LOG_INFO, "Модуль авторизации создан")

    def _check_events_q(self):
        while True:
            try:
                event = self._events_q.get_nowait()
                if not isinstance(event, Event):
                    continue

                source = event.source
                operation = event.operation

                if source in self._authorized_clients:
                    allowed_ops = self._authorized_clients[source]
                    if operation in allowed_ops:
                        self._log_message(
                            LOG_INFO, f"Разрешено: {source} -> {operation}"
                        )
                        q: Queue = self._queues_dir.get_queue(
                            SECURITY_MONITOR_QUEUE_NAME
                        )
                        q.put(
                            Event(
                                source=self.event_source_name,
                                destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
                                operation=operation,
                                parameters=event.parameters,
                            )
                        )
                    else:
                        self._log_message(
                            LOG_ERROR,
                            f"Запрещено: {source} не имеет права на {operation}",
                        )
                else:
                    self._log_message(LOG_ERROR, f"Неавторизованный клиент: {source}")

            except Empty:
                break
            except Exception as e:
                self._log_message(LOG_ERROR, f"Ошибка авторизации: {e}")

    def run(self):
        self._log_message(LOG_INFO, "Модуль авторизации запущен")
        while not self._quit:
            self._check_events_q()
            self._check_control_q()
