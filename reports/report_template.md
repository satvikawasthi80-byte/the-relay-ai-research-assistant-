# The Relay — Final Report

## 1. What I built and why
I built The Relay, a research assistant that retrieves relevant passages from exactly three specified arXiv papers and uses an AI model to generate cited answers. The pipeline includes question validation, retrieval, context preparation, generation and citation validation.

## 2. Real service and stand-in
The real model service is Groq using `openai/gpt-oss-20b`. A local FastAPI stand-in provides configurable delay, failures, rate limits and overload slowdown. I tested the Groq connection separately. The load-test runs described below used the stand-in.

## 3. Results
I attempted 55 stand-in requests across steady, burst and sustained-overload scenarios.

- Steady: [FILL from CSV]
- Burst: 15 requests; 0 successful answers.
- Sustained overload: 30 requests; 0 successful answers.
- Overall successful answers: 0 in the displayed load-test run.

The requests were refused by citation validation because the stand-in response did not provide valid paper citations. These results do not demonstrate a real provider rate limit.

## 4. Where time goes
Retrieval search timings were approximately 0.64–0.73 ms in the recorded experiments. Model and end-to-end timings must be interpreted separately using `results.csv`.

## 5. When limit hit
I did not establish a real Groq rate limit from these tests. I would need controlled requests and provider responses indicating rate limiting to make that claim.

## 6. Retrieval: quality vs cost
I compared three configurations:
- Small: chunk 300, top-k 3.
- Medium: chunk 500, top-k 5.
- Large: chunk 800, top-k 8.

Search timings were similar in this run. Retrieval relevance still needs manual grading.

## 7. How library misleads a naive retriever
Keyword similarity can retrieve passages that mention related terms without answering the question. Chunk boundaries can also separate relevant context. Retrieved passages need relevance checks, not just similarity scores.

## 8. Your feedback on Vaani
[FILL with your own feedback from using the system.]

## 9. Retries
The pipeline includes retry handling for selected temporary errors. The recorded load-test retry counts should be checked before drawing conclusions about retry effectiveness.

## 10. What person sees
The user receives an answer with paper and page citations when the system accepts the evidence. If citation validation fails, the system returns an error or refusal instead of presenting an unsupported answer.

## 11. What unsure / left out / learned
- Unsure: Actual real-service rate limits and answer quality under load.
- Left out: Complete manual relevance grading and a successful stand-in citation test.
- Learned: Retrieval, model availability and citation validation must be tested separately.

## 12. How I worked with assistant
I used an AI assistant for implementation guidance and debugging. I ran the code and experiments locally. Measurements and conclusions are based on the recorded outputs, with limitations stated explicitly.