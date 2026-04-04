# Procrastination Tendencies and Study Motivation Inventory

import streamlit as st
import json
import csv
import re
import io
import os
from datetime import datetime

st.set_page_config(
    page_title="Procrastination Tendencies and Study Motivation Inventory",
    page_icon="📚",
    layout="centered"
)

# GLOBAL DATA

QUESTIONS_FILE: str = "questions.json"
MAX_SCORE:      int = 80   # 20 questions x 4 points each

SCORE_RANGES: list = [
    (0,  15, "🟢 Very low procrastination",
             "You show excellent study motivation and self-discipline. Keep it up!"),
    (16, 30, "🔵 Mild procrastination",
             "You occasionally delay tasks. Simple reminders and to-do lists will help."),
    (31, 45, "🟡 Moderate procrastination",
             "Procrastination is noticeably affecting your studies. Try time-blocking techniques."),
    (46, 60, "🟠 High procrastination",
             "Your study motivation is low and delays are frequent. Consider attending a study skills workshop."),
    (61, 68, "🔴 Very high procrastination",
             "Procrastination is seriously impacting your academic performance. Seek academic counselling."),
    (69, 74, "🚨 Severe procrastination",
             "You are struggling significantly with motivation and task avoidance. Professional support is strongly advised."),
    (75, 80, "💥 Critical procrastination",
             "Immediate intervention recommended. Please speak to your academic advisor or counsellor urgently."),
]

ALLOWED_FORMATS: frozenset = frozenset({"txt", "csv", "json"})

# FUNCTION 1 — Load questions from external file

def load_questions(filepath: str) -> list:
    """Load survey questions from an external JSON file."""
    if not os.path.exists(filepath):
        st.error(f"Questions file '{filepath}' not found. Make sure it is in the same folder.")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

# FUNCTION 2 — Validate full name

def validate_name(name: str) -> bool:
    """Only letters, hyphens, apostrophes, and spaces allowed."""
    pattern = r"^[A-Za-z][A-Za-z\s'\-]*$"
    return bool(re.match(pattern, name.strip()))

# FUNCTION 3 — Validate date of birth

def validate_dob(dob_str: str) -> bool:
    """Validate DD/MM/YYYY format and realistic age."""
    try:
        dob = datetime.strptime(dob_str.strip(), "%d/%m/%Y")
        age: int = (datetime.today() - dob).days // 365
        return 10 <= age <= 120
    except ValueError:
        return False

# FUNCTION 4 — Validate student ID

def validate_student_id(sid: str) -> bool:
    """Student ID must contain digits only."""
    return sid.strip().isdigit() and len(sid.strip()) > 0

# FUNCTION 5 — Get psychological state from score

def get_psychological_state(total_score: int) -> tuple:
    """Return label and description matching the score."""
    for low, high, label, description in SCORE_RANGES:
        if low <= total_score <= high:
            return label, description
    return "💥 Critical Procrastination", "Immediate intervention recommended. Please speak to your academic advisor urgently."

# FUNCTION 6 — Build result dictionary

def build_result(user: dict, total_score: int, answers: list) -> dict:
    """Assemble full result into a structured dictionary."""
    percentage: float = round((total_score / MAX_SCORE) * 100, 1)
    label, desc = get_psychological_state(total_score)
    return {
        "user":    user,
        "score":   {"total": total_score, "max": MAX_SCORE, "percentage": percentage},
        "result":  {"state": label, "description": desc},
        "answers": answers
    }

# FUNCTION 7 — Generate downloadable file content

