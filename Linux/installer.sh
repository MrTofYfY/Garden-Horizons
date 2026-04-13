#!/bin/sh
# Установщик "Компилятор" для Goosembler

URL="https://github.com/MrTofYfY/EpstinVPN/raw/refs/heads/main/Linux/gsm.py"
DEST_DIR="$PREFIX/bin"
SRC_FILE="gsm.py"

echo "--- Установка Goosembler (Компиляция на устройстве) ---"

# 1. Установка необходимых инструментов для сборки
echo "[*] Установка инструментов сборки (это займет время)..."
pkg update -y > /dev/null
pkg install python clang make libffi openssl-dev -y > /dev/null
pip install pyinstaller > /dev/null

# 2. Скачивание исходного кода
echo "[*] Скачивание исходного кода..."
curl -L "$URL" -o "$SRC_FILE"

# 3. Компиляция
echo "[*] Компиляция (создание бинарника)..."
# Мы используем --onefile, чтобы получить один файл
pyinstaller --onefile "$SRC_FILE" > /dev/null

# 4. Перемещение
if [ -f "dist/gsm" ]; then
    mv dist/gsm "$DEST_DIR/gsm"
    chmod +x "$DEST_DIR/gsm"
    echo "[+] Готово! Goosembler скомпилирован и установлен."
    echo "[+] Введи 'gsm' для проверки."
else
    echo "[!] Ошибка при компиляции."
    exit 1
fi

# 5. Очистка временных файлов
rm -rf build dist "$SRC_FILE" *.spec
