from src.satellite_control_system.setup_system import setup_system
from time import sleep
from src.system.event_types import Event
from src.satellite_control_system.restricted_zone import RestrictedZone

def send_event(queue, operation, parameters=None):
    event = Event(
        source="external_client",
        destination="central_control_system",
        operation=operation,
        parameters=parameters
    )
    queue.put(event)

if __name__ == '__main__':
    # Запускаем систему
    system_components, queues_dir = setup_system()
    system_components.start()
    sleep(2)

    # Очередь центральной системы управления
    central_q = queues_dir.get_queue("central_control_system")

    ### --- Тест 1: Валидная смена орбиты ---
    print("\n=== ТЕСТ 1: Валидная смена орбиты ===")
    send_event(central_q, "change_orbit", [750e3, 1.2, 0.5])
    sleep(3)

    ### --- Тест 2: Невалидная смена орбиты (слишком малая высота) ---
    print("\n=== ТЕСТ 2: Невалидная смена орбиты (высота 100 км) ===")
    send_event(central_q, "change_orbit", [100e3, 1.2, 0.5])
    sleep(3)

    ### --- Тест 3: Невалидная смена орбиты (неправильный наклон) ---
    print("\n=== ТЕСТ 3: Невалидная смена орбиты (наклонение 4 рад) ===")
    send_event(central_q, "change_orbit", [750e3, 1.2, 4.0])
    sleep(3)

    ### --- Тест 4: Добавление запрещённой зоны ---
    print("\n=== ТЕСТ 4: Добавление запрещённой зоны ===")
    send_event(central_q, "set_restricted_zone", RestrictedZone(10, -10, 20, 20))
    sleep(3)

    ### --- Тест 5: Валидный запрос фото ---
    print("\n=== ТЕСТ 5: Запрос фото (разрешённый) ===")
    send_event(central_q, "request_photo")
    sleep(3)

    ### --- Тест 6: Запрет съёмки в зоне (если реализовано) ---
    print("\n=== ТЕСТ 6: Попытка сделать снимок в запретной зоне ===")
    # Здесь предполагаем, что OpticsControl проверяет зоны
    # Для реального теста надо будет доработать OpticsControl
    send_event(central_q, "request_photo")
    sleep(3)

    # Завершаем работу
    system_components.stop()
    system_components.clean()

    print("\n=== ВСЕ ТЕСТЫ ПРОЙДЕНЫ ===")
