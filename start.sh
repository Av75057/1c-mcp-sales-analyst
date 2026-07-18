#!/bin/bash
set -e
cd "$(dirname "$0")"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info() { echo -e "${CYAN}[INFO]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC}   $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; }

VENV=".venv"
PID_DIR="logs"
mkdir -p "$PID_DIR"

if [ ! -d "$VENV" ]; then
    err "Виртуальное окружение не найдено. Выполните: python3 -m venv .venv && source .venv/bin/activate && pip install -e ."
    exit 1
fi
source "$VENV/bin/activate"

_cmd() { local name="${!#}"; nohup "${@:1:$#-1}" > "$PID_DIR/$name.log" 2>&1 & echo $! > "$PID_DIR/$name.pid"; }

_port_check() {
    local p="${1:-8000}"
    if ss -tlnp "sport = :$p" 2>/dev/null | grep -q "LISTEN"; then
        err "Порт $p уже занят. Выполните: $0 stop"
        return 1
    fi
    return 0
}

start_web() {
    PORT="${PORT:-8000}"
    _port_check "$PORT" || return 1

    # Сборка React SPA, если есть frontend
    if [ -d "frontend" ]; then
        if [ ! -d "frontend/dist" ] || [ "$1" == "--rebuild" ]; then
            info "Сборка React SPA..."
            (cd frontend && npx vite build 2>/dev/null) || warn "Vite build skipped (проверьте frontend)"
        fi
    fi

    _cmd "$VENV/bin/uvicorn" web.app:app --host 0.0.0.0 --port "$PORT" --proxy-headers --log-level info web
    sleep 1
    if kill -0 "$(cat "$PID_DIR/web.pid")" 2>/dev/null; then
        ok "Web UI запущен (PID $(cat "$PID_DIR/web.pid")) — http://localhost:$PORT"
    else
        err "Ошибка запуска. Лог: $PID_DIR/web.log"; tail -5 "$PID_DIR/web.log"
    fi
}

start_mcp() {
    _cmd "$VENV/bin/python" -m src server mcp
    ok "MCP сервер запущен (PID $(cat "$PID_DIR/mcp.pid"))"
}

start_proxy() {
    _cmd "$VENV/bin/python" -m src proxy proxy
    ok "Proxy запущен (PID $(cat "$PID_DIR/proxy.pid")) — http://localhost:${PROXY_PORT:-8000}/v1"
}

start_react() {
    if [ ! -d "frontend/node_modules" ]; then
        info "Установка зависимостей React..."
        (cd frontend && npm install) || return 1
    fi
    if [ "$1" == "prod" ]; then
        info "Сборка React SPA для production..."
        (cd frontend && npx vite build) || return 1
        ok "React SPA собрана. Запустите: ./start.sh web"
    else
        _port_check 5173 || return 1
        info "Запуск React dev server на порту 5173..."
        _cmd npx vite --host 0.0.0.0 --port 5173 --root frontend react
        sleep 2
        ok "React Dev: http://localhost:5173 | API: http://localhost:8000"
    fi
}

stop_all() {
    for svc in web mcp proxy react; do
        pidf="$PID_DIR/$svc.pid"
        [ -f "$pidf" ] && kill "$(cat "$pidf")" 2>/dev/null && ok "$svc остановлен" || true
        rm -f "$pidf"
    done
}

status() {
    local any=0
    for svc in web mcp proxy react; do
        pidf="$PID_DIR/$svc.pid"
        if [ -f "$pidf" ] && kill -0 "$(cat "$pidf")" 2>/dev/null; then
            ok "$svc запущен (PID $(cat "$pidf"))"; any=1
        else
            warn "$svc не запущен"
        fi
    done
    [ "$any" = 0 ] && echo -e "  ${YELLOW}Запустите: $0 web  или  $0 all${NC}"
}

logs() { tail -f "$PID_DIR/${1:-web}.log" 2>/dev/null || err "Нет логов для $1"; }

case "${1:-menu}" in
    web|mcp|proxy) start_"$1" ;;
    react|react-prod) start_react "$2" ;;
    all) start_web; start_mcp; start_proxy; ok "Все сервисы запущены" ;;
    stop) stop_all ;;
    restart) stop_all; sleep 1; start_web; start_mcp; start_proxy ;;
    status) status ;;
    logs) logs "$2" ;;
    menu)
        while true; do
            echo; echo -e "${CYAN}╔══════════════════════════════╗${NC}"
            echo -e "${CYAN}║   1C MCP Sales Analyst       ║${NC}"
            echo -e "${CYAN}╚══════════════════════════════╝${NC}"; echo
            status 2>&1 | sed 's/^/  /'
            echo; echo "  1) Web UI    2) MCP       3) Proxy"
            echo "  4) React Dev 5) React Prod 6) All"
            echo "  7) Stop      8) Logs       9) Status      0) Exit"; echo
            read -rp "  Выбор: " c || break
            case "$c" in
                1) start_web;;
                2) start_mcp;;
                3) start_proxy;;
                4) start_react dev;;
                5) start_react prod;;
                6) start_web; start_mcp; start_proxy; ok "Всё запущено";;
                7) stop_all;;
                8) read -rp "  Логи (web/mcp/proxy/react): " s; logs "$s";;
                9) status;;
                0) echo; exit 0;;
                *) err "Неверный выбор";;
            esac
            echo; read -rp "  Нажмите Enter..."
        done
        ;;
    *)
        echo "Использование: $0 {web|mcp|proxy|react|all|stop|restart|status|logs|menu}"
        echo "  ./start.sh              — интерактивное меню"
        echo "  ./start.sh web          — Web UI на http://localhost:8000"
        echo "  ./start.sh web --rebuild — Web UI с пересборкой React SPA"
        echo "  ./start.sh react        — React Dev на http://localhost:5173"
        echo "  ./start.sh react prod   — Сборка React + Web UI"
        echo "  ./start.sh all          — всё сразу"
        echo "  ./start.sh stop         — остановить всё"
        echo "  ./start.sh status       — статус"
        ;;
esac
