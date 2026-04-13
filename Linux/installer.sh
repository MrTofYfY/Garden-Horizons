#!/bin/sh

# Ссылка на твой бинарник
URL="https://github.com/MrTofYfY/EpstinVPN/raw/refs/heads/main/Linux/gsm"

# Временный файл в домашней директории
TMP_FILE="$HOME/.gsm_temp_bin"

echo "--- Начинаю установку Goosembler ---"

# 1. Определяем среду
if [ -n "$PREFIX" ]; then
    echo "[*] Обнаружен Termux"
    INSTALL_DIR="$PREFIX/bin"
else
    echo "[*] Обнаружен Linux"
    INSTALL_DIR="/usr/local/bin"
fi

# 2. Скачивание
echo "[*] Скачивание..."
curl -L "$URL" -o "$TMP_FILE"

# Проверка, скачался ли файл
if [ ! -s "$TMP_FILE" ]; then
    echo "[!] Ошибка: Не удалось скачать файл (файл пуст или отсутствует)."
    rm -f "$TMP_FILE"
    exit 1
fi

# 3. Делаем исполняемым
chmod +x "$TMP_FILE"

# 4. Установка (с попыткой использования sudo)
echo "[*] Установка в $INSTALL_DIR..."

if [ -w "$INSTALL_DIR" ]; then
    # Если есть права на запись в папку, просто перемещаем
    mv "$TMP_FILE" "$INSTALL_DIR/gsm"
else
    # Если прав нет, пробуем sudo
    if command -v sudo >/dev/null 2>&1; then
        sudo mv "$TMP_FILE" "$INSTALL_DIR/gsm"
    else
        echo "[!] Ошибка: Нет прав на запись в $INSTALL_DIR и отсутствует sudo."
        echo "Попробуй запустить с правами root или проверь пути."
        rm -f "$TMP_FILE"
        exit 1
    fi
fi

# 5. Проверка успешности
if [ -f "$INSTALL_DIR/gsm" ]; then
    echo "[+] Успешно! Goosembler установлен."
    echo "[+] Введи 'gsm' для проверки."
else
    echo "[!] Ошибка при установке."
    exit 1
fi
