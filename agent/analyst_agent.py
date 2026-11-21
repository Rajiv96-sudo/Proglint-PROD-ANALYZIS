"""
Employee Productivity Analyst Agent powered by Google Gemini.
Correlates Outlook Calendar (Meeting load & Focus time) and Azure DevOps (Commits & PRs),
and evaluates Task Assignment feasibility in real-time when new tasks are created.
"""

import json
from typing import Dict, Any, List
from datetime import date, timedelta
import requests

from config.settings import get_settings
from connectors.outlook_calendar import get_outlook_calendar_metrics
from connectors.azure_devops import get_azure_devops_metrics
from synthetic_data import (
    get_synthetic_calendar,
    get_synthetic_azure_devops,
    load_tasks,
    update_task_feasibility,
    task_matches_employee,
)

SYSTEM_INSTRUCTION = """You are an expert Employee Productivity Analyst Agent.
Your role is to objectively, fairly, and constructively analyze an employee's engineering activity and workload by correlating:
1. Outlook Calendar (Meeting hours, 1:1s, group syncs, recurring meetings, and available deep-work focus hours).
2. Azure DevOps (Git commits, repositories contributed to, Pull Requests created/merged, active coding days).
3. Assigned Tasks (Workload capacity, estimated delivery hours, feasibility vs. remaining focus time).

When analyzing an employee:
- Structure the report clearly:
  1. 📅 Meeting Load & Focus Time (Outlook)
  2. 💻 Code & PR Activity (Azure DevOps)
  3. 📋 Active Tasks & Workload Feasibility
  4. 💡 Productivity Correlation & Actionable Recommendations (e.g. meeting reduction, deep-work protection).
"""


def get_full_employee_productivity_snapshot(employee_email: str, start_date: str = "", end_date: str = "", use_synthetic: bool = True) -> Dict[str, Any]:
    """
    Fetch a combined productivity snapshot across Outlook Calendar, Azure DevOps, and Assigned Tasks.
    """
    if not start_date:
        start_date = str(date.today() - timedelta(days=7))
    if not end_date:
        end_date = str(date.today())

    settings = get_settings()

    if use_synthetic or settings.use_mock_data == "true":
        cal = get_synthetic_calendar(employee_email, start_date, end_date)
        ado = get_synthetic_azure_devops(employee_email, start_date, end_date)
    else:
        cal = get_outlook_calendar_metrics(employee_email, start_date, end_date)
        ado = get_azure_devops_metrics(employee_email, start_date, end_date)

    # Filter assigned tasks for this employee
    all_tasks = load_tasks()
    employee_tasks = [t for t in all_tasks if task_matches_employee(t, employee_email)]

    return {
        "employee_email": employee_email,
        "period": {"start_date": start_date, "end_date": end_date},
        "outlook_calendar": cal,
        "azure_devops": ado,
        "assigned_tasks": employee_tasks,
    }


def _call_gemini(prompt: str, context_data: Dict[str, Any]) -> str:
    settings = get_settings()
    model = settings.gemini_model if settings.gemini_model and "2.5" not in settings.gemini_model else "gemini-flash-lite-latest"
    if not settings.is_gemini_configured:
        return (
            "⚠️ **Gemini API Key is not configured yet.**\n\n"
            "Please add `GEMINI_API_KEY=AIzaSy...` in `c:\\agent\\.env` to enable full AI reasoning."
        )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.gemini_api_key}"

    full_prompt = (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"--- CONTEXT DATA SNAPSHOT ---\n"
        f"{json.dumps(context_data, indent=2)}\n\n"
        f"--- INSTRUCTION ---\n"
        f"{prompt}"
    )

    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048},
    }

    try:
        resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        if resp.status_code == 200:
            candidates = resp.json().get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"]
            return "No response text received from Gemini."
        return f"⚠️ Gemini API Error ({resp.status_code}): {resp.text}"
    except Exception as e:
        return f"⚠️ Network error calling Gemini: {e}"


