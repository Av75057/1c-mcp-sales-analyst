# AI-аналитик 1С + MCP + DeepSeek

AI-аналитик склада и продаж на базе 1С:УНФ, MCP и DeepSeek. Замена ручного построения отчётов на текстовые запросы, AI-инсайты, симуляцию сценариев и распознавание документов.

## 🚀 Быстрый старт

```bash
# Клонировать
git clone https://github.com/Av75057/1c-mcp-sales-analyst.git
cd 1c-mcp-sales-analyst

# Настроить
cp .env.example .env
# Отредактировать .env: DEEPSEEK_API_KEY, C1_BASE_URL, C1_USERNAME, C1_PASSWORD

# Установить
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Запустить Web UI
./start.sh web
# → http://localhost:8000 | admin / admin123
```

## 📊 Страницы Web UI

| Страница | URL | Описание |
|---|---|---|
| **📊 Дашборд** | `/` | Ключевые метрики |
| **📦 Остатки** | `/stock` | Поиск, фильтр |
| **💰 Продажи** | `/sales` | Фильтры, аналитика |
| **💬 AI Чат** | `/chat` | Natural language + история сессий |
| **🔍 Поиск** | `/search` | FTS5 + fuzzy + фильтры + фасеты |
| **📄 Реализации** | `/documents/sales` | Список документов с фильтрами |
| **🔮 What-If** | `/whatif` | 4 сценария + графики |
| **📊 ABC/XYZ** | `/analysis/abc-xyz` | Матрица 3×3 |
| **🤖 Инсайты** | `/insights` | AI-инсайты |
| **📄 Документы** | `/documents` | OCR + распознавание |
| **⚙️ Статус** | `/status` | Мониторинг |
| **🔐 Админка** | `/admin` | Управление системой |

## 🔧 Функции

### AI Чат с историей
- Сессии с авто-названием из первого сообщения
- Сохранение всех сообщений и tool calls
- Контекст sliding window (3000 токенов)
- Поиск по истории, экспорт в JSON

### Продвинутый поиск номенклатуры
- FTS5 + BM25 ранжирование (локальный SQLite кэш)
- Нечёткий поиск (rapidfuzz, обработка опечаток)
- Автодополнение (Trie-структура)
- Синонимы (ноут→ноутбук, телефон→смартфон)
- Фильтры: группа, тип, наличие, цена
- Фасеты в результатах
- Аналитика поисковых запросов

### Batch-запросы к 1С
- Группировка нескольких запросов в один HTTP-вызов
- Автоматический fallback на последовательные запросы
- Агрегированные эндпоинты

### Безопасность
- JWT-аутентификация (Bearer + httponly cookies)
- RBAC: admin, analyst, viewer, api_client
- Rate limiting по ролям (slowapi)
- Security headers (CSP, HSTS, X-Frame-Options)
- CORS с белым списком
- Аудит действий (audit.log)
- Маскирование sensitive data в логах

### Админ-панель (11 модулей)
- Dashboard: метрики и алерты
- Users: CRUD + блокировка + сброс сессий
- Audit: просмотр + фильтры + экспорт CSV
- Monitoring: производительность, endpoint stats
- Settings: управление + история + откат
- Integrations: health check 1С / DeepSeek
- Tools: 15 MCP инструментов + статистика
- API Keys: создание + отзыв
- IP Blocks: блокировка IP
- Search Analytics: топ запросов
- System: ресурсы сервера

### Стабильность (Фаза 1)
- Health checks: `/health`, `/health/live`, `/health/ready`
- Circuit Breaker для DeepSeek и 1С
- Prometheus метрики: `/metrics`
- Guardrails: верификация чисел AI + защита от инъекций
- X-Request-ID для корреляции запросов

## 🔌 API Endpoints

```bash
# Аутентификация
POST /api/auth/login          # username + password → JWT
POST /api/auth/logout         # сброс cookie
GET  /api/auth/me             # текущий пользователь

# Чат
GET  /api/chat/sessions       # список сессий
POST /api/chat/sessions       # создать сессию
GET  /api/chat/sessions/{id}/messages
POST /api/chat/sessions/{id}/messages  # отправить сообщение
GET  /api/chat/search?q=      # поиск по сообщениям

# Поиск
POST /api/search/nomenclature # поиск с фильтрами
GET  /api/search/autocomplete?q=  # автодополнение
GET  /api/search/synonyms     # список синонимов

# Админка
GET  /admin/                  # дашборд
GET  /admin/users/            # пользователи
GET  /admin/audit/            # логи аудита
GET  /admin/monitoring/       # мониторинг
GET  /admin/settings/         # настройки
GET  /admin/integrations/     # интеграции
GET  /admin/tools/            # MCP инструменты
GET  /admin/system/           # система

# Мониторинг
GET  /health                  # health check
GET  /health/live             # liveness probe
GET  /metrics                 # Prometheus метрики

# 1С
POST /hs/api/v1/batch         # batch-запросы
GET  /hs/api/stock            # остатки
GET  /hs/api/sales            # продажи
```

## 🧪 Тесты

```bash
# Все тесты
pytest tests/ -v

# По модулям
pytest tests/test_search.py
pytest tests/test_chat_models.py
pytest tests/test_guardrails.py
pytest tests/test_resilience.py
pytest tests/test_admin.py
pytest tests/integration/

# С coverage
pytest tests/ --cov=src --cov=web --cov-report=term
pytest tests/ --cov=src --cov=web --cov-report=html
# → открыть htmlcov/index.html
```

## 🐳 Docker

```bash
# Сборка
docker compose build

# Запуск всех сервисов
docker compose up -d

# Только proxy + web-ui
docker compose up -d proxy open-webui

# Логи
docker compose logs -f
```

## 📁 Структура проекта

```
src/
├── admin/          # Админ-панель (11 модулей)
├── auth/           # JWT + RBAC аутентификация
├── audit/          # Аудит + AuditLogger
├── chat/           # История сессий чата
├── clients/        # C1Client + BatchC1Client
├── guardrails/     # Верификация AI + защита
├── health/         # Health checks
├── mcp/            # MCP tools registry
├── observability/  # Prometheus метрики
├── resilience/     # Circuit Breaker
├── search/         # FTS5 + fuzzy + synonyms
├── security/       # Security headers + rate limiting
└── whatif/         # What-If симуляции

web/
├── app.py          # FastAPI приложение
└── templates/      # HTML шаблоны
```

## 🔑 Переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `DEEPSEEK_API_KEY` | API ключ DeepSeek | — |
| `C1_BASE_URL` | URL HTTP-сервиса 1С | `http://localhost/1c/api` |
| `C1_USERNAME` | Пользователь 1С | `service_user` |
| `C1_PASSWORD` | Пароль 1С | `service_password` |
| `JWT_SECRET_KEY` | Секрет для JWT | — |
| `AUTH_ENABLED` | Включить аутентификацию | `true` |
| `USE_MOCK_DATA` | Использовать мок-данные | `true` |

## 📄 Лицензия

MIT License. Copyright (c) 2026 Av75057.
