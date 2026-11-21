"""
Weekend & Overtime Credit Engine.
Calculates Weekly and Monthly weekend/overtime hours and credits,
and generates clean, minimalist Certificates and Manager Alerts.
"""

import json
import os
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any, List

LEDGER_FILE = os.path.join(os.path.dirname(__file__), "credits_ledger.json")


def load_ledger() -> Dict[str, Any]:
    if os.path.exists(LEDGER_FILE):
        try:
            with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Default starter data with week/month timestamps
    today = date.today()
    default_data = {
        "rahul@proglint.com": {
            "employee_name": "Rahul Sharma",
            "total_credits": 3.0,
            "events": [
                {
                    "date": str(today - timedelta(days=6)),
                    "day_name": "Saturday",
                    "hours": 6.5,
                    "credits_awarded": 1.0,
                    "activity_type": "Production Hotfix",
                    "details": "Resolved DB connection pool timeout",
                    "month": today.strftime("%Y-%m"),
                    "week": today.strftime("%Y-W%W"),
                },
                {
                    "date": str(today - timedelta(days=7)),
                    "day_name": "Sunday",
                    "hours": 5.5,
                    "credits_awarded": 1.0,
                    "activity_type": "Incident Standby",
                    "details": "Supported auth gateway release",
                    "month": today.strftime("%Y-%m"),
                    "week": today.strftime("%Y-W%W"),
                },
                {
                    "date": str(today - timedelta(days=14)),
                    "day_name": "Sunday",
                    "hours": 4.0,
                    "credits_awarded": 1.0,
                    "activity_type": "Data Migration",
                    "details": "Executed offline Redis sync",
                    "month": today.strftime("%Y-%m"),
                    "week": (today - timedelta(days=7)).strftime("%Y-W%W"),
                },
            ],
        },
        "priya@proglint.com": {
            "employee_name": "Priya Patel",
            "total_credits": 2.0,
            "events": [
                {
                    "date": str(today - timedelta(days=6)),
                    "day_name": "Saturday",
                    "hours": 8.0,
                    "credits_awarded": 1.0,
                    "activity_type": "Pipeline Deployment",
                    "details": "Deployed PostgreSQL cluster upgrade",
                    "month": today.strftime("%Y-%m"),
                    "week": today.strftime("%Y-W%W"),
                },
                {
                    "date": str(today - timedelta(days=13)),
                    "day_name": "Saturday",
                    "hours": 7.0,
                    "credits_awarded": 1.0,
                    "activity_type": "API Maintenance",
                    "details": "Security patch release",
                    "month": today.strftime("%Y-%m"),
                    "week": (today - timedelta(days=7)).strftime("%Y-W%W"),
                },
            ],
        },
        "amit@proglint.com": {
            "employee_name": "Amit Verma",
            "total_credits": 1.5,
            "events": [
                {
                    "date": str(today - timedelta(days=7)),
                    "day_name": "Sunday",
                    "hours": 6.0,
                    "credits_awarded": 1.0,
                    "activity_type": "Architecture Review",
                    "details": "Reviewed infra DR readiness",
                    "month": today.strftime("%Y-%m"),
                    "week": today.strftime("%Y-W%W"),
                }
            ],
        },
    }
    save_ledger(default_data)
    return default_data


