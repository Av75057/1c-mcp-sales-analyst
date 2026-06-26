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

_cmd() { nohup "$@" > "$PID_DIR/$2.log" 2>&1 & echo $! > "$PID_DIR/$2.pid"; }

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

stop_all() {
    for svc in web mcp proxy; do
        pidf="$PID_DIR/$svc.pid"
        [ -f "$pidf" ] && kill "$(cat "$pidf")" 2>/dev/null && ok "$svc остановлен" || true
        rm -f "$pidf"
    done
}

status() {
    local any=0
    for svc in web mcp proxy; do
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
            echo; echo "  1) Web UI    2) MCP  3) Proxy  4) All"
            echo "  5) Stop      6) Logs 7) Status       0) Exit"; echo
            read -rp "  Выбор: " c || break
            case "$c" in
                1) start_web;; 2) start_mcp;; 3) start_proxy;;
                4) start_web; start_mcp; start_proxy; ok "Всё запущено";;
                5) stop_all;;
                6) read -rp "  Логи (web/mcp/proxy): " s; logs "$s";;
                7) status;;
                0) echo; exit 0;;
                *) err "Неверный выбор";;
            esac
            echo; read -rp "  Нажмите Enter..."
        done
        ;;
    *)
        echo "Использование: $0 {web|mcp|proxy|all|stop|restart|status|logs|menu}"
        echo "  ./start.sh        — интерактивное меню"
        echo "  ./start.sh web    — Web UI на http://localhost:8000"
        echo "  ./start.sh all    — всё сразу"
        echo "  ./start.sh stop   — остановить всё"
        echo "  ./start.sh status — статус"
        ;;
esac
