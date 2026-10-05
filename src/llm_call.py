import os

import dotenv
from openai import OpenAI, RateLimitError, APIError

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
# OpenRouter
# ============================================================

openrouter_client = None

if os.getenv("OPENROUTER_API_KEY"):
    openrouter_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        max_retries=0
    )

OPENROUTER_MODEL = "inclusionai/ling-3.0-flash-sante:free"


# ============================================================
# Provider state
# ============================================================

# If Gemini hits a daily/quota limit, don't keep retrying it
# for every subsequent request during this process.
gemini_disabled = False


# ============================================================
# Provider call
# ============================================================

def _call_provider(client, model, messages):
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )

    return response.choices[0].message.content


# ============================================================
# Main LLM function
# ============================================================

def call_llm(prompt, system_prompt=None):

    global gemini_disabled

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


    # --------------------------------------------------------
    # 1. Gemini
    # --------------------------------------------------------

    if gemini_client and not gemini_disabled:

        try:
            print("\nLLM Provider: Gemini")

            return _call_provider(
                gemini_client,
                GEMINI_MODEL,
                messages
            )

        except RateLimitError as e:

            print("\nGemini rate limit reached.")
            print("Switching to OpenRouter.")

            gemini_disabled = True

        except APIError as e:

            print("\nGemini API error:")
            print(e)
            print("Switching to OpenRouter.")


        except Exception as e:

            print("\nGemini failed:")
            print(e)
            print("Switching to OpenRouter.")


    # --------------------------------------------------------
    # 2. OpenRouter fallback
    # --------------------------------------------------------

    if openrouter_client:

        try:
            print("\nLLM Provider: OpenRouter")

            return _call_provider(
                openrouter_client,
                OPENROUTER_MODEL,
                messages
            )

        except Exception as e:

            print("\nOpenRouter failed:")
            print(e)


    # --------------------------------------------------------
    # Nothing worked
    # --------------------------------------------------------

    raise RuntimeError(
        "All configured LLM providers failed. "
        "Please check API keys, quotas, and provider status."
    )


# ============================================================
# Direct test
# ============================================================

if __name__ == "__main__":

    result = call_llm(
        "Give me one Python interview question."
    )

    print("\nRESULT:")
    print(result)