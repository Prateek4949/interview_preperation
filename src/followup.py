import json

from .llm_call import call_llm


SYSTEM_PROMPT = """
You are an AI technical interviewer.

Generate ONE follow-up interview question based on:

1. The original interview question
2. The candidate's answer
3. The evaluation of that answer

The follow-up should probe ONE important gap or test ONE deeper aspect of understanding.

Rules:

- Do not repeat the original question.
- Ask exactly ONE focused question.
- Do not combine multiple concepts or requirements into one question.
- If there are multiple gaps, choose the single most important gap to probe first.
- Keep it natural and conversational.
- Stay within the topic of the original question.
- Do not introduce an unrelated topic.
- Do not assume the candidate said something they did not say.
- If the candidate has a strong answer, ask a deeper question.
- If there is an important gap, target that gap.

Return ONLY valid JSON:

{
  "follow_up_question": "..."
}
"""


def generate_follow_up(
    original_question,
    candidate_answer,
    evaluation
):

    prompt = f"""
Original interview question:

{original_question}

Candidate answer:

{candidate_answer}

Evaluation:

{json.dumps(evaluation, indent=2)}

Generate the next follow-up question.
"""

    result = call_llm(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT
    )

    result = result.strip()

    print("\nRAW LLM RESPONSE:")
    print(result)

    if not result:
        raise ValueError("LLM returned an empty response.")

    if result.startswith("```"):
        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

    try:
        parsed = json.loads(result)

        if isinstance(parsed, str):
            return {
                "follow_up_question": parsed
            }

        return parsed

    except json.JSONDecodeError:
        # LLM returned a plain-text question
        return {
            "follow_up_question": result
        }

    if result.startswith("```"):
        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

    return json.loads(result)


if __name__ == "__main__":

    question = "Explain bagging and boosting."

    answer = """
    Bagging trains multiple models independently on different samples
    of the data. Random Forest is an example. Boosting trains models
    sequentially and focuses on previous errors.
    """

    evaluation = {
        "overall_score": 4,
        "correctness": 5,
        "completeness": 3,
        "depth": 2,
        "strengths": [
            "Correctly identifies bagging as independent training.",
            "Correctly identifies boosting as sequential."
        ],
        "gaps": [
            "No explanation of how predictions are combined.",
            "No discussion of bias-variance tradeoff.",
            "No specific boosting algorithms."
        ],
        "follow_up_needed": True
    }

    result = generate_follow_up(
        question,
        answer,
        evaluation
    )

    print(json.dumps(result, indent=2))