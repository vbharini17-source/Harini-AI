import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import settings
from explanation_module import explain_concept
from gemini_client import GeminiNotConfiguredError, GeminiRequestError
from learning_path import get_learning_recommendations
from qna import answer_question
from quiz_module import generate_quiz
from schemas import (
    ExplainRequest,
    LearningPathRequest,
    LearningPathResponse,
    QARequest,
    QuizRequest,
    QuizResponse,
    SummaryRequest,
    TextResponse,
)
from summary_module import summarize_text

logger = logging.getLogger(__name__)

app = FastAPI(
    title="EduGenie",
    description="A Gemini-powered learning assistant.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.exception_handler(GeminiNotConfiguredError)
async def gemini_not_configured_handler(
    request: Request, exc: GeminiNotConfiguredError
) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(GeminiRequestError)
async def gemini_request_error_handler(
    request: Request, exc: GeminiRequestError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.error(
        "Unhandled %s while processing %s %s",
        type(exc).__name__,
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "The server could not complete the request. Check server logs."},
    )


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.app_name},
    )


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "gemini_configured": bool(settings.gemini_api_key),
        "gemini_model": settings.gemini_model,
    }


@app.post("/qa", response_model=TextResponse)
async def qa(payload: QARequest) -> TextResponse:
    return TextResponse(result=await answer_question(payload.question))


@app.post("/explain", response_model=TextResponse)
async def explain(payload: ExplainRequest) -> TextResponse:
    return TextResponse(result=await explain_concept(payload.topic))


@app.post("/quiz", response_model=QuizResponse)
async def quiz(payload: QuizRequest) -> QuizResponse:
    return await generate_quiz(payload.text)


@app.post("/summarize", response_model=TextResponse)
async def summarize(payload: SummaryRequest) -> TextResponse:
    return TextResponse(result=await summarize_text(payload.text))


@app.post(
    "/learn/recommendations",
    response_model=LearningPathResponse,
)
async def learning_recommendations(
    payload: LearningPathRequest,
) -> LearningPathResponse:
    return await get_learning_recommendations(payload.topic, payload.level)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )