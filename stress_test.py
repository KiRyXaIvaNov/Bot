import asyncio
import random
from datetime import datetime
import time
import statistics
import sys
import os

# Добавляем путь к текущей директории для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройки теста                               #Это токен от тестового бота
BOT_TOKEN = "7590824294:AAEd8iddy-yDg06s0sQgspfMBpxjdE_gE04"  # Замените на реальный токен тестового бота!
NUM_USERS = 50  # Количество виртуальных пользователей
MESSAGES_PER_USER = 30  # Сообщений на пользователя
DELAY_BETWEEN_MESSAGES = 0.05  # Задержка между сообщениями (в секундах)
TEST_DURATION_SECONDS = 60  # Длительность теста в секундах

# Список команд для тестирования (соответствует вашему боту)
TEST_COMMANDS = [
    "/start",
    "Создать набор пар 📝",
    "Ботать 📚",
    "Инструкция 📖",
    "Вернуться назад ↩️",
    "Блиц ⚡",
    "Подробный 🔎",
    "Пропустить ➡️",
    "Завершить 🤚"
]


# Вспомогательные классы для имитации объектов telebot
class TestUser:
    def __init__(self, user_id, username, first_name):
        self.id = user_id
        self.username = username
        self.first_name = first_name
        self.is_bot = False


class TestChat:
    def __init__(self, chat_id, username, first_name):
        self.id = chat_id
        self.type = "private"
        self.username = username
        self.first_name = first_name


class TestMessage:
    def __init__(self, message_id, from_user, chat, text, date):
        self.message_id = message_id
        self.from_user = from_user
        self.chat = chat
        self.text = text
        self.date = date
        self.content_type = "text"


class VirtualUser:
    """Виртуальный пользователь для нагрузочного тестирования"""

    def __init__(self, user_id):
        self.user_id = user_id
        self.username = f"test_user_{user_id}"
        self.first_name = f"Test {user_id}"
        self.responses = []
        self.latencies = []  # Задержки обработки
        self.errors = 0
        self.start_time = None
        self.end_time = None

    def create_message(self, text):
        """Создает виртуальное сообщение в формате Telebot"""
        user = TestUser(self.user_id, self.username, self.first_name)
        chat = TestChat(self.user_id, self.username, self.first_name)

        return TestMessage(
            message_id=random.randint(1, 1000000),
            from_user=user,
            chat=chat,
            text=text,
            date=datetime.now()
        )


class StressTestResult:
    """Класс для сбора результатов тестирования"""

    def __init__(self):
        self.total_messages = 0
        self.total_latency = 0
        self.all_latencies = []
        self.errors = 0
        self.start_time = None
        self.end_time = None
        self.user_stats = {}

    def add_result(self, user_id, latency, error=False):
        self.total_messages += 1
        if not error:
            self.total_latency += latency
            self.all_latencies.append(latency)
        else:
            self.errors += 1

        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                'messages': 0,
                'total_latency': 0,
                'errors': 0
            }

        self.user_stats[user_id]['messages'] += 1
        if error:
            self.user_stats[user_id]['errors'] += 1
        else:
            self.user_stats[user_id]['total_latency'] += latency

    def get_report(self):
        """Генерирует отчет о тестировании"""
        if not self.all_latencies:
            return "Нет данных для отчета"

        total_time = (self.end_time - self.start_time).total_seconds()
        avg_latency = statistics.mean(self.all_latencies) if self.all_latencies else 0
        median_latency = statistics.median(self.all_latencies) if self.all_latencies else 0
        min_latency = min(self.all_latencies) if self.all_latencies else 0
        max_latency = max(self.all_latencies) if self.all_latencies else 0
        messages_per_second = self.total_messages / total_time if total_time > 0 else 0

        # Группировка по времени ответа
        latency_distribution = {
            '< 0.1s': len([l for l in self.all_latencies if l < 0.1]),
            '0.1-0.5s': len([l for l in self.all_latencies if 0.1 <= l < 0.5]),
            '0.5-1s': len([l for l in self.all_latencies if 0.5 <= l < 1]),
            '1-2s': len([l for l in self.all_latencies if 1 <= l < 2]),
            '> 2s': len([l for l in self.all_latencies if l >= 2])
        }

        report = f"""
{'=' * 60}
СТАТИСТИКА НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ
{'=' * 60}

📊 Общая информация:
├─ Общее время теста: {total_time:.2f} сек.
├─ Всего сообщений: {self.total_messages}
├─ Сообщений в секунду: {messages_per_second:.2f}
├─ Ошибок: {self.errors}
└─ Успешных запросов: {len(self.all_latencies)}

⏱️ Задержки обработки:
├─ Средняя задержка: {avg_latency:.3f} сек.
├─ Медианная задержка: {median_latency:.3f} сек.
├─ Минимальная задержка: {min_latency:.3f} сек.
└─ Максимальная задержка: {max_latency:.3f} сек.

📈 Распределение задержек:"""

        for category, count in latency_distribution.items():
            percentage = (count / len(self.all_latencies) * 100) if self.all_latencies else 0
            report += f"\n├─ {category}: {count} ({percentage:.1f}%)"

        report += f"""

👥 Статистика по пользователям:
├─ Количество пользователей: {len(self.user_stats)}
└─ Среднее сообщений на пользователя: {self.total_messages / len(self.user_stats):.1f}

{'=' * 60}
РЕКОМЕНДАЦИИ:
"""

        # Рекомендации на основе результатов
        if avg_latency > 1:
            report += "⚠️  КРИТИЧЕСКИЕ ЗАДЕРЖКИ! Бот работает очень медленно.\n"
            report += "   Рекомендации: Оптимизировать код, кэшировать данные, использовать базу данных.\n"
        elif avg_latency > 0.5:
            report += "⚠️  Высокие задержки! Есть проблемы с производительностью.\n"
            report += "   Рекомендации: Проверить сложные операции (база данных, ML модели).\n"
        elif avg_latency > 0.1:
            report += "✅  Приемлемые задержки, но есть пространство для улучшения.\n"
        else:
            report += "✅  Отличная производительность! Бот работает быстро.\n"

        if self.errors > 0:
            report += f"⚠️  Обнаружено {self.errors} ошибок. Проверьте обработку исключений.\n"

        if messages_per_second < 10:
            report += "⚠️  Низкая пропускная способность. Бот не справится с большой нагрузкой.\n"

        report += "\n" + "=" * 60

        return report


