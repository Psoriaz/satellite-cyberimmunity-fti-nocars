import numpy as np
from time import sleep

from src.satellite_simulator.satellite import Satellite
from src.satellite_simulator.orbit_drawer import OrbitDrawer
from src.satellite_simulator.camera import Camera
from src.satellite_control_system.optics_control import OpticsControl
from src.satellite_control_system.restricted_zones import RestrictedZonesStorage
from src.satellite_control_system.restricted_zones_manager import RestrictedZonesManager
from src.satellite_control_system.central_control_system import CentralControlSystem
from src.satellite_control_system.image_storage import ImageStorage
from src.satellite_control_system.orbit_monitoring import OrbitMonitoring
from src.satellite_control_system.orbit_control import OrbitControl
from src.satellite_control_system.orbit_limiter import OrbitLimiter
from src.satellite_control_system.authorization_module import AuthorizationModule
from src.satellite_control_system.my_security_monitor import MySecurityMonitor
from src.satellite_control_system.policies import security_policies

from src.system.queues_dir import QueuesDirectory
from src.system.system_wrapper import SystemComponentsContainer
from src.system.event_types import Event
from src.system.config import (
    LOG_INFO,
    LOG_ERROR,
    LOG_DEBUG,
    AUTHORIZATION_MODULE_QUEUE_NAME,
    CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
    SECURITY_MONITOR_QUEUE_NAME,
)


def setup_system(queues_dir):

    security_monitor = MySecurityMonitor(
        queues_dir=queues_dir, log_level=LOG_INFO, policies=security_policies
    )

    satellite = Satellite(
        altitude=1000e3,
        position_angle=0,
        inclination=np.pi / 3,
        raan=0,
        queues_dir=queues_dir,
        log_level=LOG_INFO,
    )
    drawer = OrbitDrawer(queues_dir=queues_dir, log_level=LOG_INFO)
    camera = Camera(queues_dir=queues_dir, log_level=LOG_INFO)
    zones_storage = RestrictedZonesStorage(queues_dir=queues_dir, log_level=LOG_INFO)
    zones_manager = RestrictedZonesManager(queues_dir=queues_dir, log_level=LOG_INFO)
    optics_control = OpticsControl(queues_dir=queues_dir, log_level=LOG_INFO)
    central_system = CentralControlSystem(queues_dir=queues_dir, log_level=LOG_INFO)
    orbit_control = OrbitControl(queues_dir=queues_dir, log_level=LOG_INFO)
    image_storage = ImageStorage(queues_dir=queues_dir, log_level=LOG_INFO)
    orbit_limiter = OrbitLimiter(queues_dir=queues_dir, log_level=LOG_INFO)
    orbit_monitoring = OrbitMonitoring(queues_dir=queues_dir, log_level=LOG_INFO)
    auth_module = AuthorizationModule(queues_dir=queues_dir, log_level=LOG_INFO)

    system = SystemComponentsContainer(
        components=[
            security_monitor,
            satellite,
            camera,
            drawer,
            zones_storage,
            zones_manager,
            optics_control,
            image_storage,
            orbit_control,
            orbit_limiter,
            orbit_monitoring,
            auth_module,
            central_system,
        ],
        log_level=LOG_INFO,
    )
    return system


