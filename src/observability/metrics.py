from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, generate_latest

# HTTP
http_requests_total = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"])
http_request_duration_seconds = Histogram("http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"], buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0])

# DeepSeek
deepseek_requests_total = Counter("deepseek_requests_total", "DeepSeek API calls", ["status"])
deepseek_request_duration_seconds = Histogram("deepseek_request_duration_seconds", "DeepSeek API duration", ["model"], buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0])
deepseek_errors_total = Counter("deepseek_errors_total", "DeepSeek errors by type", ["error_type"])
ai_response_tokens = Counter("ai_response_tokens_total", "AI response tokens", ["type"])

# 1С
c1_requests_total = Counter("c1_requests_total", "1C API calls", ["endpoint", "status"])
c1_request_duration_seconds = Histogram("c1_request_duration_seconds", "1C API duration", ["endpoint"], buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0])
c1_errors_total = Counter("c1_errors_total", "1C errors by type", ["error_type", "endpoint"])

# MCP Tools
mcp_tool_calls_total = Counter("mcp_tool_calls_total", "MCP tool calls", ["tool_name", "status"])
mcp_tool_duration_seconds = Histogram("mcp_tool_duration_seconds", "MCP tool duration", ["tool_name"], buckets=[0.1, 0.5, 1.0, 2.0, 5.0])

# Chat
chat_requests_total = Counter("chat_requests_total", "Chat requests", ["status"])

# Circuit Breakers
circuit_breaker_state = Gauge("circuit_breaker_state", "Circuit breaker state (0=closed, 1=open, 2=half_open)", ["name"])
circuit_breaker_failures = Counter("circuit_breaker_failures_total", "Circuit breaker failures", ["name"])


def get_metrics() -> str:
    return generate_latest().decode("utf-8")


def set_cb_state(name: str, state: str) -> None:
    mapping = {"closed": 0, "open": 1, "half_open": 2}
    circuit_breaker_state.labels(name=name).set(mapping.get(state, 0))
