from src.satellite_control_system.setup_system import setup_system
from time import sleep
from src.system.event_types import Event
from src.satellite_control_system.restricted_zone import RestrictedZone

if __name__ == '__main__':
    system_components, queues_dir = setup_system()
    system_components.start()

    # Теперь можешь работать с очередями
    central_q = queues_dir.get_queue("central_control_system")

    sleep(2)

    # Пример: отправляем команду на смену орбиты
    central_q.put(Event(
        source="external_client",
        destination="central_control_system",
        operation="change_orbit",
        parameters=[700e3, 0.1, 0.5]
    ))

    sleep(2)

    # Пример: устанавливаем запрещённую зону
    central_q.put(Event(
        source="external_client",
        destination="central_control_system",
        operation="set_restricted_zone",
        parameters=RestrictedZone(10, -10, 20, 20)
    ))

    sleep(5)

    # Останавливаем систему
    system_components.stop()
    system_components.clean()
