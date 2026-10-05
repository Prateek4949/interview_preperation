from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

questions = [
    "How do you handle class imbalance?",
    "How to handle an imbalanced dataset."
]

embeddings = model.encode(
    questions,
    normalize_embeddings=True
)

similarity = float(
    np.dot(
        embeddings[0],
        embeddings[1]
    )
)

print("Similarity:", round(similarity, 3))