import json

from .jd_matcher import load_jd
from .llm_call import call_llm


SYSTEM_PROMPT = """
You are an interview planning engine.

Your task is to analyze a candidate's JD and resume and recommend
the most relevant interview areas.

Rules:

1. Only recommend areas that exist in the supplied JD.
2. Consider both:
   - JD priorities
   - Skills, projects and experience explicitly present in the resume
3. Do not invent resume experience.
4. Recommend 3 to 6 relevant areas.
5. Prefer high-priority JD areas.
6. Give additional priority to JD areas supported by the resume.
7. Return ONLY valid JSON.
8. Do not create new area names.

Return exactly:

{
  "recommended_areas": [
    {
      "name": "SQL",
      "priority": "high",
      "reason": "High-priority JD area and relevant resume experience."
    }
  ]
}
"""


def _parse_json(result):
    result = result.strip()

    if result.startswith("```"):
        result = result.replace("```json", "", 1)
        result = result.replace("```", "")
        result = result.strip()

    return json.loads(result)


def recommend_interview_areas(
    company,
    experience_range,
    resume_text,
):
    jd = load_jd(experience_range)

    prompt = f"""
Company:
{company}

Experience range:
{experience_range}

JD:
{json.dumps(jd, indent=2)}

Candidate resume:
{resume_text or "No resume provided."}

Recommend the most relevant interview areas for this candidate.
"""

    result = call_llm(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
    )

    recommendations = _parse_json(result)

    valid_area_names = {
        area["name"]
        for area in jd["areas"]
    }

    recommended_areas = recommendations.get(
        "recommended_areas",
        []
    )

    filtered_areas = []

    for item in recommended_areas:

        if item.get("name") not in valid_area_names:
            continue

        filtered_areas.append({
            "name": item["name"],
            "priority": item.get("priority", "medium"),
            "reason": item.get(
                "reason",
                "Relevant to the selected JD."
            )
        })

    if not filtered_areas:
        raise ValueError(
            "LLM did not return any valid interview areas."
        )

    return {
        "company": company,
        "experience_range": experience_range,
        "recommended_areas": filtered_areas
    }


if __name__ == "__main__":

    resume = """
    Data Scientist with 4 years of experience.

    Worked on SQL analytics, machine learning,
    XGBoost churn prediction, A/B testing and
    recommendation systems.
    """

    result = recommend_interview_areas(
        company="Zomato",
        experience_range="3-5",
        resume_text=resume,
    )

    print("\nRECOMMENDED INTERVIEW AREAS")
    print("===========================")
    print(json.dumps(result, indent=2))