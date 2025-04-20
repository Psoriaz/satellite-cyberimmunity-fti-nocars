import sys
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
from src.satellite_control_system.interpreter import SatelliteCommandInterpreter

from src.system.queues_dir import QueuesDirectory
from src.system.system_wrapper import SystemComponentsContainer
from src.system.config import (
    LOG_INFO,
    LOG_ERROR,
    LOG_DEBUG,
)


def setup_system(queues_dir):
    """Инициализация всех компонентов системы"""
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


def main():

    if len(sys.argv) < 2:
        print(
            "Использование: python interpreter.py <имя_файла_с_командами> [тип_пользователя]"
        )
        print("Типы пользователей: admin, client_trusted, client (по умолчанию)")
        return

    command_file = sys.argv[1]
    user_type = sys.argv[2] if len(sys.argv) > 2 else "unathorized_client"

    print(f"Запуск программы (пользователь: {user_type})")

    queues_dir = QueuesDirectory()
    system = setup_system(queues_dir)
    system.start()
    sleep(5)
    try:

        interpreter = SatelliteCommandInterpreter(queues_dir, user_type)
        interpreter.execute_file(command_file)

        print("Выполнение команд завершено")

    finally:
        print("Завершение работы системы...")
        system.stop()
        system.clean()
        print("Система остановлена")


if __name__ == "__main__":
    main()
