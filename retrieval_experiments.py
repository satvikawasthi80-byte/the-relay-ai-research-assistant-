import csv
import time
from pathlib import Path

from app import config
from app.retrieval import PaperRetriever


OUTPUT_FILE = Path("retrieval_experiments.csv")

QUESTIONS = [
    "What is the main contribution of Attention Is All You Need?",
    "How does Moshi support real-time dialogue?",
    "What is Dynamic Chunking and why is it useful?"
]

SETTINGS = [
    {"name": "small", "chunk_size": 300, "top_k": 3},
    {"name": "medium", "chunk_size": 500, "top_k": 5},
    {"name": "large", "chunk_size": 800, "top_k": 8}
]


def run_experiments():

    rows = []

    original_chunk_size = config.RETRIEVAL_CHUNK_SIZE
    original_top_k = config.RETRIEVAL_TOP_K

    try:
        for setting in SETTINGS:

            print(f"\nTesting setting: {setting['name']}")

            config.RETRIEVAL_CHUNK_SIZE = setting["chunk_size"]
            config.RETRIEVAL_TOP_K = setting["top_k"]

            start_index = time.perf_counter()
            retriever = PaperRetriever()
            indexing_ms = (
                time.perf_counter() - start_index
            ) * 1000

            for question in QUESTIONS:

                start_search = time.perf_counter()

                passages = retriever.search(question)

                search_ms = (
                    time.perf_counter() - start_search
                ) * 1000

                papers_found = sorted({
                    p["paper"] for p in passages
                })

                rows.append({
                    "setting": setting["name"],
                    "chunk_size": setting["chunk_size"],
                    "top_k": setting["top_k"],
                    "question": question,
                    "indexing_ms": round(indexing_ms, 2),
                    "search_ms": round(search_ms, 2),
                    "passages_found": len(passages),
                    "papers_found": ";".join(papers_found)
                })

                print(
                    f"Search: {search_ms:.2f} ms | "
                    f"Passages: {len(passages)}"
                )

    finally:
        config.RETRIEVAL_CHUNK_SIZE = original_chunk_size
        config.RETRIEVAL_TOP_K = original_top_k

    fields = [
        "setting",
        "chunk_size",
        "top_k",
        "question",
        "indexing_ms",
        "search_ms",
        "passages_found",
        "papers_found"
    ]

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(rows)

    print("\nExperiments completed!")
    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    run_experiments()