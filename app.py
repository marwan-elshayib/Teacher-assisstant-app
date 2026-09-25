import streamlit as st
import PyPDF2
from google import genai

# Page Setup
st.set_page_config(page_title="AI Teacher Assistant & Student Hub", page_icon="🏫", layout="wide")

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS & STATE INITIALIZATION
# -----------------------------------------------------------------------------
def get_gemini_client():
    """Fetches Gemini client securely from secrets or session state."""
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key and "manual_api_key" in st.session_state:
        api_key = st.session_state["manual_api_key"]
    
    if api_key:
        api_key = api_key.strip().strip('"').strip("'")
        
    if not api_key:
        st.error("⚠️ No Gemini API Key found. Please check Secrets or enter it in the sidebar.")
        return None
        
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize Gemini Client: {e}")
        return None

def extract_text_from_files(files) -> str:
    """Parses PDF and TXT documents safely."""
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
                st.sidebar.error(f"Could not read {file.name}: {e}")
        elif file.type == "text/plain":
            combined_text += file.getvalue().decode("utf-8") + "\n"
        combined_text += f"--- End of Document: {file.name} ---\n"
    return combined_text

# Initialize persistent memory across reloads
if "curriculum_text" not in st.session_state:
    st.session_state["curriculum_text"] = ""

if "active_lesson" not in st.session_state:
    st.session_state["active_lesson"] = None

# -----------------------------------------------------------------------------
# MAIN PORTAL ROLE SELECTOR
# -----------------------------------------------------------------------------
st.sidebar.title("🏫 Hub Navigation")
user_role = st.sidebar.radio("Select Portal Role", ["Teacher Dashboard", "Student Portal"])

