import asyncio
import time
import httpx

from .retrieval import get_retriever
from .model import complete, ModelError
from .config import MAX_RETRIES


def make_context(passages):
    """Prepare retrieved passages for the AI model."""

    return "\n\n".join(
        f"[{p['paper']}, page {p['page']}] {p['text']}"
        for p in passages
    )


async def answer_question(question: str):

    started = time.perf_counter()

    if len(question.strip()) < 5:
        return {
            "answer": "Please provide a more specific question.",
            "citations": [],
            "status": "refused",
            "first_token_ms": None,
            "total_ms": 0,
            "retries": 0,
            "retrieved": 0
        }

    # STEP 1: RETRIEVAL
    try:
        passages = get_retriever().search(question)
    except (FileNotFoundError, ValueError) as e:
        return {
            "answer": f"Paper retrieval failed: {e}",
            "citations": [],
            "status": "error",
            "first_token_ms": None,
            "total_ms": (time.perf_counter() - started) * 1000,
            "retries": 0,
            "retrieved": 0
        }

    if not passages:
        return {
            "answer": (
                "The supplied papers do not provide enough "
                "searchable evidence to answer this question."
            ),
            "citations": [],
            "status": "refused",
            "first_token_ms": None,
            "total_ms": (time.perf_counter() - started) * 1000,
            "retries": 0,
            "retrieved": 0
        }

    # STEP 2: BUILD CONTEXT
    context = make_context(passages)

    system = (
        "You are a research assistant. Answer ONLY using the "
        "supplied research paper excerpts. "
        "If evidence is insufficient, explicitly say that "
        "the supplied papers do not specify the answer. "
        "Every factual claim must cite its exact source using "
        "[filename, page N]. Never invent citations. "
        "Be concise and accurate."
    )

    messages = [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"Research paper excerpts:\n{context}"
            )
        }
    ]

    # STEP 3: MODEL CALL AND RETRIES
    first_token = None

    def record_ttft(value):
        nonlocal first_token

        if first_token is None:
            first_token = value

    attempts = 0
    answer = ""
    error = None

    while attempts <= MAX_RETRIES:

        try:
            answer, meta = await complete(
                messages,
                record_ttft
            )

            error = None

        except ModelError as e:
            error = e

            if e.status_code == 429 and attempts < MAX_RETRIES:
                try:
                    wait = float(e.retry_after or 1)
                except (TypeError, ValueError):
                    wait = 1

                await asyncio.sleep(min(wait, 3))
                attempts += 1
                continue

            break

        except httpx.RequestError as e:
            error = ModelError(str(e), 503)
            break

        except RuntimeError as e:
            error = ModelError(str(e), 503)
            break

        # STEP 4: CITATION VALIDATION
        valid_citations = {
            f"[{p['paper']}, page {p['page']}]"
            for p in passages
        }

        has_citation = any(
            citation in answer
            for citation in valid_citations
        )

        if has_citation or attempts >= MAX_RETRIES:
            break

        messages.append({
            "role": "assistant",
            "content": answer
        })

        messages.append({
            "role": "user",
            "content": (
                "Your answer lacked a verifiable citation. "
                "Either cite the supplied excerpts exactly "
                "or explicitly refuse to answer."
            )
        })

        attempts += 1

    # STEP 5: FINAL RESPONSE
    elapsed = (time.perf_counter() - started) * 1000

    if error:

        status = (
            "rate_limited"
            if error.status_code == 429
            else "error"
        )

        answer = (
            "The model service is temporarily unavailable. "
            "Please retry later."
        )

        citations = []

    else:

        citations = [
            f"{p['paper']} p.{p['page']}"
            for p in passages
            if f"[{p['paper']}, page {p['page']}]" in answer
        ]

        status = "ok" if citations else "refused"

        if not citations and not any(
            phrase in answer.lower()
            for phrase in [
                "do not",
                "not specify",
                "insufficient",
                "cannot verify"
            ]
        ):
            answer = (
                "I cannot verify a supported answer "
                "from the retrieved paper passages."
            )

            status = "refused"

    return {
        "answer": answer,
        "citations": citations,
        "status": status,
        "first_token_ms": first_token,
        "total_ms": elapsed,
        "retries": attempts,
        "retrieved": len(passages)
    }