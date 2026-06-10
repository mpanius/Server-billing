# Server Billing Manager

Self-hosted панель для учета серверов, сроков оплаты и быстрых переходов к оплате у хостинг-провайдера.

Сервис не проводит платежи сам и не хранит банковские карты. Он напоминает о сроках, показывает нужный сервер, хранит ссылку на кабинет/оплату и помогает быстро перейти к провайдеру.

## Возможности

- Дашборд серверов, провайдеров и ближайших оплат.
- Поиск и фильтры по серверу, IP, аккаунту, провайдеру и статусу оплаты.
- Аккаунты хостинга: провайдер, логин, зашифрованный секрет, ссылка на кабинет, ссылка на оплату.
- Привязка нескольких серверов к одному аккаунту хостинга.
- Статусы оплаты: в порядке, скоро, срочно, просрочено.
- Страница оплаты конкретного сервера.
- Кнопка перехода на ссылку оплаты сервера или аккаунта хостинга.
- Кнопка `Отметить оплачено`, которая переносит дату на следующий период.
- История оплат с датами, суммами и комментариями.
- Аналитика расходов по месяцам и провайдерам.
- Telegram-уведомления через отдельный reminder worker.
- Настройки Telegram и расписания уведомлений в веб-панели.
- Backup SQLite-базы в Telegram по расписанию или вручную.
- Ручной запуск проверки уведомлений из панели.
- Авторизация администратора по логину и паролю.
- Смена пароля администратора в веб-панели.
- Развертывание через Docker Compose и Caddy.
- HTTPS без домена через `IP.sslip.io` или собственный домен с сертификатом Caddy.

## Установка одной командой

На чистом Linux-сервере выполните:

```bash
curl -fsSL https://raw.githubusercontent.com/AlekseyRusaleev/Server-billing/main/scripts/install.sh | sudo bash
```

Установщик спросит:

- домен, если хотите использовать свой HTTPS-домен;
- email для сертификатов Caddy, если указан домен;
- логин администратора;
- пароль администратора;
- Telegram bot token, если нужны уведомления;
- Telegram chat id, если указан токен.

Если домен не указан, установщик автоматически создаст HTTPS-адрес через `sslip.io`:

```text
https://YOUR_SERVER_IP.sslip.io
```

Обычный адрес `http://YOUR_SERVER_IP` будет редиректить на защищенную HTTPS-ссылку.

## HTTPS без домена

Свой домен не обязателен. По умолчанию используется публичный DNS-алиас `sslip.io`, который указывает на IP сервера:

```text
192.0.2.10.sslip.io -> 192.0.2.10
```

Caddy автоматически выпускает сертификат Let's Encrypt для этого имени.

## Установка с доменом

1. Создайте DNS `A`-запись домена на IP сервера.
2. Запустите install script.
3. Введите домен, например:

```text
billing.example.com
```

Caddy автоматически получит и обновит HTTPS-сертификат.

## Настройки в панели

После входа откройте раздел `Настройки`.

Там можно изменить:

- `Base URL` для ссылок в Telegram;
- Telegram bot token;
- Telegram chat id;
- дни напоминаний, например `7,3,1,0,-1`;
- периодичность проверки в секундах;
- периодичность отправки backup базы в Telegram;
- отправить тестовое Telegram-сообщение.
- отправить backup прямо сейчас;
- запустить проверку уведомлений прямо сейчас.

По умолчанию scheduler проверяет оплаты раз в сутки:

```env
CHECK_INTERVAL_SECONDS=86400
REMINDER_DAYS=7,3,1,0,-1
```

Значение `-1` означает напоминание о просроченной оплате.

Если `Backup в Telegram, дней` равен `0`, автоматическая отправка backup отключена.

## Локальный запуск для разработки

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Откройте:

```text
http://127.0.0.1:8000
```

Если `ADMIN_PASSWORD_HASH` не задан, авторизация отключена. Для проверки авторизации задайте переменные в `.env`.

## Docker локально

```bash
docker compose up --build
```

После запуска:

```text
http://127.0.0.1:8000
```

## Production Docker Compose

Production-режим использует:

- `app` - FastAPI web app;
- `scheduler` - Telegram reminder worker;
- `caddy` - reverse proxy и HTTPS.

Ручной запуск:

```bash
cp .env.example .env
docker compose -f docker-compose.prod.yml up -d --build
```

Для ручной установки нужно самостоятельно заполнить `APP_SECRET_KEY`, `APP_ENCRYPTION_KEY`, `ADMIN_USERNAME` и `ADMIN_PASSWORD_HASH`. Проще использовать `scripts/install.sh`, он генерирует эти значения автоматически.

## Настройки `.env`

```env
APP_NAME=Server Billing Manager
DATABASE_PATH=/app/data/server_billing.db
BASE_URL=https://YOUR_SERVER_IP.sslip.io
SERVER_IP=YOUR_SERVER_IP
CADDY_SITE_ADDRESS=YOUR_SERVER_IP.sslip.io
CADDY_EMAIL=
APP_SECRET_KEY=
APP_ENCRYPTION_KEY=
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
REMINDER_DAYS=7,3,1,0,-1
CHECK_INTERVAL_SECONDS=86400
BACKUP_INTERVAL_DAYS=7
```

Для домена:

```env
BASE_URL=https://billing.example.com
CADDY_SITE_ADDRESS=billing.example.com
CADDY_EMAIL=admin@example.com
```

## Telegram

Создайте бота через `@BotFather`, затем получите `chat_id` пользователя или группы, куда нужно отправлять уведомления.

Токен не хранится в репозитории. При установке он вводится интерактивно и записывается только в `.env` на вашем сервере. После установки токен и chat id можно поменять в разделе `Настройки`.

Если `TELEGRAM_BOT_TOKEN` или `TELEGRAM_CHAT_ID` пустые, reminder worker работает, но уведомления не отправляет.

## Обновление

```bash
cd /opt/server-billing
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## Данные

SQLite-база хранится в:

```text
/opt/server-billing/data/server_billing.db
```

Перед обновлениями или переносом сервера сделайте резервную копию папки `data`.

В разделе `Настройки` можно отправить текущую SQLite-базу в Telegram вручную или настроить автоматический backup раз в указанное количество дней.

## Безопасность

- Веб-панель защищена логином и паролем администратора.
- Пароль администратора хранится как PBKDF2-SHA256 hash.
- Секреты аккаунтов хостинга шифруются через Fernet при наличии `APP_ENCRYPTION_KEY`.
- Telegram token также может храниться в зашифрованном виде в настройках панели.
- Не удаляйте и не меняйте `APP_ENCRYPTION_KEY` после начала использования, иначе старые зашифрованные секреты нельзя будет расшифровать.

Для коммерческой multi-tenant версии стоит добавить пользователей, роли, аудит доступа и резервное копирование.
