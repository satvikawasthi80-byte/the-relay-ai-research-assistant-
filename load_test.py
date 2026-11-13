import asyncio
import csv
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx


API_URL = "http://127.0.0.1:8000/ask"
RESULT_FILE = Path("results.csv")
SOURCE = os.getenv("MODEL_SOURCE", "standin")

QUESTIONS = [
    "What is the main contribution of Attention Is All You Need?",
    "What is the architecture of the Transformer?",
    "What is Moshi and what problem does it address?",
    "What is the main idea of Dynamic Chunking?",
    "How does attention work in the Transformer?"
]

FIELDS = [
    "request_id",
    "scenario",
    "source",
    "start_time",
    "first_token_ms",
    "total_ms",
    "status",
    "retries",
    "tokens_in",
    "tokens_out",
    "retrieval_setting",
    "answer_grade"
]


def save_result(row):
    file_exists = RESULT_FILE.exists()

    with RESULT_FILE.open(
        "a", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


async def send_request(client, question, scenario):
    request_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc).isoformat()
    started = time.perf_counter()

    row = {
        "request_id": request_id,
        "scenario": scenario,
        "source": SOURCE,
        "start_time": start_time,
        "first_token_ms": "",
        "total_ms": "",
        "status": "error",
        "retries": 0,
        "tokens_in": "",
        "tokens_out": "",
        "retrieval_setting": "tfidf_top5_chunk500",
        "answer_grade": ""
    }

    try:
        response = await client.post(
            API_URL,
            json={"question": question}
        )

        elapsed = (time.perf_counter() - started) * 1000
        row["total_ms"] = round(elapsed, 2)

        if response.status_code == 429:
            row["status"] = "rate_limited"

        elif response.status_code == 408:
            row["status"] = "timeout"

        elif response.status_code >= 400:
            row["status"] = "error"

        else:
            result = response.json()

            row["status"] = (
                "ok" if result.get("status") == "ok"
                else "refused_correctly"
            )

            row["first_token_ms"] = (
                result.get("first_token_ms") or ""
            )

            row["retries"] = result.get("retries", 0)

        print(
            f"{scenario}: {row['status']} "
            f"| {row['total_ms']} ms"
        )

    except httpx.TimeoutException:
        row["status"] = "timeout"
        row["total_ms"] = round(
            (time.perf_counter() - started) * 1000, 2
        )

    except httpx.RequestError as error:
        row["status"] = "error"
        row["total_ms"] = round(
            (time.perf_counter() - started) * 1000, 2
        )
        print("Connection error:", error)

    except Exception as error:
        row["status"] = "error"
        row["total_ms"] = round(
            (time.perf_counter() - started) * 1000, 2
        )
        print("Unexpected error:", error)

    save_result(row)
    return row


async def run_scenario(name, total_requests, concurrency):
    print(f"\nStarting scenario: {name}")
    print(f"Requests: {total_requests}, concurrency: {concurrency}")

    limits = httpx.Limits(
        max_connections=concurrency,
        max_keepalive_connections=concurrency
    )

    timeout = httpx.Timeout(60.0)

    async with httpx.AsyncClient(
        timeout=timeout,
        limits=limits
    ) as client:

        semaphore = asyncio.Semaphore(concurrency)

        async def limited_request(index):
            async with semaphore:
                question = QUESTIONS[index % len(QUESTIONS)]
                return await send_request(
                    client, question, name
                )

        results = await asyncio.gather(
            *[
                limited_request(i)
                for i in range(total_requests)
            ]
        )

    successful = sum(
        1 for r in results if r["status"] == "ok"
    )

    failed = total_requests - successful

    print(f"Completed: {name}")
    print(f"Successful: {successful}")
    print(f"Other outcomes: {failed}")


async def main():
    print("THE RELAY LOAD TEST")
    print("Model source:", SOURCE)

    await run_scenario(
        name="steady",
        total_requests=10,
        concurrency=2
    )

    await run_scenario(
        name="burst",
        total_requests=15,
        concurrency=15
    )

    await run_scenario(
        name="sustained_overload",
        total_requests=30,
        concurrency=10
    )

    print("\nAll scenarios completed.")
    print("Results saved in:", RESULT_FILE)


if __name__ == "__main__":
    asyncio.run(main())