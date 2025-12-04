import telebot as tb  # @myyyyyy_bot_8K51T_bot
from telebot import types
import random
import sqlite3
from sentence_transformers import SentenceTransformer, util
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import pymorphy3

# YOUR_TOKEN_HERE
token = "YOUR_TOKEN_HERE"

bot = tb.TeleBot(token)

user_states = {}  # для отслеживания статуса пользователя
learning_sessions = {}

# Инициализация базы данных и создание таблицы, если ее еще не существует
def init_db():
    conn = sqlite3.connect('../presets.db', check_same_thread=False)
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
    conn = sqlite3.connect('../presets.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO presets (user_id, preset_name, preset_data)
        VALUES (?, ?, ?)
    ''', (user_id, preset_name, preset_data))
    conn.commit()
    conn.close()


# Функция для получения пресетов пользователя из бд
def get_user_presets_from_db(user_id):
    conn = sqlite3.connect('../presets.db', check_same_thread=False)
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

    def keywords(text):
        morph = pymorphy3.MorphAnalyzer()
        try:
            stop_words = set(stopwords.words('russian'))
        except LookupError:
            nltk.download('stopwords')
            stop_words = set(stopwords.words('russian'))

        stop_words.add('однако')
        try:
            text_tokenized = word_tokenize(text, language='russian')
        except LookupError:
            nltk.download('punkt_tab')
            text_tokenized = word_tokenize(text, language='russian')
        tokens = [word for word in text_tokenized if word.isalpha() or word.isnumeric()]

        i, t = 0, len(tokens) - 1
        while i < t:
            if tokens[i].lower() == 'не':
                tokens[i] += ' ' + tokens[i + 1]
                del tokens[i + 1]
                t -= 1
            i += 1

        filtered = []
        for token in tokens:
            if token.isalpha():
                wordnf = morph.parse(token)[0].normal_form
                if wordnf.replace('не ', '') not in stop_words:
                    filtered.append(wordnf)
            else:
                filtered.append(token)

        return filtered

    real_keywords, user_keywords = set(keywords(real_answer)), set(keywords(user_answer))
    if len(keywords(real_answer)) != 0:
        keyword_score = (len(user_keywords & real_keywords) / len(keywords(real_answer)))
    else:
        keyword_score = 0
    from math import ceil
    user_answer_tensor = model.encode(user_answer, convert_to_tensor=True)
    real_answer_tensor = model.encode(real_answer, convert_to_tensor=True)
    semantic_score = util.cos_sim(user_answer_tensor,real_answer_tensor).item()
    print(semantic_score, keyword_score)
    if semantic_score > 1: semantic_score = 1
    return ceil((semantic_score + 2 * keyword_score) / 3 * 100)

def blitz_check(preset,chat_id,bot,user_answer=None):
    if chat_id not in learning_sessions:
        pairs = [pair.split("==", 1) for pair in preset.split(";;") if pair.strip() and "==" in pair]
        random.shuffle(pairs)
        terms, definitions =zip(*pairs)
        learning_sessions[chat_id] = {
            "mode": "Блиц",
            "terms": terms,
            "definitions": definitions,
            "index":0, "correct": 0, "total":len(terms)
        }
    session = learning_sessions[chat_id]
    if user_answer is None:
        if session["index"] >= session["total"] :
            correct, total = session['correct'], session['total']
            percentage = (correct / total) * 100
            result = f"Блиц завершен!\n {correct}/{total} ({percentage:.1f}%)"
            bot.send_message(chat_id, result, reply_markup=menu_keyboard)
            learning_sessions.pop(chat_id)
            user_states[chat_id] = 'main_menu'
        else:
            question = f"({session['index'] + 1}/{session['total']})\n Определение: {session['definitions'][session['index']]}\n Напишите термин:"
            bot.send_message(chat_id, question, reply_markup=action_keyboard, parse_mode='Markdown')
    else:
        correct_term = session['terms'][session['index']]
        if user_answer.lower().strip() == correct_term.lower().strip():
            session['correct'] += 1
            bot.send_message(chat_id, "Правильно!", parse_mode='Markdown')
        else:
            bot.send_message(chat_id, f"Неправильно!\nПравильно: {correct_term}", parse_mode='Markdown')
        session['index'] += 1
        blitz_check(None, chat_id, bot)

def podrobno_check(preset,chat_id,bot,user_answer=None):
    if chat_id not in learning_sessions:
        pairs = [pair.split("==", 1) for pair in preset.split(";;") if pair.strip() and "==" in pair]
        random.shuffle(pairs)
        terms, definitions = zip(*pairs)
        learning_sessions[chat_id] = {
            "mode": "Подробный",
            "terms": terms,
            "definitions": definitions,
            "index": 0, "correct": 0, "total": len(terms), "skips": 0
        }
    session = learning_sessions[chat_id]
    if user_answer is None:
        if session["index"] >= session["total"]:
            correct, total = session['correct'], session['total']
            percentage = (correct / ((total - session['skips']) * 100)) * 100
            result = f"Подробный режим завершен!\n(Средняя точность {percentage:.1f}%)"
            bot.send_message(chat_id, result, reply_markup=menu_keyboard)
            learning_sessions.pop(chat_id)
            user_states[chat_id] = 'main_menu'
        else:
            question = f"({session['index'] + 1}/{session['total']})\n Термин: {session['terms'][session['index']]}\n Напишите определение:"
            bot.send_message(chat_id, question, reply_markup=action_keyboard, parse_mode='Markdown')
    else:
        correct_definition = session['definitions'][session['index']]
        similarity_score = check_answer(user_answer.strip(), correct_definition.strip())
        session['correct'] += similarity_score
        bot.send_message(chat_id, f"Точность вашего ответа ~{similarity_score}%", parse_mode='Markdown')

        if similarity_score < 90:
            bot.send_message(chat_id, f"Образец: {correct_definition}", parse_mode='Markdown')
        session['index'] += 1
        podrobno_check(None, chat_id, bot)


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
            if chat_id in current_preset and current_preset[chat_id] and chat_id in preset_name and preset_name[chat_id]:  # Если юзер ввел данные, то сохраняем
                save_preset_to_db(chat_id, preset_name[chat_id], current_preset[chat_id])
                bot.send_message(chat_id, f"Набор '{preset_name[chat_id]}' сохранен в базу данных!")

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
                                 f"Пара добавлена. Продолжайте вводить пары или нажмите 'Обратно'.",
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
                                 f"Пара(-ы) добавлена. Продолжайте вводить пары или нажмите 'Назад'.",
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
            bot.send_message(chat_id, f"Ваши наборы:\n{presets_list}\n\nВведите название набора (с учетом регистра):")

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

        if text == "Блиц":
            selected_preset_name = choice[chat_id]
            choice_index = preset_names[chat_id].index(selected_preset_name)
            preset_data = presets[chat_id][choice_index]
            blitz_check(preset_data, chat_id, bot)
            user_states[chat_id] = 'learning_in_progress'
        elif text == "Подробный":
            selected_preset_name = choice[chat_id]
            choice_index = preset_names[chat_id].index(selected_preset_name)
            preset_data = presets[chat_id][choice_index]
            podrobno_check(preset_data,chat_id,bot)
            user_states[chat_id] = 'learning_in_progress'

    elif current_state == 'learning_in_progress':
        if text == "Завершить":
            if chat_id in learning_sessions:
                session = learning_sessions.pop(chat_id)
                correct, total = session['correct'], session['total']
                if session['mode'] == 'Блиц':
                    bot.send_message(chat_id,
                f"Тест прерван\n {correct}/{total} {correct/total*100:.1f}%",
                    reply_markup=menu_keyboard)
                else:
                    bot.send_message(chat_id,
                    f"Тест прерван\n",
                    reply_markup=menu_keyboard)
            user_states[chat_id] = 'main_menu'
        elif text == "Пропустить":
            if chat_id in learning_sessions:
                session = learning_sessions[chat_id]
                session['index'] += 1
                if session['mode'] == 'Блиц':
                    blitz_check(None, chat_id, bot)
                else:
                    podrobno_check(None,chat_id, bot)
        else:

            if chat_id in learning_sessions:
                if learning_sessions[chat_id]['mode'] == 'Блиц':
                    blitz_check(None, chat_id, bot, user_answer=text)
                else:
                    podrobno_check(None, chat_id, bot, user_answer=text)
if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
