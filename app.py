import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json

# Load env vars
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Gemini API call
def get_gemini_response(prompt, retries=2):
    for attempt in range(retries):
        try:
            model = genai.GenerativeModel("models/gemini-2.0-flash")
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if attempt == retries - 1:
                return json.dumps({"error": str(e)})

# Extract text from uploaded PDF
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += str(page.extract_text())
    return text

# Extract JSON block from Gemini output
def extract_json_block(text):
    try:
        start = text.index('{')
        end = text.rindex('}') + 1
        return text[start:end]
    except ValueError:
        return None

ats_prompt_template = """
You are an advanced Applicant Tracking System designed to evaluate resumes for IT companies.

Evaluate the following resume and return the output ONLY in this JSON format:
{{
"ATS Score": "<score>/100",
"Strengths": ["Point1", "Point2", ...],
"Areas of Improvement": ["Point1", "Point2", ...]
}}

Resume:
\"\"\"{resume}\"\"\"
"""

jd_match_prompt_template = """
You are an expert ATS system evaluating resumes against job descriptions.

Compare the resume below with the provided job description. 
Return only the following JSON format:

{{
"Missing Keywords": ["keyword1", "keyword2", ...],
"Suggestions": ["Add keyword1 in project section", "Include keyword2 in your experience", ...]
}}

Resume:
\"\"\"{resume}\"\"\"

Job Description:
\"\"\"{jd}\"\"\"
"""

resume_improve_prompt_template = """
You are an expert AI resume coach. Carefully analyze the resume below.

Return a list of suggestions (in JSON format) that tells the user what sections can be improved or added. Do NOT include score or job match.

Format:
{{
"Suggestions": ["Improve education formatting", "Add a summary section", "Use more active verbs in work experience", ...]
}}

Resume:
\"\"\"{resume}\"\"\"
"""


st.set_page_config(page_title="ATS Resume Checker", layout="centered")
st.title("📄 Smart ATS Resume Checker")

# JD Panel 
st.subheader("Optional: Paste Job Description")
jd = st.text_area("Use this for job-matching analysis later", height=160)

# PDF Upload 
st.subheader("📎 Upload Resume (PDF only)")
uploaded_file = st.file_uploader("Upload your resume", type=["pdf"])

if uploaded_file:
    resume_text = input_pdf_text(uploaded_file)
    st.success("✅ Resume uploaded successfully!")

    # Buttons 
    st.divider()
    st.subheader("🔍 Run Resume Analysis")

    # ATS Score Button
    if st.button("ATS Score & Suggestions"):
        with st.spinner("Analyzing for ATS Score..."):
            prompt = ats_prompt_template.format(resume=resume_text)
            response = get_gemini_response(prompt)
            cleaned = extract_json_block(response)

            if cleaned:
                try:
                    result = json.loads(cleaned)
                    st.success("✅ ATS Analysis Complete")
                    st.metric("✅ ATS Score", result.get("ATS Score", "N/A"))
                    st.markdown("**📈Strengths:**")
                    st.write(result.get("Strengths", []))
                    st.markdown("**📉 Areas of Improvement:**")
                    st.write(result.get("Areas of Improvement", []))
                except json.JSONDecodeError:
                    st.error("⚠️ Couldn't parse ATS score response.")
                    st.code(cleaned)
            else:
                st.error("⚠️ Gemini returned an invalid response.")
                st.code(response)

    # Resume Suggestions Button
    if st.button("AI Resume Suggestions"):
        with st.spinner("Generating AI suggestions..."):
            prompt = resume_improve_prompt_template.format(resume=resume_text)
            response = get_gemini_response(prompt)
            cleaned = extract_json_block(response)

            if cleaned:
                try:
                    result = json.loads(cleaned)
                    st.success("✅ Suggestions Generated")
                    st.markdown(" **Suggestions to Improve Resume:**")
                    st.write(result.get("Suggestions", []))
                except json.JSONDecodeError:
                    st.error("⚠️ Couldn't parse suggestion response.")
                    st.code(cleaned)
            else:
                st.error("⚠️ Gemini returned an invalid response.")
                st.code(response)

    st.divider()
    st.subheader(" Analyze Against Job Description")

    if st.button(" Match Resume to Job Description"):
        if not jd.strip():
            st.warning("⚠️ Please paste a job description above.")
        else:
            with st.spinner("Matching resume with JD..."):
                prompt = jd_match_prompt_template.format(resume=resume_text, jd=jd)
                response = get_gemini_response(prompt)
                cleaned = extract_json_block(response)

                if cleaned:
                    try:
                        result = json.loads(cleaned)
                        st.success("✅ JD Comparison Complete")
                        st.markdown("❌ **Missing Keywords:**")
                        st.write(result.get("Missing Keywords", []))
                        st.markdown("💡 **Suggestions based on JD:**")
                        st.write(result.get("Suggestions", []))
                    except json.JSONDecodeError:
                        st.error("⚠️ Couldn't parse JD analysis response.")
                        st.code(cleaned)
                else:
                    st.error("Gemini returned an invalid response.")
                    st.code(response)

else:
    st.info(" Upload your PDF resume to start.")
