from src.satellite_control_system.setup_system import setup_system
from time import sleep
from src.system.event_types import Event
from src.satellite_control_system.restricted_zone import RestrictedZone

def send_event(queue, operation, parameters=None):
    """Упрощённая отправка событий"""
    event = Event(
        source="external_client",
        destination="central_control_system",
        operation=operation,
        parameters=parameters
    )
    queue.put(event)

if __name__ == '__main__':
    system_components, queues_dir = setup_system()
    system_components.start()
    sleep(2)

    central_q = queues_dir.get_queue("central_control_system")
    optics_q = queues_dir.get_queue("optics_control")
    image_storage_q = queues_dir.get_queue("image_storage")
    camera_q = queues_dir.get_queue("camera")  # эмулятор камеры

    ### --- Подготовка: Обновляем запрещённые зоны ---
    print("\n=== ПОДГОТОВКА: Добавляем запрещённую зону ===")
    optics_q.put(Event(
        source="external_client",
        destination="optics_control",
        operation="update_restricted_zones",
        parameters=[
            RestrictedZone(lat_bot_left=10, lon_bot_left=-10, lat_top_right=20, lon_top_right=20)
        ]
    ))
    sleep(1)

    ### --- ПОДГОТОВКА: Обновляем позицию спутника (вне запрещённой зоны) ---
    print("\n=== ПОДГОТОВКА: Позиция вне запрещённой зоны ===")
    optics_q.put(Event(
        source="external_client",
        destination="optics_control",
        operation="update_position",
        parameters=(50.0, 30.0)  # Позиция ВНЕ запрещённой зоны
    ))
    sleep(1)

    ### --- ТЕСТ 1: Попытка сделать снимок вне запрещённой зоны ---
    print("\n=== ТЕСТ 1: Съёмка вне запрещённой зоны ===")
    send_event(central_q, "request_photo")
    sleep(3)

    ### --- Эмуляция камеры: Возвращаем событие post_photo ---
    print("\n=== ЭМУЛЯЦИЯ КАМЕРЫ: отправляем post_photo ===")
    optics_q.put(Event(
        source="camera",
        destination="optics_control",
        operation="post_photo",
        parameters=(50.0, 30.0)  # Координаты снимка
    ))
    sleep(2)

    ### --- ПОДГОТОВКА: Позиция спутника в запрещённой зоне ---
    print("\n=== ПОДГОТОВКА: Позиция ВНУТРИ запрещённой зоны ===")
    optics_q.put(Event(
        source="external_client",
        destination="optics_control",
        operation="update_position",
        parameters=(15.0, 0.0)  # Координаты ВНУТРИ запрещённой зоны
    ))
    sleep(1)

    ### --- ТЕСТ 2: Попытка сделать снимок в запрещённой зоне ---
    print("\n=== ТЕСТ 2: Попытка съёмки в запрещённой зоне ===")
    send_event(central_q, "request_photo")
    sleep(3)

    ### --- ТЕСТ 3: Запрос всех сохранённых снимков из ImageStorage ---
    print("\n=== ТЕСТ 3: Запрос всех сохранённых снимков ===")
    image_storage_q.put(Event(
        source="external_client",
        destination="image_storage",
        operation="get_all_photos",
        parameters=None
    ))
    sleep(3)

    ### --- Завершаем работу ---
    system_components.stop()
    system_components.clean()

    print("\n=== ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ ===")
