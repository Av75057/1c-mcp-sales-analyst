#!/bin/bash
set -e
cd "$(dirname "$0")"

# Цвета
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info() { echo -e "${CYAN}[INFO]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC}   $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; }

VENV=".venv"
PID_DIR="logs"

# Проверка окружения
if [ ! -d "$VENV" ]; then
    err "Виртуальное окружение не найдено. Создаю..."
    python3 -m venv "$VENV"
    source "$VENV/bin/activate"
    pip install -e . 2>&1 | tail -1
    ok "Окружение создано"
else
    source "$VENV/bin/activate"
fi

mkdir -p "$PID_DIR"

# === Режимы ===
start_web() {
    info "Запуск Web UI на http://0.0.0.0:${PORT:-8000}"
    nohup uvicorn web.app:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --log-level info > "$PID_DIR/web.log" 2>&1 &
    echo $! > "$PID_DIR/web.pid"
    ok "Web UI запущен (PID $(cat "$PID_DIR/web.pid"))"
}

start_mcp() {
    info "Запуск MCP сервера (stdio)"
    nohup python -m src server > "$PID_DIR/mcp.log" 2>&1 &
    echo $! > "$PID_DIR/mcp.pid"
    ok "MCP сервер запущен (PID $(cat "$PID_DIR/mcp.pid"))"
}

start_proxy() {
    info "Запуск OpenAI-прокси на http://0.0.0.0:${PROXY_PORT:-8000}"
    nohup python -m src proxy > "$PID_DIR/proxy.log" 2>&1 &
    echo $! > "$PID_DIR/proxy.pid"
    ok "Proxy запущен (PID $(cat "$PID_DIR/proxy.pid"))"
}

stop_all() {
    for svc in web mcp proxy; do
        if [ -f "$PID_DIR/$svc.pid" ]; then
            kill "$(cat "$PID_DIR/$svc.pid")" 2>/dev/null && ok "$svc остановлен" || warn "$svc не запущен"
            rm -f "$PID_DIR/$svc.pid"
        fi
    done
}

status() {
    for svc in web mcp proxy; do
        if [ -f "$PID_DIR/$svc.pid" ] && kill -0 "$(cat "$PID_DIR/$svc.pid")" 2>/dev/null; then
            ok "$svc запущен (PID $(cat "$PID_DIR/$svc.pid"))"
        else
            warn "$svc не запущен"
        fi
    done
}

logs() {
    svc="${1:-web}"
    tail -f "$PID_DIR/$svc.log" 2>/dev/null || err "Нет логов для $svc"
}

# === Главное меню ===
case "${1:-menu}" in
    web)     start_web ;;
    mcp)     start_mcp ;;
    proxy)   start_proxy ;;
    all)
        start_web
        start_mcp
        start_proxy
        ok "Все сервисы запущены"
        ;;
    stop)    stop_all ;;
    restart) stop_all; sleep 1; exec "$0" all ;;
    status)  status ;;
    logs)    logs "$2" ;;
    menu)
        echo
        echo -e "${CYAN}╔════════════════════════════╗${NC}"
        echo -e "${CYAN}║   1C MCP Sales Analyst    ║${NC}"
        echo -e "${CYAN}╚════════════════════════════╝${NC}"
        echo
        echo "1) Web UI     — http://localhost:${PORT:-8000}"
        echo "2) MCP Server — stdio"
        echo "3) Proxy      — http://localhost:${PROXY_PORT:-8000}/v1"
        echo "4) ВСЁ сразу"
        echo "5) Стоп"
        echo "6) Статус"
        echo "7) Логи"
        echo "0) Выход"
        echo
        read -rp "Выбор: " choice
        case "$choice" in
            1) start_web;;
            2) start_mcp;;
            3) start_proxy;;
            4) "$0" all;;
            5) stop_all;;
            6) status;;
            7) read -rp "Какой сервис? (web/mcp/proxy): " s; logs "$s";;
            0) exit 0;;
            *) err "Неверный выбор";;
        esac
        echo
        read -rp "Нажмите Enter..."
        exec "$0" menu
        ;;
    *)
        echo "Использование: $0 {web|mcp|proxy|all|stop|restart|status|logs|menu}"
        echo
        echo "  web     — Web UI (FastAPI)"
        echo "  mcp     — MCP сервер (stdio)"
        echo "  proxy   — OpenAI-совместимый прокси"
        echo "  all     — всё сразу"
        echo "  stop    — остановить всё"
        echo "  status  — статус сервисов"
        echo "  logs    — логи (например: $0 logs web)"
        echo "  menu    — интерактивное меню"
        ;;
esac
