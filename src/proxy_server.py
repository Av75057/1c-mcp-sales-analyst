from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import settings
from src.deepseek_client import TOOL_DEFINITIONS, DeepSeekClient
from src.logger import logger
from src.tools import (
    get_receivables_tool,
    get_sales_by_manager_tool,
    get_sales_tool,
    get_stock_tool,
    list_nomenclature_tool,
)

app = FastAPI(title="1C MCP Proxy")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TOOL_NAME_TO_FUNC = {
    "get_stock": get_stock_tool,
    "get_sales": get_sales_tool,
    "get_sales_by_manager": get_sales_by_manager_tool,
    "get_receivables": get_receivables_tool,
    "list_nomenclature": list_nomenclature_tool,
}


class ChatMessage(BaseModel):
    role: str
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None


class ChatRequest(BaseModel):
    model: str = "deepseek-chat"
    messages: list[ChatMessage]
    temperature: float | None = 0.1
    max_tokens: int | None = 2000
    stream: bool = False


class ToolCallResponse(BaseModel):
    id: str
    type: str = "function"
    function: dict[str, Any]


class ChoiceMessage(BaseModel):
    role: str = "assistant"
    content: str | None = None
    tool_calls: list[ToolCallResponse] | None = None


class Choice(BaseModel):
    index: int = 0
    message: ChoiceMessage
    finish_reason: str


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[Choice]
    usage: Usage


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": settings.llm_model,
                "object": "model",
                "created": 1234567890,
                "owned_by": "deepseek",
            }
        ],
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    try:
        last_msg = request.messages[-1] if request.messages else None
        if not last_msg:
            raise HTTPException(400, "No messages")

        messages = [{"role": m.role, "content": m.content or ""} for m in request.messages]

        deepseek_client = DeepSeekClient()

        system_prompt = (
            "Ты — аналитик склада и продаж компании. Отвечай на русском языке. "
            "Используй инструменты для получения данных из 1С. Не выдумывай цифры."
        )

        chat_messages: list = [{"role": "system", "content": system_prompt}]
        for m in request.messages:
            if m.role == "tool":
                chat_messages.append({
                    "role": "tool",
                    "tool_call_id": m.tool_call_id or "",
                    "content": m.content or "",
                })
            elif m.tool_calls:
                chat_messages.append({
                    "role": "assistant",
                    "content": m.content,
                    "tool_calls": [
                        {
                            "id": tc.get("id", ""),
                            "type": "function",
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"],
                            },
                        }
                        for tc in m.tool_calls
                    ],
                })
            else:
                chat_messages.append({"role": m.role, "content": m.content or ""})

        max_iterations = 10
        total_prompt_tokens = 0
        total_completion_tokens = 0

        for _ in range(max_iterations):
            response = await deepseek_client._call_llm(chat_messages, tools=TOOL_DEFINITIONS)
            choice = response.choices[0]

            if response.usage:
                total_prompt_tokens += response.usage.prompt_tokens or 0
                total_completion_tokens += response.usage.completion_tokens or 0

            if choice.finish_reason == "stop":
                return ChatResponse(
                    id=response.id,
                    created=response.created,
                    model=request.model,
                    choices=[
                        Choice(
                            message=ChoiceMessage(
                                content=choice.message.content or "",
                            ),
                            finish_reason="stop",
                        )
                    ],
                    usage=Usage(
                        prompt_tokens=total_prompt_tokens,
                        completion_tokens=total_completion_tokens,
                        total_tokens=total_prompt_tokens + total_completion_tokens,
                    ),
                )

            if choice.finish_reason == "tool_calls":
                msg = choice.message
                chat_messages.append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in (msg.tool_calls or [])
                    ],
                })

                for tc in msg.tool_calls or []:
                    func_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        args = {}

                    func = TOOL_NAME_TO_FUNC.get(func_name)
                    if func:
                        try:
                            result = await func(**args)
                            result_text = json.dumps(result, ensure_ascii=False, default=str)
                        except Exception as e:
                            result_text = f"Ошибка: {e!s}"
                    else:
                        result_text = f"Неизвестный инструмент: {func_name}"

                    chat_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_text,
                    })
                continue

            if choice.finish_reason == "length":
                return ChatResponse(
                    id=response.id,
                    created=response.created,
                    model=request.model,
                    choices=[
                        Choice(
                            message=ChoiceMessage(
                                content=(choice.message.content or "") + "\n\n[Ответ обрезан]",
                            ),
                            finish_reason="length",
                        )
                    ],
                    usage=Usage(
                        prompt_tokens=total_prompt_tokens,
                        completion_tokens=total_completion_tokens,
                        total_tokens=total_prompt_tokens + total_completion_tokens,
                    ),
                )

        return ChatResponse(
            id="",
            created=0,
            model=request.model,
            choices=[
                Choice(
                    message=ChoiceMessage(content="Превышен лимит итераций"),
                    finish_reason="stop",
                )
            ],
            usage=Usage(),
        )

    except Exception as e:
        logger.error("Proxy error: {}", e)
        raise HTTPException(500, str(e))


async def run_async():
    import uvicorn

    config = uvicorn.Config(app, host=settings.mcp_host, port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


def run():
    import asyncio

    asyncio.run(run_async())
