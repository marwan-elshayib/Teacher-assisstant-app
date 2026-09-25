import streamlit as st
import PyPDF2
from google import genai

# Page Setup
st.set_page_config(page_title="AI Teacher & Student Learning Hub", page_icon="🏫", layout="wide")

# Helper function to get API Key
def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key and "manual_api_key" in st.session_state:
        api_key = st.session_state["manual_api_key"]
    if not api_key:
        st.error("⚠️ No Gemini API Key found. Please check Secrets or enter it in the sidebar.")
        return None
    return genai.Client(api_key=api_key)

# Helper function to extract text from files safely
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
                st.sidebar.error(f"Could not read {file.name}: {e}")
        elif file.type == "text/plain":
            combined_text += file.getvalue().decode("utf-8") + "\n"
        combined_text += f"--- End of Document: {file.name} ---\n"
    return combined_text

# Initialize session storage
if "curriculum_text" not in st.session_state:
    st.session_state["curriculum_text"] = ""

# Sidebar Setup
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
    weeks_list = [f"Week {i}" for i in range(1, 14)]
    selected_week = st.selectbox("Select Academic Week", weeks_list)

    st.divider()
    st.header("📄 Curriculum Vault")
    uploaded_files = st.file_uploader("Upload Scope & Sequence (PDF/TXT)", type=["pdf", "txt"], accept_multiple_files=True)

    # Process files immediately when uploaded
    if uploaded_files:
        if st.button("💾 Process Uploaded Files"):
            st.session_state["curriculum_text"] = extract_text_from_files(uploaded_files)
            st.success(f"Successfully processed {len(uploaded_files)} file(s)!")

# Main App Tabs
st.title("📚 AI Teacher Assistant Hub")
tab1, tab2, tab3 = st.tabs(["📖 Lesson Planner", "📝 Assessment Creator", "🎯 Support Planner"])

# TAB 1: Lesson Planner
with tab1:
    st.header(f"Planning: {selected_class} — {selected_term}, {selected_week}")
    topic = st.text_input("Topic / Objective (Leave blank to use uploaded Scope & Sequence focus)")
    duration = st.selectbox("Duration", ["45 Minutes", "60 Minutes", "90 Minutes"])
    notes = st.text_area("Specific Section Notes")

    if st.button("🚀 Generate Lesson Plan", type="primary"):
        client = get_gemini_client()
        if client:
            prompt = f"""
            You are an expert curriculum developer. Create a detailed 3-part lesson plan.
            
            Target Section: {selected_class}
            Timeframe: {selected_term}, {selected_week}
            Duration: {duration}
            Topic/Focus: {topic if topic else 'Extract focus from the uploaded curriculum context below.'}
            Section Notes: {notes}

            --- CURRICULUM CONTEXT ---
            {st.session_state['curriculum_text'] if st.session_state['curriculum_text'] else 'Standard Grade 12 English curriculum competencies.'}
            --------------------------

            Format with clear Markdown headings:
            1. Learning Objectives & Success Criteria
            2. Starter / Warm-up Activity (5-10 mins)
            3. Direct Instruction & Check for Understanding (CFU)
            4. Differentiated Practice (Support, Core, Extension)
            5. Plenary / Exit Ticket
            """
            
            with st.spinner("Generating lesson plan..."):
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Generation error: {e}")
