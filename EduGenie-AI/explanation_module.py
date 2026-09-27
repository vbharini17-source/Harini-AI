from gemini_client import generate_text


async def explain_concept(topic: str) -> str:
    prompt = f"""Explain this concept to a beginner.

TOPIC:
{topic}

Include a simple definition, how it works, an easy example, and three key points."""
    return await generate_text(
        prompt,
        system_instruction="You are EduGenie's concept explanation module.",
        max_output_tokens=1000,
    )