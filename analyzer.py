import os
import json
from database import get_tasks, get_task_by_id, get_summary, get_account_info
from filter import translate_ru_to_en

DOWNLOADS_DIR = os.path.expanduser("~/downloads")

def generate_report(limit=50):
    tasks = get_tasks('shortlisted', limit, sort_by='time')
    summary = get_summary()
    acc = get_account_info()

    lines = []
    lines.append("=" * 65)
    lines.append("SPRINTER - SEOSPRINT TASK ANALYZER & GOAL TRACKER")
    lines.append("=" * 65)
    lines.append(f"Target Goal    : ${summary['target_goal']:.2f}")
    lines.append(f"Shortlisted    : {summary['total_shortlisted_tasks']} tasks (${summary['total_shortlisted_value']:.2f})")
    lines.append(f"Progress       : {summary['goal_percentage']}% towards $100")
    lines.append(f"Completed      : {summary['completed_count']} tasks (${summary['completed_value']:.2f})")
    
    if acc:
        lines.append("-" * 65)
        lines.append("ACCOUNT DETAILS:")
        lines.append(f"  User ID      : {acc.get('user_id')}")
        lines.append(f"  Balance      : ${acc.get('balance_usd', 0.0):.2f}")
        lines.append(f"  Reputation   : {acc.get('rating', 0.0)}")
        lines.append(f"  Status       : {acc.get('status', 'Active')}")
    lines.append("-" * 65)

    if not tasks:
        lines.append("No active shortlisted tasks found.")
        lines.append("To scan, run: python3 main.py scan OR use the Kiwi Browser live HUD scanner.")
    else:
        lines.append("SORTED TASK SHORTLIST (Lowest Time-Taking to Highest):")
        lines.append(f"{'#':<3} {'ID':<8} {'EST.TIME':<10} {'PAYOUT':<10} {'TITLE (English Summary)'}")
        lines.append("-" * 65)
        for i, t in enumerate(tasks, 1):
            est = f"~{t.get('est_minutes', 2.5):.1f} min"
            title_en = translate_ru_to_en(t['title'])
            if len(title_en) > 30:
                title_en = title_en[:27] + "..."
            lines.append(f"{i:<3} {t['task_id']:<8} {est:<10} +${t['price_usd']:<9.3f} {title_en}")
            lines.append(f"    Link: {t['url']}")
        lines.append("-" * 65)

    return "\n".join(lines)

def get_task_guide(task_id):
    task = get_task_by_id(task_id)
    if not task:
        return f"[ERROR] Task ID {task_id} not found in database."

    title_en = translate_ru_to_en(task['title'])
    est_min = task.get('est_minutes', 2.0)

    lines = []
    lines.append("=" * 65)
    lines.append(f"EXECUTION GUIDE: TASK #{task['task_id']}")
    lines.append("=" * 65)
    lines.append(f"Original Title   : {task['title']}")
    lines.append(f"English Summary  : {title_en}")
    lines.append(f"Payout           : +${task['price_usd']:.3f}")
    lines.append(f"Category         : {task['category']}")
    lines.append(f"Est. Time Taken  : ~{est_min:.1f} minutes (Strictly under 5 min)")
    lines.append(f"Task Direct Link : {task['url']}")
    lines.append("-" * 65)
    lines.append("QUICK SPEED WORKFLOW (HOW TO COMPLETE FAST):")
    lines.append("1. Open Task Link in Kiwi / Android Browser:")
    lines.append(f"   {task['url']}")
    lines.append("2. Click the green button 'Start Execution' ('Начать выполнение').")
    lines.append("3. Complete Email Registration:")
    lines.append("   - Use an alias email (e.g. yourname+seo1@gmail.com) or quick webmail.")
    lines.append("   - Enter username and a standard password.")
    lines.append("   - Click the verification link sent to your email inbox.")
    lines.append("4. Verification / Report Box Submission:")
    lines.append("   - Copy the registered username / nickname or profile URL.")
    lines.append("   - Paste into SEOSprint report text area.")
    lines.append("   - Click 'Send Report' ('Отправить отчёт').")
    lines.append("-" * 65)
    lines.append("PRO TIPS FOR MAX SPEED:")
    lines.append("- Keep your email tab open side-by-side to catch the activation link instantly.")
    lines.append("- No KYC, no phone number, and no SMS code are ever needed for this task.")
    lines.append(f"- Once submitted, run: python3 main.py complete {task['task_id']}")
    lines.append("=" * 65)
    return "\n".join(lines)

def export_data(format_type="json"):
    tasks = get_tasks('shortlisted', 500, sort_by='time')
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
            title_en = translate_ru_to_en(t['title'])
            lines.append(f"{i}. [ID: {t['task_id']}] [~{t.get('est_minutes', 2.5):.1f} min] +${t['price_usd']:.3f} | {title_en}")
            lines.append(f"   URL: {t['url']}\n")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return filepath
