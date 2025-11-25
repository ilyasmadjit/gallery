import os
import telebot
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

# Токен вашего НОВОГО бота (создать через @BotFather)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# ID чатов для пересылки
CHATS = {
    'Мередианная': '-1003306164529',
    'Краснококшайская': '-1003262447183',
    'Шоссейная': '-1003254877531',
    'НЕРАСПОЗНАННЫЕ': '-1003285377080'
}

# Ваш личный user_id (чтобы бот работал только с вами)
YOUR_USER_ID = "2092701268"  # Заменить на ваш ID из @userinfobot

@app.route('/')
def home():
    return "Bot Interceptor is running! 🚀", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработка вебхуков от Telegram"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Error', 403

@bot.message_handler(func=lambda message: True)
def intercept_message(message):
    """Перехватывает все сообщения в личке с ботом"""
    
    # Проверяем, что сообщение от вас
    if str(message.from_user.id) != YOUR_USER_ID:
        print(f"Игнорируем сообщение не от владельца: {message.from_user.id}")
        return
    
    text = message.text or message.caption or ''
    print(f"📨 Перехвачено сообщение: {text}")
    
    # Определяем адрес по ключевым словам
    if 'Мередианная' in text:
        target_chat = CHATS['Мередианная']
        address = 'Мередианная'
    elif 'Краснококшайская' in text:
        target_chat = CHATS['Краснококшайская']
        address = 'Краснококшайская'
    elif 'Шоссейная' in text:
        target_chat = CHATS['Шоссейная']
        address = 'Шоссейная'
    else:
        target_chat = CHATS['НЕРАСПОЗНАННЫЕ']
        address = 'НЕРАСПОЗНАННЫЕ'
    
    # Пересылаем сообщение
    try:
        if address == 'НЕРАСПОЗНАННЫЕ':
            # Для нераспознанных отправляем с пометкой
            warning_text = f"⚠️ НЕРАСПОЗНАННЫЙ АДРЕС:\n{text}"
            bot.send_message(target_chat, warning_text)
        else:
            # Для распознанных - пересылаем оригинал
            bot.forward_message(target_chat, message.chat.id, message.message_id)
        
        print(f"✅ Переслано в {address}")
        
        # Подтверждаем вам
        bot.reply_to(message, f"✅ Переслано в {address}")
        
    except Exception as e:
        error_msg = f"❌ Ошибка пересылки: {e}"
        print(error_msg)
        bot.reply_to(message, error_msg)

if __name__ == '__main__':
    print("🚀 Bot Interceptor запущен!")
    app.run(host='0.0.0.0', port=5000, debug=False)
