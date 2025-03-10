import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import telegram
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Импорт конфигурации
from config import Config

# Настройка логгирования
logging.basicConfig(
    level=getattr(logging, Config.LOGGING['LEVEL']),
    format=Config.LOGGING['FORMAT']
)
logger = logging.getLogger(__name__)

# Инициализация Flask приложения
app = Flask(__name__)

# Настройка CORS
cors = CORS(app, resources=Config.get_cors_resources())

# Инициализация Telegram бота (если включено)
if Config.TELEGRAM['ENABLED'] and Config.TELEGRAM['TOKEN']:
    bot = telegram.Bot(token=Config.TELEGRAM['TOKEN'])
else:
    bot = None


# Асинхронная функция для отправки сообщения в Telegram
async def async_send_telegram_notification(message, form_name=None):
    if not bot or not Config.TELEGRAM['ENABLED']:
        logger.info("Уведомления Telegram отключены в настройках")
        return False

    try:
        # Параметры сообщения
        params = {
            'chat_id': Config.TELEGRAM['CHAT_ID'],
            'text': message,
            'parse_mode': Config.TELEGRAM['PARSE_MODE']
        }

        # Добавляем ID топика, если он указан
        if Config.TELEGRAM['TOPIC_ID']:
            params['message_thread_id'] = int(Config.TELEGRAM['TOPIC_ID'])

        logger.debug(f"Send telegram notification: {params}")

        # Проверка длины сообщения и разбивка при необходимости
        max_length = Config.TELEGRAM['MAX_MESSAGE_LENGTH']

        if len(message) <= max_length:
            # Если сообщение в пределах ограничения - отправляем сразу
            await bot.send_message(**params)
        else:
            # Иначе разбиваем на части и отправляем последовательно
            parts = [message[i:i + max_length] for i in range(0, len(message), max_length)]

            for i, part in enumerate(parts):
                if i > 0:
                    # Для последующих частей добавляем префикс
                    part_params = params.copy()
                    part_params['text'] = f"(Часть {i + 1}/{len(parts)}) {part}"
                    await bot.send_message(**part_params)
                else:
                    # Для первой части оставляем как есть
                    part_params = params.copy()
                    part_params['text'] = part
                    await bot.send_message(**part_params)

        logger.info("Уведомление в Telegram отправлено успешно")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления в Telegram: {e}")
        return False


# Синхронная обертка для вызова из синхронного кода
def send_telegram_notification(message, form_name=None):
    if not bot or not Config.TELEGRAM['ENABLED']:
        logger.info("Уведомления Telegram отключены в настройках")
        return False

    try:
        # Проверяем, закрыт ли текущий event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            # Если event loop не существует, создаем новый
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Запускаем асинхронную функцию и ждем результат
        result = loop.run_until_complete(async_send_telegram_notification(message, form_name))

        # Не закрываем event loop после использования
        # loop.close()  # Удаляем эту строку

        return result
    except Exception as e:
        logger.error(f"Ошибка при вызове асинхронной функции: {e}")
        return False


# Функция для отправки email
def send_email_notification(subject, message):
    if not Config.EMAIL['ENABLED'] or not Config.EMAIL['USERNAME'] or not Config.EMAIL['PASSWORD']:
        logger.info("Уведомления Email отключены в настройках")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = Config.EMAIL['FROM'] or Config.EMAIL['USERNAME']
        msg['To'] = ", ".join(Config.EMAIL['TO'])
        msg['Subject'] = subject

        msg.attach(MIMEText(message, 'html'))

        if Config.EMAIL['USE_SSL']:
            server = smtplib.SMTP_SSL(Config.EMAIL['HOST'], Config.EMAIL['PORT'])
        else:
            server = smtplib.SMTP(Config.EMAIL['HOST'], Config.EMAIL['PORT'])
            if Config.EMAIL['USE_TLS']:
                server.starttls()

        server.login(Config.EMAIL['USERNAME'], Config.EMAIL['PASSWORD'])
        server.send_message(msg)
        server.quit()

        logger.info("Email уведомление отправлено успешно")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке email уведомления: {e}")
        return False


# Создание сообщения на основе данных формы
def format_message(form_data, form_name=None):
    # Если имя формы не передано, используем значение из формы или значение по умолчанию
    if not form_name:
        form_name = form_data.get(
            Config.FORM_FIELDS['FORM_NAME_FIELD'],
            Config.FORM_FIELDS['DEFAULT_FORM_NAME']
        )

    # Заголовок формы с подстановкой имени формы и текущего времени
    header = Config.TELEGRAM['FORMAT']['HEADER'].format(
        form_name=form_name,
        datetime=datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    )

    # Форматируем все поля формы
    fields = []
    for key, value in form_data.items():
        # Пропускаем служебные поля, начинающиеся с игнорируемых префиксов
        if any(isinstance(key, str) and key.startswith(prefix) for prefix in Config.FORM_FIELDS['IGNORED_PREFIXES']):
            continue

        # Форматируем название поля, делая первую букву заглавной и заменяя подчеркивания на пробелы
        field_name = key.replace('_', ' ').capitalize() if isinstance(key, str) else key

        # Форматируем значение в зависимости от типа
        if isinstance(value, list):
            field_value = ", ".join(str(item) for item in value)
        else:
            field_value = str(value)

        # Если значение длинное, форматируем его особым образом
        if len(field_value) > Config.FORM_FIELDS['LONG_FIELD_THRESHOLD']:
            fields.append(Config.TELEGRAM['FORMAT']['LONG_FIELD'].format(
                field_name=field_name,
                field_value=field_value
            ))
        else:
            fields.append(Config.TELEGRAM['FORMAT']['FIELD'].format(
                field_name=field_name,
                field_value=field_value
            ))

    # Объединяем все в одно сообщение
    return header + "".join(fields)


