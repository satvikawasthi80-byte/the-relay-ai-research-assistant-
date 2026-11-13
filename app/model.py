import asyncio, time
import httpx
from groq import AsyncGroq
from . import config

class ModelError(Exception):
    def __init__(self, message, status_code=None, retry_after=None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after

async def complete(messages, on_first_token=None):
    start = time.perf_counter()
    if config.MODEL_SOURCE == "real":
        if not config.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is missing. Add it to .env")
        client = AsyncGroq(api_key=config.GROQ_API_KEY, timeout=config.REQUEST_TIMEOUT_SECONDS)
        try:
            stream = await client.chat.completions.create(
                model=config.GROQ_MODEL, messages=messages, temperature=0,
                max_tokens=700, stream=True
            )
            pieces = []
            async for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    if on_first_token and not pieces:
                        on_first_token((time.perf_counter() - start) * 1000)
                    pieces.append(delta)
            return "".join(pieces), {"source": "real", "tokens_in": None, "tokens_out": None}
        except Exception as e:
            status = getattr(e, "status_code", None)
            headers = getattr(e, "response", None)
            retry_after = None
            if headers is not None:
                retry_after = headers.headers.get("retry-after")
            raise ModelError(str(e), status, retry_after) from e
    async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT_SECONDS) as client:
        try:
            async with client.stream("POST", config.STANDIN_URL, json={
                "model": "standin", "messages": messages, "stream": True
            }) as response:
                if response.status_code >= 400:
                    raise ModelError(await response.aread(), response.status_code,
                                     response.headers.get("retry-after"))
                pieces = []
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    import json
                    obj = json.loads(data)
                    delta = obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        if on_first_token and not pieces:
                            on_first_token((time.perf_counter() - start) * 1000)
                        pieces.append(delta)
                return "".join(pieces), {"source": "standin", "tokens_in": None, "tokens_out": None}
        except httpx.TimeoutException as e:
            raise ModelError("Stand-in request timed out", 408) from e
