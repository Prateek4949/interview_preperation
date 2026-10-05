import sys
from pathlib import Path
import PyPDF2
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.interview_engine import InterviewEngine
from src.interview_planner import recommend_interview_areas


st.set_page_config(
    page_title="AI Interviewer",
    page_icon="🎯",
    layout="wide"
)


# ============================================================
# Session State
# ============================================================

defaults = {
    "stage": "setup",
    "engine": None,
    "current_question": None,
    "result": None,
    "resume_text": "",
    "recommended_areas": [],
    "selected_areas": [],
    "profile_analyzed": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# Header
# ============================================================

st.title("🎯 AI Interviewer")
st.caption(
    "Practice company-specific interviews using your JD, resume, "
    "and reported interview questions."
)


# ============================================================
# STAGE 1 — Setup
# ============================================================

if st.session_state.stage == "setup":

    st.header("Interview Setup")

    company = st.selectbox(
        "Company",
        ["Zomato"]
    )

    experience_range = st.selectbox(
        "Experience",
        ["3-5", "5-7"]
    )

    role = st.selectbox(
        "Role",
        ["Data Scientist", "Senior Data Scientist"]
    )

    st.subheader("Resume")

    uploaded_resume = st.file_uploader(
    "Upload your resume",
    type=["pdf", "txt"]
)

    if uploaded_resume:

        if uploaded_resume.name.lower().endswith(".pdf"):

            reader = PyPDF2.PdfReader(uploaded_resume)

            pages = []

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)

            st.session_state.resume_text = "\n".join(pages)

        else:

            st.session_state.resume_text = (
                uploaded_resume
                .read()
                .decode("utf-8")
            )

        if st.session_state.resume_text.strip():

            st.success(
                f"Resume uploaded: {uploaded_resume.name}"
            )

        else:

            st.error(
                "Could not extract text from this resume."
            )

    else:

        st.info(
            "Upload your resume as a PDF or TXT file."
        )

    st.divider()

    if st.button(
        "🔍 Analyze Profile",
        type="primary",
        disabled=not st.session_state.resume_text
    ):

        with st.spinner(
            "Analyzing your resume and JD..."
        ):

            try:

                result = recommend_interview_areas(
                    company=company,
                    experience_range=experience_range,
                    resume_text=st.session_state.resume_text,
                )

                st.session_state.recommended_areas = (
                    result["recommended_areas"]
                )

                st.session_state.company = company
                st.session_state.experience_range = (
                    experience_range
                )
                st.session_state.role = role
                st.session_state.profile_analyzed = True
                st.session_state.stage = "area_selection"

                st.rerun()

            except Exception as e:

                st.error(
                    f"Could not analyze the profile: {e}"
                )


# ============================================================
# STAGE 2 — Select Areas
# ============================================================

elif st.session_state.stage == "area_selection":

    st.header("Choose Your Interview Areas")

    st.write(
        "Based on your JD and resume, these areas are recommended. "
        "You can change the selection."
    )

    selected = []

    for area in st.session_state.recommended_areas:

        area_name = area["name"]
        priority = area["priority"]
        reason = area["reason"]

        checked = st.checkbox(
            f"{area_name} — {priority.capitalize()} priority",
            value=True,
            key=f"area_{area_name}"
        )

        st.caption(reason)

        if checked:
            selected.append(area_name)

    st.divider()

    if st.button(
        "Show Other JD Areas"
    ):

        st.session_state.show_other_areas = True

    if st.session_state.get(
        "show_other_areas",
        False
    ):

        from src.jd_matcher import load_jd

        jd = load_jd(
            st.session_state.experience_range
        )

        recommended_names = {
            area["name"]
            for area in st.session_state.recommended_areas
        }

        st.subheader("Other JD Areas")

        for area in jd["areas"]:

            if area["name"] in recommended_names:
                continue

            checked = st.checkbox(
                area["name"],
                value=False,
                key=f"other_area_{area['name']}"
            )

            if checked:
                selected.append(area["name"])

    st.session_state.selected_areas = selected

    st.divider()

    question_count = st.number_input(
        "Number of main questions",
        min_value=1,
        max_value=30,
        value=10,
        step=1
    )

    st.caption(
        "Follow-up questions are separate and are not included "
        "in this count."
    )

    st.divider()

    if not selected:

        st.warning(
            "Please select at least one interview area."
        )

    if st.button(
        "🚀 Start Interview",
        type="primary",
        disabled=not selected
    ):

        st.session_state.total_main_questions = question_count
        st.session_state.selected_areas = selected

        st.session_state.engine = InterviewEngine(
            company=st.session_state.company,
            experience_range=st.session_state.experience_range,
            selected_areas=selected,
            total_main_questions=question_count
        )

        st.session_state.stage = "interview"

        first_question = (
            st.session_state.engine.get_next_question()
        )

        if first_question is None:

            st.error(
                "No matching company-reported questions "
                "were found for this interview."
            )

            st.session_state.stage = "setup"

        else:

            st.session_state.current_question = (
                first_question
            )

            st.rerun()


