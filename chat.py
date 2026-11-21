"""
Interactive Terminal Chat with the Employee Productivity Analyst Agent.
Usage:
  python chat.py
"""

import sys
from datetime import date, timedelta
from config.settings import get_settings
from agent.analyst_agent import create_productivity_chat


def main():
    settings = get_settings()

    print("\n" + "=" * 74)
    print("  💬 EMPLOYEE PRODUCTIVITY ANALYST AGENT — INTERACTIVE CHAT")
    print("=" * 74)
    print(f"  • Model       : {settings.gemini_model}")
    print(f"  • Mode        : {settings.use_mock_data.upper()}")
    print(f"  • Outlook API : {'Live/Device' if settings.is_outlook_configured else 'Mock Fallback'}")
    print(f"  • Azure DevOps: {'Configured' if settings.is_ado_configured else 'Mock Fallback'}")
    print("=" * 74)
    print("  Type your questions naturally. Examples:")
    print("   - 'Analyze developer@proglint.com for the last 7 days'")
    print("   - 'Did they have too many meetings this week?'")
    print("   - 'How many commits and PRs did they make?'")
    print("  Type 'exit' or 'quit' to end the chat.")
    print("-" * 74 + "\n")

    if not settings.is_gemini_configured:
        print("❌ Error: GEMINI_API_KEY is not configured in c:\\agent\\.env")
        sys.exit(1)

    default_email = "developer@proglint.com"
    email_input = input(f"Enter employee email to analyze [default: {default_email}]: ").strip()
    target_email = email_input if email_input else default_email

    chat = create_productivity_chat(employee_email=target_email)
    if not chat:
        print("❌ Error: Could not initialize chat session.")
        sys.exit(1)

    print(f"\n✅ Chatting about: {target_email}")

    while True:
        try:
            user_input = input("You > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("\nGoodbye!\n")
                break

            print("\n🤖 Agent is analyzing (checking Calendar & Azure DevOps)...")
            response = chat.send_message(user_input)
            print("\n" + response.text + "\n" + "-" * 74 + "\n")

        except (KeyboardInterrupt, EOFError):
            print("\n\nSession ended.")
            break
        except Exception as e:
            print(f"\n⚠️ Error: {e}\n")


if __name__ == "__main__":
    main()

