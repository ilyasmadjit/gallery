import os
import telebot
from flask import Flask, request
from datetime import datetime
import time
import requests

app = Flask(__name__)

# Токен вашего НОВОГО бота (создать через @BotFather)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# Увеличиваем таймауты для бота
bot._api_request_timeout = 30  # 30 секунд таймаут

# ID чатов для пересылки
CHATS = {
    'Мередианная': '-1003306164529',
    'Краснококшайская': '-1003262447183',
    'Шоссейная': '-1003254877531',
    'НЕРАСПОЗНАННЫЕ': '-1003285377080'
}

# Ваш личный user_id (чтобы бот работал только с вами)
YOUR_USER_ID = "ВАШ_USER_ID"  # Заменить на ваш ID из @userinfobot

def send_with_retry(chat_id, text, max_retries=3):
    """Отправляет сообщение с повторными попытками при ошибках"""
    for attempt in range(max_retries):
        try:
            bot.send_message(chat_id, text)
            return True
        except Exception as e:
            print(f"❌ Попытка {attempt + 1} не удалась: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Ждем 2 секунды перед повторной попыткой
            else:
                return False
    return False

def forward_with_retry(chat_id, from_chat_id, message_id, max_retries=3):
    """Пересылает сообщение с повторными попытками при ошибках"""
    for attempt in range(max_retries):
        try:
            bot.forward_message(chat_id, from_chat_id, message_id)
            return True
        except Exception as e:
            print(f"❌ Попытка пересылки {attempt + 1} не удалась: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Ждем 2 секунды перед повторной попыткой
            else:
                return False
    return False

@app.route('/')
def home():
    return "Bot Interceptor is running! 🚀", 200

@app.route('/health')
def health_check():
    return "OK", 200

@app.route('/check_telegram')
def check_telegram():
    """Проверяет доступность Telegram API"""
    try:
        response = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getMe', timeout=10)
        if response.status_code == 200:
            return "✅ Telegram API доступен"
        else:
            return f"❌ Telegram API недоступен: {response.status_code}"
    except Exception as e:
        return f"❌ Ошибка подключения к Telegram: {e}"

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
    
    # Пересылаем сообщение с повторными попытками
    try:
        if address == 'НЕРАСПОЗНАННЫЕ':
            # Для нераспознанных отправляем с пометкой
            warning_text = f"⚠️ НЕРАСПОЗНАННЫЙ АДРЕС:\n{text}"
            success = send_with_retry(target_chat, warning_text)
        else:
            # Для распознанных - пересылаем оригинал
            success = forward_with_retry(target_chat, message.chat.id, message.message_id)
        
        if success:
            print(f"✅ Переслано в {address}")
            bot.reply_to(message, f"✅ Переслано в {address}")
        else:
            error_msg = "❌ Не удалось переслать после нескольких попыток"
            print(error_msg)
            bot.reply_to(message, error_msg)
        
    except Exception as e:
        error_msg = f"❌ Критическая ошибка: {e}"
        print(error_msg)
        bot.reply_to(message, error_msg)

if __name__ == '__main__':
    print("🚀 Bot Interceptor запущен!")
    app.run(host='0.0.0.0', port=5000, debug=False)
