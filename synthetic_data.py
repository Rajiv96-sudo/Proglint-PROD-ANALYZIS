"""
Synthetic Data Engine for Employee Productivity Analyst.
Generates realistic Outlook calendar meetings, Azure DevOps commits & PRs,
and persistent assigned tasks for different engineering personas.
"""

import json
import os
from datetime import date, timedelta
from typing import Dict, Any, List

TASKS_STORE_FILE = os.path.join(os.path.dirname(__file__), "synthetic_tasks.json")

PERSONAS = {
    "rahul@proglint.com": {
        "name": "Rahul Sharma",
        "role": "Senior Backend Engineer",
        "scenario": "Meeting Overload",
        "avatar": "👨‍💻",
        "base_meeting_hours": 24.5,
        "base_commits": 5,
        "base_prs": 2,
    },
    "priya@proglint.com": {
        "name": "Priya Patel",
        "role": "Core Systems Engineer",
        "scenario": "Deep Work Flow",
        "avatar": "👩‍💻",
        "base_meeting_hours": 7.0,
        "base_commits": 32,
        "base_prs": 6,
    },
    "amit@proglint.com": {
        "name": "Amit Verma",
        "role": "Tech Lead & Architect",
        "scenario": "Balanced & PR Reviews",
        "avatar": "👨‍💼",
        "base_meeting_hours": 15.0,
        "base_commits": 14,
        "base_prs": 8,
    },
}


def get_default_tasks() -> List[Dict[str, Any]]:
    return [
        {
            "id": "TASK-101",
            "title": "Migrate Payment Webhook to Azure Service Bus",
            "assignee": "rahul@proglint.com",
            "priority": "High",
            "status": "In Progress",
            "estimated_hours": 12,
            "created_date": str(date.today() - timedelta(days=3)),
            "due_date": str(date.today() + timedelta(days=2)),
            "agent_feasibility": "At Risk - Rahul has only 15.5h focus time remaining due to 24.5h meetings.",
        },
        {
            "id": "TASK-102",
            "title": "Implement Redis Caching Layer for Employee Analytics API",
            "assignee": "priya@proglint.com",
            "priority": "Highest",
            "status": "Done",
            "estimated_hours": 8,
            "created_date": str(date.today() - timedelta(days=5)),
            "due_date": str(date.today() - timedelta(days=1)),
            "agent_feasibility": "Delivered on Schedule - 33h focus time allowed uninterrupted implementation.",
        },
        {
            "id": "TASK-103",
            "title": "Architecture Review: OAuth2 Service Principal Token Rotation",
            "assignee": "amit@proglint.com",
            "priority": "Medium",
            "status": "Done",
            "estimated_hours": 6,
            "created_date": str(date.today() - timedelta(days=4)),
            "due_date": str(date.today()),
            "agent_feasibility": "Completed - Aligned with Tech Lead review schedule.",
        },
        {
            "id": "TASK-104",
            "title": "Optimize SQL Connection Pool for Azure Database PostgreSQL",
            "assignee": "priya@proglint.com",
            "priority": "High",
            "status": "In Progress",
            "estimated_hours": 10,
            "created_date": str(date.today() - timedelta(days=2)),
            "due_date": str(date.today() + timedelta(days=3)),
            "agent_feasibility": "On Track - Healthy deep-work bandwidth available.",
        },
    ]


