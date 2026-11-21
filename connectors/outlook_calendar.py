"""
Outlook Calendar Connector via Microsoft Graph API.
Supports both:
1. App-Only Access (Client Secret - if configured & active)
2. Interactive / Device Code Login (No Client Secret required; caches tokens locally so they don't expire!)
"""

import os
import atexit
from datetime import datetime
from typing import Dict, Any, List
import msal
import requests
from config.settings import get_settings

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", ".msal_token_cache.bin")


def _get_token_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache.deserialize(f.read())
        except Exception:
            pass

    def _save_cache():
        if cache.has_state_changed:
            try:
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    f.write(cache.serialize())
            except Exception:
                pass

    atexit.register(_save_cache)
    return cache


def _acquire_graph_token(settings) -> Dict[str, Any]:
    """
    Acquire Microsoft Graph access token.
    First tries Client Secret if present; if expired or not set, uses PublicClient flow (device code / cached token).
    """
    authority = f"https://login.microsoftonline.com/{settings.azure_tenant_id}"
    cache = _get_token_cache()

    # 1. If Client Secret is provided, try Confidential Client first
    if settings.azure_client_secret:
        confidential_app = msal.ConfidentialClientApplication(
            client_id=settings.azure_client_id,
            client_credential=settings.azure_client_secret,
            authority=authority,
        )
        token_res = confidential_app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" in token_res:
            return token_res
        # If secret is expired or rejected, log note and fall through to interactive/device flow
        err = token_res.get("error_description", "")
        if "AADSTS7000222" in err or "expired" in err.lower():
            print("\n⚠️ Note: AZURE_CLIENT_SECRET has expired. Falling back to Microsoft Device/Interactive sign-in...")

    # 2. Public Client Application (Device Code / Browser flow - NO SECRET NEEDED)
    public_app = msal.PublicClientApplication(
        client_id=settings.azure_client_id,
        authority=authority,
        token_cache=cache,
    )

    scopes = ["Calendars.Read", "User.Read"]

    # Check cache for existing active account
    accounts = public_app.get_accounts()
    if accounts:
        token_res = public_app.acquire_token_silent(scopes, account=accounts[0])
        if token_res and "access_token" in token_res:
            return token_res

    # Device code flow: prints instructions and waits for one-time browser sign-in
    flow = public_app.initiate_device_flow(scopes=scopes)
    if "user_code" in flow:
        print("\n" + "=" * 70)
        print("🔐 MICROSOFT OUTLOOK SIGN-IN REQUIRED (ONE-TIME):")
        print(f"👉 1. Open: {flow['verification_uri']}")
        print(f"👉 2. Enter code: {flow['user_code']}")
        print("=" * 70 + "\n")
        token_res = public_app.acquire_token_by_device_flow(flow)
        if "access_token" in token_res:
            return token_res

    return {"error": "Authentication failed. Could not acquire token via secret or device flow."}


def _parse_iso_datetime(dt_str: str) -> datetime:
    cleaned = dt_str.replace("Z", "")
    if "." in cleaned:
        base, frac = cleaned.split(".", 1)
        cleaned = f"{base}.{frac[:6]}"
    return datetime.fromisoformat(cleaned)


def _get_mock_calendar_metrics(employee_email: str, start_date: str, end_date: str) -> Dict[str, Any]:
    return {
        "source": "Outlook Calendar (MOCK DATA - Add active Azure credentials or complete device login)",
        "employee_email": employee_email,
        "period": {"start_date": start_date, "end_date": end_date},
        "summary": {
            "total_meetings_count": 14,
            "total_meeting_hours": 11.5,
            "one_on_one_hours": 2.5,
            "group_meeting_hours": 9.0,
            "recurring_meeting_hours": 6.5,
            "ad_hoc_meeting_hours": 5.0,
            "standard_work_hours": 40.0,
            "estimated_focus_hours_remaining": 28.5,
            "meeting_load_percentage": 28.75,
        },
        "meetings_breakdown": [
            {"subject": "Daily Standup", "duration_hours": 2.5, "type": "Recurring Group", "occurrences": 5},
            {"subject": "Sprint Planning & Grooming", "duration_hours": 2.0, "type": "Recurring Group", "occurrences": 1},
            {"subject": "Architecture Sync - Azure Integration", "duration_hours": 1.5, "type": "Ad-hoc Group", "occurrences": 1},
            {"subject": "Manager 1:1", "duration_hours": 1.0, "type": "1:1", "occurrences": 2},
            {"subject": "Peer Code & Design Walkthrough", "duration_hours": 1.5, "type": "1:1", "occurrences": 2},
            {"subject": "Cross-Team Bug Triage", "duration_hours": 2.0, "type": "Ad-hoc Group", "occurrences": 2},
            {"subject": "All-Hands Weekly Sync", "duration_hours": 1.0, "type": "Recurring Group", "occurrences": 1},
        ],
    }


