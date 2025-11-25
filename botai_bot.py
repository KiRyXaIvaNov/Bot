import telebot as tb  # @myyyyyy_bot_8K51T_bot
from telebot import types
import random
import os
import sqlite3
from sentence_transformers import SentenceTransformer, util

token = "YOUR_TOKEN_HERE"

bot = tb.TeleBot(token)

user_states = {}  # для отслеживания статуса пользователя
learning_sessions = {}


# # Этот код с бд не нужен
# if not os.path.exists('presets'):
#     os.mkdir('presets')

# Инициализация базы данных и создание таблицы, если ее еще не существует
def init_db():
    conn = sqlite3.connect('presets.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS presets (
            user_id INTEGER NOT NULL,
            preset_name TEXT NOT NULL,
            preset_data TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# Функция для сохранения пресета в бд
def save_preset_to_db(user_id, preset_name, preset_data):
    conn = sqlite3.connect('presets.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO presets (user_id, preset_name, preset_data)
        VALUES (?, ?, ?)
    ''', (user_id, preset_name, preset_data))
    conn.commit()
    conn.close()


# Функция для получения пресетов пользователя из бд
def get_user_presets_from_db(user_id):
    conn = sqlite3.connect('presets.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT preset_name, preset_data FROM presets 
        WHERE user_id = ?
    ''', (user_id,))
    presets = cursor.fetchall()
    conn.close()
    return presets


# Инициализируем базу данных при запуске
init_db()

current_preset = {}
preset_name = {}
preset_names, presets = {}, {}
choice = {}
chosen_preset = {}

# Создание главной клавиатуры
menu_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
menu_keyboard.row("Создать набор пар", "Инструкция")
menu_keyboard.row("Изучать")
#
# keyboard for Инструкция
instruction_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
instruction_keyboard.row("Обратно")

# keyboard for Изучать
learn_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
learn_keyboard.row("Выберите набор пар")
learn_keyboard.row("Блиц", "Подробный")
learn_keyboard.row("Обратно")

# режим
learn_mode_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
learn_mode_keyboard.row("Блиц", "Подробный")
learn_mode_keyboard.row("Обратно")

# для создания пар
create_pairs_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
create_pairs_keyboard.row("Обратно")

action_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
action_keyboard.row("Пропустить", "Завершить")  # Кнопки для действий в режиме обучения

model = SentenceTransformer('all-MiniLM-L6-v2')

def check_answer(user_answer: str, real_answer: str) -> int:
    """
    :param user_answer: ответ пользователя
    :param real_answer: ответ, который должен быть
    :return: схожесть ответа в процентах
    """
    from math import ceil
    user_answer_tensor = model.encode(user_answer, convert_to_tensor=True)
    real_answer_tensor = model.encode(real_answer, convert_to_tensor=True)
    score = util.cos_sim(user_answer_tensor,real_answer_tensor)
    return ceil(score.item()*100)

def blitz_check():
    return True


def podrobno_check():
    return True


@bot.message_handler(commands=['start'])
def button_message(message):
    """
    По команде старт выдаются кнопки
    Устанавливаем главное меню и состояние
    """
    chat_id = message.chat.id  # id пользователя для уникальности переменных
    bot.send_message(message.chat.id, 'Выберите что вам надо', reply_markup=menu_keyboard)
    user_states[chat_id] = 'main_menu'  # переводим статус в "главное меню"


# основной обработчик
@bot.message_handler(content_types=['text'])
def is_button_press(message):
    """
    Обрабатывает нажатия
    """

    chat_id = message.chat.id
    text = message.text
    current_state = user_states.get(chat_id, 'main_menu')
    if current_state == "waiting_for_pairs":  # обрабатываем состояние "ввод пар"

        if text == "Обратно":
            bot.send_message(chat_id, "Возвращаемся", reply_markup=menu_keyboard)
            user_states[chat_id] = 'main_menu'
            if chat_id in current_preset and current_preset[chat_id] and chat_id in preset_name and preset_name[
                chat_id]:  # Если юзер ввел данные, то сохраняем
                save_preset_to_db(chat_id, preset_name[chat_id], current_preset[chat_id])
                bot.send_message(chat_id, f"Набор '{preset_name[chat_id]}' сохранен в базу данных!")

            # #Этот код не нужен с бд
            # if current_preset[chat_id]:      # если есть пресет
            #     presetsfile = open('presets/' + str(chat_id) + '.txt', 'a') # открываем создавшийся под пресет файл
            #     presetsfile.write(f'{preset_name[chat_id]}$${current_preset[chat_id]}\n\n') # записываем пары
            #     presetsfile.close()

        if not preset_name[chat_id] and text != "Обратно":  # если нет пресета, создаем пары
            preset_name[chat_id] = text
            bot.send_message(chat_id,
                             f"Теперь можно вводить пары",
                             reply_markup=create_pairs_keyboard)

        elif "==" in text and ";;" in text:  # парсим пары
            pairs_message = [[x.strip() for x in pair.split('==')] for pair in text.strip(';;').split(';;')]
            if all(pairs_message):
                current_preset[chat_id] += ';;'.join(['=='.join(pair) for pair in pairs_message]) + ';;'
                bot.send_message(chat_id,
                                 f"Пара добавлена. Продолжайте вводить пары или нажмите 'Назад'.",
                                 reply_markup=create_pairs_keyboard)
            else:
                bot.send_message(chat_id,
                                 'Пожалуйста, введите термин и определение в формате "Термин==Определение;;Термин==Определение". Обе части должны быть заполнены.',
                                 reply_markup=create_pairs_keyboard)
        elif "==" in text:
            pairs_message = [x.strip() for x in text.strip(';;').split('==')]
            if all(pairs_message):
                if chat_id not in current_preset:
                    current_preset[chat_id] = ''
                current_preset[chat_id] += '=='.join(pairs_message) + ';;'
                bot.send_message(chat_id,
                                 f"Пара добавлена. Продолжайте вводить пары или нажмите 'Назад'.",
                                 reply_markup=create_pairs_keyboard)
            else:
                bot.send_message(chat_id,
                                 'Пожалуйста, введите термин и определение в формате "Термин==Определение;;Термин==Определение". Обе части должны быть заполнены.',
                                 reply_markup=create_pairs_keyboard)
        elif text != "Обратно":
            bot.send_message(chat_id,
                             'Пожалуйста, введите термин и определение в формате "Термин==Определение;;Термин==Определение". Обе части должны быть заполнены.',
                             reply_markup=create_pairs_keyboard)
    # выбираем пресет
    elif current_state == 'preset_choice':
        if text == "Обратно":
            bot.send_message(chat_id, "Возвращаемся", reply_markup=menu_keyboard)
            user_states[chat_id] = 'main_menu'
            return

        # Получение пресетов из бд
        user_presets = get_user_presets_from_db(chat_id)
        preset_names[chat_id] = [preset[0] for preset in user_presets]
        presets[chat_id] = [preset[1] for preset in user_presets]

        if not choice[chat_id]:
            choice[chat_id] = text

        if choice[chat_id] in preset_names[chat_id]:
            selected_preset_name = choice[chat_id]
            choice_index = preset_names[chat_id].index(selected_preset_name)
            chosen_preset[chat_id] = presets[chat_id][choice_index]
            user_states[chat_id] = 'learning_mode_selection'
            bot.send_message(chat_id, f"Выбран набор: '{selected_preset_name}'. Выберите режим изучения:",
                             reply_markup=learn_mode_keyboard)
        else:
            bot.send_message(chat_id, "Введённое название не найдено в списке", reply_markup=instruction_keyboard)
            choice[chat_id] = ''

    # обработка создания пар, перевод состояния в "ввод пар"
    elif current_state == "main_menu":
        if text == "Создать набор пар":
            bot.send_message(chat_id,
                             'Отдельным сообщением введите название. После этого вводите пары терминов и определений в формате "Термин==Определение" по одному в'
                             ' сообщении или в формате "Термин==Определение;;Термин==Определение" по несколько за сообщение.\n',
                             reply_markup=create_pairs_keyboard)
            user_states[chat_id] = 'waiting_for_pairs'  # Меняем состояние
            current_preset[chat_id] = ''
            preset_name[chat_id] = ''

        elif text == "Инструкция":
            instruction_text = """
Это инструкцию к чат-боту "Ботай-бот".
Кнопка "Создать пары": вы вводите свои пары "термин-определение", которые вы хотите изучить.
Кнопка "Изучать" подразделяется на два режима: "блиц" и "подробный".
Блиц - пользователь по определению должен написать термин по выданному определению.
Подробный - пользователь по термину должен дать подробное определение.
                    """
            bot.send_message(chat_id, instruction_text, reply_markup=instruction_keyboard)
            # Состояние остается 'main_menu', если клавиатура инструкции не меняет состояние

        elif text == "Изучать":
            bot.send_message(chat_id, "Выберите набор пар для изучения:", reply_markup=instruction_keyboard)
            user_states[chat_id] = 'preset_choice'

            # Получаем пресеты из базы данных
            user_presets = get_user_presets_from_db(chat_id)

            if not user_presets:
                bot.send_message(chat_id, "У вас пока нет сохраненных наборов.")
                user_states[chat_id] = 'main_menu'
                return

            preset_names[chat_id] = [preset[0] for preset in user_presets]
            presets[chat_id] = [preset[1] for preset in user_presets]

            # Показываем список доступных пресетов
            presets_list = "\n".join([f"• {name}" for name in preset_names[chat_id]])
            bot.send_message(chat_id, f"Ваши наборы:\n{presets_list}\n\nВведите название набора:")

            # # Код больше не нужен с бд
            # with open('presets/' + str(chat_id) + '.txt', 'r') as file:
            #     name_preset_pairs = [x.split('$$') for x in list(file) if x != '\n']
            #     preset_names[chat_id] = [x[0] for x in name_preset_pairs] # тут обработанные пресет-неймы!
            #     presets[chat_id] = [x[1].strip() for x in name_preset_pairs] # тут обработанные пресеты!

            # bot.send_message(chat_id, f"{'\n'.join(preset_names[chat_id])}")

            choice[chat_id] = ''

        elif text == "Обратно":  # Обработка "Обратно" из главного меню (если бы она там была)
            # Эта ветка, скорее всего, не выполнится, если "Обратно" есть только в подменю.
            # Но для полноты:
            bot.send_message(chat_id, "Вы уже в главном меню.", reply_markup=menu_keyboard)

        else:
            # Если в главном меню ввели что-то непонятное
            bot.send_message(chat_id, "Неизвестная команда. Пожалуйста, выберите опцию из меню.",
                             reply_markup=menu_keyboard)

    elif current_state == 'learning_mode_selection':

        if text == "Обратно":
            bot.send_message(chat_id, "Возвращаемся в главное меню:", reply_markup=menu_keyboard)
            user_states[chat_id] = 'main_menu'
            return
        '''сюда дописать выбор режимов и проверку по пресету, проверки черех объявленные в начале кода функциях'''


if __name__ == '__main__':
    print("Бот запущен...")

    bot.infinity_polling()