# ============================================================
# STAGE 3 — Interview
# ============================================================

elif st.session_state.stage == "interview":

    engine = st.session_state.engine

    st.header("🎤 Interview")

    current_area = engine.get_current_area()

    if current_area:

        st.caption(
            f"Current area: **{current_area['name']}**"
        )

    question = st.session_state.current_question

    if question:

        if isinstance(question, dict):

            question_text = question.get(
                "question",
                ""
            )

        else:

            question_text = question

        st.subheader("Question")

        st.write(question_text)

        answer = st.text_area(
            "Your answer",
            height=180,
            key="answer_box"
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "Submit Answer",
                type="primary"
            ):

                if not answer.strip():

                    st.warning(
                        "Please enter an answer."
                    )

                else:

                    try:

                        result = engine.submit_answer(
                            answer
                        )

                        st.session_state.result = result

                        if result["type"] == "follow_up":

                            st.session_state.current_question = {
                                "question": result["question"]
                            }

                        elif result["type"] == "next_question":

                            st.session_state.current_question = {
                                "question": result["question"]
                            }

                        elif result["type"] == "finished":

                            st.session_state.stage = "assessment"

                        st.rerun()

                    except RuntimeError as e:

                        st.error(str(e))

        with col2:

            if st.button(
                "🛑 End Interview & Get Assessment"
            ):

                st.session_state.stage = "assessment"

                st.session_state.result = {
                    "type": "stopped"
                }

                st.rerun()


# ============================================================
# STAGE 4 — Assessment
# ============================================================

elif st.session_state.stage == "assessment":

    st.header("📊 Interview Assessment")

    engine = st.session_state.engine

    if engine:

        assessment = engine.get_assessment()

        st.metric(
            "Overall Score",
            f"{assessment['overall_score']}/10"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Questions Attempted",
                assessment["questions_attempted"]
            )

        with col2:
            st.metric(
                "Main Questions",
                assessment["main_questions"]
            )

        with col3:
            st.metric(
                "Follow-ups",
                assessment["follow_ups"]
            )

        st.subheader("Area Performance")

        for area, score in assessment[
            "area_scores"
        ].items():

            st.write(
                f"**{area}: {score}/10**"
            )

            st.progress(
                min(score / 10, 1.0)
            )

        if assessment["strong_areas"]:

            st.subheader("💪 Strong Areas")

            for area in assessment[
                "strong_areas"
            ]:

                st.write(f"✓ {area}")

        if assessment["weak_areas"]:

            st.subheader("📚 Areas to Improve")

            for area in assessment[
                "weak_areas"
            ]:

                st.write(f"⚠ {area}")

        st.divider()

        st.subheader("📝 Question-by-Question Review")

        st.write(
            "Review your answers carefully. The goal is to identify "
            "what you knew, what you missed, and what you should prepare next."
        )

        for review in assessment["question_reviews"]:

            question_number = review["number"]
            score = review["score"]
            area = review["jd_area"]
            question_type = review["type"]

            if score >= 7:
                indicator = "🟢"
            elif score >= 5:
                indicator = "🟡"
            else:
                indicator = "🔴"

            label = (
                f"{indicator} Question {question_number} "
                f"— {area} — {score}/10"
            )

            with st.expander(label):

                st.markdown("### Question")

                st.write(
                    review["question"]
                )

                st.markdown("### Your Answer")

                if review["answer"].strip():

                    st.info(
                        review["answer"]
                    )

                else:

                    st.warning(
                        "No answer was provided."
                    )

                st.markdown("### Evaluation")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Correctness",
                        f"{review['correctness']}/10"
                    )

                with col2:
                    st.metric(
                        "Completeness",
                        f"{review['completeness']}/10"
                    )

                with col3:
                    st.metric(
                        "Depth",
                        f"{review['depth']}/10"
                    )

                if review["strengths"]:

                    st.markdown("### ✅ What You Did Well")

                    for strength in review["strengths"]:

                        st.write(
                            f"• {strength}"
                        )

                if review["gaps"]:

                    st.markdown("### ⚠️ What You Missed")

                    for gap in review["gaps"]:

                        st.write(
                            f"• {gap}"
                        )

                if review["follow_up_needed"]:

                    st.markdown(
                        "### 📚 What You Should Prepare"
                    )

                    if review["follow_up_reason"]:

                        st.write(
                            review["follow_up_reason"]
                        )

                    if review["gaps"]:

                        for gap in review["gaps"]:

                            st.write(
                                f"• {gap}"
                            )

    else:

        st.info(
            "No interview assessment is available."
        )

    st.divider()

    if st.button(
        "🔄 Start New Interview",
        type="primary"
    ):

        for key in defaults:

            if key in st.session_state:

                del st.session_state[key]

        st.rerun()