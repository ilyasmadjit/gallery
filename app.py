import os
import telebot
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

# Токен бота из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# ID чатов для пересылки
CHATS = {
    'Мередианная': '-1003306164529',
    'Краснококшайская': '-1003401940240',  # НОВЫЙ АДРЕС!
    'Шоссейная': '-1003254877531',
    'НЕРАСПОЗНАННЫЕ': '-1003285377080'  # НОВАЯ ГРУППА ДЛЯ НЕРАСПОЗНАННЫХ
}

# Список для хранения ошибок (в памяти)
failed_messages = []

@app.route('/')
def home():
    return "Telegram Bot Router is running! 🚀", 200

@app.route('/health')
def health_check():
    return "OK", 200

@app.route('/failed')
def show_failed():
    """Показывает все непересланные сообщения"""
    if not failed_messages:
        return "Нет непересланных сообщений ✅"
    
    html = "<h1>🚨 Непересланные сообщения</h1>"
    for msg in reversed(failed_messages[-20:]):  # Последние 20 сообщений
        html += f"""
        <div style='border:1px solid red; margin:10px; padding:10px;'>
            <p><strong>Время:</strong> {msg['time']}</p>
            <p><strong>Пользователь:</strong> {msg['user']}</p>
            <p><strong>Текст:</strong> {msg['text']}</p>
            <p><strong>Ошибка:</strong> {msg['error']}</p>
        </div>
        """
    return html

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработка вебхуков от Telegram"""
    print("=== ПОЛУЧЕН ВЕБХУК ОТ TELEGRAM ===")
    
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Error', 403

def save_failed_message(text, user, error):
    """Сохраняет информацию о неудачной пересылке"""
    log_entry = {
        'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'user': user,
        'text': text,
        'error': error
    }
    
    failed_messages.append(log_entry)
    
    # Сохраняем только последние 50 сообщений
    if len(failed_messages) > 50:
        failed_messages.pop(0)
    
    # Логируем в консоль
    print(f"⚠️ НЕПЕРЕСЛАННОЕ СООБЩЕНИЕ")
    print(f"   Время: {log_entry['time']}")
    print(f"   Пользователь: {user}")
    print(f"   Текст: {text}")
    print(f"   Ошибка: {error}")
    print("=" * 50)

@bot.message_handler(func=lambda message: True)
def route_message(message):
    """Маршрутизация сообщений по ключевым словам"""
    text = message.text or message.caption or ''
    user_info = f"{message.from_user.first_name or 'Unknown'} (ID: {message.from_user.id})"
    
    print(f"📨 Получено сообщение от {user_info}: {text}")
    
    # Определяем адрес по ключевым словам
    if 'Мередианная' in text:
        target_chat = CHATS['Мередианная']
        address = 'Мередианная'
        print("📍 Направляем в Мередианную")
    elif 'Краснококшайская' in text:
        target_chat = CHATS['Краснококшайская']
        address = 'Краснококшайская'
        print("📍 Направляем в Краснококшайскую")
    elif 'Шоссейная' in text:
        target_chat = CHATS['Шоссейная']
        address = 'Шоссейная'
        print("📍 Направляем в Шоссейную")
    else:
        print("❌ Адрес не распознан - отправляем в группу НЕРАСПОЗНАННЫХ")
        target_chat = CHATS['НЕРАСПОЗНАННЫЕ']
        address = 'НЕРАСПОЗНАННЫЕ'
    
    # Пересылаем сообщение
    try:
        print(f"🔄 Пытаемся переслать в чат {target_chat}")
        
        if address == 'НЕРАСПОЗНАННЫЕ':
            # Для нераспознанных отправляем с пометкой
            warning_text = f"⚠️ НЕРАСПОЗНАННЫЙ АДРЕС:\n{text}\n👤 От: {user_info}"
            bot.send_message(target_chat, warning_text)
        else:
            # Для распознанных - пересылаем оригинал
            bot.forward_message(target_chat, message.chat.id, message.message_id)
            
        print(f"✅ Успешно переслано в {address}")
        
    except Exception as e:
        error_msg = f"Ошибка пересылки в {address}: {str(e)}"
        print(f"❌ {error_msg}")
        
        # Сохраняем информацию об ошибке
        save_failed_message(text, user_info, error_msg)

if __name__ == '__main__':
    print("🚀 Telegram Bot Router запущен!")
    app.run(host='0.0.0.0', port=5000, debug=False)