def full_system_demo():
    """Демонстрация всех основных функций системы управления спутником"""

    queues_dir = QueuesDirectory()
    system = setup_system(queues_dir)
    system.start()

    try:
        print("\n=== Ожидание инициализации компонентов ===")
        sleep(5)

        auth_q = queues_dir.get_queue(AUTHORIZATION_MODULE_QUEUE_NAME)

        # Определяем псевдо-пользователей для демонстрации
        ADMIN_SOURCE = "admin"
        USER_SPECIAL_SOURCE = "client_trusted"
        USER_REGULAR_SOURCE = "client"
        UNAUTHORIZED_SOURCE = "unauthorized_user"

        # region --- 1. Операции с фотографиями (проверка разных прав) ---
        print("\n=== 1.1 Тест снимка от АДМИНА (должен пройти) ===")
        auth_q.put(
            Event(
                source=ADMIN_SOURCE,
                destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                operation="request_photo",
                parameters=None,
            )
        )
        sleep(2)

        print("\n=== 1.2 Тест снимка от ДОВЕРЕННОГО пользователя (должен пройти) ===")
        auth_q.put(
            Event(
                source=USER_SPECIAL_SOURCE,
                destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                operation="request_photo",
                parameters=None,
            )
        )
        sleep(2)

        print("\n=== 1.3 Тест снимка от ОБЫЧНОГО пользователя (должен пройти) ===")
        auth_q.put(
            Event(
                source=USER_REGULAR_SOURCE,
                destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                operation="request_photo",
                parameters=None,
            )
        )
        sleep(2)

        print(
            "\n=== 1.4 Тест снимка от НЕАВТОРИЗОВАННОГО пользователя (должен быть отклонен) ==="
        )
        auth_q.put(
            Event(
                source=UNAUTHORIZED_SOURCE,
                destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                operation="request_photo",
                parameters=None,
            )
        )
        sleep(2)

        # endregion

        # region --- 2. Операции с запрещенными зонами (только админ) ---
        print(
            "\n=== 2.1 Добавление зоны от ОБЫЧНОГО пользователя (должно быть отклонено) ==="
        )
        zone_1_id = 1
        auth_q.put(
            Event(
                source=USER_REGULAR_SOURCE,
                destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                operation="add_zone_request",
                parameters=(zone_1_id, -10, -10, 10, 10),
            )
        )
        sleep(3)

        print("\n=== 2.2 Добавление зоны от АДМИНА (должно пройти) ===")
        auth_q.put(
            Event(
                source=ADMIN_SOURCE,
                destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                operation="add_zone_request",
                parameters=(
                    zone_1_id,
                    -10,
                    -10,
                    10,
                    10,
                ),
            )
        )
        sleep(3)

        print("\n=== 2.3 Добавление второй зоны от АДМИНА (должно пройти) ===")
        zone_2_id = 2
        auth_q.put(
            Event(
                source=ADMIN_SOURCE,
                destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                operation="add_zone_request",
                parameters=(
                    zone_2_id,
                    30,
                    30,
                    170,
                    170,
                ),
            )
        )
        sleep(3)

        print("\n=== Ожидание перемещения спутника... ===")
        sleep(10)

        print("\n=== 2.4 Тест снимка в запрещенной зоне (должен быть отклонен) ===")
        auth_q.put(
            Event(
                source=USER_REGULAR_SOURCE,
                destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                operation="request_photo",
                parameters=None,
            )
        )
        sleep(2)

        print(
            f"\n=== 2.5 Удаление зоны от ДОВЕРЕННОГО пользователя (должно быть отклонено) ==="
        )
        auth_q.put(
            Event(
                source=USER_SPECIAL_SOURCE,
                destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                operation="remove_zone_request",
                parameters=zone_1_id,
            )
        )
        sleep(2)

        print(f"\n=== 2.6 Удаление зоны от АДМИНА (должно пройти) ===")
        auth_q.put(
            Event(
                source=ADMIN_SOURCE,
                destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                operation="remove_zone_request",
                parameters=zone_1_id,
            )
        )
        sleep(2)

        # endregion

        # region --- 3. Операции с орбитой (проверка разных прав) ---
        print(
            "\n=== 3.1 Изменение орбиты от ОБЫЧНОГО пользователя (должно быть отклонено) ==="
        )
        new_orbit_params_valid = [850e3, np.pi / 4, np.pi / 2]
        auth_q.put(
            Event(
                source=USER_REGULAR_SOURCE,
                destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                operation="change_orbit",
                parameters=new_orbit_params_valid,
            )
        )
        sleep(2)

        print("\n=== 3.2 Изменение орбиты от СПЕЦ пользователя (должно пройти) ===")
        auth_q.put(
            Event(
                source=USER_SPECIAL_SOURCE,
                destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                operation="change_orbit",
                parameters=new_orbit_params_valid,
            )
        )
        sleep(2)

        print("\n=== 3.3 Тест снимка на новой орбите (от спец пользователя) ===")
        auth_q.put(
            Event(
                source=USER_SPECIAL_SOURCE,
                destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                operation="request_photo",
                parameters=None,
            )
        )
        sleep(3)

        print(
            "\n=== 3.4 Изменение орбиты на НЕДОПУСТИМЫЕ параметры от АДМИНА (должно быть отклонено системой контроля) ==="
        )
        new_orbit_params_invalid = [100e3, np.pi / 6, np.pi / 4]
        auth_q.put(
            Event(
                source=ADMIN_SOURCE,
                destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                operation="change_orbit",
                parameters=new_orbit_params_invalid,
            )
        )
        sleep(3)

        print(
            "\n=== 3.5 Финальный тест снимка (от админа, на текущей допустимой орбите) ==="
        )
        auth_q.put(
            Event(
                source=ADMIN_SOURCE,
                destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                operation="request_photo",
                parameters=None,
            )
        )
        sleep(3)

        print("\n=== Демонстрация завершена ===")

        auth_q.put(
            Event(
                source=ADMIN_SOURCE,
                destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                operation="get_all_images",
                parameters=None,
            )
        )
    finally:
        print("\n=== Завершение работы системы ===")
        sleep(3)
        system.stop()
        system.clean()
        print("Система остановлена")


if __name__ == "__main__":
    full_system_demo()
