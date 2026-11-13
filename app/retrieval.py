import re
from pathlib import Path

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from . import config


PAPERS_DIR = Path("data/papers")


def clean_text(text):
    """Remove unnecessary whitespace from extracted PDF text."""
    text = re.sub(r"\s+", " ", text or "")
    return text.strip()


def split_into_chunks(text, chunk_size=500):
    """Split text into chunks using word count."""
    words = text.split()
    chunks = []

    for start in range(0, len(words), chunk_size):
        chunk = " ".join(words[start:start + chunk_size])

        if chunk.strip():
            chunks.append(chunk)

    return chunks


class PaperRetriever:

    def __init__(self):
        self.passages = []
        self.vectorizer = None
        self.matrix = None

        self.load_papers()

    def load_papers(self):
        """Read all downloaded research paper PDFs."""

        if not PAPERS_DIR.exists():
            raise FileNotFoundError(
                f"Paper directory not found: {PAPERS_DIR}"
            )

        pdf_files = sorted(PAPERS_DIR.glob("*.pdf"))

        if not pdf_files:
            raise FileNotFoundError(
                "No PDF papers found. Run python download_papers.py first."
            )

        for pdf_path in pdf_files:

            reader = PdfReader(str(pdf_path))

            for page_number, page in enumerate(reader.pages, start=1):

                text = clean_text(page.extract_text())

                if not text:
                    continue

                chunks = split_into_chunks(
                    text,
                    config.RETRIEVAL_CHUNK_SIZE
                )

                for chunk in chunks:
                    self.passages.append({
                        "paper": pdf_path.name,
                        "page": page_number,
                        "text": chunk
                    })

        if not self.passages:
            raise ValueError("No searchable text found in the PDFs.")

        self.build_index()

    def build_index(self):
        """Convert passages into TF-IDF vectors."""

        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2)
        )

        texts = [p["text"] for p in self.passages]

        self.matrix = self.vectorizer.fit_transform(texts)

    def search(self, question):
        """Find the most relevant passages for a question."""

        if not question.strip():
            return []

        query_vector = self.vectorizer.transform([question])

        scores = cosine_similarity(
            query_vector,
            self.matrix
        ).flatten()

        ranked_indices = scores.argsort()[::-1]

        results = []

        for index in ranked_indices:

            score = float(scores[index])

            if score <= 0:
                continue

            passage = self.passages[index].copy()
            passage["score"] = score

            results.append(passage)

            if len(results) >= config.RETRIEVAL_TOP_K:
                break

        return results


_retriever = None


def get_retriever():
    """Return a shared retriever instance."""

    global _retriever

    if _retriever is None:
        _retriever = PaperRetriever()

    return _retriever