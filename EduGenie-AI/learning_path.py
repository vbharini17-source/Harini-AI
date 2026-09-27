from pydantic import BaseModel, Field

from gemini_client import generate_structured
from schemas import LearningPathResponse, LearningStep


class GeneratedLearningPath(BaseModel):
    steps: list[LearningStep] = Field(min_length=3, max_length=8)
    study_tips: list[str] = Field(min_length=3, max_length=8)


async def get_learning_recommendations(
    topic: str, level: str
) -> LearningPathResponse:
    prompt = f"""Create a practical learning path for the topic and level below.
Progress from foundational concepts to advanced concepts. Give each stage a
name, topics, estimated time, and useful resources. Do not invent specific URLs.

TOPIC: {topic}
LEVEL: {level}"""
    result = await generate_structured(
        prompt,
        GeneratedLearningPath,
        system_instruction="You are an educational curriculum assistant.",
        temperature=0.35,
        max_output_tokens=2200,
    )
    return LearningPathResponse(
        topic=topic,
        level=level,
        steps=result.steps,
        study_tips=result.study_tips,
    )