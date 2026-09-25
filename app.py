import streamlit as st
import PyPDF2
from google import genai
from google.genai import types

# Page Setup
st.set_page_config(page_title="AI Teacher & Student Learning Hub", page_icon="🏫", layout="wide")

# Helper function to get API Key
def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key and "manual_api_key" in st.session_state:
        api_key = st.session_state["manual_api_key"]
    if not api_key:
        st.error("⚠️ No Gemini API Key found. Please configure your key in sidebar or Streamlit Secrets.")
        return None
    return genai.Client(api_key=api_key)

# Helper function to extract text from files
def extract_text_from_files(files) -> str:
    combined_text = ""
    for file in files:
        combined_text += f"\n--- Document: {file.name} ---\n"
        if file.type == "application/pdf":
            try:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        combined_text += extracted + "\n"
            except Exception as e:
                st.warning(f"Could not read {file.name}: {e}")
        elif file.type == "text/plain":
            combined_text += file.getvalue().decode("utf-8") + "\n"
        combined_text += f"--- End of Document: {file.name} ---\n"
    return combined_text

# Initialize global state for Live Lessons
if "active_lesson" not in st.session_state:
    st.session_state["active_lesson"] = None

# =============================================================================
# ROLE SELECTOR (Teacher vs. Student)
# =============================================================================
user_role = st.sidebar.radio("👤 Select Portal Role", ["Teacher Dashboard", "Student Portal"])

# -----------------------------------------------------------------------------
# TEACHER DASHBOARD
# -----------------------------------------------------------------------------
if user_role == "Teacher Dashboard":
    st.title("📚 Teacher Assistant & Live Broadcast Hub")

    with st.sidebar:
        st.header("⚙️ Configuration")
        if "GEMINI_API_KEY" in st.secrets:
            st.success("🔒 API Key loaded securely!")
        else:
            manual_key = st.text_input("Enter Gemini API Key", type="password")
            if manual_key:
                st.session_state["manual_api_key"] = manual_key

        st.divider()
        st.header("🏫 Class & Year Selector")
        selected_class = st.selectbox("Select Target Section", ["12 Gen 1", "12 Gen 2", "12 Advanced 1", "12 Advanced 2"])
        selected_term = st.selectbox("Select Academic Term", ["Term 1", "Term 2", "Term 3"])
        weeks_list = [f"Week {i}" for i in range(1, 13)]
        selected_week = st.selectbox("Select Academic Week", weeks_list)

        st.divider()
        st.header("📄 Curriculum Vault")
        uploaded_files = st.file_uploader("Upload Scope & Sequence (PDF/TXT)", type=["pdf", "txt"], accept_multiple_files=True)

    curriculum_context = extract_text_from_files(uploaded_files) if uploaded_files else ""

    tab1, tab2, tab3, tab4 = st.tabs([
        "📖 Lesson Planner",
        "📡 Live Broadcast Mode",
        "📝 Assessment Creator",
        "🎯 Support Planner"
    ])

    # TAB 1: Lesson Planner
    with tab1:
        st.header(f"Planning: {selected_class} — {selected_term}, {selected_week}")
        topic = st.text_input("Topic / Learning Objective Override", placeholder="e.g., Analyzing Rhetorical Appeals in Political Speeches")
        duration = st.selectbox("Duration", ["45 Minutes", "60 Minutes", "90 Minutes"])
        notes = st.text_area("Section Specific Notes")

        if st.button("🚀 Generate Lesson Plan", type="primary"):
            client = get_gemini_client()
            if client:
                prompt = f"""
                Create a full lesson plan for {selected_class} ({selected_term}, {selected_week}).
                Topic: {topic}
                Duration: {duration}
                Notes: {notes}
                Curriculum Context: {curriculum_context if curriculum_context else 'Standard Grade 12 English standards.'}
                
                Include:
                1. Objectives & Success Criteria
                2. Starter Hook (5-10m)
                3. Direct Instruction & CFU Prompts
                4. Differentiated Practice (Support, Core, Extension)
                5. Plenary / Exit Ticket
                """
                with st.spinner("Generating lesson..."):
                    try:
                        res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                        st.markdown(res.text)
                        st.session_state["current_generated_lesson"] = res.text
                    except Exception as e:
                        st.error(f"Error: {e}")

    # TAB 2: Live Broadcast Control
    with tab2:
        st.header("🔴 Broadcast Live Lesson to Students")
        st.write("Start a live lesson broadcast so students logged into the **Student Portal** can follow along on their devices.")

        if "current_generated_lesson" in st.session_state:
            st.info("Ready to broadcast the currently generated lesson.")
            if st.button("📡 Broadcast Live Lesson Now", type="primary"):
                st.session_state["active_lesson"] = {
                    "class": selected_class,
                    "term": selected_term,
                    "week": selected_week,
                    "content": st.session_state["current_generated_lesson"]
                }
                st.success(f"LIVE BROADCAST ACTIVE for {selected_class}! Students can now join.")
        else:
            st.warning("Please generate a lesson plan in Tab 1 first before starting a broadcast.")

        if st.session_state["active_lesson"]:
            if st.button("🛑 End Live Lesson"):
                st.session_state["active_lesson"] = None
                st.success("Broadcast ended.")

    # TAB 3: Assessment Creator
    with tab3:
        st.header("Assessment Builder")
        assess_type = st.selectbox("Type", ["Quiz", "Diagnostic", "Unit Test"])
        num_q = st.slider("Questions", 5, 20, 10)
        if st.button("Generate Assessment"):
            client = get_gemini_client()
            if client:
                prompt = f"Create a {assess_type} with {num_q} questions for {selected_class} based on {selected_term}, {selected_week}."
                with st.spinner("Generating..."):
                    res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                    st.markdown(res.text)

    # TAB 4: Support Planner
    with tab4:
        st.header("Intervention Planner")
        obs = st.text_area("Paste Student Performance Notes")
        if st.button("Generate Support Strategy"):
            client = get_gemini_client()
            if client:
                prompt = f"Analyze these student observations and generate an intervention plan: {obs}"
                with st.spinner("Analyzing..."):
                    res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                    st.markdown(res.text)