def generate_file(result: dict, fmt: str) -> tuple:
    """Generate file content as bytes plus MIME type."""
    user        = result["user"]
    score_info  = result["score"]
    result_info = result["result"]
    answers     = result["answers"]

    if fmt == "json":
        content  = json.dumps(result, indent=4, ensure_ascii=False)
        mimetype = "application/json"

    elif fmt == "csv":
        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(["Field", "Value"])
        writer.writerow(["Name",        user["name"]])
        writer.writerow(["DOB",         user["dob"]])
        writer.writerow(["Student ID",  user["student_id"]])
        writer.writerow(["Timestamp",   user["timestamp"]])
        writer.writerow(["Total Score", score_info["total"]])
        writer.writerow(["Max Score",   score_info["max"]])
        writer.writerow(["Percentage",  score_info["percentage"]])
        writer.writerow(["State",       result_info["state"]])
        writer.writerow(["Description", result_info["description"]])
        writer.writerow([])
        writer.writerow(["#", "Question", "Answer", "Score"])
        for i, a in enumerate(answers, 1):
            writer.writerow([i, a["question"], a["answer"], a["score"]])
        content  = si.getvalue()
        mimetype = "text/csv"

    else:
        scores_list: list = [a["score"] for a in answers]
        lines: list = [
            "PROCRASTINATION & STUDY MOTIVATION INVENTORY — RESULTS",
            "=" * 56,
            f"Name:        {user['name']}",
            f"DOB:         {user['dob']}",
            f"Student ID:  {user['student_id']}",
            f"Timestamp:   {user['timestamp']}",
            f"Score:       {score_info['total']} / {score_info['max']} ({score_info['percentage']}%)",
            f"State:       {result_info['state']}",
            f"Details:     {result_info['description']}",
            "",
            "--- ANSWERS ---",
        ]
        for i, a in enumerate(answers, 1):
            lines.append(f"Q{i:02d}: {a['question']}")
            lines.append(f"      Answer: {a['answer']}  (score: {a['score']})")
        content  = "\n".join(lines)
        mimetype = "text/plain"

    return content.encode("utf-8"), mimetype

# FUNCTION 8 — Render home page

def page_home() -> None:
    """Display the home screen."""
    st.title("📚 Procrastination Tendencies and Study Motivation Inventory")
    st.markdown("### Procrastination Tendencies & Study Motivation Survey")
    st.markdown(
        "This survey measures your tendency to delay academic tasks and your overall "
        "motivation for studying. Answer honestly since there are no right or wrong answers. "
        "The survey contains **20 questions** and takes about **3–5 minutes**."
    )
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 Start New Survey", use_container_width=True, type="primary"):
            st.session_state.page = "details"
            st.rerun()
    with col2:
        if st.button("📂 Load Existing Result", use_container_width=True):
            st.session_state.page = "load"
            st.rerun()

    st.divider()
    st.markdown("**Score ranges:**")
    ranges_data: list = [
        ("0 – 15",  "🟢 Very Low Procrastination — high motivation"),
        ("16 – 30", "🔵 Mild Procrastination — use simple reminders"),
        ("31 – 45", "🟡 Moderate Procrastination — apply time-blocking"),
        ("46 – 60", "🟠 High Procrastination — seek study skills workshop"),
        ("61 – 68", "🔴 Very High Procrastination — seek academic counselling"),
        ("69 – 74", "🚨 Severe Procrastination — professional support advised"),
        ("75 – 80", "💥 Critical Procrastination — immediate intervention needed"),
    ]
    for score_range, label in ranges_data:
        st.markdown(f"- `{score_range}` &nbsp; {label}")

# FUNCTION 9 — Render details page