def load_tasks() -> List[Dict[str, Any]]:
    if os.path.exists(TASKS_STORE_FILE):
        try:
            with open(TASKS_STORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    tasks = get_default_tasks()
    save_tasks(tasks)
    return tasks


def save_tasks(tasks: List[Dict[str, Any]]) -> None:
    try:
        with open(TASKS_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2)
    except Exception:
        pass


def add_synthetic_task(title: str, assignees: List[str], priority: str, estimated_hours: int, due_date: str) -> Dict[str, Any]:
    tasks = load_tasks()
    new_id = f"TASK-{100 + len(tasks) + 1}"
    if isinstance(assignees, str):
        assignees_list = [a.strip() for a in assignees.split(",") if a.strip()]
    else:
        assignees_list = [a.strip() for a in assignees if a.strip()]

    new_task = {
        "id": new_id,
        "title": title,
        "assignee": ", ".join(assignees_list),
        "assignees": assignees_list,
        "priority": priority,
        "status": "Assigned",
        "estimated_hours": estimated_hours,
        "created_date": str(date.today()),
        "due_date": due_date,
        "agent_feasibility": "Pending Agent Evaluation...",
    }
    tasks.insert(0, new_task)
    save_tasks(tasks)
    return new_task


def task_matches_employee(task: Dict[str, Any], employee_email: str) -> bool:
    target = employee_email.lower().strip()
    assignees = task.get("assignees", [])
    if assignees:
        return any(target == a.lower().strip() for a in assignees)
    return target in task.get("assignee", "").lower()


def update_task_feasibility(task_id: str, evaluation_text: str) -> None:
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["agent_feasibility"] = evaluation_text
            break
    save_tasks(tasks)


def delete_task(task_id: str) -> None:
    tasks = load_tasks()
    tasks = [t for t in tasks if t.get("id") != task_id]
    save_tasks(tasks)


def update_task_status(task_id: str, new_status: str) -> None:
    tasks = load_tasks()
    for t in tasks:
        if t.get("id") == task_id:
            t["status"] = new_status
            break
    save_tasks(tasks)


def reset_tasks() -> None:
    save_tasks(get_default_tasks())


def get_all_assignees() -> List[str]:
    tasks = load_tasks()
    emails = set(PERSONAS.keys())
    for t in tasks:
        for a in t.get("assignees", []):
            if a:
                emails.add(a.lower().strip())
        if t.get("assignee"):
            for a in t["assignee"].split(","):
                if a.strip():
                    emails.add(a.lower().strip())
    return sorted(list(emails))


def get_synthetic_calendar(employee_email: str, start_date: str, end_date: str) -> Dict[str, Any]:
    p = PERSONAS.get(employee_email.lower(), {
        "name": employee_email.split("@")[0].capitalize(),
        "role": "Software Engineer",
        "base_meeting_hours": 14.0,
        "base_commits": 16,
    })

    meeting_hours = p.get("base_meeting_hours", 14.0)
    focus_hours = max(40.0 - meeting_hours, 0.0)

    if meeting_hours > 20:
        breakdown = [
            {"subject": "Daily Standup & Blockers", "duration_hours": 2.5, "type": "Recurring Group", "occurrences": 5},
            {"subject": "Cross-Team Architecture Sync", "duration_hours": 4.0, "type": "Ad-hoc Group", "occurrences": 2},
            {"subject": "Sprint Grooming & Poker", "duration_hours": 3.5, "type": "Recurring Group", "occurrences": 2},
            {"subject": "Customer Incident Triage", "duration_hours": 4.5, "type": "Ad-hoc Group", "occurrences": 3},
            {"subject": "Manager 1:1 Catchup", "duration_hours": 1.5, "type": "1:1", "occurrences": 1},
            {"subject": "Company All Hands", "duration_hours": 2.0, "type": "Recurring Group", "occurrences": 1},
            {"subject": "Vendor Integration Review", "duration_hours": 3.5, "type": "Ad-hoc Group", "occurrences": 2},
            {"subject": "Team Retrospective", "duration_hours": 3.0, "type": "Recurring Group", "occurrences": 1},
        ]
    elif meeting_hours < 10:
        breakdown = [
            {"subject": "Daily Standup", "duration_hours": 2.5, "type": "Recurring Group", "occurrences": 5},
            {"subject": "Manager 1:1", "duration_hours": 1.0, "type": "1:1", "occurrences": 1},
            {"subject": "Sprint Planning", "duration_hours": 2.0, "type": "Recurring Group", "occurrences": 1},
            {"subject": "Tech Design Sync", "duration_hours": 1.5, "type": "1:1", "occurrences": 1},
        ]
    else:
        breakdown = [
            {"subject": "Daily Standup", "duration_hours": 2.5, "type": "Recurring Group", "occurrences": 5},
            {"subject": "Sprint Planning & Backlog", "duration_hours": 3.0, "type": "Recurring Group", "occurrences": 1},
            {"subject": "Pull Request Architecture Reviews", "duration_hours": 4.5, "type": "1:1", "occurrences": 3},
            {"subject": "Engineering Leadership Sync", "duration_hours": 2.5, "type": "Group", "occurrences": 2},
            {"subject": "Mentoring & 1:1s", "duration_hours": 2.5, "type": "1:1", "occurrences": 3},
        ]

    return {
        "source": "Synthetic Outlook Calendar Engine",
        "employee_name": p["name"],
        "employee_email": employee_email,
        "period": {"start_date": start_date, "end_date": end_date},
        "summary": {
            "total_meetings_count": len(breakdown) * 2,
            "total_meeting_hours": round(meeting_hours, 1),
            "standard_work_hours": 40.0,
            "estimated_focus_hours_remaining": round(focus_hours, 1),
            "meeting_load_percentage": round((meeting_hours / 40.0) * 100, 1),
        },
        "meetings_breakdown": breakdown,
    }


def get_synthetic_azure_devops(employee_email: str, start_date: str, end_date: str) -> Dict[str, Any]:
    p = PERSONAS.get(employee_email.lower(), {
        "name": employee_email.split("@")[0].capitalize(),
        "base_commits": 16,
        "base_prs": 4,
    })

    commits_count = p.get("base_commits", 16)
    prs_count = p.get("base_prs", 4)

    return {
        "source": "Synthetic Azure DevOps Engine (dev.azure.com/proglint)",
        "organization": "https://dev.azure.com/proglint",
        "employee_name": p["name"],
        "employee_email": employee_email,
        "period": {"start_date": start_date, "end_date": end_date},
        "summary": {
            "total_commits": commits_count,
            "repositories_contributed": 3,
            "pull_requests_created": prs_count,
            "pull_requests_merged": max(prs_count - 1, 1),
            "pull_requests_active": 1,
            "active_coding_days": min(commits_count, 5),
            "lines_added_estimate": commits_count * 45,
            "lines_deleted_estimate": commits_count * 12,
        },
        "recent_commits": [
            {
                "repo": "proglint-core-api",
                "commit_id": "8f1a23c",
                "date": f"{end_date}T16:15:00Z",
                "comment": f"feat(service): implement async event streaming for {p['name']}",
            },
            {
                "repo": "proglint-core-api",
                "commit_id": "4d9b110",
                "date": f"{end_date}T11:40:00Z",
                "comment": "fix(db): optimize connection pool parameters to prevent timeout",
            },
            {
                "repo": "proglint-web-dashboard",
                "commit_id": "c12e78a",
                "date": f"{start_date}T14:30:00Z",
                "comment": "refactor(ui): streamline user metrics caching policy",
            },
        ],
    }