def audit_pending_tasks_and_deadlines(employee_email: str) -> str:
    """
    Audits an employee's pending tasks based on assigned duration, remaining days to due date,
    and available focus time remaining in their calendar.
    """
    snapshot = get_full_employee_productivity_snapshot(employee_email)
    cal_summary = snapshot["outlook_calendar"].get("summary", {})
    focus_hours = cal_summary.get("estimated_focus_hours_remaining", 40.0)
    meeting_hours = cal_summary.get("total_meeting_hours", 0.0)
    pending_tasks = [t for t in snapshot.get("assigned_tasks", []) if t.get("status") != "Done"]

    if not pending_tasks:
        return f"✅ **No pending tasks found for {employee_email}!** All assigned tasks are marked as Done."

    total_pending_hours = sum(t.get("estimated_hours", 0) for t in pending_tasks)

    prompt = (
        f"Perform an active task audit and schedule tracking for {employee_email}:\n\n"
        f"CALENDAR CONSTRAINTS:\n"
        f"• Total Meeting Hours: {meeting_hours}h\n"
        f"• Available Focus Hours: {focus_hours}h (out of 40h standard week)\n\n"
        f"PENDING TASKS ({len(pending_tasks)} tasks totaling {total_pending_hours} hours):\n"
        f"{json.dumps(pending_tasks, indent=2)}\n\n"
        f"Provide a structured 3-part Task Tracking & Priority Assessment:\n"
        f"1. ⏱️ DURATION & DEADLINE RISK AUDIT: (Compare each pending task's remaining duration to due date against focus hours)\n"
        f"2. 🎯 RECOMMENDED EXECUTION ORDER: (Which task should be prioritized first, second, etc., based on urgency and priority)\n"
        f"3. ⚠️ BOTTLENECK & CAPACITY WARNING: (Explicitly flag if total pending hours ({total_pending_hours}h) exceed remaining focus time ({focus_hours}h), and provide actionable calendar/task triage)."
    )

    return _call_gemini(prompt, snapshot)


def generate_weekend_recognition_content(employee_name: str, employee_email: str, weekend_details: str, hours: float, credits_awarded: float) -> Dict[str, str]:
    """
    Uses Gemini to generate:
    1. A formal Manager Alert Email.
    2. An inspiring, official Certificate Citation.
    """
    prompt = (
        f"You are the Employee Recognition & Well-being Agent.\n"
        f"An employee has worked during non-working days / weekend:\n"
        f"• Employee Name: {employee_name} ({employee_email})\n"
        f"• Hours Logged: {hours} hours\n"
        f"• Credits Awarded: +{credits_awarded} Employee Credits\n"
        f"• Activity Summary: {weekend_details}\n\n"
        f"Please output a valid JSON object with the following exact keys:\n"
        f'{{\n'
        f'  "manager_email_subject": "...",\n'
        f'  "manager_email_body": "...",\n'
        f'  "certificate_citation": "..."\n'
        f'}}\n\n'
        f"Guidelines:\n"
        f"- manager_email_subject: Short and professional alert with employee name and hours.\n"
        f"- manager_email_body: Comprehensive email notifying manager of weekend work, details, credit awarded, and advising compensatory time off.\n"
        f"- certificate_citation: Inspiring, formal 2-sentence award citation praising their commitment, dedication, and impact during critical non-working hours.\n"
        f"Return ONLY the raw JSON object, without backticks."
    )

    raw_response = _call_gemini(prompt, {"employee": employee_email, "hours": hours})
    
    # Try parsing JSON, or provide clean fallback
    try:
        clean = raw_response.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        if clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        parsed = json.loads(clean.strip())
        return parsed
    except Exception:
        return {
            "manager_email_subject": f"[Employee Credit Alert] {employee_name} contributed {hours}h during non-working hours",
            "manager_email_body": (
                f"Hi Engineering Leadership,\n\n"
                f"This is an automated notification from the Productivity Agent. {employee_name} ({employee_email}) "
                f"logged {hours} hours of dedicated engineering activity during non-working days (weekend).\n\n"
                f"• Contribution: {weekend_details}\n"
                f"• Employee Credits Awarded: +{credits_awarded} Credit(s)\n\n"
                f"Recommendation: Please authorize compensatory time off (comp-off) to recognize their dedication and ensure healthy work-life balance.\n\n"
                f"Best regards,\nProglint Productivity Agent"
            ),
            "certificate_citation": (
                f"In distinguished recognition of exceptional dedication and critical engineering support delivered during non-working hours. "
                f"Your commitment to product stability and selfless teamwork exemplifies the highest standards of engineering excellence."
            ),
        }