def save_ledger(data: Dict[str, Any]) -> None:
    try:
        with open(LEDGER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def calculate_period_summary(employee_email: str, period_type: str = "Weekly") -> Dict[str, Any]:
    """
    Calculates weekend/overtime hours and credits on a Weekly or Monthly cadence.
    """
    ledger = load_ledger()
    emp_record = ledger.get(employee_email.lower().strip(), {
        "employee_name": employee_email.split("@")[0].capitalize(),
        "total_credits": 0.0,
        "events": [],
    })

    events = emp_record.get("events", [])
    today = date.today()
    current_week = today.strftime("%Y-W%W")
    current_month = today.strftime("%Y-%m")

    if period_type.lower() == "weekly":
        filtered = [e for e in events if e.get("week") == current_week or (today - date.fromisoformat(e.get("date", str(today)))).days <= 7]
        period_label = f"Week {today.strftime('%W')}, {today.strftime('%Y')}"
    else:  # Monthly
        filtered = [e for e in events if e.get("month") == current_month or (today - date.fromisoformat(e.get("date", str(today)))).days <= 30]
        period_label = today.strftime("%B %Y")

    total_hours = sum(e.get("hours", 0.0) for e in filtered)
    total_credits = sum(e.get("credits_awarded", 0.0) for e in filtered)

    return {
        "employee_name": emp_record.get("employee_name", employee_email.split("@")[0].capitalize()),
        "employee_email": employee_email,
        "period_type": period_type,
        "period_label": period_label,
        "total_hours": round(total_hours, 1),
        "total_credits": round(total_credits, 1),
        "days_worked_count": len(filtered),
        "events": filtered,
    }


def award_employee_credit(employee_email: str, employee_name: str, day_name: str, hours: float, activity_type: str, details: str) -> Dict[str, Any]:
    ledger = load_ledger()
    emp_key = employee_email.lower().strip()
    today = date.today()

    if emp_key not in ledger:
        ledger[emp_key] = {
            "employee_name": employee_name,
            "total_credits": 0.0,
            "events": [],
        }

    credit_amount = 1.0 if hours >= 4.0 else 0.5
    cert_id = f"CERT-{today.strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"

    new_event = {
        "date": str(today),
        "day_name": day_name,
        "hours": round(hours, 1),
        "credits_awarded": credit_amount,
        "activity_type": activity_type,
        "details": details,
        "certificate_id": cert_id,
        "month": today.strftime("%Y-%m"),
        "week": today.strftime("%Y-W%W"),
    }

    ledger[emp_key]["events"].insert(0, new_event)
    ledger[emp_key]["total_credits"] = round(ledger[emp_key]["total_credits"] + credit_amount, 1)

    save_ledger(ledger)
    return new_event


def generate_simple_certificate_html(employee_name: str, period_type: str, period_label: str, total_hours: float, credits_earned: float, certificate_id: str) -> str:
    """
    Generates a clean, simple, and elegant certificate without excessive text.
    """
    today_str = date.today().strftime("%B %d, %Y")
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
    body {{
        margin: 0;
        background: #F8FAFC;
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 20px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    .cert-card {{
        background: #FFFFFF;
        width: 100%;
        max-width: 720px;
        border: 4px solid #0F172A;
        border-radius: 12px;
        padding: 40px 35px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.08);
        text-align: center;
        box-sizing: border-box;
    }}
    .cert-org {{
        font-size: 13px;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: #64748B;
        font-weight: 700;
        margin-bottom: 8px;
    }}
    .cert-heading {{
        font-size: 26px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: 0.5px;
        margin: 0 0 20px 0;
    }}
    .cert-sub {{
        font-size: 14px;
        color: #64748B;
        margin-bottom: 8px;
    }}
    .cert-name {{
        font-size: 30px;
        font-weight: 800;
        color: #2563EB;
        margin-bottom: 20px;
    }}
    .cert-citation {{
        font-size: 15px;
        color: #334155;
        max-width: 540px;
        margin: 0 auto 25px auto;
        line-height: 1.5;
    }}
    .stats-row {{
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-bottom: 30px;
    }}
    .stat-box {{
        background: #F1F5F9;
        border-radius: 8px;
        padding: 12px 24px;
        min-width: 130px;
    }}
    .stat-num {{
        font-size: 22px;
        font-weight: 800;
        color: #0F172A;
    }}
    .stat-tag {{
        font-size: 11px;
        text-transform: uppercase;
        color: #64748B;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-top: 2px;
    }}
    .cert-footer {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-top: 1px solid #E2E8F0;
        padding-top: 20px;
        margin-top: 15px;
    }}
    .sig {{
        text-align: left;
    }}
    .sig-right {{
        text-align: right;
    }}
    .sig-name {{
        font-size: 13px;
        font-weight: 700;
        color: #0F172A;
    }}
    .sig-role {{
        font-size: 11px;
        color: #64748B;
    }}
    .cert-badge {{
        background: #FEF3C7;
        color: #B45309;
        font-size: 11px;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
        border: 1px solid #FDE68A;
        display: inline-block;
    }}
</style>
</head>
<body>
<div class="cert-card">
    <div class="cert-org">PROGLINT ENGINEERING</div>
    <div class="cert-heading">Certificate of Appreciation</div>
    
    <div class="cert-sub">Proudly presented to</div>
    <div class="cert-name">{employee_name}</div>
    
    <div class="cert-citation">
        In recognition of dedicated weekend contributions during <strong>{period_label}</strong>.
    </div>
    
    <div class="stats-row">
        <div class="stat-box">
            <div class="stat-num">{total_hours}h</div>
            <div class="stat-tag">{period_type} Overtime</div>
        </div>
        <div class="stat-box">
            <div class="stat-num">+{credits_earned}</div>
            <div class="stat-tag">Credits Awarded</div>
        </div>
        <div class="stat-box">
            <div class="stat-num">{today_str}</div>
            <div class="stat-tag">Issue Date</div>
        </div>
    </div>
    
    <div class="cert-footer">
        <div class="sig">
            <div class="sig-name">Productivity Agent</div>
            <div class="sig-role">Automated Audit & Verification</div>
        </div>
        <div class="cert-badge">COMP-OFF ELIGIBLE</div>
        <div class="sig-right">
            <div class="sig-name">Engineering Leadership</div>
            <div class="sig-role">ID: {certificate_id}</div>
        </div>
    </div>
</div>
</body>
</html>"""
