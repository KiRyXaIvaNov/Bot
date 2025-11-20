import telebot as tb #@myyyyyy_bot_8K51T_bot
from telebot import types
import random
import os

token = "7590824294:AAEd8iddy-yDg06s0sQgspfMBpxjdE_gE04"
bot = tb.TeleBot(token)

user_states = {} # для отслеживания статуса пользователя
learning_sessions = {}

if not os.path.exists('presets'):
    os.mkdir('presets')

#Создание главной клавиатуры
menu_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
menu_keyboard.row("Создать пары", "Инструкция")
menu_keyboard.row("Изучать")
#
#keyboard for Инструкция
instruction_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
instruction_keyboard.row("Обратно")

#keyboard for ИЗучать
learn_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
learn_keyboard.row("Выберите набор пар")
learn_keyboard.row("Блиц", "Подробный")
learn_keyboard.row("Обратно")

#режим
learn_mode_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
learn_mode_keyboard.row("Блиц", "Подробный")
learn_mode_keyboard.row("Обратно")

# для создания пар
create_pairs_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
create_pairs_keyboard.row("Обратно")

action_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
action_keyboard.row("Пропустить", "Завершить") # Кнопки для действий в режиме обучения
@bot.message_handler(commands=['start'])
def button_message(message):
    """
    По команде старт выдаются кнопки
    Устанавливаем главное меню и состояние
    """
    chat_id = message.chat.id
    bot.send_message(message.chat.id,'Выберите что вам надо',reply_markup=menu_keyboard)
   #if chat_id not in termins_dict:
   #    termins_dict[chat_id] = {}
#   if os.path.exists('presets') and str(chat_id)+ '.txt' not in os.listdir('presets'):
#       os.mkdir('presets')
#       presets = open('presets/' + str(chat_id) + '.txt', 'w')
#       presets.close()
    user_states[chat_id] = 'main_menu'

