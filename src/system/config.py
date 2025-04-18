CLIENT_QUEUE_NAME = "client" # клиент
CONNECTION_QUEUE_NAME = "connection"  # модуль связь
AUTHORIZE_QUEUE_NAME = "authorize" # модуль авторизации
CENTRAL_CONTROL_SYSTEM_QUEUE_NAME = "central control system" # ЦСУ
IMAGE_STORAGE_QUEUE_NAME = "image storage" # хранилище изображений
FORBIDDEN_ZONE_STORAGE_QUEUE_NAME = "forbidden zone storage" # хранилище запрещенных зон
INTERPRETATOR_QUEUE_NAME = "interpretator" # интерпретатор
ORBIT_MONITORING_QUEUE_NAME = "orbit monitoring" # монитооринг орбиты
ORBIT_LIMITER_QUEUE_NAME = "orbit limiter" # ограничитель орбиты
ORBIT_CONTROL_QUEUE_NAME = "orbit_control" # система контроля орбиты
ORBIT_DRAWER_QUEUE_NAME = "orbit_drawer" # отрисовщик
SATELITE_QUEUE_NAME = "satellite" # спутник
OPTICS_CONTROL_QUEUE_NAME = "optics_control" # система контроля оптики
CAMERA_QUEUE_NAME = "camera" # симулятор камеры
SECURITY_MONITOR_QUEUE_NAME = "security" # монитор безопасности

DEFAULT_LOG_LEVEL = 2  # 1 - errors, 2 - verbose, 3 - debug
LOG_FAILURE = 0
LOG_ERROR = 1
LOG_INFO  = 2
LOG_DEBUG = 3
CRITICALITY_STR = [
    "ОТКАЗ", "ОШИБКА", "ИНФО", "ОТЛАДКА"
]
