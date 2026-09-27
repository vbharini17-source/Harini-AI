from gemini_client import generate_text


async def answer_question(question: str) -> str:
    prompt = f"""Answer this question for a student in a clear, easy-to-scan way.

QUESTION:
{question}

Start with a concise direct answer. For questions that need explanation, use
short labeled sections such as "Why it works:", "Example:", and "Key takeaway:".
Use plain text, short paragraphs, and bullets only when listing several items.
For simple questions, answer briefly without forcing extra sections. Explain
unfamiliar terms and state uncertainty when appropriate. Do not invent citations."""
    return await generate_text(
        prompt,
        system_instruction="You are EduGenie, a patient educational assistant.",
        max_output_tokens=900,
    )