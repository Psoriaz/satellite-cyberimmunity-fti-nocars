from src.system.security_policy_type import SecurityPolicy
from src.system.config import (
    AUTHORIZATION_MODULE_QUEUE_NAME,
    CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
    IMAGE_STORAGE_QUEUE_NAME,
    RESTRICTED_ZONE_STORAGE_QUEUE_NAME,
    ORBIT_MONITORING_QUEUE_NAME,
    ORBIT_LIMITER_QUEUE_NAME,
    ORBIT_CONTROL_QUEUE_NAME,
    ORBIT_DRAWER_QUEUE_NAME,
    SATELITE_QUEUE_NAME,
    OPTICS_CONTROL_QUEUE_NAME,
    CAMERA_QUEUE_NAME,
    RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
)

# Политики безопасности, определяющие разрешенные взаимодействия между компонентами
security_policies = [
    # Обычный пользователь -> AuthorizationModule
    SecurityPolicy(
        source="client",
        destination=AUTHORIZATION_MODULE_QUEUE_NAME,
        operation="request_photo",
    ),
    # Пользователь с спец. возможностями -> AuthorizationModule
    SecurityPolicy(
        source="special",
        destination=AUTHORIZATION_MODULE_QUEUE_NAME,
        operation="request_photo",
    ),
    SecurityPolicy(
        source="special",
        destination=AUTHORIZATION_MODULE_QUEUE_NAME,
        operation="change_orbit",
    ),
    # Администратор -> AuthorizationModule
    SecurityPolicy(
        source="admin",
        destination=AUTHORIZATION_MODULE_QUEUE_NAME,
        operation="request_photo",
    ),
    SecurityPolicy(
        source="admin",
        destination=AUTHORIZATION_MODULE_QUEUE_NAME,
        operation="get_all_images",
    ),
    SecurityPolicy(
        source="admin",
        destination=AUTHORIZATION_MODULE_QUEUE_NAME,
        operation="change_orbit",
    ),
    SecurityPolicy(
        source="admin",
        destination=AUTHORIZATION_MODULE_QUEUE_NAME,
        operation="add_zone_request",
    ),
    SecurityPolicy(
        source="admin",
        destination=AUTHORIZATION_MODULE_QUEUE_NAME,
        operation="remove_zone_request",
    ),
    # Модуль авторизации -> ЦСМ
    SecurityPolicy(
        source=AUTHORIZATION_MODULE_QUEUE_NAME,
        destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        operation="request_photo",
    ),
    SecurityPolicy(
        source=AUTHORIZATION_MODULE_QUEUE_NAME,
        destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        operation="add_zone_request",
    ),
    SecurityPolicy(
        source=AUTHORIZATION_MODULE_QUEUE_NAME,
        destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        operation="remove_zone_request",
    ),
    SecurityPolicy(
        source=AUTHORIZATION_MODULE_QUEUE_NAME,
        destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        operation="change_orbit",
    ),
    SecurityPolicy(
        source=AUTHORIZATION_MODULE_QUEUE_NAME,
        destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        operation="get_all_images",
    ),
    # ЦСМ -> Камера
    SecurityPolicy(
        source=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        destination=CAMERA_QUEUE_NAME,
        operation="request_photo",
    ),
    # ЦСМ -> Менеджер запрещенных зон
    SecurityPolicy(
        source=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        destination=RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
        operation="add_zone_request",
    ),
    SecurityPolicy(
        source=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        destination=RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
        operation="remove_zone_request",
    ),
    # ЦСМ -> Мониторинг орбиты
    SecurityPolicy(
        source=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        destination=ORBIT_MONITORING_QUEUE_NAME,
        operation="check_orbit_params",
    ),
    # ЦСМ -> Контроль оптики
    SecurityPolicy(
        source=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        destination=OPTICS_CONTROL_QUEUE_NAME,
        operation="zones_update",
    ),
    SecurityPolicy(
        source=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        destination=OPTICS_CONTROL_QUEUE_NAME,
        operation="camera_update",
    ),
    SecurityPolicy(
        source=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        destination=OPTICS_CONTROL_QUEUE_NAME,
        operation="post_photo",
    ),
    # ЦСМ -> Спутник
    SecurityPolicy(
        source=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        destination=SATELITE_QUEUE_NAME,
        operation="change_orbit",
    ),
    # ЦСМ -> Хранилище изображений
    SecurityPolicy(
        source=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        destination=IMAGE_STORAGE_QUEUE_NAME,
        operation="save_image",
    ),
    SecurityPolicy(
        source=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        destination=IMAGE_STORAGE_QUEUE_NAME,
        operation="get_all_images",
    ),
    # Ограничитель орбиты -> Контроль орбиты
    SecurityPolicy(
        source=ORBIT_LIMITER_QUEUE_NAME,
        destination=ORBIT_CONTROL_QUEUE_NAME,
        operation="set_orbit_limits",
    ),
    # Мониторинг орбиты -> Контроль орбиты
    SecurityPolicy(
        source=ORBIT_MONITORING_QUEUE_NAME,
        destination=ORBIT_CONTROL_QUEUE_NAME,
        operation="check_orbit_change",
    ),
    # Мониторинг орбиты -> Центральная система управления
    SecurityPolicy(
        source=ORBIT_MONITORING_QUEUE_NAME,
        destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        operation="orbit_changed",
    ),
    # Контроль орбиты -> ЦСУ
    SecurityPolicy(
        source=ORBIT_CONTROL_QUEUE_NAME,
        destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        operation="orbit_change_approved",
    ),
    SecurityPolicy(
        source=ORBIT_CONTROL_QUEUE_NAME,
        destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        operation="orbit_change_rejected",
    ),
    # Модуль запрещенных зон -> Хранилище запрещенных зон
    SecurityPolicy(
        source=RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
        destination=RESTRICTED_ZONE_STORAGE_QUEUE_NAME,
        operation="add_restricted_zone",
    ),
    SecurityPolicy(
        source=RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
        destination=RESTRICTED_ZONE_STORAGE_QUEUE_NAME,
        operation="remove_restricted_zone",
    ),
    SecurityPolicy(
        source=RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
        destination=RESTRICTED_ZONE_STORAGE_QUEUE_NAME,
        operation="get_all_zones",
    ),
    # Модуль запрещенных зон -> Центральная система управления
    SecurityPolicy(
        source=RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
        destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        operation="zones_update",
    ),
    SecurityPolicy(
        source=RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
        destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        operation="point_check_result",
    ),
    # Модуль запрещенных зон -> Отрисовщик
    SecurityPolicy(
        source=RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
        destination=ORBIT_DRAWER_QUEUE_NAME,
        operation="draw_restricted_zone",
    ),
    # Хранилище запрещенных зон -> Центральная система управления
    SecurityPolicy(
        source=RESTRICTED_ZONE_STORAGE_QUEUE_NAME,
        destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        operation="point_check_result",
    ),
    # Хранилище запрещенных зон -> Модуль запрещенных зон
    SecurityPolicy(
        source=RESTRICTED_ZONE_STORAGE_QUEUE_NAME,
        destination=RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
        operation="draw_zone",
    ),
    SecurityPolicy(
        source=RESTRICTED_ZONE_STORAGE_QUEUE_NAME,
        destination=RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
        operation="zone_operation_result",
    ),
    SecurityPolicy(
        source=RESTRICTED_ZONE_STORAGE_QUEUE_NAME,
        destination=RESTRICTED_ZONES_MANAGER_QUEUE_NAME,
        operation="all_zones_data",
    ),
    # Хранилище изображений -> ЦСУ
    SecurityPolicy(
        source=IMAGE_STORAGE_QUEUE_NAME,
        destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        operation="image_saved",
    ),
    # Контроль оптики -> ЦСУ
    SecurityPolicy(
        source=OPTICS_CONTROL_QUEUE_NAME,
        destination=CENTRAL_CONTROL_SYSTEM_QUEUE_NAME,
        operation="photo_processed",
    ),
    # Контроль оптики -> Отрисовщик
    SecurityPolicy(
        source=OPTICS_CONTROL_QUEUE_NAME,
        destination=ORBIT_DRAWER_QUEUE_NAME,
        operation="update_photo_map",
    ),
]
