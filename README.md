# Telegram Bot with Monthly Predictions

A Telegram bot for private chats that delivers one prediction per month to each user. Users choose one of three inline buttons, and the choice is irreversible for the calendar month. Administrators manage predictions through an inline admin panel inside Telegram.

## Features

### User Features
- Receive monthly prediction with media (photo/video/GIF/animation)
- Choose one of 3 buttons (irreversible choice)
- One choice per month limit
- Automatic monthly broadcast

### Admin Features
- Inline admin panel via /start
- Create predictions with step-by-step FSM flow
- Schedule predictions for automatic broadcast (GMT+3)
- View current/scheduled predictions
- View monthly statistics
- Send test predictions to yourself
- Cancel scheduled predictions

## Technology Stack

- **Python 3.12**
- **aiogram 3** - Async Telegram framework
- **PostgreSQL** - Database
- **SQLAlchemy 2 + Alembic** - ORM and migrations
- **APScheduler** - Scheduled broadcasts
- **Docker + Docker Compose** - Containerization

## Project Structure

```
bot/
├── config/          # Configuration and settings
├── db/              # Database models and migrations
│   └── migrations/  # Alembic migrations
├── handlers/        # Message and callback handlers
│   ├── user/        # User-facing handlers
│   └── admin/       # Admin panel handlers
├── keyboards/       # Inline keyboard builders
├── middlewares/     # Database and auth middlewares
├── scheduler/       # APScheduler jobs
├── services/        # Business logic layer
├── states/          # FSM states
└── main.py          # Entry point
```

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Docker & Docker Compose (for containerized deployment)

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/your-username/tg-bot-prediction.git
cd tg-bot-prediction
```

2. Create and configure `.env`:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start PostgreSQL (or use Docker):
```bash
docker run -d --name postgres \
  -e POSTGRES_USER=prediction_bot \
  -e POSTGRES_PASSWORD=prediction_bot_password \
  -e POSTGRES_DB=prediction_bot \
  -p 5432:5432 \
  postgres:16-alpine
```

5. Run migrations:
```bash
alembic upgrade head
```

6. Start the bot:
```bash
python -m bot.main
```

### Docker Compose Deployment

1. Create and configure `.env`:
```bash
cp .env.example .env
# Edit .env with your settings
```

2. Build and start services:
```bash
docker-compose up -d --build
```

3. Run migrations:
```bash
docker-compose exec bot alembic upgrade head
```

4. View logs:
```bash
docker-compose logs -f bot
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| BOT_TOKEN | Telegram Bot API token | Required |
| ADMIN_IDS | Comma-separated admin Telegram IDs | Required |
| DB_HOST | PostgreSQL host | localhost |
| DB_PORT | PostgreSQL port | 5432 |
| DB_NAME | Database name | prediction_bot |
| DB_USER | Database user | prediction_bot |
| DB_PASSWORD | Database password | prediction_bot_password |
| SCHEDULER_TIMEZONE | Timezone for scheduling (GMT+3) | Europe/Moscow |
| LOG_LEVEL | Logging level | INFO |

## Usage

### For Admins

1. Send `/start` to the bot
2. You'll see the admin panel with options:
   - **Текущее предсказание** - View current/scheduled predictions
   - **Статистика** - View monthly statistics
   - **Создать новое предсказание** - Create a new prediction
   - **Отправить тест себе** - Send a test prediction

### Creating a Prediction

1. Click "Создать новое предсказание"
2. Upload media (photo/video/GIF/animation)
3. Enter the post text
4. Enter 3 initial button texts
5. Enter 3 final button texts (shown after selection)
6. Choose publication date and time (GMT+3)
7. Confirm or recreate

### For Users

1. Send `/start` to the bot
2. If there's an active prediction, you'll receive it with 3 buttons
3. Choose one button - the choice is final!
4. The button will change to show your result
5. You can only receive one prediction per month

## Database Schema

### Tables

- **users** - Telegram users
- **predictions** - Prediction content and scheduling
- **user_prediction_choices** - User selections

### Constraints

- Maximum 1 active prediction
- Maximum 1 scheduled prediction
- 1 choice per user per month

## Broadcasting

- Automatic broadcast at scheduled time (GMT+3)
- Rate-limited sending (25 messages per batch)
- Retry logic for failed sends
- Users are never removed from database on errors
- All users receive broadcasts regardless of previous errors

## License

MIT
