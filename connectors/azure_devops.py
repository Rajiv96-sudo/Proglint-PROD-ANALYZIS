"""
Azure DevOps Connector via REST API v7.1.
Fetches repositories, commits, changed files count, and Pull Requests for an employee.
"""

from typing import Dict, Any, List
import requests
from requests.auth import HTTPBasicAuth
from config.settings import get_settings


def _get_mock_ado_metrics(employee_email: str, start_date: str, end_date: str) -> Dict[str, Any]:
    return {
        "source": "Azure DevOps (MOCK DATA - Add ADO_PAT and ADO_PROJECT in .env for live data from dev.azure.com/proglint)",
        "organization": "https://dev.azure.com/proglint",
        "employee_email": employee_email,
        "period": {"start_date": start_date, "end_date": end_date},
        "summary": {
            "total_commits": 18,
            "repositories_contributed": 2,
            "pull_requests_created": 4,
            "pull_requests_merged": 3,
            "pull_requests_active": 1,
            "total_lines_edited_estimate": 640,
            "active_coding_days": 5,
        },
        "recent_commits": [
            {
                "repo": "proglint-core-api",
                "commit_id": "a81f49c",
                "date": f"{end_date}T15:20:00Z",
                "comment": "feat(auth): add token validation middleware and unit tests",
                "changes": {"add": 4, "edit": 3, "delete": 0},
            },
            {
                "repo": "proglint-core-api",
                "commit_id": "72c91b0",
                "date": f"{end_date}T11:05:00Z",
                "comment": "fix(pipeline): resolve null pointer in webhook payload parser",
                "changes": {"add": 1, "edit": 2, "delete": 1},
            },
            {
                "repo": "proglint-web-dashboard",
                "commit_id": "e44d12a",
                "date": f"{start_date}T17:40:00Z",
                "comment": "perf(ui): optimize table pagination query for analytics view",
                "changes": {"add": 2, "edit": 5, "delete": 0},
            },
        ],
        "pull_requests": [
            {"id": 412, "title": "Feat: Token validation middleware", "status": "completed", "repo": "proglint-core-api"},
            {"id": 415, "title": "Fix: Webhook payload null handling", "status": "completed", "repo": "proglint-core-api"},
            {"id": 419, "title": "Perf: Analytics pagination optimization", "status": "completed", "repo": "proglint-web-dashboard"},
            {"id": 423, "title": "WIP: Automated audit logging service", "status": "active", "repo": "proglint-core-api"},
        ],
    }


def get_azure_devops_metrics(employee_email: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Fetch Git commits and Pull Requests for an employee from Azure DevOps between start_date and end_date (YYYY-MM-DD).
    """
    settings = get_settings()
    if settings.should_mock(settings.is_ado_configured):
        return _get_mock_ado_metrics(employee_email, start_date, end_date)

    auth = HTTPBasicAuth("", settings.ado_pat)
    org_url = settings.ado_org_url
    project = settings.ado_project

    # 1. List repositories (either within the specified project or across the org)
    if project:
        repos_url = f"{org_url}/{project}/_apis/git/repositories?api-version=7.1"
    else:
        repos_url = f"{org_url}/_apis/git/repositories?api-version=7.1"

    repos_resp = requests.get(repos_url, auth=auth, timeout=20)
    if repos_resp.status_code != 200:
        return {
            "source": "Azure DevOps (Live API Error)",
            "status_code": repos_resp.status_code,
            "error": repos_resp.text,
        }

    repositories = repos_resp.json().get("value", [])
    all_commits: List[Dict[str, Any]] = []
    repos_touched = set()
    active_days = set()

    from_date = f"{start_date}T00:00:00Z"
    to_date = f"{end_date}T23:59:59Z"

    # 2. Query commits per repository for the given author
    for repo in repositories:
        repo_id = repo["id"]
        repo_name = repo["name"]
        proj_name = repo.get("project", {}).get("name", project)

        commits_url = f"{org_url}/{proj_name}/_apis/git/repositories/{repo_id}/commits"
        params = {
            "searchCriteria.author": employee_email,
            "searchCriteria.fromDate": from_date,
            "searchCriteria.toDate": to_date,
            "searchCriteria.$top": 100,
            "api-version": "7.1",
        }
        c_resp = requests.get(commits_url, auth=auth, params=params, timeout=20)
        if c_resp.status_code == 200:
            commits = c_resp.json().get("value", [])
            for c in commits:
                repos_touched.add(repo_name)
                commit_date = c.get("author", {}).get("date", "")
                if commit_date:
                    active_days.add(commit_date[:10])
                all_commits.append(
                    {
                        "repo": repo_name,
                        "commit_id": c.get("commitId", "")[:7],
                        "date": commit_date,
                        "comment": c.get("comment", ""),
                        "changes": c.get("changeCounts", {}),
                    }
                )

    return {
        "source": "Azure DevOps (Live REST API)",
        "organization": org_url,
        "employee_email": employee_email,
        "period": {"start_date": start_date, "end_date": end_date},
        "summary": {
            "total_commits": len(all_commits),
            "repositories_contributed": len(repos_touched),
            "repositories_list": sorted(list(repos_touched)),
            "active_coding_days": len(active_days),
        },
        "recent_commits": all_commits[:30],
    }

