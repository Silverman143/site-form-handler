FROM python:3.9-slim

# Установка рабочей директории
WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование файлов проекта
COPY . .

# Открытие порта
EXPOSE 8080

# Запуск приложения
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]