from src.system.config import (
    SECURITY_MONITOR_QUEUE_NAME,
    AUTHORIZATION_MODULE_QUEUE_NAME,
)
from src.system.event_types import Event
from time import sleep
from multiprocessing import Queue


class SatelliteCommandInterpreter:
    """Интерпретатор команд для системы управления спутником"""

    def __init__(self, queues_dir, user_type="admin"):
        """
        Инициализация интерпретатора
        """
        self.queues_dir = queues_dir
        self.q: Queue = queues_dir.get_queue(SECURITY_MONITOR_QUEUE_NAME)
        self.user_type = user_type
        self.command_delay = 5  # задержка между командами в секундах

    def parse_command(self, line):
        """
        Разбор команды из строки текста
        """
        line = line.strip()
        if not line:
            return None  # Пустая строка

        parts = line.split()

        # Обработка команды ORBIT
        if parts[0] == "ORBIT" and len(parts) >= 4:
            try:
                altitude = float(parts[1])  # высота в метрах
                raan = float(parts[2])  # в радианах
                inclination = float(parts[3])  # в радианах
                return "change_orbit", [altitude, raan, inclination]
            except ValueError:
                print(f"Ошибка: неверный формат параметров для команды ORBIT: {line}")
                return None

        # Обработка команды MAKE PHOTO
        elif parts[0] == "MAKE" and len(parts) >= 2 and parts[1] == "PHOTO":
            return "request_photo", None

        # Обработка команды ADD ZONE
        elif parts[0] == "ADD" and parts[1] == "ZONE" and len(parts) >= 7:
            try:
                zone_id = int(parts[2])
                lat1 = float(parts[3])
                lon1 = float(parts[4])
                lat2 = float(parts[5])
                lon2 = float(parts[6])
                return "add_zone_request", (zone_id, lat1, lon1, lat2, lon2)
            except ValueError:
                print(
                    f"Ошибка: неверный формат параметров для команды ADD ZONE: {line}"
                )
                return None

        # Обработка команды REMOVE ZONE
        elif parts[0] == "REMOVE" and parts[1] == "ZONE" and len(parts) >= 3:
            try:
                zone_id = int(parts[2])
                return "remove_zone_request", zone_id
            except ValueError:
                print(
                    f"Ошибка: неверный формат параметров для команды REMOVE ZONE: {line}"
                )
                return None

        else:
            print(f"Ошибка: неизвестная команда: {line}")
            return None

    def execute_file(self, filename):
        """
        Выполнение команд из файла
        """
        try:
            with open(filename, "r", encoding="utf-8") as file:
                lines = file.readlines()

            print(f"Загружено {len(lines)} строк из файла {filename}")

            for i, line in enumerate(lines, 1):
                # Парсим и выполняем команду
                result = self.parse_command(line)
                if result:
                    operation, parameters = result
                    print(f"Выполняется команда [{i}]: {line.strip()}")

                    self.q.put(
                        Event(
                            source=self.user_type,
                            destination=AUTHORIZATION_MODULE_QUEUE_NAME,
                            operation=operation,
                            parameters=parameters,
                        )
                    )

                    # Задержка между командами
                    sleep(self.command_delay)

        except FileNotFoundError:
            print(f"Ошибка: файл {filename} не найден")
        except Exception as e:
            print(f"Ошибка при выполнении файла: {e}")
