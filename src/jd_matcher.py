import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from .db import connect


ROOT = Path(__file__).resolve().parents[1]
JD_DIR = ROOT / "data" / "jds"

MODEL_NAME = "all-MiniLM-L6-v2"

# Only show matches above this semantic similarity.
SIMILARITY_THRESHOLD = 0.35


# JD area → acceptable question types/topics
AREA_RULES = {
    "Python": {
        "question_types": {"Coding"},
        "topics": {"Python", "Pandas", "NumPy"}
    },

    "SQL": {
        "question_types": {"SQL"},
        "topics": {"SQL"}
    },

    "Statistics": {
        "question_types": {"Statistics"},
        "topics": {
            "Statistics",
            "Probability",
            "Hypothesis Testing",
            "Statistical Significance",
            "P-value and Confidence Intervals"
        }
    },

    "Machine Learning": {
        "question_types": {"Technical", "Case Study"},
        "topics": {
            "Machine Learning",
            "Machine Learning Algorithms",
            "Class Imbalance",
            "Imbalanced dataset handling",
            "Bias and Variance"
        }
    },

    "Experimentation": {
        "question_types": {"Statistics", "Case Study"},
        "topics": {
            "A/B Testing",
            "Statistical Significance",
            "P-value and Confidence Intervals"
        }
    },

    "Data Analysis": {
        "question_types": {"Technical", "Case Study"},
        "topics": {
            "EDA",
            "Data Analysis",
            "Exploratory Data Analysis"
        }
    },

    "Recommendation Systems": {
        "question_types": {"Technical", "Case Study", "System Design"},
        "topics": {
            "Recommendation Systems",
            "Recommender System Design",
            "Recommendation Evaluation Metrics",
            "Cold-Start Problem"
        }
    },

    "Forecasting": {
        "question_types": {"Technical", "Case Study"},
        "topics": {
            "Forecasting",
            "Demand Forecasting",
            "Time Series"
        }
    },

    "Case Studies": {
        "question_types": {"Case Study", "System Design"},
        "topics": set()
    },

    "Machine Learning System Design": {
        "question_types": {"System Design"},
        "topics": {
            "ML Framework Design",
            "Machine Learning System Design"
        }
    }
}


def load_jd(experience_range):

    if experience_range == "3-5":
        file_path = JD_DIR / "zomato_ds_3_5.json"

    elif experience_range == "5-7":
        file_path = JD_DIR / "zomato_ds_5_7.json"

    else:
        raise ValueError(
            "Experience range must be '3-5' or '5-7'"
        )

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_questions(company="Zomato"):

    with connect() as conn:

        rows = conn.execute(
            """
            SELECT
                id,
                question,
                topic,
                question_type
            FROM questions
            WHERE company = ?
            AND duplicate_of IS NULL
            """,
            (company,)
        ).fetchall()

    return [dict(row) for row in rows]


def match_questions(experience_range, top_k=3):

    jd = load_jd(experience_range)
    questions = get_questions(jd["company"])

    model = SentenceTransformer(MODEL_NAME)

    question_texts = [
        q["question"]
        for q in questions
    ]

    question_embeddings = model.encode(
        question_texts,
        normalize_embeddings=True
    )

    results = []

    for area in jd["areas"]:

        area_name = area["name"]

        rules = AREA_RULES.get(
            area_name,
            {
                "question_types": set(),
                "topics": set()
            }
        )

        candidates = []

        for index, question in enumerate(questions):

            topic_match = (
                question["topic"] in rules["topics"]
            )

            type_match = (
                question["question_type"]
                in rules["question_types"]
            )

            # Metadata filter
            if not topic_match and not type_match:
                continue

            candidates.append({
                "index": index,
                "question": question,
                "topic_match": topic_match,
                "type_match": type_match
            })

        matched = []

        if candidates:

            area_text = (
                area["name"]
                + " "
                + " ".join(area["skills"])
            )

            area_embedding = model.encode(
                area_text,
                normalize_embeddings=True
            )

            for candidate in candidates:

                index = candidate["index"]

                similarity = float(
                    np.dot(
                        question_embeddings[index],
                        area_embedding
                    )
                )

                if not candidate["topic_match"] and not candidate["type_match"]:
                    if similarity < SIMILARITY_THRESHOLD:
                        continue

                score = similarity

                # Small boost for exact metadata matches
                if candidate["topic_match"]:
                    score += 0.10

                elif candidate["type_match"]:
                    score += 0.05

                matched.append({
                    "question_id": candidate["question"]["id"],
                    "question": candidate["question"]["question"],
                    "topic": candidate["question"]["topic"],
                    "question_type": candidate["question"]["question_type"],
                    "similarity": round(similarity, 3),
                    "score": round(score, 3)
                })

        matched.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        results.append({
            "area": area_name,
            "priority": area["priority"],
            "matches": matched[:top_k]
        })

    return results


if __name__ == "__main__":

    results = match_questions(
        experience_range="3-5",
        top_k=3
    )

    for item in results:

        print("\n==============================")
        print(
            item["area"],
            "| Priority:",
            item["priority"]
        )
        print("==============================")

        if not item["matches"]:
            print("No strong company-reported questions found.")
            continue

        for match in item["matches"]:

            print(
                f"{match['score']} "
                f"(semantic: {match['similarity']}) - "
                f"{match['question']}"
            )