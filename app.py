import os
import telebot
from flask import Flask, request

app = Flask(__name__)

# Токен бота из переменных окружения (правильно)
BOT_TOKEN = os.environ.get('BOT_TOKEN')  # Только имя переменной!
bot = telebot.TeleBot(BOT_TOKEN)  # Переименовано в bot

# ID чатов для пересылки
CHATS = {
    'Мередианная': '-1003306164529',    # В кавычках - ок
    'Краснокошайская': '-1003262447183', # Добавить кавычки
    'Шоссейная': '-1003254877531'        # Добавить кавычки
}

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Error', 403

@bot.message_handler(func=lambda message: True)
def route_message(message):
    text = message.text or message.caption or ''
    
    # Определяем адрес по ключевым словам
    if 'Мередианная' in text:
        target_chat = CHATS['Мередианная']
    elif 'Краснокошайская' in text:
        target_chat = CHATS['Краснокошайская']
    elif 'Шоссейная' in text:
        target_chat = CHATS['Шоссейная']
    else:
        # Если адрес не распознан, можно обработать особым образом
        return
    
    # Пересылаем сообщение
    try:
        if message.text:
            bot.send_message(target_chat, text)
        elif message.photo:
            bot.send_photo(target_chat, message.photo[-1].file_id, caption=text)
        # Добавьте обработку других типов сообщений при необходимости
    except Exception as e:
        print(f"Ошибка при пересылке: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
