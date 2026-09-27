from gemini_client import generate_text


async def summarize_text(text: str) -> str:
    prompt = f"""Summarize this educational text. Preserve important facts, remove
repetition, give a short overview and 4-8 key points when useful, and do not add
unsupported information.

TEXT:
{text}"""
    return await generate_text(
        prompt,
        system_instruction="You are EduGenie's academic summarization module.",
        max_output_tokens=1200,
    )