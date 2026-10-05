import json

from .llm_call import call_llm


SYSTEM_PROMPT = """
You are an AI technical interviewer evaluating a candidate's answer.

Evaluate the candidate based on:

1. Correctness
2. Completeness
3. Depth of understanding

Be fair to partially correct answers.

Important:
- Do not penalize an answer simply because it does not contain every possible detail.
- Distinguish between a fundamentally incorrect answer and an incomplete answer.
- Give credit for technically correct concepts even when the explanation is brief.
- Identify what the candidate did correctly.
- Identify meaningful gaps in the answer.
- Do not invent statements that the candidate did not make.

Scoring:

overall_score:
- 0 = Completely incorrect or irrelevant
- 1-2 = Mostly incorrect
- 3-4 = Partially correct but significant gaps
- 5-6 = Generally correct with some important gaps
- 7-8 = Strong answer with minor gaps
- 9 = Very strong answer
- 10 = Excellent, complete, and deep answer

correctness:
How technically correct is the answer?

completeness:
How much of the expected answer did the candidate cover?

depth:
How deeply does the candidate demonstrate understanding?

Follow-up rules:

- Set follow_up_needed to true when an important gap, ambiguity, or lack of depth should be probed further.
- Set follow_up_needed to false when the answer is sufficiently strong or no meaningful follow-up is needed.
- If follow_up_needed is true, identify only ONE most important gap for the next question.
- follow_up_reason must explain only that ONE gap.
- Do not list multiple gaps or multiple possible follow-up topics in follow_up_reason.
- The follow_up_reason should justify the immediate next follow-up question, not summarize all weaknesses.
- The follow-up should help determine whether the candidate truly understands the topic.
- Do not require implementation details unless implementation is relevant to the question.
- When choosing the next follow-up, select exactly ONE item from the gaps list.
- Do not combine two or more gaps in follow_up_reason.

Return ONLY valid JSON.

Use exactly this structure:

{
  "overall_score": 0,
  "correctness": 0,
  "completeness": 0,
  "depth": 0,
  "strengths": [],
  "gaps": [],
  "follow_up_needed": false,
  "follow_up_reason": ""
}
"""


def evaluate_answer(question, answer):

    prompt = f"""
Interview question:

{question}

Candidate answer:

{answer}

Evaluate the candidate's answer.
"""

    result = call_llm(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT
    )

    result = result.strip()

    if result.startswith("```"):
        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

    return json.loads(result)


if __name__ == "__main__":

    question = "Explain bagging and boosting."

    answer = """
    Bagging trains multiple models independently on different samples
    of the data and combines their predictions. Random Forest is an
    example. Boosting trains models sequentially where each new model
    focuses more on previous errors.
    """

    result = evaluate_answer(
        question,
        answer
    )

    print(json.dumps(result, indent=2))