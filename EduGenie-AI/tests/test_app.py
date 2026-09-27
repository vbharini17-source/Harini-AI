from fastapi.testclient import TestClient

import asyncio
from types import SimpleNamespace

import main
import gemini_client
from gemini_client import GeminiRequestError, _generate_content, _to_request_error
from schemas import LearningPathResponse, LearningStep, QuizQuestion, QuizResponse

client = TestClient(main.app)


def test_health_reports_unconfigured_key(monkeypatch):
    monkeypatch.setattr(main.settings, "gemini_api_key", "")
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["gemini_configured"] is False


def test_home_page_loads():
    response = client.get("/")

    assert response.status_code == 200
    assert "EduGenie" in response.text


def test_empty_question_is_rejected():
    response = client.post("/qa", json={"question": "  "})

    assert response.status_code == 422


def test_learning_level_is_validated():
    response = client.post(
        "/learn/recommendations",
        json={"topic": "Algebra", "level": "expert"},
    )

    assert response.status_code == 422


def test_qa_route_returns_generated_answer(monkeypatch):
    async def fake_answer(question: str) -> str:
        return f"Answer: {question}"

    monkeypatch.setattr(main, "answer_question", fake_answer)
    response = client.post("/qa", json={"question": "What is a cell?"})

    assert response.status_code == 200
    assert response.json() == {"result": "Answer: What is a cell?"}


def test_gemini_failure_returns_actionable_json(monkeypatch):
    async def fail_answer(question: str) -> str:
        raise GeminiRequestError("Gemini rejected the request. Check the API key.")

    monkeypatch.setattr(main, "answer_question", fail_answer)
    response = client.post("/qa", json={"question": "Explain gravity"})

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Gemini rejected the request. Check the API key."
    }


def test_gemini_overload_returns_friendly_retry_message():
    error = _to_request_error(
        type("ProviderError", (Exception,), {"code": 503})()
    )

    assert error.status_code == 503
    assert str(error) == "Gemini is temporarily busy. Please try again in a minute."


def test_gemini_503_uses_configured_fallback(monkeypatch):
    monkeypatch.setattr(
        gemini_client.settings,
        "gemini_fallback_model",
        "gemini-flash-lite-latest",
    )
    requested_models = []

    def generate_content(**kwargs):
        requested_models.append(kwargs["model"])
        if len(requested_models) == 1:
            raise type("ProviderError", (Exception,), {"code": 503})()
        return "fallback response"

    async def run_in_thread(function, **kwargs):
        return function(**kwargs)

    monkeypatch.setattr(gemini_client.asyncio, "to_thread", run_in_thread)
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=generate_content)
    )
    result = asyncio.run(
        _generate_content(
            client,
            model="gemini-3.8-flash",
            contents="test",
            config=None,
        )
    )

    assert result == "fallback response"
    assert requested_models == [
        "gemini-3.8-flash",
        "gemini-flash-lite-latest",
    ]


def test_unexpected_failure_returns_json(monkeypatch):
    async def fail_answer(question: str) -> str:
        raise RuntimeError("unexpected failure")

    monkeypatch.setattr(main, "answer_question", fail_answer)
    response = TestClient(main.app, raise_server_exceptions=False).post(
        "/qa", json={"question": "Explain gravity"}
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "The server could not complete the request. Check server logs."
    }


def test_quiz_question_requires_answer_to_match_option():
    try:
        QuizQuestion(
            question="Pick one",
            options=["A", "B", "C", "D"],
            correct_answer="E",
            explanation="Not an option",
        )
    except ValueError:
        return
    raise AssertionError("A non-option answer should be rejected")


def test_quiz_response_accepts_valid_question():
    response = QuizResponse(
        questions=[
            QuizQuestion(
                question="Pick one",
                options=["A", "B", "C", "D"],
                correct_answer="A",
                explanation="A is correct.",
            )
        ]
    )

    assert response.questions[0].correct_answer == "A"


def test_learning_path_response_shape():
    response = LearningPathResponse(
        topic="Fractions",
        level="beginner",
        steps=[
            LearningStep(
                stage=f"Stage {number}",
                topics=["Basics"],
                estimated_time="1 hour",
                resources=["Textbook"],
            )
            for number in range(1, 4)
        ],
        study_tips=["Practice", "Review", "Take breaks"],
    )

    assert len(response.steps) == 3