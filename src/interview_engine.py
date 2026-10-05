from .jd_matcher import load_jd, match_questions
from .evaluator import evaluate_answer
from .followup import generate_follow_up
from .assessment import build_assessment


class InterviewEngine:

    def __init__(
        self,
        company,
        experience_range,
        selected_areas=None,
        total_main_questions=10,
    ):
        self.company = company
        self.experience_range = experience_range
        self.jd = load_jd(experience_range)

        self.selected_areas = selected_areas or [
            area["name"]
            for area in self.jd["areas"]
        ]

        self.total_main_questions = total_main_questions

        valid_areas = {
            area["name"]
            for area in self.jd["areas"]
        }

        invalid_areas = [
            area
            for area in self.selected_areas
            if area not in valid_areas
        ]

        if invalid_areas:
            raise ValueError(
                f"Invalid interview areas: {invalid_areas}"
            )

        # Get company-reported questions
        matched_results = match_questions(
            experience_range=experience_range,
            top_k=3
        )

        # Keep ONLY the areas selected by the candidate
        self.matched_results = [
            item
            for item in matched_results
            if item["area"] in self.selected_areas
        ]

        # Build the actual interview question queue
        self.question_queue = self._build_question_queue()

        self.current_question_index = 0
        self.current_question = None
        self.current_jd_area = None

        self.active_follow_up = None
        self.follow_up_count = 0
        self.max_follow_ups = 2

        self.history = []

    # ========================================================
    # Current Area
    # ========================================================

    def get_current_area(self):
        if not self.current_question:
            return None

        area_name = self._get_question_area(
            self.current_question
        )

        for area in self.jd["areas"]:
            if area["name"] == area_name:
                return area

        return None

    # ========================================================
    # Build Interview Question Queue
    # ========================================================

    def _build_question_queue(self):

        questions_by_area = {}

        for item in self.matched_results:

            area = item["area"]

            questions_by_area[area] = [
                match
                for match in item["matches"]
            ]

        queue = []

        areas_with_questions = [
            area
            for area in self.selected_areas
            if questions_by_area.get(area)
        ]

        area_index = 0

        while (
            len(queue) < self.total_main_questions
            and areas_with_questions
        ):

            area = areas_with_questions[
                area_index % len(areas_with_questions)
            ]

            area_questions = questions_by_area[area]

            if area_questions:
                queue.append(
                    area_questions.pop(0)
                )

            if not area_questions:

                areas_with_questions.remove(area)

                if areas_with_questions:
                    area_index %= len(
                        areas_with_questions
                    )

                continue

            area_index += 1

        return queue

    # ========================================================
    # Assessment
    # ========================================================

    def get_assessment(self):
        return build_assessment(self.history)

    # ========================================================
    # Current Question
    # ========================================================

    def get_next_question(self):

        if self.current_question_index >= len(
            self.question_queue
        ):
            return None

        question = self.question_queue[
            self.current_question_index
        ]

        self.current_question = question

        self.current_jd_area = self._get_question_area(
            question
        )

        self.active_follow_up = None
        self.follow_up_count = 0

        return question

    def _get_question_area(self, question):

        question_id = question.get("question_id")

        for item in self.matched_results:

            for match in item["matches"]:

                if match["question_id"] == question_id:
                    return item["area"]

        return "Unknown"

    # ========================================================
    # Follow-up
    # ========================================================

    def generate_follow_up_if_needed(
        self,
        original_question,
        candidate_answer,
        evaluation,
    ):

        if not evaluation.get(
            "follow_up_needed",
            False
        ):
            return None

        if self.follow_up_count >= self.max_follow_ups:
            return None

        follow_up = generate_follow_up(
            original_question=original_question,
            candidate_answer=candidate_answer,
            evaluation=evaluation
        )

        self.follow_up_count += 1

        self.active_follow_up = (
            follow_up["follow_up_question"]
        )

        return self.active_follow_up

    # ========================================================
    # Submit Answer
    # ========================================================

    def submit_answer(self, answer):

        if not self.current_question:
            raise ValueError(
                "No active interview question."
            )

        # ----------------------------------------------------
        # Follow-up answer
        # ----------------------------------------------------

        if self.active_follow_up:

            follow_up_question = self.active_follow_up

            evaluation = evaluate_answer(
                question=follow_up_question,
                answer=answer
            )

            self.history.append({
                "type": "follow_up",
                "jd_area": self.current_jd_area,
                "question": follow_up_question,
                "topic": self.current_question.get(
                    "topic",
                    "Unknown"
                ),
                "question_type": self.current_question.get(
                    "question_type",
                    "Unknown"
                ),
                "answer": answer,
                "evaluation": evaluation
            })

            next_follow_up = (
                self.generate_follow_up_if_needed(
                    original_question=follow_up_question,
                    candidate_answer=answer,
                    evaluation=evaluation
                )
            )

            if next_follow_up:

                return {
                    "type": "follow_up",
                    "question": next_follow_up,
                    "evaluation": evaluation
                }

            # Follow-up limit reached
            self.active_follow_up = None

            self.current_question_index += 1

            next_question = self.get_next_question()

            if next_question is None:

                return {
                    "type": "finished",
                    "evaluation": evaluation
                }

            return {
                "type": "next_question",
                "question": next_question["question"],
                "evaluation": evaluation
            }

        # ----------------------------------------------------
        # Main question answer
        # ----------------------------------------------------

        question = self.current_question

        evaluation = evaluate_answer(
            question=question["question"],
            answer=answer
        )

        self.history.append({
            "type": "main_question",
            "jd_area": self.current_jd_area,
            "question": question["question"],
            "topic": question.get(
                "topic",
                "Unknown"
            ),
            "question_type": question.get(
                "question_type",
                "Unknown"
            ),
            "answer": answer,
            "evaluation": evaluation
        })

        follow_up = (
            self.generate_follow_up_if_needed(
                original_question=question["question"],
                candidate_answer=answer,
                evaluation=evaluation
            )
        )

        if follow_up:

            return {
                "type": "follow_up",
                "question": follow_up,
                "evaluation": evaluation
            }

        # Move to next MAIN question
        self.current_question_index += 1

        next_question = self.get_next_question()

        if next_question is None:

            return {
                "type": "finished",
                "evaluation": evaluation
            }

        return {
            "type": "next_question",
            "question": next_question["question"],
            "evaluation": evaluation
        }

    # ========================================================
    # Utility
    # ========================================================

    def is_finished(self):

        return (
            self.current_question_index
            >= len(self.question_queue)
        )

    def get_history(self):
        return self.history


# ============================================================
# Test
# ============================================================

if __name__ == "__main__":

    engine = InterviewEngine(
        company="Zomato",
        experience_range="3-5",
        selected_areas=[
            "SQL",
            "Machine Learning"
        ],
        total_main_questions=4
    )

    print("\nINTERVIEW PLAN")
    print("================")

    print(
        "Selected areas:",
        engine.selected_areas
    )

    print(
        "Requested main questions:",
        engine.total_main_questions
    )

    print(
        "Actual questions available:",
        len(engine.question_queue)
    )

    print("\nQUESTIONS")
    print("================")

    for index, question in enumerate(
        engine.question_queue,
        start=1
    ):

        print(
            f"{index}. "
            f"[{engine._get_question_area(question)}] "
            f"{question['question']}"
        )