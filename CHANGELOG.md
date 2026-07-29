# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/)

## [0.1.0] - 2026-07-30

### Added
- MCP-сервер для 1С:Предприятие с AI-аналитикой продаж
- 22+ модулей: auth (JWT+RBAC), audit, search (FTS5+fuzzy),
  guardrails, what-if (4 сценария), rag, reflection (AI-критик)
- Frontend: React + TypeScript + ECharts (12 типов графиков)
- AI-чат с streaming (WebSocket), историей сессий
- ABC/XYZ анализ, AI-инсайты, OCR документов
- Batch-запросы к 1С, кэширование, Circuit Breaker
- Docker Compose для развёртывания
- CI/CD: GitHub Actions (grace-lint, backend, frontend, e2e)
- Prometheus-метрики, health checks (liveness/readiness)
- Админ-панель (11 модулей)

### Fixed
- CI/CD: 13 исправлений (weasyprint deps, E2E server, coverage)
- TypeScript: 20 ошибок (implicit any, unused vars, type mismatches)
- Тесты: mock plotly export, unskip test_charts/test_deepseek
- Очистка корня: dev-скрипты → scripts/dev/

### Security
- JWT + RBAC (4 роли), rate limiting, security headers
- InjectionDetector, ReadOnlyGuard, маскирование ПДн
