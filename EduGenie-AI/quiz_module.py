from pydantic import BaseModel, Field

from gemini_client import generate_structured
from schemas import QuizQuestion, QuizResponse


class GeneratedQuiz(BaseModel):
    questions: list[QuizQuestion] = Field(min_length=3, max_length=3)


async def generate_quiz(passage: str) -> QuizResponse:
    prompt = f"""Create exactly three multiple-choice questions from this passage.
Each question must have exactly four options, one correct answer matching an
option, and an explanation. Base every question only on the supplied passage.

PASSAGE:
{passage}"""
    quiz = await generate_structured(
        prompt,
        GeneratedQuiz,
        system_instruction="You generate accurate educational quizzes.",
        temperature=0.25,
    )
    return QuizResponse(questions=quiz.questions)