# =============================================================================
# 1. TEACHER DASHBOARD
# =============================================================================
if user_role == "Teacher Dashboard":
    st.title("📚 AI Teacher Assistant & Classroom Command Center")

    with st.sidebar:
        st.divider()
        st.header("⚙️ Configuration")
        if "GEMINI_API_KEY" in st.secrets:
            st.success("🔒 API Key loaded securely!")
        else:
            manual_key = st.text_input("Enter Gemini API Key", type="password")
            if manual_key:
                st.session_state["manual_api_key"] = manual_key

        st.divider()
        st.header("🏫 Class & Pacing Selector")
        selected_class = st.selectbox("Select Target Section", ["12 Gen 1", "12 Gen 2", "12 Advanced 1", "12 Advanced 2", "All Grade 12 Sections"])
        selected_term = st.selectbox("Select Academic Term", ["Term 1", "Term 2", "Term 3"])
        
        weeks_list = [f"Week {i}" for i in range(1, 14)]
        selected_week = st.selectbox("Select Academic Week", weeks_list)

        st.divider()
        st.header("📄 Curriculum Context Vault")
        uploaded_files = st.file_uploader("Upload Scope & Sequence (PDF/TXT)", type=["pdf", "txt"], accept_multiple_files=True)

        if uploaded_files:
            if st.button("💾 Process Uploaded Files"):
                st.session_state["curriculum_text"] = extract_text_from_files(uploaded_files)
                st.success(f"Loaded {len(uploaded_files)} file(s) into memory!")

    # Teacher Functional Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📖 Weekly Lesson Architect",
        "📡 Live Broadcast Control",
        "📝 Assessment Builder",
        "🎯 Diagnostic & Support Planner"
    ])

    # TAB 1: Lesson Planner
    with tab1:
        st.header(f"Lesson Planner: {selected_class} — {selected_term}, {selected_week}")
        topic = st.text_input("Topic / Objective Focus (Leave blank to auto-extract from uploaded Scope & Sequence)")
        duration = st.selectbox("Lesson Duration", ["45 Minutes", "60 Minutes", "90 Minutes (Block)"])
        notes = st.text_area("Specific Section Requirements / Notes", placeholder="e.g., 12 Gen 1 needs extra vocabulary practice; prepare sentence frames...")

        if st.button("🚀 Generate Lesson Plan", type="primary", key="btn_lesson"):
            client = get_gemini_client()
            if client:
                prompt_text = f"""
                You are an expert master teacher and curriculum developer.
                Generate a structured, interactive 3-part lesson plan based on the following context.

                Target Section: {selected_class}
                Academic Pacing: {selected_term}, {selected_week}
                Lesson Duration: {duration}
                Topic/Focus: {topic if topic else 'Extract the exact topic and skill for this Term and Week from the curriculum context below.'}
                Section Notes: {notes}

                --- UPLOADED CURRICULUM CONTEXT ---
                {st.session_state['curriculum_text'] if st.session_state['curriculum_text'] else 'Standard Grade 12 English curriculum competencies.'}
                -----------------------------------

                Format strictly using Markdown:
                # Lesson Plan: {selected_class} — {selected_term}, {selected_week}
                1. **Learning Objectives & Success Criteria** (SWBAT / WILF)
                2. **Starter / Hook Activity** (5–10 mins)
                3. **Direct Instruction & Check for Understanding (CFU)** (With 3 targeted questions)
                4. **Differentiated Practice Tasks**:
                   - *Support Tier (Scaffolded)*
                   - *Core Tier (Standard)*
                   - *Extension Tier (Advanced)*
                5. **Plenary / Exit Ticket** (10 mins)
                6. **Required Materials & Key Vocabulary**
                """
                with st.spinner(f"Building lesson plan for {selected_class}..."):
                    try:
                        res = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=prompt_text
                        )
                        st.markdown(res.text)
                        st.session_state["latest_lesson_plan"] = res.text
                        st.download_button("📥 Download Lesson Plan (.txt)", res.text, file_name=f"Lesson_{selected_class}_{selected_term}_{selected_week}.txt")
                    except Exception as e:
                        st.error(f"Error generating lesson: {e}")

    # TAB 2: Live Broadcast Control
    with tab2:
        st.header("🔴 Live Classroom Broadcast")
        st.write("Broadcast your active lesson directly to student devices logged into the **Student Portal**.")

        if "latest_lesson_plan" in st.session_state:
            st.info(f"Lesson currently ready to broadcast for **{selected_class}** ({selected_term}, {selected_week}).")
            if st.button("📡 Start Live Broadcast Now", type="primary"):
                st.session_state["active_lesson"] = {
                    "class": selected_class,
                    "term": selected_term,
                    "week": selected_week,
                    "content": st.session_state["latest_lesson_plan"]
                }
                st.success(f"LIVE BROADCAST IS NOW ACTIVE FOR {selected_class}!")
        else:
            st.warning("Please generate a lesson plan in the 'Weekly Lesson Architect' tab first before starting a broadcast.")

        if st.session_state["active_lesson"]:
            st.divider()
            st.write(f"**Currently Broadcasting:** {st.session_state['active_lesson']['class']} ({st.session_state['active_lesson']['term']}, {st.session_state['active_lesson']['week']})")
            if st.button("🛑 End Live Broadcast"):
                st.session_state["active_lesson"] = None
                st.success("Broadcast ended successfully.")

    # TAB 3: Assessment Builder
    with tab3:
        st.header(f"Assessment Creator: {selected_class} — {selected_term}")
        col1, col2 = st.columns(2)
        with col1:
            assess_type = st.selectbox("Assessment Type", ["Weekly Formative Quiz", "Mid-Term Diagnostic", "End-of-Term Summative Exam", "Rubric & Task Brief"])
            num_q = st.slider("Number of Questions", 5, 25, 10)
        with col2:
            q_types = st.multiselect("Question Formats", ["Multiple Choice (MCQ)", "Short Answer", "Text Analysis", "Essay Response"], default=["Multiple Choice (MCQ)", "Short Answer"])

        if st.button("📝 Generate Assessment", type="primary", key="btn_assess"):
            client = get_gemini_client()
            if client:
                prompt_text = f"""
                Create a {assess_type} with {num_q} questions for {selected_class} ({selected_term}, {selected_week}).
                Included Formats: {', '.join(q_types)}

                Context: {st.session_state['curriculum_text'] if st.session_state['curriculum_text'] else 'Standard Grade 12 competencies.'}

                Format in two distinct sections:
                PART 1: Student Test Paper (Ready for print/copying).
                PART 2: Teacher Answer Key with marking guidance and rubrics.
                """
                with st.spinner("Building assessment and answer keys..."):
                    try:
                        res = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=prompt_text
                        )
                        st.markdown(res.text)
                        st.download_button("📥 Download Assessment (.txt)", res.text, file_name=f"Assessment_{selected_class}_{selected_term}_{selected_week}.txt")
                    except Exception as e:
                        st.error(f"Error generating assessment: {e}")

    # TAB 4: Support Planner
    with tab4:
        st.header("Student Support & Intervention Planner")
        obs_data = st.text_area("Paste Assessment Scores or Observed Misconceptions", height=150, placeholder="e.g., 40% of students in 12 Gen 1 struggled with identifying thesis statements during Week 3...")
        support_goal = st.text_input("Remediation Goal / Timeline", placeholder="e.g., 2-week catch-up plan before re-assessment")

        if st.button("🛠️ Generate Support Strategy", type="primary", key="btn_support"):
            if not obs_data:
                st.warning("Please paste student performance notes.")
            else:
                client = get_gemini_client()
                if client:
                    prompt_text = f"""
                    Analyze student performance data for {selected_class} ({selected_term}, {selected_week}):
                    Data/Notes: {obs_data}
                    Timeline: {support_goal}

                    Generate a structured Support & Intervention Plan:
                    1. Root Cause Misconception Analysis
                    2. Targeted Small-Group Intervention Strategy (Support Tier)
                    3. Extension Tasks for High Performers
                    4. Teacher Progress Tracking Checklist
                    """
                    with st.spinner("Formulating strategy..."):
                        try:
                            res = client.models.generate_content(
                                model="gemini-2.5-flash",
                                contents=prompt_text
                            )
                            st.markdown(res.text)
                            st.download_button("📥 Download Support Plan (.txt)", res.text, file_name=f"Support_Plan_{selected_class}_{selected_week}.txt")
                        except Exception as e:
                            st.error(f"Error: {e}")