# -----------------------------------------------------------------------------
# STUDENT PORTAL
# -----------------------------------------------------------------------------
else:
    st.title("🎓 Student Learning & Practice Portal")

    with st.sidebar:
        st.header("🔐 Student Login")
        student_name = st.text_input("Enter Your Name", value="Student")
        student_class = st.selectbox("Select Your Class Section", ["12 Gen 1", "12 Gen 2", "12 Advanced 1", "12 Advanced 2"])
        target_support = st.selectbox("Choose Your Practice Focus Level", ["Support Tier (Guided Cues & Hints)", "Core Tier (Standard Practice)", "Challenge Tier (Advanced Evaluation)"])

    student_tab1, student_tab2 = st.tabs(["📡 Join Active Live Lesson", "🧠 Personalized Self-Paced Practice"])

    # STUDENT TAB 1: Live Lesson
    with student_tab1:
        st.header("Live Classroom View")
        active_lesson = st.session_state.get("active_lesson", None)

        if active_lesson and active_lesson["class"] == student_class:
            st.success(f"🔴 Live Lesson Broadcast Active: {active_lesson['term']} - {active_lesson['week']}")
            st.markdown(active_lesson["content"])
        elif active_lesson:
            st.info(f"An active lesson is currently broadcasting for **{active_lesson['class']}**. Your class is set to **{student_class}**.")
        else:
            st.warning("No active lesson broadcast at the moment. Waiting for teacher to start class...")

    # STUDENT TAB 2: AI Tutor & Practice
    with student_tab2:
        st.header(f"Personalized Practice for {student_name}")
        practice_topic = st.text_input("What skill or topic would you like to practice today?", placeholder="e.g., Rhetorical devices, Thesis statements, Vocabulary")
        
        if st.button("✨ Generate Custom Practice Task", type="primary"):
            client = get_gemini_client()
            if client:
                prompt = f"""
                You are an encouraging, supportive AI English Tutor.
                Student Name: {student_name}
                Class Level: {student_class}
                Practice Tier: {target_support}
                Practice Topic: {practice_topic if practice_topic else 'Grade 12 English core reading comprehension'}

                Create a short, interactive practice exercise for this student:
                1. A brief 2-paragraph reading excerpt.
                2. 3 targeted questions tailored to their tier ({target_support}).
                3. Provide 2 helpful hints/cues for each question to guide them if they get stuck.
                4. Include a reflection question at the end.
                """
                with st.spinner("Preparing your personalized exercise..."):
                    try:
                        res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                        st.markdown(res.text)
                    except Exception as e:
                        st.error(f"Error loading practice task: {e}")
