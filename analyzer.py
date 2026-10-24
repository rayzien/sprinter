import os
import json
from database import get_tasks, get_task_by_id, get_summary

DOWNLOADS_DIR = os.path.expanduser("~/downloads")

def generate_report(limit=50):
    tasks = get_tasks('shortlisted', limit)
    summary = get_summary()

    lines = []
    lines.append("=" * 60)
    lines.append("SPRINTER TASK ANALYSIS & RUNNER REPORT")
    lines.append("=" * 60)
    lines.append(f"Target Goal    : ${summary['target_goal']:.2f}")
    lines.append(f"Shortlisted    : {summary['total_shortlisted_tasks']} tasks (${summary['total_shortlisted_value']:.2f})")
    lines.append(f"Progress       : {summary['goal_percentage']}%")
    lines.append(f"Completed      : {summary['completed_count']} tasks (${summary['completed_value']:.2f})")
    lines.append("-" * 60)

    if not tasks:
        lines.append("No active shortlisted tasks found. Run 'python3 main.py scan' first.")
    else:
        lines.append("TOP RECOMMENDED TASKS (Fast 2-3 Min Turnaround):")
        for i, t in enumerate(tasks[:20], 1):
            lines.append(f"{i:02d}. [ID: {t['task_id']}] +${t['price_usd']:.3f} (Score: {t['score']})")
            lines.append(f"    Title: {t['title']}")
            lines.append(f"    Link : {t['url']}")
            lines.append("")

    return "\n".join(lines)

def get_task_guide(task_id):
    task = get_task_by_id(task_id)
    if not task:
        return f"[ERROR] Task ID {task_id} not found in database."

    lines = []
    lines.append("=" * 60)
    lines.append(f"EXECUTION GUIDE FOR TASK #{task['task_id']}")
    lines.append(f"Title: {task['title']}")
    lines.append(f"Payout: +${task['price_usd']:.3f}")
    lines.append(f"Link: {task['url']}")
    lines.append("-" * 60)
    lines.append("STEP-BY-STEP WORKFLOW (Est. 2-3 minutes):")
    lines.append("1. Open the task link on your mobile browser (Kiwi/Chrome).")
    lines.append("2. Click 'Start Execution' / 'Начать выполнение'.")
    lines.append("3. Navigate to the registration page:")
    lines.append("   - Use an alias email or dedicated secondary Gmail/Outlook.")
    lines.append("   - Keep passwords standardized for speed.")
    lines.append("4. Confirm the email confirmation link in your inbox.")
    lines.append("5. Proof / Verification Submission:")
    lines.append("   - Copy your registered username or profile link.")
    lines.append("   - Paste into SEOSprint report box and click 'Submit Report'.")
    lines.append("=" * 60)
    return "\n".join(lines)

def export_data(format_type="json"):
    tasks = get_tasks('shortlisted', 500)
    summary = get_summary()

    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

    if format_type.lower() == "json":
        filepath = os.path.join(DOWNLOADS_DIR, "sprinter_shortlist.json")
        payload = {
            "summary": summary,
            "tasks": tasks
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return filepath
    else:
        filepath = os.path.join(DOWNLOADS_DIR, "sprinter_shortlist.txt")
        lines = [
            f"SPRINTER SHORTLIST EXPORT - {len(tasks)} Tasks - Total: ${summary['total_shortlisted_value']:.2f}\n"
        ]
        for i, t in enumerate(tasks, 1):
            lines.append(f"{i}. [ID: {t['task_id']}] +${t['price_usd']:.3f} | {t['title']}")
            lines.append(f"   URL: {t['url']}\n")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return filepath
