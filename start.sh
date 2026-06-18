#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
echo "Starting 1C MCP Proxy on http://localhost:8000"
echo "Logs: /tmp/proxy.log"
nohup python3 -m src proxy > /tmp/proxy.log 2>&1 &
echo $! > /tmp/proxy.pid
echo "PID: $(cat /tmp/proxy.pid)"
