# GRACE Integration Guide

## Для DeepSeek API / Open WebUI

### System Prompt с GRACE-контекстом

При инициализации сессии LLM передавайте следующий system prompt:

```
Ты — AI-аналитик склада и продаж на базе 1С:УНФ.

Перед выполнением задачи:
1. Прочитай docs/knowledge-graph.xml — пойми, какие объекты 1С и инструменты связаны.
2. Найди нужный контракт в docs/requirements.xml — проверь входы/выходы инструмента.
3. Используй docs/development-plan.xml, чтобы понять архитектуру модулей.
4. После изменений запусти docs/verification-plan.xml для проверки.

Доступные MCP-инструменты (18 шт):
- Данные: get_stock, get_sales, get_sales_by_manager, get_receivables, get_purchases, list_nomenclature
- Аналитика: get_analytics_context, get_sales_documents, forecast_sales, forecast_stockout, compare_forecasts, abc_xyz_analysis
- What-if: simulate_scenario, list_whatif_scenarios
- Визуализация: create_chart
- Метаданные 1С: config, describe, get_structure

Формат ответа всегда JSON с ключами: success, data/error.
```

### MCP Resource: Knowledge Graph

Добавьте в MCP сервер ресурс, который отдаёт knowledge-graph LLM:

```python
# START_BLOCK_knowledge_graph_resource
@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="grace://knowledge-graph",
            name="GRACE Knowledge Graph",
            description="Граф зависимостей объектов 1С и MCP инструментов",
            mimeType="application/xml",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "grace://knowledge-graph":
        with open("docs/knowledge-graph.xml") as f:
            return f.read()
    raise ValueError(f"Unknown resource: {uri}")
# END_BLOCK_knowledge_graph_resource
```

### Для Open WebUI

1. Загрузите `docs/requirements.xml` и `docs/knowledge-graph.xml` как файлы контекста в Open WebUI.
2. В настройках «Функции» добавьте pre-prompt:

```
<context>
<requirements>{{FILE:docs/requirements.xml}}</requirements>
<knowledge-graph>{{FILE:docs/knowledge-graph.xml}}</knowledge-graph>
</context>
```

3. Настройте инструменты MCP через Open WebUI → Connections → MCP Server: `uv run mcp run src/server.py`

### Pre-commit Hook

Установлен в `.git/hooks/pre-commit`. Автоматически запускает `scripts/grace-lint.sh` перед каждым коммитом. Для ручного запуска:

```bash
./scripts/grace-lint.sh
```

### CI/CD

В `.github/workflows/ci.yml` добавлен шаг `grace-lint`, который выполняется перед тестами. При ошибках GRACE-артефактов пайплайн останавливается.

### Быстрый старт

```bash
# Проверить GRACE-артефакты
./scripts/grace-lint.sh

# Проверить MCP протокол
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m src server

# Запустить тесты
USE_MOCK_DATA=true python -m pytest tests/ -v
```
