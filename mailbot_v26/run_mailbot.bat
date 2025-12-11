@echo off
title MailBot Premium v26 - Launcher
chcp 65001 >nul

echo ==============================================
echo        MAILBOT PREMIUM v26 LAUNCHER
echo ==============================================
echo.

:: -------------------------------
:: 1. Проверка наличия Python
:: -------------------------------
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python не найден!
    echo    Скачай и установи Python 3.10–3.12 с python.org
    pause
    exit /B 1
)

echo OK: Python найден.
echo.

:: -------------------------------
:: 2. Создать venv, если нет
:: -------------------------------
IF NOT EXIST venv (
    echo Создаю виртуальное окружение...
    python -m venv venv
)

echo Активирую окружение...
call venv\Scripts\activate
echo.

:: -------------------------------
:: 3. Установка зависимостей
:: -------------------------------
IF EXIST requirements.txt (
    echo Устанавливаю зависимости...
    pip install --upgrade pip
    pip install -r requirements.txt
) ELSE (
    echo WARNING: requirements.txt не найден!
    echo Продолжаю без установки зависимостей.
)

echo.

:: -------------------------------
:: 4. Проверка конфигов
:: -------------------------------
IF NOT EXIST config\config.ini (
    echo WARNING: ОТСУТСТВУЕТ config\config.ini!
    echo Создай config.ini перед запуском бота.
    pause
)

IF NOT EXIST config\accounts.ini (
    echo WARNING: ОТСУТСТВУЕТ config\accounts.ini!
    echo Укажи хотя бы один IMAP-аккаунт.
    pause
)

IF NOT EXIST config\keys.ini (
    echo WARNING: ОТСУТСТВУЕТ config\keys.ini !
    echo Укажи Cloudflare API ключи и Telegram bot token.
    pause
)

echo Конфиги проверены.
echo.

:: -------------------------------
:: 5. Запуск MailBot
:: -------------------------------
echo STARTING MAILBOT...
echo Логи пишутся в mailbot.log
echo.

python start.py >> mailbot.log 2>&1

echo.
echo ==============================================
echo   MailBot завершил выполнение (или упал)
echo   Проверяй mailbot.log
echo ==============================================
pause
