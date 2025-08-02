# 🚀 Быстрый запуск NoSugar Bot

## Минимальная настройка

### 1. Получите токены
- **Telegram Bot Token**: Напишите [@BotFather](https://t.me/BotFather) и создайте бота
- **DeepSeek API Key**: Получите на [DeepSeek](https://platform.deepseek.com/)

### 2. Настройте окружение
```bash
# Скопируйте конфигурацию
cp env.example .env

# Отредактируйте .env файл
nano .env
```

### 3. Запустите с Docker (рекомендуется)
```bash
# Запуск с PostgreSQL
docker-compose up -d

# Проверка логов
docker-compose logs -f bot
```

### 4. Или запустите локально
```bash
# Установите PostgreSQL и создайте БД
createdb nosugar_bot

# Установите зависимости
pip install -r requirements.txt

# Инициализируйте БД
python manage.py init-db

# Запустите бота
python main.py
```

## Проверка работы

1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Попробуйте функции:
   - ✅ Чек-ин
   - 📊 Статистика
   - 🍳 Рецепты
   - 🎯 Челлендж

## Полезные команды

```bash
# Проверка конфигурации
python manage.py check-config

# Создание миграции
python manage.py create-migration "Add new feature"

# Обновление БД
python manage.py upgrade-db

# Запуск тестов
pytest

# Остановка Docker
docker-compose down
```

## Структура проекта
```
nosugar_bot/
├── main.py              # Точка входа
├── config.py            # Конфигурация
├── manage.py            # Управление
├── requirements.txt     # Зависимости
├── docker-compose.yml   # Docker
├── database/           # Модели БД
├── handlers/           # Обработчики
├── services/           # Бизнес-логика
└── tests/              # Тесты
```

## Поддержка

- 📖 Полная документация: [README.md](README.md)
- 🐛 Проблемы: создайте Issue
- 💬 Вопросы: напишите в Telegram

## Быстрые ссылки

- [Полная документация](README.md)
- [Docker развертывание](README.md#docker-рекомендуется)
- [Настройка БД](README.md#настройка-базы-данных)
- [API документация](README.md#использование) 