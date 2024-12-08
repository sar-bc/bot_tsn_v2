
# Телеграм бот для ТСН

## Для сбора показаний приборов учета

в корне проекта создать файл .env с константами

TOKEN = ''

DB_HOST = 'localhost'

DB_USER = '*****'

DB_PASSWORD = '*****'

DB_NAME = 'db_name'

  

# Чтобы установить бота на aiogram на сервере Debian, следуйте этим шагам:

  

### Шаг 1: Установка необходимых зависимостей

  

1. Обновите систему:
```console
sudo apt update && sudo apt upgrade
```

2. Установите Python и pip:
sudo apt install python3 python3-pip

### Шаг 2: Создание виртуального окружения

Создайте виртуальное окружение для вашего проекта:
```console
sudo apt install python3-venv  # Убедитесь, что venv установлен
python3 -m venv .venv  # Создайте виртуальное окружение
```
### Шаг 3: Активация виртуального окружения
```console
source .venv/bin/activate  # Активация виртуального окружения
```
### Шаг 4: Клонирование или копирование кода бота

Если ваш код хранится в репозитории, вы можете клонировать его:
```console
git clone https://github.com/yourusername/yourrepository.git
cd yourrepository  # Перейдите в каталог вашего проекта
```
Если код у вас локально, используйте scp или rsync для копирования на сервер.
### Шаг 5: Установка зависимостей проекта
Если у вас есть файл requirements.txt, установите зависимости:
```console
pip install -r requirements.txt
```
### Шаг 6: Настройка переменных окружения
Если ваш бот использует переменные окружения, создайте файл .env
### Шаг 7: Запуск бота
Запустите бота:
```console
python main.py  # Замените на имя вашего файла с ботом
```
### Шаг 8: Запуск бота в фоновом режиме
Чтобы бот работал в фоновом режиме, вы можете использовать screen.
1. Установите screen, если он не установлен:
```
sudo apt install screen
```
2. Запустите screen:
```
screen
```
3. Запустите вашего бота:
```
python main.py
```

4. Чтобы выйти из screen, нажмите Ctrl + A, затем D (это отсоединит сессию).

5. Чтобы вернуться в сессию screen, используйте:
```
screen -r
```
### Шаг 9: Настройка автозапуска (опционально)

Если хотите, чтобы бот автоматически запускался при перезагрузке сервера, создайте файл службы systemd:
```
sudo nano /etc/systemd/system/tsn_bot.service
```
Пример содержимого файла:
```code
[Unit]
Description=TSNZV Bot
After=network.target

[Service]
ExecStart=/home/sar-bc/bots/bot_tsn_v2/.venv/bin/python /home/sar-bc/bots/bot_tsn_v2/main.py
WorkingDirectory=/home/sar-bc/bots/bot_tsn_v2/
Restart=always
User=sar-bc

[Install]
WantedBy=multi-user.target
```
### Шаг 10: Активация службы

После создания файла службы выполните следующие команды:
```
sudo systemctl daemon-reload  # Перезагрузите systemd
sudo systemctl start tsn_bot     # Запустите службу
sudo systemctl enable tsn_bot   # Включите автозапуск при загрузке
sudo systemctl status tsn_bot # проверить статус вашего бота 

sudo systemctl stop tsn_bot
```
### Заключение

Теперь ваш бот на aiogram должен работать на сервере Debian. Убедитесь, что вы проверяете логи на наличие ошибок и что бот правильно реагирует на сообщения. 