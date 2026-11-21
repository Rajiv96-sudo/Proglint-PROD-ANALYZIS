"""
Employee Productivity Analyst Agent — Streamlit Web Dashboard
Includes Synthetic Data Personas, Automated Task Assignment with Agent Impact Analysis,
Visual Productivity Metrics, and Interactive Gemini Chat.
"""

from datetime import date, timedelta
import importlib
import streamlit as st

from config.settings import get_settings
import synthetic_data
import agent.analyst_agent

# Ensure submodules are fresh on every Streamlit rerun
importlib.reload(synthetic_data)
importlib.reload(agent.analyst_agent)

from synthetic_data import (
    PERSONAS,
    load_tasks,
    add_synthetic_task,
    delete_task,
    update_task_status,
    reset_tasks,
    get_all_assignees,
)
from agent.analyst_agent import (
    get_full_employee_productivity_snapshot,
    evaluate_task_assignment,
    audit_pending_tasks_and_deadlines,
    run_productivity_agent,
    create_productivity_chat,
)


def task_matches_employee(task, email):
    target = str(email).lower().strip()
    assignees = task.get("assignees", [])
    if assignees:
        return any(target == str(a).lower().strip() for a in assignees)
    return target in str(task.get("assignee", "")).lower()

st.set_page_config(
    page_title="Employee Productivity Analyst Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

settings = get_settings()

# Custom CSS for styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1E232A;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #30363D;
    }
    .badge-safe { background-color: #238636; color: white; padding: 3px 8px; border-radius: 12px; font-weight: bold; }
    .badge-risk { background-color: #D29922; color: white; padding: 3px 8px; border-radius: 12px; font-weight: bold; }
    .badge-overload { background-color: #DA3633; color: white; padding: 3px 8px; border-radius: 12px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Employee Productivity Analyst Agent")
st.caption("Powered by Google Gemini • Correlating Outlook Calendar, Azure DevOps, and Live Task Allocation")

# --- SIDEBAR: Controls & Persona Picker ---
with st.sidebar:
    st.header("👥 Select Employee Persona")
    persona_options = list(PERSONAS.keys()) + ["Custom Email"]
    selected_option = st.selectbox(
        "Choose Persona / Scenario",
        options=persona_options,
        format_func=lambda x: f"{PERSONAS[x]['avatar']} {PERSONAS[x]['name']} ({PERSONAS[x]['scenario']})" if x in PERSONAS else "✏️ Custom Email",
    )

    if selected_option in PERSONAS:
        employee_email = selected_option
        p_info = PERSONAS[selected_option]
        st.info(f"**Role:** {p_info['role']}\n\n**Scenario:** {p_info['scenario']}")
    else:
        employee_email = st.text_input("Enter Corporate Email", value="rahul@proglint.com")

    st.divider()
    st.header("⚙️ Data Mode")
    use_synthetic = st.toggle("Use Synthetic Data Generator", value=True, help="Toggle off when live Azure keys are configured")
    
    st.subheader("📅 Timeframe")
    default_end = date.today()
    default_start = default_end - timedelta(days=7)
    start_date = st.date_input("Start Date", value=default_start)
    end_date = st.date_input("End Date", value=default_end)

    st.divider()
    st.caption(f"**Gemini Model:** `{settings.gemini_model}`")
    st.caption(f"**API Status:** {'🟢 Ready' if settings.is_gemini_configured else '🔴 Set Key in .env'}")

# --- DATA RETRIEVAL ---
snapshot = get_full_employee_productivity_snapshot(
    employee_email=employee_email,
    start_date=str(start_date),
    end_date=str(end_date),
    use_synthetic=use_synthetic,
)

cal_summary = snapshot["outlook_calendar"].get("summary", {})
ado_summary = snapshot["azure_devops"].get("summary", {})
tasks_assigned = snapshot.get("assigned_tasks", [])

# Helper for Streamlit dataframe width compatibility
def display_df(data):
    try:
        st.dataframe(data, width="stretch")
    except TypeError:
        st.dataframe(data, use_container_width=True)


# --- TOP METRIC CARDS ---
c1, c2, c3, c4 = st.columns(4)
meeting_hrs = cal_summary.get("total_meeting_hours", 0)
focus_hrs = cal_summary.get("estimated_focus_hours_remaining", 0)
commits = ado_summary.get("total_commits", 0)
active_tasks_count = len([t for t in tasks_assigned if t.get("status") != "Done"])

c1.metric("📅 Meeting Burden", f"{meeting_hrs} hrs", f"{cal_summary.get('total_meetings_count', 0)} meetings")
c2.metric("🧠 Focus Time Left", f"{focus_hrs} hrs", "Out of 40h standard week")
c3.metric("💻 Git Commits (ADO)", f"{commits} commits", f"{ado_summary.get('pull_requests_merged', 0)} PRs merged")
c4.metric("📋 Active Tasks", f"{active_tasks_count} tasks", f"{len(tasks_assigned)} total assigned")

# Focus vs Meeting Progress Bar
meeting_pct = min(int((meeting_hrs / 40.0) * 100), 100)
st.progress(meeting_pct, text=f"Meeting Load: {meeting_pct}% of standard work week ({meeting_hrs}h in meetings / {focus_hrs}h focus time remaining)")

st.divider()

# --- MAIN TABS ---
tab_tasks, tab_report, tab_chat, tab_data = st.tabs([
    "📝 Assign Task & Agent Impact Analysis",
    "📊 Executive AI Productivity Report",
    "💬 Interactive Agent Chat",
    "📋 Raw Data (Calendar & Commits)",
])

# ============================================================================
# TAB 1: TASK ASSIGNMENT & REAL-TIME AGENT EVALUATION
# ============================================================================
with tab_tasks:
    st.subheader("🚀 Assign Task to One or Multiple Team Members")
    st.write("Assign a task to **one or more developers**. The **Gemini Agent is called immediately** to cross-examine each person's calendar, detect workload bottlenecks, and recommend optimal task distribution.")

    # Show latest evaluation banner if present
    if "latest_evaluation" in st.session_state and st.session_state["latest_evaluation"]:
        eval_data = st.session_state["latest_evaluation"]
        st.info(f"### 🤖 Latest Agent Feasibility Report for `{eval_data['id']}` ({eval_data['title']}):\n\n{eval_data['evaluation']}")
        if st.button("Dismiss Evaluation Banner"):
            st.session_state["latest_evaluation"] = None
            st.rerun()

    with st.expander("➕ **Create & Assign Task (Supports Multiple People)**", expanded=True):
        with st.form("new_task_form"):
            col_t1, col_t2 = st.columns([3, 1])
            with col_t1:
                task_title = st.text_input("Task Title", placeholder="e.g. Implement OAuth2 Refresh Token Rotation in Auth Gateway")
            with col_t2:
                task_priority = st.selectbox("Priority", ["Highest", "High", "Medium", "Low"], index=1)

            # Multi-Assignee selector
            all_known = get_all_assignees()
            default_assignees = [employee_email] if employee_email in all_known else [all_known[0]]
            selected_assignees = st.multiselect(
                "Select Assignees (Choose 1 or more team members)",
                options=all_known,
                default=default_assignees,
                help="You can select multiple employees for collaborative tasks",
            )
            custom_extra = st.text_input("Or add custom email(s) (comma-separated, optional):", placeholder="e.g. dev1@proglint.com, dev2@proglint.com").strip()

            col_t3, col_t4 = st.columns(2)
            with col_t3:
                task_hours = st.number_input("Total Estimated Effort (Hours)", min_value=1, max_value=80, value=8, step=1)
            with col_t4:
                task_due = st.date_input("Due Date", value=date.today() + timedelta(days=3))

            submit_task = st.form_submit_button("🚀 Assign Task & Call Agent", type="primary")

        if submit_task and task_title:
            final_assignees = list(selected_assignees)
            if custom_extra:
                for email_part in custom_extra.split(","):
                    clean = email_part.strip()
                    if clean and clean not in final_assignees:
                        final_assignees.append(clean)

            if not final_assignees:
                st.error("Please select or enter at least one assignee!")
            else:
                with st.spinner(f"🤖 Calling Gemini Agent to evaluate schedule feasibility for {len(final_assignees)} assignees..."):
                    new_task = add_synthetic_task(
                        title=task_title,
                        assignees=final_assignees,
                        priority=task_priority,
                        estimated_hours=int(task_hours),
                        due_date=str(task_due),
                    )
                    evaluation = evaluate_task_assignment(new_task, final_assignees)
                    st.session_state["latest_evaluation"] = {
                        "id": new_task["id"],
                        "title": new_task["title"],
                        "evaluation": evaluation,
                    }
                st.success(f"✅ Task {new_task['id']} assigned to {', '.join(final_assignees)}!")
                st.rerun()

    st.divider()

    # Active Tasks Table & Management
    col_h1, col_h2, col_h3 = st.columns([3, 2, 1])
    with col_h1:
        st.subheader(f"📋 Tasks Involving {employee_email}")
    with col_h2:
        audit_btn = st.button("🤖 Audit Pending Tasks (Ask Agent)", type="secondary", help="Analyzes remaining days, urgency, and calendar capacity for pending tasks")
    with col_h3:
        if st.button("🧹 Reset Tasks"):
            reset_tasks()
            st.session_state["latest_evaluation"] = None
            st.rerun()

    # If user clicked the optional audit button
    if audit_btn:
        with st.spinner(f"🤖 Gemini Agent is auditing pending deadlines and priority order for {employee_email}..."):
            audit_report = audit_pending_tasks_and_deadlines(employee_email)
        st.markdown("### ⏱️ Agent Task Deadline & Priority Audit:")
        st.info(audit_report)
        st.divider()

    all_current_tasks = load_tasks()
    emp_tasks = [t for t in all_current_tasks if task_matches_employee(t, employee_email)]

    if emp_tasks:
        for t in emp_tasks:
            t_id = t.get("id")
            status = t.get("status")
            status_color = "🟢" if status == "Done" else ("🔵" if status == "In Progress" else "🟡")
            assigned_display = t.get("assignee", employee_email)

            # Deadline and duration tracking calculation
            due_str = t.get("due_date", "")
            try:
                due_d = date.fromisoformat(due_str)
                days_left = (due_d - date.today()).days
                if status == "Done":
                    deadline_badge = "✅ Completed"
                elif days_left < 0:
                    deadline_badge = f"🔴 **Overdue by {abs(days_left)}d**"
                elif days_left == 0:
                    deadline_badge = "🟡 **Due Today!**"
                elif days_left <= 2:
                    deadline_badge = f"🟡 **Due in {days_left}d (Urgent)**"
                else:
                    deadline_badge = f"🟢 **{days_left}d remaining**"
            except Exception:
                deadline_badge = f"📅 Due: {due_str}"

            with st.container():
                st.markdown(f"**{status_color} {t_id}: {t.get('title')}** | `Status: {status}` | `Priority: {t.get('priority')}` | `Est: {t.get('estimated_hours')}h` | {deadline_badge}")
                st.caption(f"👥 **Assignees:** `{assigned_display}` | **Agent Evaluation:** {t.get('agent_feasibility', 'N/A')}")
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 6])
                with col_btn1:
                    if status != "Done" and st.button("Mark Done", key=f"done_{t_id}"):
                        update_task_status(t_id, "Done")
                        st.rerun()
                with col_btn2:
                    if st.button("Delete", key=f"del_{t_id}"):
                        delete_task(t_id)
                        st.rerun()
                st.divider()
    else:
        st.write(f"No tasks currently assigned to **{employee_email}**. Use the form above to assign one!")

# ============================================================================
# TAB 2: EXECUTIVE AI PRODUCTIVITY REPORT
# ============================================================================
with tab_report:
    st.subheader("📊 Comprehensive Productivity & Correlation Report")
    st.write(f"Generate an objective synthesis for **{employee_email}** analyzing meeting load vs. Git commit throughput.")

    if st.button("⚡ Generate AI Executive Report", type="primary"):
        with st.spinner("Gemini is analyzing meeting fragmentation, focus hours, and commit velocity..."):
            prompt = (
                f"Analyze employee {employee_email} from {start_date} to {end_date}. "
                f"Correlate their meeting hours with Git commits and PRs. "
                f"Explain if meeting fragmentation blocked deep-work time and provide recommendations."
            )
            report = run_productivity_agent(prompt, employee_email=employee_email, start_date=str(start_date), end_date=str(end_date))
        st.markdown(report)

# ============================================================================
# TAB 3: CONVERSATIONAL AGENT CHAT
# ============================================================================
with tab_chat:
    st.subheader("💬 Chat Directly with the Productivity Analyst Agent")
    st.write(f"Ask any question about **{employee_email}** (e.g. *'What is blocking them?'*, *'Should we reassign the 12h task?'*, *'How can we reduce their meetings?'*).")

    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant", "content": f"Hello! I am ready to analyze **{employee_email}**. Ask me any question about their schedule, commits, or task capacity!"}
        ]

    if "chat_session" not in st.session_state or st.session_state.get("chat_email") != employee_email:
        st.session_state["chat_session"] = create_productivity_chat(employee_email=employee_email, start_date=str(start_date), end_date=str(end_date))
        st.session_state["chat_email"] = employee_email

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_query = st.chat_input("Type your question here...")
    if user_query:
        st.session_state["messages"].append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Gemini Agent is reasoning..."):
                response = st.session_state["chat_session"].send_message(user_query)
                st.markdown(response.text)
                st.session_state["messages"].append({"role": "assistant", "content": response.text})

# ============================================================================
# TAB 4: RAW DATA INSPECTOR
# ============================================================================
with tab_data:
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.subheader("📅 Outlook Meetings Breakdown")
        display_df(snapshot["outlook_calendar"].get("meetings_breakdown", []))
    with col_d2:
        st.subheader("💻 Azure DevOps Commits")
        display_df(snapshot["azure_devops"].get("recent_commits", []))
