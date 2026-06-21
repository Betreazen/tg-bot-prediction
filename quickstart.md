# Быстрый запуск на Ubuntu

## 1. Клонирование репозитория

```bash
cd /opt
git clone https://github.com/YOUR_USERNAME/tg-bot-prediction.git
cd tg-bot-prediction
```

## 2. Настройка окружения

Единственный шаг настройки — заполнить `.env`:

```bash
cp .env.example .env
nano .env
```

Обязательно задайте три параметра:

```env
BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_IDS=ваш_telegram_id            # можно несколько через запятую
DB_PASSWORD=надёжный_случайный_пароль  # например: openssl rand -hex 24
```

Остальное менять не нужно. `DB_HOST`/`DB_PORT` подставляются автоматически —
бот общается с базой по внутренней сети Docker.

## 3. Запуск

```bash
docker compose up -d --build
```

Миграции базы применяются автоматически при старте — больше никуда заходить не
нужно.

## 4. Проверка

```bash
docker compose ps
docker compose logs -f bot
```

## Запуск нескольких ботов на одном сервере

Стек полностью изолирован: своя сеть, свой том и свои контейнеры с префиксом
проекта. Порт Postgres на хост **не публикуется**, поэтому конфликтов портов с
другими ботами нет.

Если нужно поднять несколько копий этого бота на одной машине, задайте каждой
уникальное имя проекта в её `.env`:

```env
COMPOSE_PROJECT_NAME=prediction-bot-2
```

## Остановка

```bash
docker compose down
```

Полная очистка вместе с базой данных:

```bash
docker compose down -v
```

## Обновление

```bash
git pull
docker compose up -d --build
```

## Логи

```bash
docker compose logs -f bot
docker compose logs -f postgres
```
