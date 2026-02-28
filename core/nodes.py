import os
import json
import smtplib
import re
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

# --- SaaS-Level HTML Template ---

def build_enterprise_html(person: str, tasks: list) -> str:
    """Renders a SaaS-style task assignment email."""
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

# --- Workflow Nodes ---

def summarize_node(state: WorkflowState) -> WorkflowState:
    llm = get_llm()
    prompt = f"Summarize these meeting topics formally (No tasks/names):\n\n{state['input_data']}"
    response = llm.invoke([HumanMessage(content=prompt)])
    state["summary"] = response.content
    state["history"].append("summarize")
    return state

def extract_tasks_node(state: WorkflowState) -> WorkflowState:
    """Robust extraction of tasks with strict JSON schema enforcement and retry logic."""
    llm = get_llm()
    
    prompt = f"""
You are a strict enterprise task extraction engine. Your sole function is to parse meeting notes and extract tasks — but ONLY for people whose names exactly match the ALLOWED TEAM MEMBERS list below.

ALLOWED TEAM MEMBERS (case-sensitive, exact match required):
{', '.join(TEAM_MEMBERS)}

YOUR RULES — FOLLOW WITHOUT EXCEPTION:

1. ONLY extract tasks where the assigned person's name exactly matches one of the ALLOWED TEAM MEMBERS listed above.
2. If a name in the input does NOT appear in the ALLOWED TEAM MEMBERS list, COMPLETELY IGNORE that task. Do not include it. Do not reassign it.
3. DO NOT reassign any task to a different person. If a person is not allowed, the task is dropped — not moved.
4. DO NOT fabricate, infer, or invent tasks that are not explicitly stated in the input.
5. DO NOT produce placeholder or explanatory text such as "Priya is not assigned any tasks" or "No tasks found for Rohit".
6. If no valid tasks exist for allowed team members, return exactly: []
7. Your output MUST be a valid JSON array. Nothing else. No markdown. No code fences. No explanation text. No preamble.

OUTPUT FORMAT (strict):
[
  {{
    "person": "<Exact name from ALLOWED TEAM MEMBERS>",
    "formal_task": "<Task rewritten in formal corporate English>",
    "deadline": "<Specific date or 'To Be Confirmed'>",
    "priority": "<High | Medium | Low | Normal>"
  }}
]

EXAMPLES:

Example 1:
ALLOWED TEAM MEMBERS: Raj, Anjali, Priya, Amit
Input: "Rohit should handle the DevOps migration."
Output: []

Example 2:
ALLOWED TEAM MEMBERS: Raj, Anjali, Priya, Amit
Input: "Raj needs to complete the API documentation by Friday. Rohit will manage server setup."
Output:
[
  {{
    "person": "Raj",
    "formal_task": "Complete and finalize the API documentation.",
    "deadline": "Friday",
    "priority": "Normal"
  }}
]

Example 3:
ALLOWED TEAM MEMBERS: Raj, Anjali, Priya, Amit
Input: "Sneha and Vikram will handle client onboarding."
Output: []

NOW PROCESS THE FOLLOWING INPUT:
{state['input_data']}
"""
    
    def parse_with_fallback(text):
        # 1. Try direct json.loads
        try:
            return json.loads(text.strip())
        except: pass
        
        # 2. Try regex extraction
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except: pass
        return None

    # First Attempt
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()
    extracted = parse_with_fallback(content)
    
    # Retry Logic
    if extracted is None:
        retry_prompt = f"INVALID JSON RECEIVED. Previous output: {content}\n\nReturn ONLY a valid JSON array. No explanation."
        response = llm.invoke([HumanMessage(content=retry_prompt)])
        content = response.content.strip()
        extracted = parse_with_fallback(content)

    if extracted is not None:
        processed_tasks = []
        for t in extracted:
            name = str(t.get("person", "")).strip().capitalize()
            if name in TEAM_MEMBERS:
                t["person"] = name
                processed_tasks.append(t)
        
        state["assigned_tasks"] = processed_tasks
        if len(processed_tasks) > 0:
            state["email_status"] = "ready"
    else:
        state["assigned_tasks"] = []
        state.setdefault("errors", []).append(f"JSON Parsing Failure. Raw output: {content}")

    state["history"].append("extract_tasks")
    return state

def send_email_node(state: WorkflowState) -> WorkflowState:
    """Dispatches individual task emails to team members."""
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
            if not recipient: continue
            
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
