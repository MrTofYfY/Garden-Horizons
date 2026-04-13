#!/bin/sh
# Goosembler Universal Installer

URL="https://github.com/MrTofYfY/EpstinVPN/raw/refs/heads/main/Linux/gsm"
# Скачиваем прямо в домашнюю папку пользователя
DEST="$HOME/gsm"

echo "--- Начинаю установку Goosembler ---"

# 1. Скачивание
echo "[*] Скачивание файла..."
curl -L "$URL" -o "$DEST"

# Проверка
if [ ! -f "$DEST" ]; then
    echo "[!] Ошибка: Файл не скачался!"
    exit 1
fi

# 2. Права
chmod +x "$DEST"

# 3. Перемещение
# Определяем, куда ставить
if [ -n "$PREFIX" ]; then
    # Это Termux, ставим в $PREFIX/bin (он доступен для выполнения)
    INSTALL_DIR="$PREFIX/bin"
else
    # Это обычный Linux
    INSTALL_DIR="/usr/local/bin"
fi

echo "[*] Перемещение в $INSTALL_DIR..."
mv "$DEST" "$INSTALL_DIR/gsm"

# Финал
if [ -f "$INSTALL_DIR/gsm" ]; then
    echo "[+] Успешно! Установлено в $INSTALL_DIR/gsm"
    echo "[+] Введи 'gsm', чтобы запустить."
else
    echo "[!] Ошибка: не удалось переместить файл."
    exit 1
fi
