import streamlit as st
import pdfplumber
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import openai

openai.api_key = st.secrets["OPENAI_API_KEY"]



def get_resume_suggestions(resume_text, role):
    prompt = f"""
You are a helpful career coach. The user is applying for the role of {role}.
Here is their resume text:

{resume_text}

Please provide 3 clear and actionable suggestions to improve their resume for better chances in this role.
"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error getting suggestions: {e}"


# ---------- PDF generation function ----------
def generate_pdf(role, score, matched, missing):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "Resume Match Report")

    c.setFont("Helvetica", 12)
    y = height - 90
    c.drawString(50, y, f"Job Role: {role}")
    y -= 20
    c.drawString(50, y, f"Match Score: {score:.2f}%")
    y -= 30

    c.drawString(50, y, "Matched Skills:")
    y -= 20
    for skill in matched:
        c.drawString(70, y, f"✔ {skill}")
        y -= 15

    y -= 10
    c.drawString(50, y, "Missing Skills:")
    y -= 20
    for skill in missing:
        c.drawString(70, y, f"✘ {skill}")
        y -= 15

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# ---------- Job roles & skills dict ----------
job_roles = {
    "Data Analyst": ["python", "sql", "excel", "tableau", "powerbi", "machine learning"],
    "Software Engineer": ["python", "java", "c++", "git", "docker", "kubernetes"],
    "Data Scientist": ["python", "machine learning", "statistics", "r", "deep learning", "sql"],
    "Product Manager": ["communication", "agile", "roadmap", "stakeholder", "leadership", "jira"],
    "Python Developer": ["python", "django", "flask", "rest api", "sql", "git", "oop"],
    "Machine Learning Engineer": ["python", "machine learning", "deep learning", "tensorflow", "pytorch", "data preprocessing", "model deployment"]
}

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Resume Matcher", layout="centered")
st.title("📄 Resume Matcher ")

# Select Job Role
selected_role = st.selectbox("Select Job Role:", list(job_roles.keys()))
required_skills = job_roles[selected_role]

# Upload Resume PDF
resume_file = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])

if resume_file is not None:
    st.success("✅ Resume uploaded successfully!")

    # Extract resume text
    with pdfplumber.open(resume_file) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

    # Show extracted text in expander
    with st.expander("📃 View Extracted Resume Text"):
        st.write(text)

    # Skill matching logic
    matched_skills = [skill for skill in required_skills if skill.lower() in text.lower()]
    missing_skills = [skill for skill in required_skills if skill.lower() not in text.lower()]
    match_score = (len(matched_skills) / len(required_skills)) * 100 if required_skills else 0

    # Display match results
    st.subheader("🧠 Job Match Results")
    st.write("✅ **Matched Skills:**", ", ".join(matched_skills) if matched_skills else "None")
    st.write("❌ **Missing Skills:**", ", ".join(missing_skills) if missing_skills else "None")
    st.write(f"📊 **Match Score:** {match_score:.2f}%")

    # Prepare text report
    text_report = f"""
Job Role: {selected_role}
Match Score: {match_score:.2f}%

Matched Skills:
{', '.join(matched_skills) if matched_skills else 'None'}

Missing Skills:
{', '.join(missing_skills) if missing_skills else 'None'}
"""

    # Download buttons
    st.download_button(
        label="📥 Download Match Report (Text)",
        data=text_report,
        file_name=f"{selected_role.replace(' ', '_')}_match_report.txt",
        mime="text/plain"
    )

    pdf_report = generate_pdf(selected_role, match_score, matched_skills, missing_skills)
    st.download_button(
        label="📄 Download Match Report (PDF)",
        data=pdf_report,
        file_name=f"{selected_role.replace(' ', '_')}_match_report.pdf",
        mime="application/pdf"
    )
     # GPT Resume Improvement Suggestions
    st.subheader("💡 Resume Improvement Suggestions (Powered by GPT)")
    if st.button("Get Suggestions"):
        with st.spinner("Analyzing resume..."):
            suggestions = get_resume_suggestions(text, selected_role)
            st.markdown(suggestions)

else:
    st.info("📥 Please upload a resume (PDF) to start matching.")