# =============================================================================
# 2. STUDENT PORTAL
# =============================================================================
else:
    st.title("🎓 Student Learning Portal")

    with st.sidebar:
        st.divider()
        st.header("🔐 Student Login")
        student_name = st.text_input("Your Name", value="Student")
        student_class = st.selectbox("Your Class Section", ["12 Gen 1", "12 Gen 2", "12 Advanced 1", "12 Advanced 2"])
        support_level = st.selectbox("Practice Support Level", ["Support Tier (Guided Cues & Sentence Starters)", "Core Tier (Standard Practice)", "Extension Tier (Challenge)"])

    student_tab1, student_tab2 = st.tabs(["📡 Join Active Live Lesson", "🧠 Self-Paced Adaptive Practice"])

    # STUDENT TAB 1: Live Lesson View
    with student_tab1:
        st.header("Live Classroom View")
        active_lesson = st.session_state.get("active_lesson", None)

        if active_lesson and (active_lesson["class"] == student_class or active_lesson["class"] == "All Grade 12 Sections"):
            st.success(f"🔴 LIVE LESSON ACTIVE: {active_lesson['class']} ({active_lesson['term']} - {active_lesson['week']})")
            st.markdown(active_lesson["content"])
        elif active_lesson:
            st.info(f"An active broadcast is running for **{active_lesson['class']}**. Your section is set to **{student_class}** in the sidebar.")
        else:
            st.warning("No active broadcast running right now. Waiting for teacher to start class...")

    # STUDENT TAB 2: Self-Paced Adaptive Practice
    with student_tab2:
        st.header(f"Personalized Practice for {student_name}")
        practice_topic = st.text_input("What topic or skill would you like to practice today?", placeholder="e.g., Rhetorical devices, Thesis statements, Vocabulary")

        if st.button("✨ Start Practice Exercise", type="primary", key="btn_student_practice"):
            client = get_gemini_client()
            if client:
                prompt_text = f"""
                You are an encouraging, supportive English AI Tutor.
                Student Name: {student_name}
                Class Section: {student_class}
                Practice Tier: {support_level}
                Focus Topic: {practice_topic if practice_topic else 'Grade 12 English core reading comprehension'}

                Create a short, interactive practice exercise:
                1. A brief 2-paragraph reading excerpt.
                2. 3 targeted questions tailored to their tier ({support_level}).
                3. Include 2 helpful hints/cues for each question to guide them if they get stuck.
                4. Include a reflection question at the end.
                """
                with st.spinner("Preparing your personalized exercise..."):
                    try:
                        res = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=prompt_text
                        )
                        st.markdown(res.text)
                    except Exception as e:
                        st.error(f"Error loading practice: {e}")
