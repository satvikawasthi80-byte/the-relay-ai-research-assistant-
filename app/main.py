from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .pipeline import answer_question


app = FastAPI(
    title="The Relay",
    description="AI Research Assistant for three arXiv papers",
    version="1.0.0"
)


class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=4000,
        description="Ask a question about the supplied research papers"
    )


@app.get("/")
async def home():
    return {
        "project": "The Relay",
        "message": "AI Research Assistant is running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "The Relay API"
    }


@app.post("/ask")
async def ask(req: AskRequest):

    try:
        result = await answer_question(req.question)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )