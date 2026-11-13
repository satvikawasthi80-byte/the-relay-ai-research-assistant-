# The Relay — research-paper assistant

A reproducible Python starter implementation for the assignment. It includes:
- a FastAPI assistant pipeline (question routing → retrieval → answer → citation check → optional retry/refusal)
- exact-version arXiv PDF downloader
- local TF-IDF retrieval with three configurable retrieval settings
- Groq chat-completions integration (streaming and non-streaming)
- controllable stand-in model server (delay, failure, 429, load-dependent latency, streaming)
- asynchronous load runner that writes `results.csv`
- 15 evaluation questions and report templates

## 1. Setup (Python 3.10+)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env       # Windows PowerShell: Copy-Item .env.example .env
```

Add your own `GROQ_API_KEY` to `.env`. Never commit or submit `.env`.

## 2. Download the required exact paper versions

```bash
python download_papers.py
```

The downloader requests:
- `1706.03762v7`
- `2410.00037v1`
- `2507.07955v2`

Check the PDF headers/title pages after download. Do not silently substitute a later version.

## 3. Run the assistant

Index papers:
```bash
python -m app.indexer
```

Start API:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Ask:
```bash
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d "{\"question\":\"What is multi-head attention?\"}"
```

For real Groq calls, set `MODEL_SOURCE=real` in `.env`. For stand-in calls, set `MODEL_SOURCE=standin` and `STANDIN_URL=http://127.0.0.1:8001/v1/chat/completions`.

## 4. Run the stand-in

In a second terminal:
```bash
uvicorn standin.server:app --host 127.0.0.1 --port 8001
```

Tune behaviour using environment variables:
- `STANDIN_BASE_DELAY_MS` (default 350)
- `STANDIN_JITTER_MS` (default 250)
- `STANDIN_FAIL_RATE` (default 0.03)
- `STANDIN_429_RATE` (default 0.03)
- `STANDIN_CAPACITY` (default 4; concurrency above this adds delay)
- `STANDIN_CHUNK_DELAY_MS` (default 25)

This is a deliberately simplified model of provider behaviour, not an exact Groq emulator.

## 5. Load testing

With the assistant and stand-in running:
```bash
python load_test.py --url http://127.0.0.1:8000/ask --scenario steady --requests 20 --rate 4
python load_test.py --url http://127.0.0.1:8000/ask --scenario burst --requests 30 --rate 30
python load_test.py --url http://127.0.0.1:8000/ask --scenario overload --requests 60 --rate 20
```
The runner appends one row per request to `results.csv`. `source` is inferred from `MODEL_SOURCE`.
Only label a run `real` if it actually called Groq. Keep raw CSV unchanged.

## 6. Retrieval experiments

Run:
```bash
python retrieval_experiments.py
```
It compares at least three chunk-size/top-k/reranking settings using the evaluation set. The included lightweight reranker is lexical overlap; it is not a learned cross-encoder. Review grades and citations manually before reporting them.

## 7. Important measurement rules

- The app records TTFT and total latency at the request level.
- `start_time` is an ISO timestamp.
- If a request is cancelled before a first token, `first_token_ms` is blank.
- Never fabricate results. `not measured` belongs in the write-up where a metric was not collected.
- Groq limits vary by model and organization. Record your actual Console limits and response headers/errors. Do not copy generic limits as your own.
- The Groq free-tier limit table may not expose all values; write `not exposed` / `not measured` rather than guessing.

## 8. Submission

Submit:
1. source code (exclude `.env`, `.venv`, caches)
2. `results.csv`
3. two-page report based on `reports/report_template.md`
4. actual assistant conversation history / exported prompts

The report template is a starting point. Replace every placeholder with measured evidence and your own decisions.
