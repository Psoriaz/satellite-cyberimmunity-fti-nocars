from multiprocessing import Queue
from queue import Empty
from src.system.custom_process import BaseCustomProcess
from src.system.queues_dir import QueuesDirectory
from src.system.event_types import Event
from src.system.config import LOG_DEBUG, LOG_ERROR, LOG_INFO, DEFAULT_LOG_LEVEL, \
    OPTICS_CONTROL_QUEUE_NAME, ORBIT_DRAWER_QUEUE_NAME, CAMERA_QUEUE_NAME
from src.satellite_control_system.restricted_zone import RestrictedZone

class OpticsControl(BaseCustomProcess):
    """ Модуль управления оптической аппаратурой """
    log_prefix = "[OPTIC]"
    event_source_name = OPTICS_CONTROL_QUEUE_NAME
    events_q_name = event_source_name

    def __init__(self, queues_dir: QueuesDirectory, log_level: int = DEFAULT_LOG_LEVEL):
        super().__init__(
            log_prefix=OpticsControl.log_prefix,
            queues_dir=queues_dir,
            events_q_name=OpticsControl.event_source_name,
            event_source_name=OpticsControl.event_source_name,
            log_level=log_level)

        self._log_message(LOG_INFO, "Модуль управления оптикой создан")

        # Модель запрещённых зон (пока пусто, надо будет потом получать реальные зоны)
        self.restricted_zones: list[RestrictedZone] = []

        # Текущая позиция спутника (заглушка: вручную выставляем для тестов)
        self.current_lat = 0.0
        self.current_lon = 0.0

    def _check_events_q(self):
        """Проверяем очередь событий"""
        while True:
            try:
                event: Event = self._events_q.get_nowait()

                if not isinstance(event, Event):
                    return

                match event.operation:
                    case 'request_photo':
                        self._send_photo_request()

                    case 'post_photo':
                        # Приходит готовый снимок — отправляем его на отрисовку
                        q: Queue = self._queues_dir.get_queue(ORBIT_DRAWER_QUEUE_NAME)
                        lat, lon = event.parameters
                        q.put(Event(
                            source=self._event_source_name,
                            destination=ORBIT_DRAWER_QUEUE_NAME,
                            operation='update_photo_map',
                            parameters=(lat, lon)))
                        self._log_message(LOG_DEBUG, f"Рисуем снимок на карте: ({lat}, {lon})")

                    case 'update_position':
                        # Обновление позиции спутника
                        self.current_lat, self.current_lon = event.parameters
                        self._log_message(LOG_INFO, f"Обновлена позиция: lat={self.current_lat}, lon={self.current_lon}")

                    case 'update_restricted_zones':
                        # Обновление списка запрещённых зон
                        self.restricted_zones = event.parameters
                        self._log_message(LOG_INFO, f"Обновлены запрещённые зоны: {len(self.restricted_zones)} зон")

            except Empty:
                break

    def _send_photo_request(self):
            """Обработка запроса на съёмку"""
            if self._in_restricted_zone(self.current_lat, self.current_lon):
                self._log_message(LOG_ERROR, f"Съёмка запрещена в текущей зоне! (lat={self.current_lat}, lon={self.current_lon})")
                return  # Снимок запрещён

            try:
                camera_q = self._queues_dir.get_queue("camera")
                camera_q.put(Event(
                    source=self._event_source_name,
                    destination="camera",
                    operation="request_photo",
                    parameters=None
                ))
                self._log_message(LOG_INFO, f"Разрешена съёмка, отправляем запрос в камеру: lat={self.current_lat}, lon={self.current_lon}")
            except KeyError:
                self._log_message(LOG_ERROR, "Очередь камеры не найдена!")



    def _in_restricted_zone(self, lat, lon):
            """Проверка, попадает ли координата в запрещённую зону"""
            for zone in self.restricted_zones:
                if zone.lat_bot_left <= lat <= zone.lat_top_right and zone.lon_bot_left <= lon <= zone.lon_top_right:
                    return True
            return False

    def run(self):
        self._log_message(LOG_INFO, "Модуль управления оптикой активен")

        while not self._quit:
            try:
                self._check_events_q()
                self._check_control_q()
            except Exception as e:
                self._log_message(LOG_ERROR, f"Ошибка системы контроля оптики: {e}")
