# Proglint-PROD-ANALYZIS: Employee Productivity Analyst Agent

An enterprise AI Agent powered by **Google Gemini** (`gemini-flash-lite-latest`) that objectively correlates **Outlook Calendar** (meeting load & focus time), **Azure DevOps** (Git commits & Pull Requests), and **Live Task Workload Tracking** to detect developer burnout, schedule bottlenecks, and delivery feasibility.

---

## 🚀 Key Features

- **📅 Calendar & Deep-Work Focus Time Engine:**
  - Calculates total meeting hours, 1:1s, group syncs, and recurring meetings.
  - Automatically computes remaining uninterrupted focus hours out of a 40-hour standard work week.
- **💻 Azure DevOps Git & PR Correlation:**
  - Tracks commit volume, active coding days, and Pull Request lifecycle (Created, Merged, Active).
- **📝 Multi-Assignee Task Manager & Real-Time Agent Evaluation:**
  - Create and assign tasks to single or multiple team members.
  - Automatically triggers the Gemini Agent to evaluate schedule feasibility, flag delivery risks, and recommend optimal workload splits.
- **⏱️ Task Duration & Deadline Tracking:**
  - Color-coded countdown badges (Overdue, Due Today, Urgent, On Track).
  - Optional **"Audit Pending Tasks"** button to prioritize the backlog and detect capacity bottlenecks.
- **⚡ Hybrid Architecture:**
  - Includes a realistic **Synthetic Data Engine** with personas (Rahul, Priya, Amit).
  - Seamless 1-click toggle to **Live Microsoft Graph** and **Live Azure DevOps REST APIs**.
- **📊 Interactive Streamlit Web UI & CLI Chat:**
  - Web dashboard (`streamlit run app.py`) with metric cards, progress bars, and conversational chat.
  - Terminal chat (`python chat.py`).

---

## 🛠️ Project Structure

```text
c:\agent\
├── .env.example              # Template for API keys & settings
├── requirements.txt          # Python dependencies
├── app.py                    # Streamlit Web Dashboard & Multi-Assignee UI
├── chat.py                   # Terminal interactive chat runner
├── main.py                   # CLI diagnostics & execution
├── synthetic_data.py         # Realistic Calendar, Git & Task generator
├── synthetic_tasks.json      # Persistent task store
├── config/
│   └── settings.py           # Configuration loader
├── agent/
│   └── analyst_agent.py      # Gemini Agent logic & reasoning engine
└── connectors/
    ├── outlook_calendar.py   # Microsoft Graph API connector (Secret / Device login)
    └── azure_devops.py       # Azure DevOps REST API connector (dev.azure.com/proglint)
```

---

## ⚙️ Quick Start

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your keys:
```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-flash-lite-latest
USE_MOCK_DATA=auto
ADO_ORG_URL=https://dev.azure.com/proglint
ADO_PAT=your_azure_devops_pat
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
```

### 3. Launch Web Dashboard
```powershell
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## 👥 Predefined Synthetic Personas
1. **👨‍💻 Rahul Sharma** (*Senior Backend Engineer*): 24.5h meetings, 15.5h focus time, 5 commits (Meeting Overload scenario).
2. **👩‍💻 Priya Patel** (*Core Systems Engineer*): 7.0h meetings, 33.0h focus time, 32 commits, 6 PRs (Deep Work Flow scenario).
3. **👨‍💼 Amit Verma** (*Tech Lead & Architect*): 15.0h meetings, 14 commits, 8 PR reviews (Review & Alignment scenario).

