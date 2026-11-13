import time
from pathlib import Path

import requests


PAPERS_DIR = Path("data/papers")

PAPERS = [
    {
        "name": "attention_is_all_you_need_v7.pdf",
        "url": "https://export.arxiv.org/pdf/1706.03762v7"
    },
    {
        "name": "moshi_v1.pdf",
        "url": "https://export.arxiv.org/pdf/2410.00037v1"
    },
    {
        "name": "dynamic_chunking_v2.pdf",
        "url": "https://export.arxiv.org/pdf/2507.07955v2"
    }
]


def download_paper(paper):

    filename = PAPERS_DIR / paper["name"] 

    print(f"\nDownloading: {paper['name']}")

    for attempt in range(3):

        try:
            response = requests.get(
                paper["url"],
                timeout=90
            )

            response.raise_for_status()

            content = response.content

            if not content.startswith(b"%PDF-"):
                raise ValueError(
                    "Downloaded content is not a valid PDF."
                )

            filename.write_bytes(content)

            print(
                f"Downloaded successfully: "
                f"{len(content) / 1024:.2f} KB"
            )

            return True

        except Exception as error:

            print(f"Attempt {attempt + 1} failed: {error}")

            if attempt < 2:
                time.sleep(2)

    return False


def main():

    PAPERS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    successful = 0

    for paper in PAPERS:

        if download_paper(paper):
            successful += 1

    print("\nDownload summary:")
    print(f"Successful: {successful}/{len(PAPERS)}")

    if successful != len(PAPERS):
        raise SystemExit(
            "Some papers could not be downloaded."
        )

    print("All three paper PDFs are downloaded!")


if __name__ == "__main__":
    main()