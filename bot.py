import telebot, os
from telebot import types

from utils import User, fcs_validator, birth_date_validator, count_age
from utils import phone_number_validation, exist_user, add_user_db, user_status

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
user_dict = {}

@bot.message_handler(commands=['start',])
def send_welcome(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardRemove()
    if not exist_user(chat_id):
        user = User()
        user.chat_id = chat_id
        user_dict[chat_id] = user
        msg = bot.reply_to(message, 'Привет. Ты здесь впервые, поэтому давай зарегистрируемся. Введи свои ФИО.', reply_markup=markup)
        bot.register_next_step_handler(msg, process_name_step)
    else:
        user = exist_user(chat_id)
        user_dict[chat_id] = user
        st = 'Привет, {}. Ты как всегда можешь узнать информацию о себе набрав "/info"'.format(user.name)
        msg = bot.reply_to(message, st, reply_markup=markup)
        bot.register_next_step_handler(msg, process_info_stage)

def process_name_step(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    if fcs_validator(message.text):
        user.surname, user.name, user.patronymic = [title.capitalize() for title in message.text.split()]
        msg = bot.reply_to(message, 'Теперь введи дату рождения в формате ДД.ММ.ГГГГ')
        bot.register_next_step_handler(msg, process_age_step)
    else:
        msg = bot.reply_to(message, 'Неверный формат ФИО. Пример правильного "Пупкин Иван Петрович"')
        bot.register_next_step_handler(msg, process_name_step)

def process_age_step(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    if birth_date_validator(message.text):
        user.age = count_age(message.text)
        btn = types.KeyboardButton(text='Поделиться телефоном', request_contact=True)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(btn)
        st = """Теперь введи номер своего телефона или поделись контактом. Если будешь вводить вручную - вводи только
        цифры, без + и ()"""
        msg = bot.reply_to(message, st, reply_markup=markup)
        bot.register_next_step_handler(msg, process_phone_step)
    else:
        msg = bot.reply_to(message, 'Неверный формат даты. Пример правльного "29.12.2008"')
        bot.register_next_step_handler(msg, process_age_step)

def process_phone_step(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    markup = types.ReplyKeyboardRemove()
    text = (message.text or message.contact.phone_number[1:])
    if not phone_number_validation(text)[0]:
        msg = bot.reply_to(message, 'Неверный формат номера телефона. Попробуй еще раз.')
        bot.register_next_step_handler(msg, process_phone_step)
    elif not phone_number_validation(text)[1]:
        msg = bot.reply_to(message, 'Такой номер телефона уже кем-то используется. Введи, пожалуйста другой.')
        bot.register_next_step_handler(msg, process_phone_step)
    else:
        user.phone = text
        user.status = user_status(user.phone)
        add_user_db(user)
        st = 'Поздравляю. Теперь ты зарегистрирован. В любое время напиши мне "/info" и я сообщу о твоей принадлежности рангу'
        msg = bot.reply_to(message, st, reply_markup=markup)
        bot.clear_step_handler_by_chat_id(user.chat_id)
        # bot.register_next_step_handler(msg, process_info_stage)

@bot.message_handler(commands=['info'])
def process_info_stage(message):
    chat_id = message.chat.id
    try:
        user = user_dict[chat_id]
    except KeyError:
        btn = types.KeyboardButton(text='Вспомни пожалуйста')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(btn)
        msg = bot.reply_to(message, 'Вспоминаю тебя', reply_markup=markup)
        bot.register_next_step_handler(msg, send_welcome)
    else:
        if user.status[0] == 'Ranked':
            inf = 'Вы принадлежите рангу'
        else:
            inf = 'Вы не принадлежите рангу'
        msg = bot.reply_to(message, inf)

bot.enable_save_next_step_handlers(delay=2)

bot.load_next_step_handlers()

bot.polling()
