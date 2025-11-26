import os
import telebot
from flask import Flask, request
from datetime import datetime
import re
import imaplib
import email
import time
import threading

app = Flask(__name__)

# Токен вашего бота
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# Данные Яндекс.Почты
EMAIL_USER = os.environ.get('elena.itresh@yandex.ru')  # ваш@yandex.ru
EMAIL_PASSWORD = os.environ.get('rlquzmkwpbnsqjcr')  # пароль приложения

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
    
    # Телефон
    phone_match = re.search(r'Телефон:\s*([^\n]+)', body)
    if phone_match:
        booking_data['phone'] = phone_match.group(1).strip()
    
    # Запись диалога
    record_match = re.search(r'Запись диалог:\s*([^\n]+)', body)
    if record_match:
        booking_data['record_url'] = record_match.group(1).strip()
    
    # Дата оповещения
    notify_match = re.search(r'Дата оповещения\s*([^\n]+)', body)
    if notify_match:
        booking_data['notification_date'] = notify_match.group(1).strip()
    
    # Резюме диалога
    summary_match = re.search(r'Резюме диалога:(.*?)(?=< Пред\.|$)', body, re.DOTALL)
    if summary_match:
        summary_text = summary_match.group(1)
        
        name_match = re.search(r'Имя гостя\s*([^\n]+)', summary_text)
        if name_match:
            booking_data['guest_name'] = name_match.group(1).strip()
        
        address_match = re.search(r'Адрес\s*([^\n]+)', summary_text)
        if address_match:
            booking_data['address'] = address_match.group(1).strip()
        
        people_match = re.search(r'Сколько человек\s*([^\n]+)', summary_text)
        if people_match:
            booking_data['people_count'] = people_match.group(1).strip()
        
        date_match = re.search(r'Дата и время\s*([^\n]+)', summary_text)
        if date_match:
            booking_data['date_time'] = date_match.group(1).strip()
    
    return booking_data

def send_to_telegram(booking_data):
    """Отправляет бронь в Telegram"""
    address = booking_data['address'] or 'НЕРАСПОЗНАННЫЕ'
    target_chat = CHATS.get(address, CHATS['НЕРАСПОЗНАННЫЕ'])
    
    telegram_message = f"""
🎯 <b>НОВАЯ БРОНЬ</b>

📍 <b>Адрес:</b> {booking_data['address'] or 'Не указан'}
👤 <b>Гость:</b> {booking_data['guest_name'] or 'Не указан'}
👥 <b>Кол-во человек:</b> {booking_data['people_count'] or 'Не указано'}
📅 <b>Дата и время:</b> {booking_data['date_time'] or 'Не указано'}
📞 <b>Телефон:</b> {booking_data['phone'] or 'Не указан'}
🔊 <b>Запись:</b> {booking_data['record_url'] or 'Нет'}
⏰ <b>Оповещение:</b> {booking_data['notification_date'] or 'Не указано'}

💬 <b>Тип:</b> Входящий звонок
    """
    
    try:
        bot.send_message(target_chat, telegram_message, parse_mode='HTML')
        print(f"✅ Бронь переслана в {address}")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")
        return False

def check_emails():
    """Проверяет почту каждые 2 минуты"""
    while True:
        try:
            if EMAIL_USER and EMAIL_PASSWORD:
                print("🔍 Проверяем почту...")
                
                mail = imaplib.IMAP4_SSL('imap.yandex.ru', 993)
                mail.login(EMAIL_USER, EMAIL_PASSWORD)
                mail.select('inbox')
                
                status, messages = mail.search(None, 'UNSEEN')
                email_ids = messages[0].split()
                
                print(f"📧 Найдено новых писем: {len(email_ids)}")
                
                for email_id in email_ids:
                    process_email(mail, email_id)
                
                mail.close()
                mail.logout()
            else:
                print("⚠️ Данные почты не настроены")
                
        except Exception as e:
            print(f"❌ Ошибка проверки почты: {e}")
        
        time.sleep(120)  # 2 минуты

def process_email(mail, email_id):
    """Обрабатывает одно письмо"""
    try:
        status, msg_data = mail.fetch(email_id, '(RFC822)')
        email_body = msg_data[0][1]
        mail_message = email.message_from_bytes(email_body)
        
        subject = mail_message['subject']
        from_email = mail_message['from']
        
        # Получаем текст письма
        body = ""
        if mail_message.is_multipart():
            for part in mail_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            body = mail_message.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        print(f"📧 Обрабатываем письмо: {subject}")
        
        # Парсим и отправляем в Telegram
        booking_data = parse_exact_format(body)
        send_to_telegram(booking_data)
        
    except Exception as e:
        print(f"❌ Ошибка обработки письма: {e}")

# Запускаем проверку почты в отдельном потоке
email_thread = threading.Thread(target=check_emails)
email_thread.daemon = True
email_thread.start()

@app.route('/')
def home():
    return "🚀 Email to Telegram Router (прямой IMAP) работает!", 200

@app.route('/health')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    print("🚀 Запущен прямой IMAP к Яндекс.Почте!")
    app.run(host='0.0.0.0', port=5000, debug=False)
