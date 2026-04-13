#!/bin/sh
echo "--- Начинаю установку Goosembler ---"

# 1. Установка зависимостей
echo "[*] Обновление и установка инструментов..."
pkg update -y
pkg install -y python clang make libffi openssl binutils patchelf

echo "[*] Установка PyInstaller..."
pip install --upgrade pip
pip install pyinstaller

# 2. Скачивание
URL="https://github.com/MrTofYfY/EpstinVPN/raw/main/Linux/gsm.py"
echo "[*] Скачивание исходника..."
curl -L "$URL" -o gsm.py

# 3. Компиляция (теперь мы увидим ошибки, если они будут!)
echo "[*] Компиляция (подожди, это может занять время)..."
pyinstaller --onefile gsm.py

# 4. Проверка и перемещение
if [ -f "dist/gsm" ]; then
    mv dist/gsm "$PREFIX/bin/gsm"
    chmod +x "$PREFIX/bin/gsm"
    echo "[+] УСПЕШНО! Введи 'gsm' для проверки."
else
    echo "[!] ОШИБКА: Компиляция провалилась. Сделай скриншот ошибки выше и пришли мне."
    exit 1
fi
