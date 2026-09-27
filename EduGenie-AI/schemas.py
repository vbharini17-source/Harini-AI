from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from config import settings


def clean_text(value: str, max_chars: int) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Input cannot be empty.")
    if len(value) > max_chars:
        raise ValueError(f"Input is too long. Maximum is {max_chars} characters.")
    return value


class QARequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        return clean_text(value, settings.max_input_chars)


class ExplainRequest(BaseModel):
    topic: str

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, value: str) -> str:
        return clean_text(value, settings.max_input_chars)


class QuizRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return clean_text(value, settings.max_quiz_chars)


class SummaryRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return clean_text(value, settings.max_input_chars)


class LearningPathRequest(BaseModel):
    topic: str
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, value: str) -> str:
        return clean_text(value, 500)

    @field_validator("level", mode="before")
    @classmethod
    def normalize_level(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class TextResponse(BaseModel):
    result: str


class QuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(min_length=4, max_length=4)
    correct_answer: str
    explanation: str

    @model_validator(mode="after")
    def correct_answer_is_an_option(self) -> "QuizQuestion":
        if self.correct_answer not in self.options:
            raise ValueError("correct_answer must match one of the options.")
        return self


class QuizResponse(BaseModel):
    questions: list[QuizQuestion] = Field(min_length=1, max_length=10)


class LearningStep(BaseModel):
    stage: str
    topics: list[str]
    estimated_time: str
    resources: list[str]


class LearningPathResponse(BaseModel):
    topic: str
    level: Literal["beginner", "intermediate", "advanced"]
    steps: list[LearningStep] = Field(min_length=3, max_length=8)
    study_tips: list[str] = Field(min_length=3, max_length=8)