# Сохранение данных формы в лог (опционально)
def log_form_data(form_data, form_name):
    if not Config.LOGGING['SAVE_FORM_DATA']:
        return

    try:
        # Создаем директорию для логов, если её нет
        log_dir = Config.LOGGING['FORM_LOGS_DIR']
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Имя файла на основе текущей даты и названия формы
        date_str = datetime.now().strftime('%Y-%m-%d')
        sanitized_form_name = ''.join(c if c.isalnum() else '_' for c in form_name)
        filename = f"{log_dir}/{date_str}_{sanitized_form_name}.log"

        # Добавляем дату и время к данным
        log_data = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "form_name": form_name,
            "ip": request.remote_addr,
            "user_agent": request.user_agent.string if request.user_agent else "Unknown",
            "data": form_data
        }

        # Записываем данные в файл
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')

        logger.info(f"Данные формы сохранены в лог: {filename}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных формы в лог: {e}")


# Универсальный маршрут для обработки данных форм
@app.route(f"{Config.API['PREFIX']}{Config.API['FORM_ENDPOINT']}", methods=['POST'])
def handle_form_submit():
    try:
        # Получение JSON данных из запроса
        form_data = request.json

        if not form_data:
            return jsonify({
                "success": False,
                "error": Config.API['RESPONSE_MESSAGES']['ERROR_NO_DATA']
            }), 400

        # Определяем название формы (можно передать через спец. поле)
        form_name = form_data.get(
            Config.FORM_FIELDS['FORM_NAME_FIELD'],
            Config.FORM_FIELDS['DEFAULT_FORM_NAME']
        )

        # Определяем заголовок для email
        email_subject = Config.EMAIL['SUBJECT_TEMPLATE'].format(form_name=form_name)

        # Форматируем сообщение
        notification_message = format_message(form_data, form_name)

        # Отправка уведомлений
        telegram_sent = send_telegram_notification(notification_message, form_name)
        email_sent = send_email_notification(email_subject, notification_message.replace('\n', '<br>'))

        # Записываем данные в лог-файл (если включено)
        log_form_data(form_data, form_name)

        if telegram_sent or email_sent:
            return jsonify({"success": True, "message": Config.API['RESPONSE_MESSAGES']['SUCCESS']}), 200
        else:
            return jsonify({"success": False, "error": Config.API['RESPONSE_MESSAGES']['ERROR_SENDING']}), 500

    except Exception as e:
        logger.error(f"Ошибка при обработке формы: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# Сохраняем поддержку старого API для обратной совместимости
@app.route(f"{Config.API['PREFIX']}{Config.API['CONTACT_ENDPOINT']}", methods=['POST'])
def handle_contact_form():
    return handle_form_submit()


# Маршрут для проверки работоспособности
@app.route(f"{Config.API['PREFIX']}{Config.API['HEALTH_ENDPOINT']}", methods=['GET'])
def health_check():
    # Проверяем основные компоненты системы
    status = {
        "status": "ok",
        "components": {
            "telegram": "active" if bot and Config.TELEGRAM['ENABLED'] else "inactive",
            "email": "active" if Config.EMAIL['ENABLED'] else "inactive",
            "logging": "active" if Config.LOGGING['SAVE_FORM_DATA'] else "inactive"
        },
        "version": "1.0.0",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify(status), 200


# Запуск приложения
if __name__ == '__main__':
    # Создаем .env файл если его нет
    if not os.path.exists('.env'):
        logger.warning("Файл .env не найден. Используются значения по умолчанию.")

    logger.info(
        f"Запускаем сервер на {Config.HOST}:{Config.PORT} в режиме {'разработки' if Config.DEBUG else 'продакшн'}")
    logger.info(f"Разрешенные источники (CORS): {Config.CORS_SETTINGS['ALLOWED_ORIGINS']}")

    if bot:
        logger.info(f"Telegram бот {'активирован' if Config.TELEGRAM['ENABLED'] else 'деактивирован'}")
    else:
        logger.warning("Telegram бот не настроен")

    logger.info(f"Email уведомления {'активированы' if Config.EMAIL['ENABLED'] else 'деактивированы'}")

    logger.info("Доступные эндпоинты:")
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        logger.info(f"  {rule.endpoint:25} {methods:20} {rule}")

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )