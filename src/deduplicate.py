from sentence_transformers import SentenceTransformer
import numpy as np

from .db import connect


MODEL_NAME = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.88


def cosine_similarity(a, b):
    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )


def deduplicate():
    model = SentenceTransformer(MODEL_NAME)

    with connect() as conn:
        rows = conn.execute("""
            SELECT
                id,
                company,
                role,
                question,
                normalized_question,
                report_count,
                duplicate_of
            FROM questions
            WHERE duplicate_of IS NULL
            ORDER BY id
        """).fetchall()

        if len(rows) < 2:
            print("Not enough questions to deduplicate.")
            return

        questions = [
            row["normalized_question"]
            for row in rows
        ]

        print(f"Embedding {len(questions)} questions...")

        embeddings = model.encode(
            questions,
            normalize_embeddings=True
        )

        duplicate_count = 0

        for i in range(len(rows)):
            current = rows[i]

            for j in range(i + 1, len(rows)):
                candidate = rows[j]

                # Only compare same company and role
                if (
                    current["company"] != candidate["company"]
                    or current["role"] != candidate["role"]
                ):
                    continue

                similarity = cosine_similarity(
                    embeddings[i],
                    embeddings[j]
                )

                if similarity >= SIMILARITY_THRESHOLD:

                    print("\nPossible duplicate:")
                    print(f"  [{current['id']}] {current['question']}")
                    print(f"  [{candidate['id']}] {candidate['question']}")
                    print(f"  Similarity: {similarity:.3f}")

                    # Keep the older question as canonical
                    canonical = current
                    duplicate = candidate

                    conn.execute("""
                        UPDATE questions
                        SET
                            duplicate_of = ?,
                            report_count = 0
                        WHERE id = ?
                    """, (
                        canonical["id"],
                        duplicate["id"]
                    ))

                    conn.execute("""
                        UPDATE questions
                        SET report_count = report_count + 1
                        WHERE id = ?
                    """, (
                        canonical["id"],
                    ))

                    duplicate_count += 1

        conn.commit()

    print(f"\nDuplicates found: {duplicate_count}")


if __name__ == "__main__":
    deduplicate()