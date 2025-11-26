import os
import telebot
from flask import Flask, request
from datetime import datetime
import re

app = Flask(__name__)

# Токен вашего бота
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# ID чатов для пересылки
CHATS = {
    'Мередианная': '-1003306164529',
    'Краснококшайская': '-1003262447183', 
    'Шоссейная': '-1003254877531',
    'НЕРАСПОЗНАННЫЕ': '-1003285377080'
}

def parse_exact_format(body):
    """Точный парсинг формата Мехт"""
    booking_data = {
        'address': None,
        'guest_name': None,
        'people_count': None,
        'date_time': None,
        'phone': None,
        'record_url': None,
        'notification_date': None
    }
    
    # ТОЧНОЕ соответствие формату
    
    # Телефон (строка после "Телефон: ")
    phone_match = re.search(r'Телефон:\s*([^\n]+)', body)
    if phone_match:
        booking_data['phone'] = phone_match.group(1).strip()
    
    # Запись диалога (URL)
    record_match = re.search(r'Запись диалог:\s*([^\n]+)', body)
    if record_match:
        booking_data['record_url'] = record_match.group(1).strip()
    
    # Дата оповещения
    notify_match = re.search(r'Дата оповещения\s*([^\n]+)', body)
    if notify_match:
        booking_data['notification_date'] = notify_match.group(1).strip()
    
    # Резюме диалога (блок)
    summary_match = re.search(r'Резюме диалога:(.*?)(?=< Пред\.|$)', body, re.DOTALL)
    if summary_match:
        summary_text = summary_match.group(1)
        
        # Имя гостя (строго по формату)
        name_match = re.search(r'Имя гостя\s*([^\n]+)', summary_text)
        if name_match:
            booking_data['guest_name'] = name_match.group(1).strip()
        
        # Адрес (строго по формату)
        address_match = re.search(r'Адрес\s*([^\n]+)', summary_text)
        if address_match:
            booking_data['address'] = address_match.group(1).strip()
        
        # Количество человек (строго по формату)
        people_match = re.search(r'Сколько человек\s*([^\n]+)', summary_text)
        if people_match:
            booking_data['people_count'] = people_match.group(1).strip()
        
        # Дата и время (строго по формату)
        date_match = re.search(r'Дата и время\s*([^\n]+)', summary_text)
        if date_match:
            booking_data['date_time'] = date_match.group(1).strip()
    
    return booking_data

@app.route('/')
def home():
    return "Email to Telegram Router is running! 🚀", 200

@app.route('/email_webhook', methods=['POST'])
def email_webhook():
    """Принимаем письма от n8n"""
    try:
        # Данные письма от n8n
        email_data = request.get_json()
        
        # Извлекаем тему и текст письма
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        from_email = email_data.get('from', '')
        
        print(f"📧 Получено письмо: {subject}")
        
        # Парсим СТРОГО по формату Мехт
        booking = parse_exact_format(body)
        
        # Определяем адрес ТОЛЬКО из поля "Адрес"
        if booking['address']:
            address = booking['address']
        else:
            address = 'НЕРАСПОЗНАННЫЕ'
        
        # Определяем целевой чат
        target_chat = CHATS.get(address, CHATS['НЕРАСПОЗНАННЫЕ'])
        
        # Форматируем сообщение ТОЧНО как в примере
        telegram_message = f"""
🎯 <b>НОВАЯ БРОНЬ</b>

📍 <b>Адрес:</b> {booking['address'] or 'Не указан'}
👤 <b>Гость:</b> {booking['guest_name'] or 'Не указан'}
👥 <b>Кол-во человек:</b> {booking['people_count'] or 'Не указано'}
📅 <b>Дата и время:</b> {booking['date_time'] or 'Не указано'}
📞 <b>Телефон:</b> {booking['phone'] or 'Не указан'}
🔊 <b>Запись:</b> {booking['record_url'] or 'Нет'}
⏰ <b>Оповещение:</b> {booking['notification_date'] or 'Не указано'}

💬 <b>Тип:</b> Входящий звонок
        """
        
        # Отправляем в Telegram
        bot.send_message(target_chat, telegram_message, parse_mode='HTML')
        print(f"✅ Бронь переслана в {address}")
        
        return {'status': 'success', 'address': address}, 200
        
    except Exception as e:
        print(f"❌ Ошибка обработки письма: {e}")
        return {'status': 'error', 'message': str(e)}, 500

if __name__ == '__main__':
    print("🚀 Email to Telegram Router запущен!")
    app.run(host='0.0.0.0', port=5000, debug=False)