async def simulate_user(user_id, result, stop_event):
    """Имитирует действия одного пользователя"""
    # Импортируем обработчик из вашего основного файла
    try:
        from botai_bot import is_button_press  # Импортируйте из вашего файла
    except ImportError:
        print("❌ Ошибка: Не могу импортировать функцию is_button_press")
        print("   Убедитесь, что файл с ботом называется bot.py или измените импорт")
        return

    user = VirtualUser(user_id)

    while not stop_event.is_set():
        # Выбираем случайную команду
        command = random.choice(TEST_COMMANDS)

        # Создаем сообщение
        message = user.create_message(command)

        # Измеряем время обработки
        start_time = time.time()

        try:
            # Вызываем обработчик напрямую
            is_button_press(message)
            latency = time.time() - start_time

            # Сохраняем результат
            result.add_result(user_id, latency)

            # Выводим прогресс (раз в 100 сообщений)
            if result.total_messages % 100 == 0:
                print(f"✓ Обработано {result.total_messages} сообщений | "
                      f"Текущая задержка: {latency:.3f} сек.")

        except Exception as e:
            latency = time.time() - start_time
            result.add_result(user_id, latency, error=True)

            # Выводим ошибку только иногда, чтобы не засорять консоль
            if random.random() < 0.01:  # 1% шанс вывести ошибку
                print(f"❌ Ошибка у пользователя {user_id}: {str(e)[:50]}...")

        # Задержка между сообщениями
        await asyncio.sleep(DELAY_BETWEEN_MESSAGES)


async def run_stress_test():
    """Запускает нагрузочный тест"""
    print("🚀 Начинаем нагрузочное тестирование бота...")
    print(f"📊 Параметры теста:")
    print(f"   ├─ Пользователей: {NUM_USERS}")
    print(f"   ├─ Сообщений на пользователя: {MESSAGES_PER_USER}")
    print(f"   ├─ Длительность: {TEST_DURATION_SECONDS} сек.")
    print(f"   └─ Задержка между сообщениями: {DELAY_BETWEEN_MESSAGES} сек.")
    print("-" * 60)

    # Создаем объект для сбора результатов
    result = StressTestResult()
    result.start_time = datetime.now()

    # Создаем событие для остановки теста
    stop_event = asyncio.Event()

    # Запускаем таймер для остановки теста
    async def timer():
        await asyncio.sleep(TEST_DURATION_SECONDS)
        stop_event.set()

    # Создаем задачи для пользователей
    tasks = []
    for user_id in range(1, NUM_USERS + 1):
        task = asyncio.create_task(simulate_user(user_id, result, stop_event))
        tasks.append(task)

    # Запускаем таймер
    timer_task = asyncio.create_task(timer())

    # Ждем завершения таймера
    await timer_task

    # Даем небольшую паузу для завершения всех задач
    await asyncio.sleep(1)

    # Отменяем все задачи пользователей
    for task in tasks:
        task.cancel()

    # Ждем завершения всех задач
    await asyncio.gather(*tasks, return_exceptions=True)

    # Завершаем тест
    result.end_time = datetime.now()

    # Выводим отчет
    print("\n" + "=" * 60)
    print("📋 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)

    report = result.get_report()
    print(report)

    # Дополнительная информация
    print("\n💡 Советы по интерпретации результатов:")
    print("1. < 0.1 сек. - Отличная производительность")
    print("2. 0.1-0.5 сек. - Хорошая производительность")
    print("3. 0.5-1 сек. - Приемлемая, но требует оптимизации")
    print("4. > 1 сек. - Требует срочной оптимизации")
    print("\n📈 Целевые показатели:")
    print("- Средняя задержка < 0.3 сек.")
    print("- Сообщений в секунду > 20")
    print("- Ошибок < 1%")

    # Сохраняем отчет в файл
    with open("stress_test_report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n📄 Полный отчет сохранен в: stress_test_report.txt")


def main():
    """Главная функция запуска теста"""
    print("""
    ╔══════════════════════════════════════════════════╗
    ║         НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ БОТА           ║
    ╚══════════════════════════════════════════════════╝

    Перед запуском убедитесь, что:
    1. Бот НЕ запущен через bot.infinity_polling()
    2. У вас установлены все зависимости
    3. Указан правильный токен бота
    4. Файл с ботом находится в той же папке

    Настройки теста можно изменить в начале файла:
    - NUM_USERS: Количество виртуальных пользователей
    - MESSAGES_PER_USER: Сообщений на пользователя
    - DELAY_BETWEEN_MESSAGES: Задержка между сообщениями
    - TEST_DURATION_SECONDS: Длительность теста

    Нажмите Enter для запуска теста...
    """)

    input()  # Ждем нажатия Enter

    try:
        asyncio.run(run_stress_test())
    except KeyboardInterrupt:
        print("\n\n❌ Тест прерван пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при запуске теста: {e}")


if __name__ == "__main__":
    main()