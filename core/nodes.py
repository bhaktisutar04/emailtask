
import os
import json
import smtplib
import re
import dateparser
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langchain_core.messages import HumanMessage
from core.state import WorkflowState
from core.models import get_llm

# --- Configuration ---
TEAM_MEMBERS = ["Raj", "Anjali", "Priya", "Amit"]
TEAM_EMAILS = {
    "Raj": os.getenv("EMAIL_RAJ", "sutarbhakti2004@gmail.com"),
    "Anjali": os.getenv("EMAIL_ANJALI", "sutarbhakti2004@gmail.com"),
    "Priya": os.getenv("EMAIL_PRIYA", "sutarbhakti2004@gmail.com"),
    "Amit": os.getenv("EMAIL_AMIT", "sutarbhakti2004@gmail.com")
}

# ---------------------------------------------------
# DEADLINE NORMALIZATION (SMART VERSION)
# ---------------------------------------------------

def normalize_deadline(deadline_text: str) -> str:
    """
    Converts natural language deadlines into
    standardized datetime format (YYYY-MM-DD HH:MM).
    """
    if not deadline_text or deadline_text.lower() == "to be confirmed":
        return "To Be Confirmed"

    parsed_date = dateparser.parse(
        deadline_text,
        settings={
            "PREFER_DATES_FROM": "future",
            "RETURN_AS_TIMEZONE_AWARE": False
        }
    )

    if parsed_date:
        return parsed_date.strftime("%Y-%m-%d %H:%M")

    return "To Be Confirmed"

# ---------------------------------------------------
# EMAIL TEMPLATE
# ---------------------------------------------------

def build_enterprise_html(person: str, tasks: list) -> str:
    task_html = ""
    for t in tasks:
        priority_color = {
            "High": "#b91c1c",
            "Medium": "#d97706",
            "Low": "#059669",
            "Normal": "#4b5563"
        }.get(t['priority'], "#4b5563")
        
        task_html += f"""
        <div style="background: #fdfdfd; border: 1px solid #eaebed; border-radius: 12px; padding: 20px; margin: 16px 0; border-left: 4px solid #1e3a8a;">
            <div style="display: inline-block; padding: 4px 12px; border-radius: 20px; color: #ffffff; background: {priority_color}; font-size: 11px; font-weight: bold; text-transform: uppercase; margin-bottom: 12px;">
                {t['priority']} Priority
            </div>
            <p style="margin: 0; font-size: 16px; color: #1e293b; font-weight: 600;">{t['formal_task']}</p>
            <p style="margin: 12px 0 0; font-size: 13px; color: #64748b;">📅 <b>Deadline:</b> {t['deadline']}</p>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="background-color: #f4f6f8; font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 40px 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05);">
            <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 40px 32px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700;">Task Directive</h1>
                <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0; font-size: 14px;">Official PMO Notification</p>
            </div>
            <div style="padding: 40px 32px;">
                <p style="font-size: 18px; color: #111827; margin-top: 0; font-weight: 600;">Hi {person},</p>
                <p style="color: #4b5563; font-size: 15px; line-height: 1.6;">The following directives have been issued to you based on the recent project review:</p>
                {task_html}
                <p style="color: #4b5563; font-size: 14px; margin-top: 32px;">Kindly acknowledge receipt of these tasks and project timelines.</p>
            </div>
            <div style="background: #f9fafb; padding: 24px; border-top: 1px solid #f3f4f6; text-align: center;">
                <p style="color: #94a3b8; font-size: 11px; margin: 0; text-transform: uppercase; letter-spacing: 0.05em;">AI PMO System | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    </body>
    </html>
    """

# ---------------------------------------------------
# WORKFLOW NODES
# ---------------------------------------------------

def summarize_node(state: WorkflowState) -> WorkflowState:
    llm = get_llm()
    prompt = f"Summarize these meeting topics formally (No tasks/names):\n\n{state['input_data']}"
    response = llm.invoke([HumanMessage(content=prompt)])
    state["summary"] = response.content
    state["history"].append("summarize")
    return state


def extract_tasks_node(state: WorkflowState) -> WorkflowState:
    llm = get_llm()

    prompt = f"""
Extract tasks ONLY for: {', '.join(TEAM_MEMBERS)}

Return STRICT JSON array only.

FORMAT:
[
  {{
    "person": "Name",
    "formal_task": "Formal task",
    "deadline": "Natural deadline text",
    "priority": "High | Medium | Low | Normal"
  }}
]

Input:
{state['input_data']}
"""

    def parse_with_fallback(text):
        try:
            return json.loads(text.strip())
        except:
            match = re.search(r"\[.*\]", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    return None
        return None

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()
    extracted = parse_with_fallback(content)

    if extracted is None:
        state["assigned_tasks"] = []
        state.setdefault("errors", []).append(f"JSON Parsing Failure: {content}")
    else:
        processed_tasks = []
        for t in extracted:
            name = str(t.get("person", "")).strip().capitalize()
            if name in TEAM_MEMBERS:
                t["person"] = name

                # 🔥 SMART DEADLINE NORMALIZATION HERE
                t["deadline"] = normalize_deadline(t.get("deadline", ""))

                processed_tasks.append(t)

        state["assigned_tasks"] = processed_tasks
        if processed_tasks:
            state["email_status"] = "ready"

    state["history"].append("extract_tasks")
    return state


def send_email_node(state: WorkflowState) -> WorkflowState:
    if not state.get("assigned_tasks"):
        state["email_status"] = "skipped"
        return state

    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        state["email_status"] = "failed"
        return state

    grouped = {}
    for t in state["assigned_tasks"]:
        grouped.setdefault(t["person"], []).append(t)

    state["sent_to"] = []

    try:
        server = smtplib.SMTP(os.getenv("SMTP_SERVER", "smtp.gmail.com"), 587)
        server.starttls()
        server.login(sender_email, sender_password)

        for person, tasks in grouped.items():
            recipient = TEAM_EMAILS.get(person)
            if not recipient:
                continue

            msg = MIMEMultipart()
            msg['From'] = f"Project Management Office <{sender_email}>"
            msg['To'] = recipient
            msg['Subject'] = f"Directives Issued: {len(tasks)} New Assigned Tasks"

            msg.attach(MIMEText(build_enterprise_html(person, tasks), "html"))
            server.send_message(msg)
            state["sent_to"].append(person)

        server.quit()
        state["email_status"] = "dispatched"

    except Exception as e:
        state["email_status"] = "failed"
        state.setdefault("errors", []).append(str(e))

    state["history"].append("send_email")
    return state
