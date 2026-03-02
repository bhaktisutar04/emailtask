# import streamlit as st
# import os
# from datetime import datetime
# from dotenv import load_dotenv
# from core.engine import build_workflow
# from data.database import init_db, log_execution

# load_dotenv()

# # --- Page Setup ---
# st.set_page_config(
#     page_title="AI Task Distribution System",
#     layout="centered"
# )

# init_db()

# # --- Custom Styling ---
# st.markdown("""
# <style>
# .main {
#     background-color: #f8fafc;
# }

# .stTextArea textarea {
#     border-radius: 12px;
#     border: 1px solid #e2e8f0;
#     padding: 15px;
#     font-size: 16px;
# }

# .stButton button {
#     border-radius: 50px;
#     padding: 12px 24px;
#     font-weight: 600;
#     background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
#     color: white;
#     border: none;
# }

# .stButton button:hover {
#     opacity: 0.9;
#     color: white;
# }

# h1 {
#     color: #1e293b;
#     font-weight: 800;
#     letter-spacing: -0.02em;
# }

# .success-box {
#     background-color: #f0fdf4;
#     border: 1px solid #bbf7d0;
#     padding: 20px;
#     border-radius: 12px;
#     color: #166534;
#     font-weight: 600;
#     text-align: center;
# }
# </style>
# """, unsafe_allow_html=True)

# # --- UI Interface ---
# st.title("AI Task Distribution System")
# st.markdown(
#     "Instantly convert meeting discussions into professional corporate directives and notify your team."
# )

# st.divider()

# notes_input = st.text_area(
#     "Meeting Discussion Notes",
#     placeholder="Paste meeting discussion notes here (English, Hindi, or Hinglish)...",
#     height=350,
#     label_visibility="collapsed"
# )

# if st.button("Generate & Send Task Emails", use_container_width=True):

#     if not notes_input.strip():
#         st.warning("Please provide input data to generate tasks.")

#     elif not os.getenv("GROQ_API_KEY"):
#         st.error("System configuration missing (API Key).")

#     else:
#         with st.spinner("Analyzing requirements and dispatching emails..."):
#             try:
#                 # Execution
#                 workflow = build_workflow()

#                 initial_state = {
#                     "input_data": notes_input,
#                     "summary": None,
#                     "assigned_tasks": [],
#                     "raw_llm_output": None,
#                     "parsed_json": None,
#                     "email_status": None,
#                     "sent_to": [],
#                     "failed_to": [],
#                     "history": [],
#                     "errors": [],
#                     "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                 }

#                 result = workflow.invoke(initial_state)

#                 # Persistence & Logging
#                 log_execution(
#                     f"AI-TASK-{datetime.now().strftime('%H%M%S')}",
#                     notes_input,
#                     result
#                 )

#                 # Result Feedback
#                 if result.get("email_status") == "dispatched":
#                     st.markdown(
#                         '<div class="success-box">✅ Task emails successfully delivered to all assigned members.</div>',
#                         unsafe_allow_html=True
#                     )

#                 elif result.get("email_status") == "skipped":
#                     st.info("No actionable tasks identified for Raj, Anjali, Priya, or Amit.")

#                 else:
#                     st.error("Operation failed. Please verify SMTP credentials.")

#             except Exception as e:
#                 st.error("A system error occurred. Please try again.")

# # --- Footer ---

# st.divider()


import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
from core.engine import build_workflow
from data.database import init_db, log_execution

load_dotenv()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Task Distribution System",
    layout="wide"
)

init_db()

# ---------------- CUSTOM WIDTH CONTROL ----------------
st.markdown("""
<style>
.main > div {
    max-width: 1200px;
    padding-left: 2rem;
    padding-right: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
<h1 style='text-align:center; margin-bottom:5px;'>
AI Task Distribution System
</h1>
<p style='text-align:center; color:gray; margin-top:0;'>
Enterprise AI-Powered Task Assignment Engine
</p>
<hr style='margin-top:15px; margin-bottom:25px;'>
""", unsafe_allow_html=True)

# ---------------- MAIN LAYOUT ----------------
col1, col2 = st.columns([1, 1.4], gap="large")

# ================= LEFT PANEL =================
with col1:
    st.markdown("""
    <div style="
        background:white;
        padding:25px;
        border-radius:18px;
        border:1px solid #e5e7eb;
    ">
    <h3 style="margin-top:0;">SYSTEM CONFIGURATION</h3>
    <hr>

    <b>Team Members:</b>
    <ul>
        <li>Raj</li>
        <li>Anjali</li>
        <li>Priya</li>
        <li>Amit</li>
    </ul>

    <p style="color:#b91c1c; font-weight:600;">
    ⚠ Works ONLY for these 4 members.
    Other names will be ignored.
    </p>

    <hr>

    <h4>HOW THE SYSTEM WORKS</h4>

    <p> → Input Meeting Notes → AI Summarization → Extract Tasks (4 members only) </p>
    <p> → Validate & Filter → Send Enterprise Emails → Log Execution</p>
    
    </div>
    """, unsafe_allow_html=True)

# ================= RIGHT PANEL =================
with col2:
    st.markdown("""
    <div style="
        background:white;
        padding:25px;
        border-radius:18px;
        border:1px solid #e5e7eb;
    ">
    <h3 style="margin-top:0;">Meeting Discussion Notes</h3>
    """, unsafe_allow_html=True)

    notes_input = st.text_area(
        "",
        placeholder="Paste meeting discussion notes here...",
        height=260
    )

    st.markdown("<br>", unsafe_allow_html=True)

    generate_clicked = st.button(
        "Generate & Send Task Emails",
        use_container_width=True
    )

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- WORKFLOW EXECUTION ----------------
if generate_clicked:

    if not notes_input.strip():
        st.warning("Please provide meeting discussion notes.")

    elif not os.getenv("GROQ_API_KEY"):
        st.error("System configuration missing (API Key).")

    else:
        with st.spinner("Processing and dispatching emails..."):
            try:
                workflow = build_workflow()

                initial_state = {
                    "input_data": notes_input,
                    "summary": None,
                    "assigned_tasks": [],
                    "raw_llm_output": None,
                    "parsed_json": None,
                    "email_status": None,
                    "sent_to": [],
                    "failed_to": [],
                    "history": [],
                    "errors": [],
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                result = workflow.invoke(initial_state)

                log_execution(
                    f"AI-TASK-{datetime.now().strftime('%H%M%S')}",
                    notes_input,
                    result
                )

                if result.get("email_status") == "dispatched":
                    st.success("✅ Task emails successfully delivered.")

                elif result.get("email_status") == "skipped":
                    st.info("No valid tasks identified for Raj, Anjali, Priya, or Amit.")

                else:
                    st.error("Operation failed. Please verify SMTP credentials.")

            except Exception:
                st.error("A system error occurred. Please try again.")
