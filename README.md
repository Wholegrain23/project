### SelfJibz — мини‑магазин на FastAPI

Небольшое веб‑приложение (FastAPI + Jinja2) с каталогом товаров, избранным, корзиной и простой авторизацией на сессиях в памяти. Подходит для демонстрации шаблонов, форм и работы со статикой.

## Возможности
- **Главная страница** с приветственным блоком
- **Каталог** с товарами и действиями: «В избранное», «В корзину»
- **Избранное**: просмотр и удаление
- **Корзина**: просмотр, удаление и итоговая сумма
- **Регистрация/Вход/Выход** (сессии в памяти, без БД)
- **Статика**: логотип и изображения товаров
- **Кастомизация**: выбор базового товара, цвета и размера; предпросмотр и добавление кастомного варианта в корзину

## Требования
- Python 3.10+
- Windows/Mac/Linux

## Быстрый запуск (Windows)
```powershell
# 1) Создать и активировать виртуальное окружение
python -m venv .venv
.\.venv\Scripts\Activate

# 2) Установить зависимости
python -m pip install --upgrade pip
pip install fastapi uvicorn jinja2 python-multipart

# 3) Запустить сервер разработки на 8001
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Открыть в браузере
# http://localhost:8001
```

На Linux/macOS команды активации окружения отличаются:
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install fastapi uvicorn jinja2 python-multipart
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## Структура проекта
```text
static/
  main.py
  static/
    images/
      logo.png
      product1.jpg
      product2.jpg
      product3.jpg
      title.png
  templates/
    base.html
    cart.html
    catalog.html
    favorites.html
    index.html
    login.html
    register.html
```

## Маршруты
- **GET /**: главная
- **GET /catalog**: каталог (товары по 3 в ряд)
- **GET /customize**: страница кастомизации (выбор базового товара, цвета, размера)
- **GET /favorites**: избранное
- **GET /cart**: корзина
- **GET /register**, **GET /login**: страницы форм
- **POST /register**, **POST /login**: обработка форм
- **GET /logout**: выход, удаление cookie и серверной сессии
- **POST /add_favorite**, **POST /remove_favorite**
- **POST /add_cart**, **POST /remove_cart**
- **POST /customize_add_cart**: добавить кастомный товар в корзину

## Кастомизация
- Откройте страницу `GET /customize` или кнопку «Кастомизация» на главной/в шапке.
- Выберите:
  - **Базовый товар** — берётся из каталога и использует реальное изображение (`product1.jpg`, `product2.jpg`, `product3.jpg`).
  - **Цвет** — применяется как цветовая тонировка поверх изображения в предпросмотре.
  - **Размер** — S/M/L.
- Нажмите «В корзину», чтобы создать кастомный вариант и добавить его в корзину.
- Для добавления в корзину требуется авторизация.
- Сформированный товар сохраняет название/бренд/цену базового товара и выбранные параметры; изображение — фото базового товара.

## Данные и сессии
- Пользователи, избранное и корзина хранятся в памяти процесса. При перезапуске приложения данные обнуляются.
- Для обработки форм FastAPI нужен пакет `python-multipart` (он указан в команде установки).

## Изображения товаров
- В `static/images` лежат: `product1.jpg`, `product2.jpg`, `product3.jpg`, `logo.png`, `title.png`.
- Для товаров с id 4–9 используются существующие изображения‑плейсхолдеры, чтобы не было 404.
- Кастомизация использует изображения существующих товаров для предпросмотра и итогового товара.

## Частые проблемы
- **Порт 8001 занят (Windows)**:
  ```powershell
  Get-NetTCPConnection -LocalPort 8001 -State Listen |
    Select-Object -ExpandProperty OwningProcess |
    ForEach-Object { Stop-Process -Id $_ -Force }
  ```
  Затем перезапустите сервер: `python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload`.

- **422 при отправке форм**: убедитесь, что установлен `python-multipart`.

## Развёртывание (кратко)
- Рекомендуется запускать за обратным прокси (Nginx/Caddy) и использовать процесс‑менеджер (systemd, Supervisor, Windows‑служба). Пример базового запуска без перезагрузки кода:
  ```bash
  python -m uvicorn main:app --host 0.0.0.0 --port 8001
  ```
