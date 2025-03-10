import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()


def parse_env_string(value, default=''):
    """Преобразует строку, заменяя текстовые \n на настоящие переносы строк"""
    env_value = os.getenv(value, default)
    return env_value.replace('\\n', '\n')

class Config:
    """
    Класс для управления конфигурацией приложения
    """
    # Основные настройки приложения
    DEBUG = os.getenv('FLASK_ENV', 'production').lower() == 'development'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8080))

    # Настройки CORS
    CORS_SETTINGS = {
        'ALLOWED_ORIGINS': os.getenv('ALLOWED_ORIGINS', 'https://your-website.com').split(','),
        'ALLOWED_METHODS': os.getenv('ALLOWED_METHODS', 'GET,POST,OPTIONS').split(','),
        'ALLOWED_HEADERS': os.getenv('ALLOWED_HEADERS', 'Content-Type,Authorization').split(','),
        'MAX_AGE': int(os.getenv('CORS_MAX_AGE', 86400))  # 24 часа в секундах
    }

    # Настройки Telegram
    TELEGRAM = {
        'ENABLED': os.getenv('ENABLE_TELEGRAM', 'true').lower() == 'true',
        'TOKEN': os.getenv('TELEGRAM_TOKEN', ''),
        'CHAT_ID': os.getenv('TELEGRAM_CHAT_ID', ''),
        'TOPIC_ID': os.getenv('TELEGRAM_TOPIC_ID', ''),
        'PARSE_MODE': os.getenv('TELEGRAM_PARSE_MODE', 'HTML'),
        # Форматирование сообщений
        'FORMAT': {
            'HEADER': parse_env_string('TELEGRAM_FORMAT_HEADER',
                                       '<b>Новое сообщение из формы: {form_name}</b>\n<b>Дата и время:</b> {datetime}\n\n'),
            'FIELD': parse_env_string('TELEGRAM_FORMAT_FIELD',
                                      '<b>{field_name}:</b> {field_value}\n'),
            'LONG_FIELD': parse_env_string('TELEGRAM_FORMAT_LONG_FIELD',
                                           '<b>{field_name}:</b>\n{field_value}\n')
        },
        # Ограничение Telegram на размер сообщения
        'MAX_MESSAGE_LENGTH': int(os.getenv('TELEGRAM_MAX_MESSAGE_LENGTH', 4096))
    }

    # Настройки Email
    EMAIL = {
        'ENABLED': os.getenv('ENABLE_EMAIL', 'true').lower() == 'true',
        'HOST': os.getenv('EMAIL_HOST', 'smtp.gmail.com'),
        'PORT': int(os.getenv('EMAIL_PORT', 587)),
        'USERNAME': os.getenv('EMAIL_USER', ''),
        'PASSWORD': os.getenv('EMAIL_PASSWORD', ''),
        'TO': os.getenv('EMAIL_TO', '').split(','),
        'FROM': os.getenv('EMAIL_FROM', ''),
        'SUBJECT_TEMPLATE': os.getenv('EMAIL_SUBJECT_TEMPLATE', 'Новое сообщение: {form_name}'),
        'USE_TLS': os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true',
        'USE_SSL': os.getenv('EMAIL_USE_SSL', 'false').lower() == 'true',
    }

    # Настройки логирования
    LOGGING = {
        'LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        'FORMAT': os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        'SAVE_FORM_DATA': os.getenv('LOG_SAVE_FORM_DATA', 'true').lower() == 'true',
        'FORM_LOGS_DIR': os.getenv('FORM_LOGS_DIR', 'form_logs')
    }

    # Настройки API
    API = {
        'PREFIX': os.getenv('API_PREFIX', '/api'),
        'FORM_ENDPOINT': os.getenv('API_FORM_ENDPOINT', '/form-submit'),
        'CONTACT_ENDPOINT': os.getenv('API_CONTACT_ENDPOINT', '/contact'),
        'HEALTH_ENDPOINT': os.getenv('API_HEALTH_ENDPOINT', '/health'),
        'RESPONSE_MESSAGES': {
            'SUCCESS': os.getenv('API_SUCCESS_MESSAGE', 'Форма успешно отправлена'),
            'ERROR_NO_DATA': os.getenv('API_ERROR_NO_DATA', 'Нет данных формы'),
            'ERROR_SENDING': os.getenv('API_ERROR_SENDING', 'Ошибка при отправке уведомлений')
        }
    }

    # Фильтрация полей формы
    FORM_FIELDS = {
        'IGNORED_PREFIXES': os.getenv('FORM_IGNORED_PREFIXES', '_,csrf,captcha').split(','),
        'FORM_NAME_FIELD': os.getenv('FORM_NAME_FIELD', '_form_name'),
        'DEFAULT_FORM_NAME': os.getenv('DEFAULT_FORM_NAME', 'Обратная связь'),
        'LONG_FIELD_THRESHOLD': int(os.getenv('FORM_LONG_FIELD_THRESHOLD', 100))
    }

    # Защита от спама (опционально)
    SPAM_PROTECTION = {
        'ENABLED': os.getenv('SPAM_PROTECTION_ENABLED', 'false').lower() == 'true',
        'MAX_SUBMISSIONS_PER_IP': int(os.getenv('MAX_SUBMISSIONS_PER_IP', 10)),
        'TIME_WINDOW_SECONDS': int(os.getenv('SPAM_TIME_WINDOW_SECONDS', 3600)),  # 1 час
        'RATE_LIMIT_RESET_INTERVAL': int(os.getenv('RATE_LIMIT_RESET_INTERVAL', 86400))  # 24 часа
    }

    # Дополнительные настройки
    ADDITIONAL = {
        'ALLOWED_FILE_TYPES': os.getenv('ALLOWED_FILE_TYPES', '').split(','),
        'MAX_FILE_SIZE_MB': float(os.getenv('MAX_FILE_SIZE_MB', 5.0)),
        'CUSTOM_HEADERS': {header.split(':')[0]: header.split(':')[1]
                           for header in os.getenv('CUSTOM_HEADERS', '').split(',')
                           if ':' in header and header.strip()},
    }

    @classmethod
    def get_cors_resources(cls):
        """
        Возвращает настройки CORS в формате, необходимом для Flask-CORS
        """
        return {
            f"{cls.API['PREFIX']}/*": {
                "origins": cls.CORS_SETTINGS['ALLOWED_ORIGINS'],
                "methods": cls.CORS_SETTINGS['ALLOWED_METHODS'],
                "allow_headers": cls.CORS_SETTINGS['ALLOWED_HEADERS'],
                "max_age": cls.CORS_SETTINGS['MAX_AGE']
            }
        }
