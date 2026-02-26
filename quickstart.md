# Быстрый запуск на Ubuntu

## 1. Клонирование репозитория

```bash
cd /opt
git clone https://github.com/YOUR_USERNAME/tg-bot-prediction.git
cd tg-bot-prediction
```

## 2. Настройка окружения

```bash
cp .env.example .env
nano .env
```

Заполните переменные:

```env
BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_IDS=ваш_telegram_id
DB_HOST=db
DB_PORT=5432
DB_NAME=prediction_bot
DB_USER=prediction_bot
DB_PASSWORD=надежный_пароль
SCHEDULER_TIMEZONE=Europe/Moscow
LOG_LEVEL=INFO
```

> **Важно:** `DB_HOST=db` — имя сервиса в docker-compose, не меняйте.

## 3. Запуск

```bash
docker-compose up -d --build
```

## 4. Проверка

```bash
docker-compose ps
docker-compose logs -f bot
```

## 5. Остановка

```bash
docker-compose down
```

Для полной очистки (включая базу данных):

```bash
docker-compose down -v
```

## 6. Обновление

```bash
git pull
docker-compose up -d --build
```

## 7. Просмотр логов

```bash
docker-compose logs -f bot
docker-compose logs -f db
```