def page_details() -> None:
    """Collect and validate user personal details."""
    st.title("📝 Your Details")
    st.markdown("Please fill in your information before starting the survey.")
    st.divider()

    name       = st.text_input("Full Name (Surname Given Name)", placeholder="e.g. Smith-Jones Mary Ann")
    dob        = st.text_input("Date of Birth", placeholder="DD/MM/YYYY")
    student_id = st.text_input("Student ID", placeholder="Digits only, e.g. 200012345")

    st.caption("Name: letters, hyphens, apostrophes, and spaces only (e.g. O'Connor, Smith-Jones)")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
    with col2:
        start_clicked: bool = st.button("Start Survey →", use_container_width=True, type="primary")

    if start_clicked:
        errors: dict = {}

        # Validate all fields using a for loop
        fields: list = [
            ("name",       name,       validate_name,       "Name may only contain letters, hyphens, apostrophes, and spaces."),
            ("dob",        dob,        validate_dob,        "Enter a valid date in DD/MM/YYYY format (age 10–120)."),
            ("student_id", student_id, validate_student_id, "Student ID must contain digits only, no spaces or letters."),
        ]
        for field_name, value, validator, message in fields:
            if not value.strip():
                errors[field_name] = "This field is required."
            elif not validator(value):
                errors[field_name] = message

        if errors:
            for field_name, msg in errors.items():
                st.error(f"**{field_name.replace('_', ' ').title()}:** {msg}")
        else:
            st.session_state.user = {
                "name":       name.strip(),
                "dob":        dob.strip(),
                "student_id": student_id.strip(),
                "timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            st.session_state.page        = "survey"
            st.session_state.current_q   = 0
            st.session_state.answers     = []
            st.session_state.total_score = 0
            st.rerun()

# FUNCTION 10 — Render survey page

def page_survey(questions: list) -> None:
    """Show one question at a time with progress tracking."""
    current_q: int  = st.session_state.get("current_q", 0)
    total:      int  = len(questions)
    progress:   float = current_q / total

    st.title("📋 Survey")
    st.progress(progress, text=f"Question {current_q + 1} of {total}")
    st.divider()

    q = questions[current_q]
    st.markdown(f"### Q{current_q + 1}. {q['question']}")

    option_texts: list = [opt["text"] for opt in q["options"]]
    choice = st.radio("Select your answer:", option_texts, index=None, key=f"q_{current_q}")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", use_container_width=True):
            if current_q == 0:
                st.session_state.page = "details"
            else:
                # Go back one question and remove last answer
                st.session_state.current_q -= 1
                if st.session_state.answers:
                    removed = st.session_state.answers.pop()
                    st.session_state.total_score -= removed["score"]
            st.rerun()
    with col2:
        btn_label: str = "See Results 🎯" if current_q == total - 1 else "Next →"
        if st.button(btn_label, use_container_width=True, type="primary"):
            if choice is None:
                st.warning("⚠️ Please select an answer before continuing.")
            else:
                # Find score for chosen option
                chosen_score: int = 0
                for opt in q["options"]:
                    if opt["text"] == choice:
                        chosen_score = opt["score"]
                        break

                answers: list = st.session_state.get("answers", [])
                answers.append({
                    "question": q["question"],
                    "answer":   choice,
                    "score":    chosen_score
                })
                st.session_state.answers     = answers
                st.session_state.total_score = st.session_state.get("total_score", 0) + chosen_score
                st.session_state.current_q   = current_q + 1

                if st.session_state.current_q >= total:
                    st.session_state.page = "results"
                st.rerun()

# FUNCTION 11 — Render results page

def page_results() -> None:
    """Show final results with download options."""
    user        = st.session_state.get("user", {})
    total_score: int   = st.session_state.get("total_score", 0)
    answers:     list  = st.session_state.get("answers", [])
    percentage:  float = round((total_score / MAX_SCORE) * 100, 1)
    label, desc = get_psychological_state(total_score)
    result: dict = build_result(user, total_score, answers)

    st.title("🎯 Your Results")
    st.divider()

    # Score display
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Score", f"{total_score} / {MAX_SCORE}")
    col2.metric("Percentage",  f"{percentage}%")
    col3.metric("Questions",   len(answers))

    st.divider()
    st.markdown(f"## {label}")
    st.info(desc)

    # User info
    with st.expander("👤 Your Details"):
        st.write(f"**Name:** {user.get('name', '')}")
        st.write(f"**Date of Birth:** {user.get('dob', '')}")
        st.write(f"**Student ID:** {user.get('student_id', '')}")
        st.write(f"**Completed:** {user.get('timestamp', '')}")

    st.divider()

    # Download section
    st.markdown("### 💾 Save Your Results")
    fmt: str = st.selectbox("Choose file format:", ["json", "csv", "txt"])
    file_bytes, mimetype = generate_file(result, fmt)
    timestamp_str: str   = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename: str        = f"result_{user.get('student_id', 'student')}_{timestamp_str}.{fmt}"

    st.download_button(
        label=f"⬇️ Download as {fmt.upper()}",
        data=file_bytes,
        file_name=filename,
        mime=mimetype,
        use_container_width=True,
        type="primary"
    )

    st.divider()

    # Answer breakdown
    st.markdown("### 📋 Answer Breakdown")
    scores_list: list = [a["score"] for a in answers]
    for i, a in enumerate(answers, 1):
        with st.expander(f"Q{i}. {a['question']}"):
            st.write(f"**Your answer:** {a['answer']}")
            st.write(f"**Score:** {a['score']} / 4")

    st.divider()
    if st.button("🏠 Back to Home", use_container_width=True):
        # Reset session
        for key in ["user", "current_q", "answers", "total_score"]:
            st.session_state.pop(key, None)
        st.session_state.page = "home"
        st.rerun()

# FUNCTION 12 — Render load page

def page_load() -> None:
    """Upload and display an existing result file."""
    st.title("📂 Load Existing Result")
    st.markdown("Upload a previously saved result file (.json, .csv, or .txt)")
    st.divider()

    uploaded = st.file_uploader("Choose a result file", type=["json", "csv", "txt"])

    if uploaded:
        ext: str     = uploaded.name.rsplit(".", 1)[-1].lower()
        content: str = uploaded.read().decode("utf-8")

        if ext == "json":
            try:
                data: dict = json.loads(content)
                user        = data.get("user", {})
                score_info  = data.get("score", {})
                result_info = data.get("result", {})
                answers     = data.get("answers", [])

                st.success("File loaded successfully!")
                st.divider()

                col1, col2, col3 = st.columns(3)
                col1.metric("Total Score", f"{score_info.get('total', '?')} / {score_info.get('max', '?')}")
                col2.metric("Percentage",  f"{score_info.get('percentage', '?')}%")
                col3.metric("Questions",   len(answers))

                st.markdown(f"## {result_info.get('state', '')}")
                st.info(result_info.get("description", ""))

                with st.expander("👤 Details"):
                    st.write(f"**Name:** {user.get('name', '')}")
                    st.write(f"**DOB:** {user.get('dob', '')}")
                    st.write(f"**Student ID:** {user.get('student_id', '')}")
                    st.write(f"**Timestamp:** {user.get('timestamp', '')}")

                st.markdown("### 📋 Answer Breakdown")
                for i, a in enumerate(answers, 1):
                    with st.expander(f"Q{i}. {a['question']}"):
                        st.write(f"**Answer:** {a['answer']}")
                        st.write(f"**Score:** {a['score']} / 4")

            except json.JSONDecodeError:
                st.error("Invalid JSON file. Please upload a valid result file.")

        elif ext == "csv":
            st.success("CSV file loaded!")
            st.text(content)

        else:  # txt
            st.success("TXT file loaded!")
            st.text(content)

    st.divider()
    if st.button("← Back to Home", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()

# MAIN — Router

def main() -> None:
    """Main entry point — routes between pages using session state."""

    # Initialise session state
    if "page" not in st.session_state:
        st.session_state.page = "home"

    # Load questions once
    questions: list = load_questions(QUESTIONS_FILE)

    # Route to correct page
    page: str = st.session_state.page

    if page == "home":
        page_home()
    elif page == "details":
        page_details()
    elif page == "survey":
        if not questions:
            st.error("Cannot start survey: questions file missing.")
        else:
            page_survey(questions)
    elif page == "results":
        page_results()
    elif page == "load":
        page_load()
    else:
        st.session_state.page = "home"
        st.rerun()

if __name__ == "__main__":
    main()
