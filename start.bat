@echo off
setlocal

if not exist "venv\Scripts\activate.bat" (
    echo Создаём виртуальное окружение...
    python -m venv venv
)

echo Активируем виртуальное окружение...
call venv\Scripts\activate.bat

echo Устанавливаем зависимости из requirements.txt...
pip install --upgrade pip
pip install -r requirements.txt

echo Запускаем бота...
python -m bot.main

endlocal
