import streamlit as st
import pdfplumber
from docx import Document
import requests

# ---------------------------------------
# OLLAMA CONFIG
# ---------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

# ---------------------------------------
# TECH SKILL DATABASE
# ---------------------------------------
TECH_SKILLS = [
    "python", "java", "mysql", "sql", "django", "flask",
    "html", "css", "javascript", "react",
    "aws", "docker", "git",
    "machine learning", "data science"
]

# ---------------------------------------
# RESUME TEXT EXTRACTION
# ---------------------------------------
def extract_resume_text(file):
    text = ""
    if file.name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    else:
        doc = Document(file)
        for p in doc.paragraphs:
            text += p.text + " "
    return text.lower()

# ---------------------------------------
# SKILL EXTRACTION
# ---------------------------------------
def extract_skills(text):
    return list(set([s for s in TECH_SKILLS if s in text]))

# ---------------------------------------
# QUESTION GENERATION (LLAMA 3)
# ---------------------------------------
def generate_questions(skill):
    prompt = f"""
    You are a technical interviewer.

    Generate exactly 3 interview questions for the skill "{skill}".

    Rules:
    - Output ONLY the questions
    - NO headings
    - NO explanations
    - NO introductory text
    - Each question must be on a new line
    - Questions must be practical and technical
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
    )

    data = response.json()

    if "response" not in data:
        return [
            f"What is {skill}?",
            f"Explain a project where you used {skill}.",
            f"What challenges did you face using {skill}?"
        ]

    questions = [
        q.strip("-•0123456789. ")
        for q in data["response"].split("\n")
        if q.strip()
    ]

    return questions[:3]

# ---------------------------------------
# ANSWER EVALUATION (LLAMA 3)
# ---------------------------------------
def evaluate_answer(skill, question, answer):
    prompt = f"""
    You are a technical interviewer.

    Skill: {skill}
    Question: {question}
    Candidate Answer: {answer}

    Evaluate the answer honestly.

    Give:
    - Score between 0 and 10
    - One-line feedback

    Format:
    Score: X
    Feedback: ...
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]

# ---------------------------------------
# STREAMLIT UI
# ---------------------------------------
st.set_page_config("AI Interview System", layout="centered")
st.title("AI Resume-Based Interview System")

resume = st.file_uploader("Upload Resume (PDF / DOCX)", type=["pdf", "docx"])

if resume:
    resume_text = extract_resume_text(resume)
    skills = extract_skills(resume_text)

    if skills:
        st.success("Skills detected from resume:")
        st.write(", ".join(skills))

        st.subheader("Interview Test")

        answers = []
        total_score = 0
        max_score = 0

        for skill in skills:
            st.markdown(f"## 🔹 {skill.upper()}")

            questions = generate_questions(skill)

            for i, q in enumerate(questions):
                st.write(f"**Q{i+1}: {q}**")
                ans = st.text_area("Your Answer", key=f"{skill}_{i}")

                if ans:
                    answers.append((skill, q, ans))
                max_score += 10

        if st.button("Submit Interview"):
            st.subheader("Interview Evaluation")

            for skill, q, ans in answers:
                evaluation = evaluate_answer(skill, q, ans)
                st.markdown(f"**{skill.upper()} – {q}**")
                st.write(evaluation)

                try:
                    score = int(
                        [line for line in evaluation.split("\n") if "Score" in line][0].split(":")[1]
                    )
                    total_score += score
                except:
                    pass

            percentage = (total_score / max_score) * 100
            st.subheader("Final Result")
            st.write(f"**Total Score:** {total_score} / {max_score}")
            st.write(f"**Percentage:** {percentage:.2f}%")

            if percentage >= 75:
                st.success("Excellent Performance")
            elif percentage >= 50:
                st.warning("Good Performance")
            else:
                st.error("Needs Improvement")

    else:
        st.warning("No technical skills detected in resume.")