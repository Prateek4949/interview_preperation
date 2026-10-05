from collections import defaultdict


def build_assessment(history):

    if not history:
        return {
            "overall_score": 0,
            "questions_attempted": 0,
            "main_questions": 0,
            "follow_ups": 0,
            "strong_areas": [],
            "weak_areas": [],
            "area_scores": {},
            "question_reviews": []
        }

    all_scores = []
    area_data = defaultdict(list)

    main_questions = 0
    follow_ups = 0

    question_reviews = []

    for index, item in enumerate(history, start=1):

        evaluation = item.get(
            "evaluation",
            {}
        )

        score = evaluation.get(
            "overall_score"
        )

        if score is None:
            continue

        all_scores.append(score)

        if item["type"] == "main_question":
            main_questions += 1
        elif item["type"] == "follow_up":
            follow_ups += 1

        jd_area = item.get(
            "jd_area",
            "Unknown"
        )

        area_data[jd_area].append(score)

        # --------------------------------------------
        # Detailed question review
        # --------------------------------------------

        question_reviews.append({
            "number": index,
            "type": item.get(
                "type",
                "main_question"
            ),
            "jd_area": jd_area,
            "question": item.get(
                "question",
                ""
            ),
            "answer": item.get(
                "answer",
                ""
            ),
            "score": score,
            "correctness": evaluation.get(
                "correctness",
                0
            ),
            "completeness": evaluation.get(
                "completeness",
                0
            ),
            "depth": evaluation.get(
                "depth",
                0
            ),
            "strengths": evaluation.get(
                "strengths",
                []
            ),
            "gaps": evaluation.get(
                "gaps",
                []
            ),
            "follow_up_needed": evaluation.get(
                "follow_up_needed",
                False
            ),
            "follow_up_reason": evaluation.get(
                "follow_up_reason",
                ""
            )
        })

    overall_score = (
        round(
            sum(all_scores) / len(all_scores),
            1
        )
        if all_scores
        else 0
    )

    area_scores = {}

    for area, scores in area_data.items():

        area_scores[area] = round(
            sum(scores) / len(scores),
            1
        )

    strong_areas = [
        area
        for area, score in area_scores.items()
        if score >= 7
    ]

    weak_areas = [
        area
        for area, score in area_scores.items()
        if score < 5
    ]

    return {
        "overall_score": overall_score,
        "questions_attempted": len(all_scores),
        "main_questions": main_questions,
        "follow_ups": follow_ups,
        "strong_areas": strong_areas,
        "weak_areas": weak_areas,
        "area_scores": area_scores,
        "question_reviews": question_reviews
    }