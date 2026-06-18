#!/bin/bash
if [ -f /tmp/proxy.pid ]; then
    kill $(cat /tmp/proxy.pid) 2>/dev/null
    rm /tmp/proxy.pid
    echo "Proxy stopped"
else
    echo "Proxy not running (no PID file)"
fi
