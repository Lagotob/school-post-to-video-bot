FROM python:3.10-slim

# Установка системных зависимостей, включая FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Сначала принудительно копируем и обновляем pip
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# Копируем остальные файлы проекта
COPY . /app

CMD ["python", "bot.py"]
