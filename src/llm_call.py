import os

import dotenv
from openai import OpenAI

dotenv.load_dotenv()


# ============================================================
# Gemini
# ============================================================

gemini_client = None

if os.getenv("GEMINI_API_KEY"):
    gemini_client = OpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        max_retries=0
    )

GEMINI_MODEL = "gemini-3.5-flash-lite"


# ============================================================
# LLM Call
# ============================================================

def call_llm(prompt, system_prompt=None):

    if not gemini_client:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    messages = []

    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    messages.append({
        "role": "user",
        "content": prompt
    })

    response = gemini_client.chat.completions.create(
        model=GEMINI_MODEL,
        messages=messages
    )

    return response.choices[0].message.content


# ============================================================
# Direct test
# ============================================================

if __name__ == "__main__":

    result = call_llm(
        "Give me one Python interview question."
    )

    print("\nRESULT:")
    print(result)