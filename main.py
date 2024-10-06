import telebot
import sqlite3
import json
from telebot import types
from config import *

# Инициализация бота
bot = telebot.TeleBot(API_TOKEN)

# Подключение к базе данных
conn = sqlite3.connect('support_requests.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы для запросов
cursor.execute('''
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    department TEXT,
    message TEXT,
    status TEXT DEFAULT 'open'
)
''')
conn.commit()

# Загрузка часто задаваемых вопросов из JSON файла
with open('faq.json', 'r', encoding='utf-8') as faq_file:
    faq_data = json.load(faq_file)

# Приветственное сообщение с клавиатурой
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🛒 Часто задаваемые вопросы")
    btn2 = types.KeyboardButton("👨‍💻 Связаться с программистами")
    btn3 = types.KeyboardButton("💼 Связаться с отделом продаж")
    markup.add(btn1, btn2, btn3)

    bot.send_message(message.chat.id, "👋 Привет! Я бот поддержки интернет-магазина \"Продаем все на свете\"!\nЧем могу помочь?", reply_markup=markup)

# Функция для автоматического ответа на вопросы из FAQ
def send_faq(message):
    faq_list = "\n\n".join([f"❓ *{q}*\n{a}" for q, a in faq_data.items()])
    bot.send_message(message.chat.id, f"*Часто задаваемые вопросы:*\n\n{faq_list}", parse_mode="Markdown")


# Функция для записи запроса в базу данных
def log_request(user_id, username, department, message):
    cursor.execute('INSERT INTO requests (user_id, username, department, message) VALUES (?, ?, ?, ?)',
                   (user_id, username, department, message))
    conn.commit()

# Обработка нажатий на кнопки клавиатуры
@bot.message_handler(func=lambda message: message.text in ["🛒 Часто задаваемые вопросы", "👨‍💻 Связаться с программистами", "💼 Связаться с отделом продаж"])
def handle_keyboard_buttons(message):
    user_id = message.from_user.id
    username = message.from_user.username
    user_message = message.text

    # Обработка нажатия кнопки
    if user_message == "🛒 Часто задаваемые вопросы":
        send_faq(message)
    elif user_message == "👨‍💻 Связаться с программистами":
        bot.reply_to(message, "👨‍💻 Ваш запрос направлен к программистам. Мы свяжемся с вами.")
        log_request(user_id, username, 'Программисты', user_message)
    elif user_message == "💼 Связаться с отделом продаж":
        bot.reply_to(message, "💼 Ваш запрос направлен в отдел продаж. Мы скоро свяжемся с вами.")
        log_request(user_id, username, 'Отдел продаж', user_message)

# Обработка текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_message(message):
    user_id = message.from_user.id
    username = message.from_user.username
    user_message = message.text.lower()

    # Проверка на наличие вопроса в базе часто задаваемых вопросов (FAQ)
    found_answer = None
    department = 'Общий'  # По умолчанию присвоим общий департамент
    for question, answer in faq_data.items():
        if question.lower() in user_message:
            found_answer = answer
            department = 'FAQ'  # Если ответ найден в FAQ, укажем это как департамент
            break

    if found_answer:
        bot.reply_to(message, found_answer)
    # Проверка на запрос к программистам или отделу продаж
    elif 'сайт' in user_message or 'оплата' in user_message:
        department = 'Программисты'
        bot.reply_to(message, "👨‍💻 Ваш запрос направлен к программистам. Мы свяжемся с вами.")
    elif 'товар' in user_message or 'доставка' in user_message:
        department = 'Отдел продаж'
        bot.reply_to(message, "💼 Ваш запрос направлен в отдел продаж. Мы скоро свяжемся с вами.")
    else:
        bot.reply_to(message, "Ваш запрос не распознан, но мы обработаем его и передадим нужному специалисту.")

    # Логирование запроса в базу данных
    log_request(user_id, username, department, user_message)

# Обработка голосовых сообщений
@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    user_id = message.from_user.id
    username = message.from_user.username
    file_id = message.voice.file_id
    
    # Получаем файл аудио через Telegram API
    file_info = bot.get_file(file_id)
    voice_file = bot.download_file(file_info.file_path)

    # Логирование голосового сообщения
    log_request(user_id, username, 'Голосовое сообщение', 'Голосовое сообщение получено')

    # Ответ пользователю
    bot.reply_to(message, "🎤 Ваше голосовое сообщение получено, мы его обработаем и передадим нужному специалисту.")

# Старт бота
if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)
