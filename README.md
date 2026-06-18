# 1C MCP Sales Analyst

**AI-аналитик склада и продаж на базе 1С + MCP + DeepSeek**

Замена ручного построения отчётов СКД на текстовые запросы к данным учёта. Пользователь пишет вопрос на русском языке — AI анализирует данные из 1С и выдаёт ответ.

## Архитектура

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Пользователь │────▶│  chat.py /   │────▶│  DeepSeek   │
│  (CLI / Web) │     │  web_ui.py   │     │  API (V3)   │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  1C Tools    │
                    │ (Function    │
                    │  Calling)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  1C HTTP     │
                    │  Services    │
                    │ (или Mock)   │
                    └──────────────┘
```

LLM работает в облаке DeepSeek, инструменты (get_stock, get_sales и др.) вызываются через Function Calling. Данные поступают из 1С через HTTP-сервисы или из встроенного мока для демо.

## Быстрый старт

### Предварительные требования

- Python 3.11+
- Ключ DeepSeek API ([deepseek.com](https://platform.deepseek.com))

### Установка

```bash
# Клонировать репозиторий
git clone https://github.com/your-username/1c-mcp-sales-analyst.git
cd 1c-mcp-sales-analyst

# Создать .env файл
cp .env.example .env
# Отредактировать .env: указать DEEPSEEK_API_KEY

# Установить зависимости
pip install -e .
pip install -e ".[web]"  # если нужен Web UI
```

### Запуск CLI

```bash
python chat.py "Покажи топ-5 товаров на складе в Москве, которые не продавались 30 дней"
```

### Запуск Web UI

```bash
streamlit run web_ui.py
```

### Запуск через Docker

```bash
docker-compose up --build
```

## Примеры запросов

| Запрос | Что делает AI |
|--------|--------------|
| "Покажи топ-5 товаров на складе в Москве, которые не продавались 30 дней" | get_stock + get_sales → фильтр → сортировка |
| "Какая выручка за последнюю неделю по менеджеру Иванов?" | get_sales_by_manager |
| "Сколько единиц товара 'Гвоздь 100мм' на всех складах?" | get_stock |
| "Кто из клиентов задолжал больше 100 000 рублей?" | get_receivables |

## Структура проекта

```
├── src/
│   ├── __main__.py         # Точка входа (python -m src)
│   ├── config.py           # Конфигурация из .env
│   ├── logger.py           # Логирование (loguru)
│   ├── deepseek_client.py  # Клиент DeepSeek API + Function Calling
│   ├── tools.py            # Инструменты для вызова 1С
│   ├── server.py           # MCP-сервер
│   └── clients/
│       ├── c1_client.py    # HTTP-клиент для 1С (реальный)
│       └── mock_c1_client.py # Мок-клиент для демо
├── chat.py                 # CLI-клиент
├── web_ui.py               # Streamlit Web UI
├── 1c_http_services/       # Документация по HTTP-сервисам 1С
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Переменные окружения (.env)

| Переменная | По умолчанию | Описание |
|-----------|-------------|----------|
| DEEPSEEK_API_KEY | — | Ключ API DeepSeek |
| C1_BASE_URL | http://localhost/1c/api | URL сервера 1С |
| C1_USERNAME | service_user | Логин 1С |
| C1_PASSWORD | service_password | Пароль 1С |
| MCP_HOST | 0.0.0.0 | Хост MCP-сервера |
| MCP_PORT | 8000 | Порт MCP-сервера |
| LLM_MODEL | deepseek-chat | Модель DeepSeek |
| LLM_TEMPERATURE | 0.1 | Температура LLM |
| USE_MOCK_DATA | true | Использовать мок вместо 1С |

## 1С HTTP-сервисы

Для подключения к реальной 1С необходимо опубликовать HTTP-сервисы. См. [1c_http_services/README.md](1c_http_services/README.md).

По умолчанию `USE_MOCK_DATA=true` — проект работает с демо-данными без 1С.

## MCP-сервер

Запуск MCP-сервера:

```bash
python -m src server
```

Сервер работает на stdio-транспорте и совместим с MCP-клиентами (Claude Desktop и др.).

## Разработка

### Логирование

Логи пишутся в `logs/mcp_server.log` и в stdout. Уровень настраивается через `LOG_LEVEL`.

### Технологии

- **LLM**: DeepSeek API (V3) — Function Calling
- **MCP**: Anthropic MCP SDK
- **1С**: HTTP-сервисы (JSON)
- **CLI**: click
- **Web UI**: Streamlit
- **Логирование**: loguru

## Лицензия

MIT
