import numpy as np
from time import sleep

from src.satellite_simulator.satellite import Satellite
from src.satellite_simulator.camera import Camera
from src.satellite_simulator.orbit_drawer import OrbitDrawer

from src.satellite_control_system.authorization_module import AuthorizationModule
from src.satellite_control_system.central_control_system import CentralControlSystem
from src.satellite_control_system.orbit_monitoring import OrbitMonitor
from src.satellite_control_system.orbit_limiter import OrbitLimiter
from src.satellite_control_system.restricted_zones import RestrictedZonesStorage
from src.satellite_control_system.orbit_control import OrbitControl
from src.satellite_control_system.optics_control import OpticsControl
from src.satellite_control_system.security_monitor import SecurityMonitor
from src.satellite_control_system.image_storage import ImageStorage

from src.system.system_wrapper import SystemComponentsContainer
from src.system.queues_dir import QueuesDirectory
from src.system.config import LOG_DEBUG, DEFAULT_LOG_LEVEL


def setup_system():
    queues_dir = QueuesDirectory()

    # Модули управления
    authorization_module = AuthorizationModule(
        queues_dir=queues_dir,
        log_level=LOG_DEBUG
    )

    central_control_system = CentralControlSystem(
        queues_dir=queues_dir,
        log_level=LOG_DEBUG
    )

    orbit_monitor = OrbitMonitor(
        queues_dir=queues_dir,
        log_level=LOG_DEBUG
    )

    orbit_limiter = OrbitLimiter(
        queues_dir=queues_dir,
        log_level=LOG_DEBUG
    )

    restricted_zones_storage = RestrictedZonesStorage(
        queues_dir=queues_dir,
        log_level=LOG_DEBUG
    )

    orbit_control = OrbitControl(
        queues_dir=queues_dir,
        log_level=LOG_DEBUG
    )

    optics_control = OpticsControl(
        queues_dir=queues_dir,
        log_level=LOG_DEBUG
    )

    security_monitor = SecurityMonitor(
        queues_dir=queues_dir,
        log_level=LOG_DEBUG
    )

    image_storage = ImageStorage(
        queues_dir=queues_dir,
        log_level=LOG_DEBUG
    )

    # Симуляция спутника
    satellite = Satellite(
        altitude=1000e3,
        position_angle=0,
        inclination=np.pi/3,
        raan=0,
        queues_dir=queues_dir,
        log_level=LOG_DEBUG
    )

    camera = Camera(
        queues_dir=queues_dir,
        log_level=LOG_DEBUG
    )

    drawer = OrbitDrawer(
        queues_dir=queues_dir,
        log_level=LOG_DEBUG
    )

    # Собираем все модули в один контейнер
    system_components = SystemComponentsContainer(
        components=[
            authorization_module,
            central_control_system,
            orbit_monitor,
            orbit_limiter,
            restricted_zones_storage,
            orbit_control,
            optics_control,
            security_monitor,
            image_storage,
            satellite,
            camera,
            drawer
        ],
        log_level=LOG_DEBUG
    )

    return system_components, queues_dir