# основной обработчик
@bot.message_handler(content_types= ['text'])
def is_button_press(message):
    """
    Обрабатывает нажатия
    """

    chat_id = message.chat.id
    text = message.text
    current_state = user_states.get(chat_id, 'main_menu')
    if current_state == "waiting_for_pairs":
        presets = open('presets/' + str(chat_id) + '.txt', 'a')
        if text == "Обратно":
            bot.send_message(chat_id, "Возвращаемся", reply_markup=menu_keyboard)
            user_states[chat_id] = 'main_menu'
            presets.write('\n\n')
            presets.close()
        elif "==" in text and ";;" in text:
            pairs_message = [[x.strip() for x in pair.split('==')] for pair in text.strip(';;').split(';;')]
            if all(pairs_message):
                presets.write(';;'.join(['=='.join(pair) for pair in pairs_message]) + ';;')
                bot.send_message(chat_id,
                                 f"Пара добавлена. Продолжайте вводить пары или нажмите 'Назад'.",
                                 reply_markup=create_pairs_keyboard)
            else:
                bot.send_message(chat_id,
                                 'Пожалуйста, введите термин и определение в формате "Термин==Определение;;Термин==Определение". Обе части должны быть заполнены.',
                                 reply_markup=create_pairs_keyboard)
        elif "==" in text:
            pairs_message = [x.strip() for x in text.split('==')]
            if all(pairs_message):
                presets.write('=='.join(pairs_message) + ';;')
                bot.send_message(chat_id,
                                 f"Пара добавлена. Продолжайте вводить пары или нажмите 'Назад'.",
                                 reply_markup=create_pairs_keyboard)
            else:
                bot.send_message(chat_id,
                                 'Пожалуйста, введите термин и определение в формате "Термин==Определение;;Термин==Определение". Обе части должны быть заполнены.',
                                 reply_markup=create_pairs_keyboard)

        '''
        elif ':' in text or '-' in text:  # Проверяем наличие разделителя
            separator = None
            if ':' in text:
                separator = ':'
            elif '-' in text:
                separator = '-'
#git config --global user.name KiRyXaIvaNov git config --global user.email kirillka2007@list.ru
            if separator:
                try:
                    term, definition = text.split(separator, 1)
                    term = term.strip()
                    definition = definition.strip()

                    if term and definition:

                        
                        if chat_id not in termins_dict:  # На всякий случай
                            termins_dict[chat_id] = {}
                        termins_dict[chat_id][term] = definition
                        print(termins_dict)
                        
                        # Сообщение об успехе и остаемся в том же состоянии
                        bot.send_message(chat_id,
                                         f"Пара '{term}' - '{definition}' добавлена. Продолжайте вводить пары или нажмите 'Назад'.",
                                         reply_markup=create_pairs_keyboard)
                        # Состояние user_states[chat_id] остается 'waiting_for_pairs'
                    else:
                        bot.send_message(chat_id,
                                         "Пожалуйста, введите термин и определение через двоеточие или тире. Обе части должны быть заполнены.",
                                         reply_markup=create_pairs_keyboard)
                except Exception as e:  # Ловим любое исключение
                    print(f"Ошибка при обработке пары: {e}")  # Для отладки
                    bot.send_message(chat_id, "Произошла ошибка при распознавании пары. Попробуйте снова.",
                                     reply_markup=create_pairs_keyboard)
            else:
                bot.send_message(chat_id,
                                 "Пожалуйста, используйте двоеточие (:) или тире (-) для разделения термина и определения.",
                                 reply_markup=create_pairs_keyboard)
        else:
            # Если пользователь в режиме ввода, но ввел что-то другое (не "Назад", не пару)
            bot.send_message(chat_id,
                             "Вы находитесь в режиме ввода пар. Введите 'Термин: Определение' или нажмите 'Назад'.",
                             reply_markup=create_pairs_keyboard)
        return  # Обработали в режиме ожидания, выходим
    
    '''






    elif current_state == "main_menu":
        if text == "Создать пары":
            bot.send_message(chat_id,
                             'Введите пары термином и определений в формате "Термин==Определение" по одному в'
                             ' сообщении или в формате "Термин==Определение;;Термин==Определение" по несколько за сообщение.\n',
                             reply_markup=create_pairs_keyboard)
            user_states[chat_id] = 'waiting_for_pairs'  # Меняем состояние

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
            bot.send_message(chat_id, "Выберите набор пар для изучения:", reply_markup=learn_keyboard)
            # Состояние остается 'main_menu', если клавиатура изучения не меняет состояние

        elif text == "Обратно":  # Обработка "Обратно" из главного меню (если бы она там была)
            # Эта ветка, скорее всего, не выполнится, если "Обратно" есть только в подменю.
            # Но для полноты:
            bot.send_message(chat_id, "Вы уже в главном меню.", reply_markup=menu_keyboard)

        else:
            # Если в главном меню ввели что-то непонятное
            bot.send_message(chat_id, "Неизвестная команда. Пожалуйста, выберите опцию из меню.",
                             reply_markup=menu_keyboard)

        
    elif text == "Обратно":
        bot.send_message(chat_id, "Возвращаемся в главное меню:", reply_markup=menu_keyboard)
        user_states[chat_id] = 'main_menu'

    elif text == "Выберите набор пар":
        bot.send_message(chat_id, "Выберите режим изучения:", reply_markup=learn_mode_keyboard)

    elif text == "Блиц":
        bot.send_message(chat_id, "Режим блиц активирован!",
                         reply_markup=learn_mode_keyboard)  # Остаемся в режиме изучения
    elif text == "Подробный":
        bot.send_message(chat_id, "Режим подробного изучения активирован!",
                         reply_markup=learn_mode_keyboard)  # Остаемся в режиме изучения

    elif current_state == 'learning_mode_selection':
        # сюда вываливается список со строками-пресетами
        preset_list = list(open('presets/' + str(chat_id) + '.txt', 'r'))

        if text == "Обратно":
            bot.send_message(chat_id, "Возвращаемся в главное меню:", reply_markup=menu_keyboard)
            user_states[chat_id] = 'main_menu'
            return

          # переделать с нуля
        elif text == "Блиц":
            # Переходим в режим блица, но сначала нужно подготовить пары
            terms = ['a', 'b', 'c']
            if not terms:
                bot.send_message(chat_id, "У вас пока нет сохраненных пар для изучения. Создайте их!",
                                 reply_markup=learn_keyboard)
                return
            random.shuffle(terms)
            learning_sessions[chat_id] = {
                'mode': 'blitz',
                'current_term_index': 0,
                'score': {'correct': 0, 'total': 0},
                'terms_to_learn': terms
            }
            user_states[chat_id] = 'in_blitz_mode'

            return


    elif text == "Обратно":
        bot.send_message(chat_id, "Возвращаемся в главное меню:", reply_markup=menu_keyboard)
        user_states[chat_id] = 'main_menu'
        return



if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
