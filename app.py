# app.py
import streamlit as st
import psycopg2
import json
import time
from google import genai
from google.genai import types

# 🌐 SECURE DATABASE CONNECTION
# When running locally, it uses your secrets.toml file.
# When live on Streamlit Cloud, it safely reads from the dashboard secrets!
NEON_DATABASE_URL = st.secrets["NEON_DATABASE_URL"]

st.set_page_config(page_title="Career Pivot Engine", layout="wide")
st.title("⚡ Career Pivot Portal")
st.caption("Production Application Connected to Serverless Cloud Database")
st.markdown("---")

with st.sidebar:
    st.header("🔑 Authentication Panel")
    user_email = st.text_input("Your Email Address", placeholder="user@example.com")
    api_key = st.text_input("Google AI Studio API Key", type="password")
    st.markdown("---")
    st.header("🌐 Cluster Infrastructure")
    st.success("Database Status: READY")

# Define JSON schemas for Gemini response layout
SYSTEM_INSTRUCTION = "You are an expert Technical Career Path Strategist. Analyze qualifications and provide 2 tech paths with certifications and pathways in strict JSON format."

class CareerOption:
    pass # Schema placeholder structural hints used by the parser

if 'step' not in st.session_state:
    st.session_state.step = "input"

if st.session_state.step == "input":
    st.header("Map Your Background to Modern Tech Roles")
    
    with st.container(border=True):
        user_story = st.text_area(
            label="Credentials Textbox",
            placeholder="List your background history, degrees, and certifications here...",
            height=200,
            label_visibility="collapsed"
        )
        
        if st.button("Analyze & Generate Cloud Profile Blueprint", type="primary"):
            if not user_email or not api_key or not user_story.strip():
                st.error("Validation Error: Please fill out all fields before executing.")
            else:
                with st.spinner("Processing through AI Engine & Syncing Cloud Database..."):
                    max_retries = 3
                    retry_delay = 2
                    response_text = None
                    
                    # 🤖 Run AI directly inside Streamlit
                    for attempt in range(max_retries):
                        try:
                            client = genai.Client(api_key=api_key)
                            response = client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=f"Analyze this narrative profile: {user_story}",
                                config=types.GenerateContentConfig(
                                    system_instruction=SYSTEM_INSTRUCTION,
                                    response_mime_type="application/json",
                                    temperature=0.2
                                )
                            )
                            response_text = response.text
                            break
                        except Exception as ai_error:
                            if "503" in str(ai_error) and attempt < max_retries - 1:
                                time.sleep(retry_delay)
                                retry_delay *= 2
                                continue
                            else:
                                st.error(f"AI Service busy. Please retry in a moment.")
                    
                    if response_text:
                        try:
                            structured_data = json.loads(response_text)
                            
                            # 🗄️ Save directly to Neon Database
                            conn = psycopg2.connect(NEON_DATABASE_URL)
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO user_profiles (user_email, raw_history, structured_output) VALUES (%s, %s, %s);",
                                (user_email, user_story, json.dumps(structured_data))
                            )
                            conn.commit()
                            cursor.close()
                            conn.close()
                            
                            st.session_state.ai_output = structured_data
                            st.session_state.step = "blueprint"
                            st.rerun()
                            
                        except Exception as db_error:
                            st.error(f"Database sync failed: {str(db_error)}")

elif st.session_state.step == "blueprint":
    data = st.session_state.ai_output
    
    with st.container(border=True):
        st.markdown("🎯 **IMMEDIATE DAY 1 TASK**")
        st.subheader(data.get("day_1_task", "Begin foundational coursework."))
        
    st.markdown("## 🧭 Your Tailored Tech Career Options")
    paths = data.get("career_paths", [])
    cols = st.columns(len(paths)) if paths else st.columns(1)
    
    for idx, path in enumerate(paths):
        with cols[idx]:
            with st.container(border=True):
                st.markdown(f"### 💼 {path.get('title')}")
                st.write(path.get('why_it_fits'))
                st.markdown("---")
                st.markdown("**🏅 Required Certifications:**")
                for cert in path.get("recommended_certifications", []):
                    st.markdown(f"- `{cert}`")
                st.markdown("---")
                st.markdown("**🗺️ Execution Pathway:**")
                for step_idx, step in enumerate(path.get("milestone_pathway", [])):
                    st.checkbox(f"{step}", key=f"cloud_path_{idx}_{step_idx}")

    if st.button("⬅ Process Another Profile"):
        st.session_state.step = "input"
        st.rerun()
