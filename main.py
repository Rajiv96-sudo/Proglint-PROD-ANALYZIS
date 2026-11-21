"""
CLI Runner & Diagnostics check for the Employee Productivity Analyst Agent.
Usage:
  python main.py --check
  python main.py --email developer@proglint.com --start 2026-11-10 --end 2026-11-17
"""

import argparse
import json
from datetime import date, timedelta
from config.settings import get_settings


def print_access_status() -> None:
    s = get_settings()
    print("=" * 72)
    print("  EMPLOYEE PRODUCTIVITY AGENT - ACCESS & CONFIGURATION CHECK")
    print("=" * 72)
    print(f"  Data Mode (USE_MOCK_DATA) : {s.use_mock_data.upper()}")
    print(f"  1. Gemini API Key         : {'[CONFIGURED]' if s.is_gemini_configured else '[MISSING -> Set GEMINI_API_KEY in .env]'}")
    print(f"  2. Outlook Calendar API   : {'[CONFIGURED]' if s.is_outlook_configured else '[MISSING -> Using Mock Data until AZURE_TENANT_ID/CLIENT_ID set]'}")
    print(f"  3. Azure DevOps API       : {'[CONFIGURED]' if s.is_ado_configured else f'[MISSING -> Using Mock Data until ADO_PAT set for {s.ado_org_url}]'}")
    print("=" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(description="Employee Productivity Analyst Agent CLI")
    parser.add_argument("--check", action="store_true", help="Check which API credentials are configured")
    parser.add_argument("--email", type=str, default="developer@proglint.com", help="Employee email address")
    parser.add_argument("--start", type=str, default=str(date.today() - timedelta(days=7)), help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default=str(date.today()), help="End date (YYYY-MM-DD)")
    parser.add_argument("--json", action="store_true", help="Print raw JSON snapshot from connectors")
    args = parser.parse_args()

    print_access_status()
    if args.check:
        return

    try:
        from agent.analyst_agent import get_full_employee_productivity_snapshot, run_productivity_agent
    except ImportError as e:
        print(f"\n❌ Missing required Python library: {e}")
        print("👉 Please install dependencies by running:")
        print("   pip install -r requirements.txt\n")
        return

    snapshot = get_full_employee_productivity_snapshot(args.email, args.start, args.end)
    if args.json:
        print(json.dumps(snapshot, indent=2))
        return

    cal = snapshot["outlook_calendar"].get("summary", {})
    ado = snapshot["azure_devops"].get("summary", {})

    print(f"\n📊 SNAPSHOT FOR: {args.email} ({args.start} to {args.end})")
    print(f"  • Outlook Meetings : {cal.get('total_meeting_hours', 0)} hrs across {cal.get('total_meetings_count', 0)} meetings (Focus time left: {cal.get('estimated_focus_hours_remaining', 0)} hrs)")
    print(f"  • Azure DevOps     : {ado.get('total_commits', 0)} commits across {ado.get('repositories_contributed', 0)} repos")
    print("\n🤖 GEMINI ANALYST REPORT:")
    print("-" * 72)

    prompt = (
        f"Analyze the productivity for {args.email} from {args.start} to {args.end}. "
        f"Summarize meeting hours and commits, and explain how meeting load impacted focus time."
    )
    print(run_productivity_agent(prompt, employee_email=args.email, start_date=args.start, end_date=args.end))


if __name__ == "__main__":
    main()