def get_outlook_calendar_metrics(employee_email: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Fetch Outlook calendar events and compute meeting hours for an employee between start_date and end_date (YYYY-MM-DD).
    """
    settings = get_settings()
    if settings.should_mock(settings.is_outlook_configured):
        return _get_mock_calendar_metrics(employee_email, start_date, end_date)

    token_result = _acquire_graph_token(settings)
    if "access_token" not in token_result:
        return {
            "source": "Outlook Calendar (Live API Error)",
            "error": token_result.get("error_description", token_result.get("error", "Failed to acquire MS Graph token.")),
        }

    headers = {
        "Authorization": f"Bearer {token_result['access_token']}",
        "Prefer": 'outlook.timezone="UTC"',
    }

    start_iso = f"{start_date}T00:00:00Z"
    end_iso = f"{end_date}T23:59:59Z"

    # In delegated/user mode or application mode:
    # Try querying the specific user's calendar; fallback to /me/calendarView if delegated to own user
    url = (
        f"https://graph.microsoft.com/v1.0/users/{employee_email}/calendarView"
        f"?startDateTime={start_iso}&endDateTime={end_iso}"
        f"&$select=subject,start,end,isAllDay,isCancelled,responseStatus,attendees,type&$top=250"
    )

    resp = requests.get(url, headers=headers, timeout=20)
    if resp.status_code == 403 or resp.status_code == 404:
        # If accessing another user's calendar is restricted, try /me/calendarView
        fallback_url = (
            f"https://graph.microsoft.com/v1.0/me/calendarView"
            f"?startDateTime={start_iso}&endDateTime={end_iso}"
            f"&$select=subject,start,end,isAllDay,isCancelled,responseStatus,attendees,type&$top=250"
        )
        resp = requests.get(fallback_url, headers=headers, timeout=20)

    if resp.status_code != 200:
        return {
            "source": "Outlook Calendar (Live API Error)",
            "status_code": resp.status_code,
            "error": resp.text,
        }

    events = resp.json().get("value", [])
    total_hours = 0.0
    one_on_one_hours = 0.0
    group_hours = 0.0
    recurring_hours = 0.0
    ad_hoc_hours = 0.0
    valid_meetings: List[Dict[str, Any]] = []

    for ev in events:
        if ev.get("isCancelled") or ev.get("isAllDay"):
            continue
        response_type = (ev.get("responseStatus") or {}).get("response", "").lower()
        if response_type == "declined":
            continue

        start_dt = _parse_iso_datetime(ev["start"]["dateTime"])
        end_dt = _parse_iso_datetime(ev["end"]["dateTime"])
        duration = max((end_dt - start_dt).total_seconds() / 3600.0, 0.0)

        attendees = ev.get("attendees", [])
        is_one_on_one = len(attendees) <= 2
        is_recurring = ev.get("type") in ("occurrence", "exception", "seriesMaster")

        total_hours += duration
        if is_one_on_one:
            one_on_one_hours += duration
        else:
            group_hours += duration

        if is_recurring:
            recurring_hours += duration
        else:
            ad_hoc_hours += duration

        valid_meetings.append(
            {
                "subject": ev.get("subject", "(No Subject)"),
                "start": ev["start"]["dateTime"],
                "duration_hours": round(duration, 2),
                "attendee_count": len(attendees),
                "is_one_on_one": is_one_on_one,
                "is_recurring": is_recurring,
            }
        )

    return {
        "source": "Outlook Calendar (Live Microsoft Graph API)",
        "employee_email": employee_email,
        "period": {"start_date": start_date, "end_date": end_date},
        "summary": {
            "total_meetings_count": len(valid_meetings),
            "total_meeting_hours": round(total_hours, 2),
            "one_on_one_hours": round(one_on_one_hours, 2),
            "group_meeting_hours": round(group_hours, 2),
            "recurring_meeting_hours": round(recurring_hours, 2),
            "ad_hoc_meeting_hours": round(ad_hoc_hours, 2),
            "estimated_focus_hours_remaining": round(max(40.0 - total_hours, 0.0), 2),
        },
        "meetings_breakdown": valid_meetings[:30],
    }
