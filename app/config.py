import os
from dotenv import load_dotenv

load_dotenv()


# Model configuration
MODEL_SOURCE = os.getenv("MODEL_SOURCE", "standin").lower()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.1-8b-instant"
)


# Stand-in configuration
STANDIN_URL = os.getenv(
    "STANDIN_URL",
    "http://127.0.0.1:8001/v1/chat/completions"
)


# Request configuration
REQUEST_TIMEOUT_SECONDS = float(
    os.getenv("REQUEST_TIMEOUT_SECONDS", "35")
)

MAX_RETRIES = int(
    os.getenv("MAX_RETRIES", "1")
)


# Retrieval configuration
RETRIEVAL_CHUNK_SIZE = int(
    os.getenv("RETRIEVAL_CHUNK_SIZE", "500")
)

RETRIEVAL_TOP_K = int(
    os.getenv("RETRIEVAL_TOP_K", "5")
)

RETRIEVAL_RERANK = (
    os.getenv("RETRIEVAL_RERANK", "true").lower() == "true"
)