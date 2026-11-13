import asyncio
import json
import os
import time

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel


app = FastAPI(title="The Relay Stand-in Model")


# Configurable behaviour through environment variables
BASE_DELAY = float(os.getenv("STANDIN_DELAY", "0.5"))
FAIL_RATE = float(os.getenv("STANDIN_FAIL_RATE", "0"))
RATE_LIMIT_EVERY = int(os.getenv("STANDIN_RATE_LIMIT_EVERY", "0"))
OVERLOAD_THRESHOLD = int(os.getenv("STANDIN_OVERLOAD_THRESHOLD", "5"))
OVERLOAD_DELAY = float(os.getenv("STANDIN_OVERLOAD_DELAY", "2"))

active_requests = 0
request_count = 0


class ChatRequest(BaseModel):
    model: str = "standin"
    messages: list
    stream: bool = True


def get_answer(messages):
    """Generate a predictable stand-in answer."""

    question = ""

    for message in reversed(messages):
        if message.get("role") == "user":
            question = message.get("content", "")
            break

    return (
        "This is a simulated stand-in model response. "
        "The system received your research question and processed "
        "the supplied context. This response is for pipeline and "
        "load testing only, not a verified research answer."
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "active": active_requests
    }


@app.post("/v1/chat/completions")
async def chat_completions(body: ChatRequest, request: Request):

    global active_requests, request_count

    request_count += 1
    current_request = request_count

    # Simulated rate limit
    if (
        RATE_LIMIT_EVERY > 0
        and current_request % RATE_LIMIT_EVERY == 0
    ):
        return JSONResponse(
            status_code=429,
            content={"error": "Simulated rate limit"},
            headers={"Retry-After": "1"}
        )

    # Simulated random failure
    import random

    if random.random() < FAIL_RATE:
        return JSONResponse(
            status_code=503,
            content={"error": "Simulated model failure"}
        )

    active_requests += 1

    try:
        delay = BASE_DELAY

        if active_requests > OVERLOAD_THRESHOLD:
            delay += OVERLOAD_DELAY

        await asyncio.sleep(delay)

        answer = get_answer(body.messages)

        async def generate():

            # Stream response word by word
            for word in answer.split():

                chunk = {
                    "choices": [
                        {
                            "delta": {
                                "content": word + " "
                            }
                        }
                    ]
                }

                yield f"data: {json.dumps(chunk)}\n\n"

                await asyncio.sleep(0.03)

            yield "data: [DONE]\n\n"

        if body.stream:
            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )

        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": answer
                    }
                }
            ]
        }

    finally:
        active_requests -= 1