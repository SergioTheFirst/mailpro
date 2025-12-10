@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

title MailBot Premium v26 - Launcher

echo ==============================================
echo        MAILBOT PREMIUM v26 LAUNCHER
echo ==============================================
echo.

:: --------------------------------
:: 1. Определяем каталоги
:: --------------------------------
set "SCRIPT_DIR=%~dp0"
if not defined SCRIPT_DIR set "SCRIPT_DIR=.\"
:: Переходим в корень репозитория (одна ступень выше mailbot_v26)
pushd "%SCRIPT_DIR%.." >nul
set "ROOT_DIR=%cd%"
set "PROJECT_DIR=%ROOT_DIR%\mailbot_v26"
set "VENV_PY=%PROJECT_DIR%\venv\Scripts\python.exe"
set "REQ_FILE=%PROJECT_DIR%\requirements.txt"
set "LOG_FILE=%PROJECT_DIR%\mailbot.log"

echo 📂 Working dir: %ROOT_DIR%

:: --------------------------------
:: 2. Проверка наличия Python
:: --------------------------------
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python не найден в PATH.
    echo    Установи Python 3.10+ и добавь в PATH.
    pause
    exit /B 1
)

echo ✅ Python найден в PATH.
echo.

:: --------------------------------
:: 3. Создать venv, если нет
:: --------------------------------
if not exist "%VENV_PY%" (
    echo Создаю виртуальное окружение...
    python -m venv "%PROJECT_DIR%\venv"
)

echo Использую интерпретатор: "%VENV_PY%"

echo Устанавливаю/обновляю зависимости...
if exist "%REQ_FILE%" (
    "%VENV_PY%" -m pip install --upgrade pip
    "%VENV_PY%" -m pip install -r "%REQ_FILE%"
) else (
    echo ⚠ requirements.txt не найден: %REQ_FILE%
)

echo.
:: --------------------------------
:: 4. Проверка конфигов
:: --------------------------------
if not exist "%PROJECT_DIR%\config\config.ini" (
    echo ⚠ ОТСУТСТВУЕТ %PROJECT_DIR%\config\config.ini!
    echo Создай config.ini перед запуском бота.
    pause
)

if not exist "%PROJECT_DIR%\config\accounts.ini" (
    echo ⚠ ОТСУТСТВУЕТ %PROJECT_DIR%\config\accounts.ini!
    echo Укажи хотя бы один IMAP-аккаунт.
    pause
)

if not exist "%PROJECT_DIR%\config\keys.ini" (
    echo ⚠ ОТСУТСТВУЕТ %PROJECT_DIR%\config\keys.ini !
    echo Укажи Cloudflare API ключи и Telegram bot token.
    pause
)

echo Конфиги проверены.
echo.

:: --------------------------------
:: 5. Запуск MailBot
:: --------------------------------
echo 🚀 ЗАПУСК MAILBOT...
echo Логи пишутся в %LOG_FILE%
echo.

"%VENV_PY%" "%PROJECT_DIR%\start.py" >> "%LOG_FILE%" 2>&1

echo.
echo ==============================================
echo   MailBot завершил выполнение (или упал)
echo   Проверяй mailbot.log
echo ==============================================
pause

popd >nul
endlocal
