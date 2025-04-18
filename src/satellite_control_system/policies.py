from src.system.security_policy_type import SecurityPolicy
from src.system.config import CLIENT_QUEUE_NAME, CONNECTION_QUEUE_NAME, AUTHORIZE_QUEUE_NAME, \
    CENTRAL_CONTROL_SYSTEM_QUEUE_NAME, IMAGE_STORAGE_QUEUE_NAME, SECURITY_MONITOR_QUEUE_NAME, \
    INTERPRETATOR_QUEUE_NAME, ORBIT_MONITORING_QUEUE_NAME, ORBIT_CONTROL_QUEUE_NAME, \
    FORBIDDEN_ZONE_CONTROL_QUEUE_NAME, FORBIDDEN_ZONE_STORAGE_QUEUE_NAME, \
    SATELITE_QUEUE_NAME, ORBIT_DRAWER_QUEUE_NAME, \
    ORBIT_LIMITER_QUEUE_NAME, OPTICS_CONTROL_QUEUE_NAME, CAMERA_QUEUE_NAME


policies = [
    SecurityPolicy(
        source=CLIENT_QUEUE_NAME,
        destination=CONNECTION_QUEUE_NAME,
        operation='send_program'
    ),
    SecurityPolicy(
        source=CONNECTION_QUEUE_NAME,
        destination=AUTHORIZE_QUEUE_NAME,
        operation='check_authorization'
    ),
    SecurityPolicy(
        source=AUTHORIZE_QUEUE_NAME,
        destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        operation='send_program'
    ),
    SecurityPolicy(
        source=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        destination=IMAGE_STORAGE_QUEUE_NAME,
        operation='save_image'
    ),
    SecurityPolicy(
        source=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        destination=IMAGE_STORAGE_QUEUE_NAME,
        operation='get_image'
    ),
    SecurityPolicy(
        source=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        destination=SECURITY_MONITOR_QUEUE_NAME,
        operation='save_image'
    ),
    SecurityPolicy(
        source=SECURITY_MONITOR_QUEUE_NAME,
        destination=INTERPRETATOR_QUEUE_NAME,
        operation='create_program'
    ),
    SecurityPolicy(
        source=INTERPRETATOR_QUEUE_NAME,
        destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        operation='return_created_program'
    ),
    SecurityPolicy(
        source=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        destination=ORBIT_CONTROL_QUEUE_NAME,
        operation='send_limiters'
    ),
    SecurityPolicy(
        source=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        destination=ORBIT_MONITORING_QUEUE_NAME,
        operation='check_orbit_params'
    ),
    SecurityPolicy(
        source=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        destination=FORBIDDEN_ZONE_CONTROL_QUEUE_NAME,
        operation='check_forbidden_zones'
    ),
    SecurityPolicy(
        source=FORBIDDEN_ZONE_CONTROL_QUEUE_NAME,
        destination=FORBIDDEN_ZONE_STORAGE_QUEUE_NAME,
        operation='get_forbidden_zones'
    ),
    SecurityPolicy(
        source=FORBIDDEN_ZONE_STORAGE_QUEUE_NAME,
        destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        operation='return_forbidden_zones'
    ),
    SecurityPolicy(
        source=FORBIDDEN_ZONE_CONTROL_QUEUE_NAME,
        destination=OPTICS_CONTROL_QUEUE_NAME,
        operation='take_photo'
    ),
    SecurityPolicy(
        source=OPTICS_CONTROL_QUEUE_NAME,
        destination=CAMERA_QUEUE_NAME,
        operation='take_photo'
    ),
    SecurityPolicy(
        source=OPTICS_CONTROL_QUEUE_NAME,
        destination=IMAGE_STORAGE_QUEUE_NAME ,
        operation='save_photo'
    ),
    SecurityPolicy(
        source=ORBIT_MONITORING_QUEUE_NAME,
        destination=ORBIT_CONTROL_QUEUE_NAME,
        operation='send_params'
    ),
    SecurityPolicy(
        source=ORBIT_LIMITER_QUEUE_NAME,
        destination=ORBIT_CONTROL_QUEUE_NAME,
        operation='send_limiters'
    ),
]

# TODO поменять связи для хранилища запрещенных зон