def evaluate_task_assignment(task: Dict[str, Any], assignees: Any) -> str:
    """
    Called automatically when a new task is assigned in the UI.
    Analyzes schedule feasibility for one or multiple assignees.
    """
    if isinstance(assignees, str):
        assignees_list = [a.strip() for a in assignees.split(",") if a.strip()]
    else:
        assignees_list = [a.strip() for a in assignees if a.strip()]

    if not assignees_list:
        assignees_list = ["developer@proglint.com"]

    multi_context = {}
    summary_text = ""

    for email in assignees_list:
        snap = get_full_employee_productivity_snapshot(email)
        cal = snap["outlook_calendar"].get("summary", {})
        multi_context[email] = {
            "meeting_hours": cal.get("total_meeting_hours", 0.0),
            "focus_hours": cal.get("estimated_focus_hours_remaining", 40.0),
            "active_tasks": len(snap.get("assigned_tasks", [])),
        }
        summary_text += (
            f"• Assignee: {email} | Meetings: {multi_context[email]['meeting_hours']}h | "
            f"Focus Available: {multi_context[email]['focus_hours']}h | Existing Tasks: {multi_context[email]['active_tasks']}\n"
        )

    task_hours = task.get("estimated_hours", 8)
    prompt = (
        f"A new task has just been assigned to: {', '.join(assignees_list)}\n"
        f"• Task Title: {task.get('title')}\n"
        f"• Priority: {task.get('priority')}\n"
        f"• Total Estimated Effort: {task_hours} hours\n"
        f"• Due Date: {task.get('due_date')}\n\n"
        f"Assignees Current Capacity:\n{summary_text}\n"
        f"Provide a concise multi-assignee evaluation:\n"
        f"1. OVERALL FEASIBILITY: [SAFE / AT RISK / OVERLOAD]\n"
        f"2. INDIVIDUAL ASSIGNEE BREAKDOWN: (Assess if each member can take on this load given their meetings)\n"
        f"3. COLLABORATION RECOMMENDATION: (How to split the effort, who should lead, or calendar focus recommendations)."
    )

    evaluation = _call_gemini(prompt, {"task": task, "assignees_capacity": multi_context})
    update_task_feasibility(task.get("id", ""), evaluation[:180] + "...")
    return evaluation


def run_productivity_agent(user_prompt: str, employee_email: str = "rahul@proglint.com", start_date: str = "", end_date: str = "") -> str:
    snapshot = get_full_employee_productivity_snapshot(employee_email, start_date, end_date)
    return _call_gemini(user_prompt, snapshot)


class SimpleChatSession:
    def __init__(self, employee_email: str, start_date: str, end_date: str):
        self.employee_email = employee_email
        self.start_date = start_date
        self.end_date = end_date
        self.history: List[Dict[str, str]] = []

    def send_message(self, message: str) -> Any:
        snapshot = get_full_employee_productivity_snapshot(self.employee_email, self.start_date, self.end_date)
        settings = get_settings()
        model = settings.gemini_model if settings.gemini_model and "2.5" not in settings.gemini_model else "gemini-flash-lite-latest"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.gemini_api_key}"

        self.history.append({"role": "user", "text": message})

        context_prompt = (
            f"{SYSTEM_INSTRUCTION}\n\n"
            f"--- DATA SNAPSHOT FOR {self.employee_email} ---\n"
            f"{json.dumps(snapshot, indent=2)}\n\n"
            f"--- CONVERSATION HISTORY ---\n"
        )
        for h in self.history[:-1]:
            context_prompt += f"{h['role'].upper()}: {h['text']}\n"
        context_prompt += f"USER: {message}\nASSISTANT:"

        payload = {
            "contents": [{"parts": [{"text": context_prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048},
        }

        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
            if resp.status_code == 200:
                candidates = resp.json().get("candidates", [])
                ans = candidates[0]["content"]["parts"][0]["text"] if candidates else "No response generated."
            else:
                ans = f"⚠️ Gemini API Error ({resp.status_code}): {resp.text}"
        except Exception as e:
            ans = f"⚠️ Network error: {e}"

        self.history.append({"role": "assistant", "text": ans})

        class ResponseObj:
            text = ans

        return ResponseObj()


def create_productivity_chat(employee_email: str = "rahul@proglint.com", start_date: str = "", end_date: str = ""):
    return SimpleChatSession(employee_email, start_date, end_date)
