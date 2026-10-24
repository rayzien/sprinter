#!/usr/bin/env python3
import sys
import argparse
import json
from config import load_config, save_config, update_cookies_from_raw
from crawler import run_scan
from analyzer import generate_report, get_task_guide, export_data
from database import get_tasks, update_task_status, get_summary, save_task
from server import start_server

def handle_cookies(args):
    cfg = load_config()
    if args.set:
        updated = update_cookies_from_raw(args.set)
        print("[CONFIG] Cookies updated successfully:")
        for k, v in updated.items():
            print(f"  {k}: {v[:8]}...{v[-4:] if len(v) > 12 else ''}")
    elif args.show:
        print("[CONFIG] Active Session Configuration:")
        print(f"  Base URL      : {cfg.get('base_url')}")
        print(f"  PHPSESSID     : {cfg.get('phpsessid', 'none')}")
        print(f"  Language      : {cfg.get('lang', 'en')}")
        print(f"  Target Goal   : ${cfg.get('target_goal_usd', 100.0):.2f}")
    else:
        print("[USAGE] python3 main.py cookies --set <token> OR python3 main.py cookies --show")

def handle_scan(args):
    cfg = load_config()
    goal = args.goal if args.goal is not None else cfg.get("target_goal_usd", 100.0)
    pages = args.pages if args.pages is not None else cfg.get("max_scan_pages", 50)
    run_scan(max_pages=pages, target_goal=goal)

def handle_list(args):
    tasks = get_tasks('shortlisted', args.limit)
    if not tasks:
        print("[INFO] Shortlist is currently empty. Run 'python3 main.py scan' to populate.")
        return
    print(f"\n{'ID':<8} {'PAYOUT':<10} {'SCORE':<7} {'CATEGORY':<14} {'TITLE'}")
    print("-" * 75)
    for t in tasks:
        title = t['title'][:35] + "..." if len(t['title']) > 35 else t['title']
        print(f"{t['task_id']:<8} +${t['price_usd']:<9.3f} {t['score']:<7} {t['category']:<14} {title}")
    summary = get_summary()
    print("-" * 75)
    print(f"Total: {summary['total_shortlisted_tasks']} tasks | Total Value: ${summary['total_shortlisted_value']:.2f} ({summary['goal_percentage']}% of ${summary['target_goal']:.2f})")

def handle_guide(args):
    print(get_task_guide(args.task_id))

def handle_complete(args):
    update_task_status(args.task_id, 'completed')
    print(f"[STATUS] Task #{args.task_id} marked as COMPLETED.")
    summary = get_summary()
    print(f"[PROGRESS] Completed: {summary['completed_count']} tasks (${summary['completed_value']:.2f})")

def handle_export(args):
    path = export_data(args.format)
    print(f"[EXPORT] Successfully saved shortlist to:\n{path}")

def handle_status(args):
    print(generate_report())

def handle_import_json(args):
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else data.get("tasks", [])
        count = 0
        for item in items:
            tid = item.get("taskId") or item.get("task_id") or item.get("id")
            if not tid:
                continue
            save_task({
                "task_id": tid,
                "title": item.get("title", ""),
                "url": item.get("url", f"https://seosprint.net/taskread/{tid}"),
                "price_usd": float(item.get("priceUSD", item.get("price_usd", 0.0))),
                "category": item.get("category", "Registration"),
                "emp_name": item.get("empName", item.get("emp_name", "")),
                "page_found": item.get("page", 1),
                "score": int(item.get("score", 75))
            })
            count += 1
        print(f"[IMPORT] Successfully imported {count} tasks into Sprinter database.")
        handle_status(None)
    except Exception as e:
        print(f"[ERROR] Failed to import JSON: {e}")

def handle_server(args):
    start_server(args.port)

def main():
    parser = argparse.ArgumentParser(description="Sprinter - SEOSprint Autonomous Task Analyzer & Goal Tracker")
    subparsers = parser.add_subparsers(dest="command")

    p_cookies = subparsers.add_parser("cookies", help="Manage session cookies")
    p_cookies.add_argument("--set", help="Set cookie string or PHPSESSID token")
    p_cookies.add_argument("--show", action="store_true", help="Show current cookies")

    p_scan = subparsers.add_parser("scan", help="Run automated task scanner")
    p_scan.add_argument("--goal", type=float, default=None, help="Target goal in USD (e.g. 100.0)")
    p_scan.add_argument("--pages", type=int, default=None, help="Maximum pages to scan (e.g. 50)")

    p_list = subparsers.add_parser("list", help="List shortlisted tasks")
    p_list.add_argument("--limit", type=int, default=25, help="Number of tasks to display")

    p_guide = subparsers.add_parser("guide", help="Get execution guide for a task")
    p_guide.add_argument("task_id", help="Task ID")

    p_complete = subparsers.add_parser("complete", help="Mark a task as completed")
    p_complete.add_argument("task_id", help="Task ID")

    p_export = subparsers.add_parser("export", help="Export shortlist to Downloads")
    p_export.add_argument("--format", choices=["json", "txt"], default="json", help="Export format")

    subparsers.add_parser("status", help="Display overall runner progress & summary")

    p_import = subparsers.add_parser("import-json", help="Import tasks from browser JSON export")
    p_import.add_argument("file", help="Path to JSON file")

    p_server = subparsers.add_parser("server", help="Start real-time receiver server on port 8080")
    p_server.add_argument("--port", type=int, default=8080, help="Server port")

    args = parser.parse_args()

    if args.command == "cookies":
        handle_cookies(args)
    elif args.command == "scan":
        handle_scan(args)
    elif args.command == "list":
        handle_list(args)
    elif args.command == "guide":
        handle_guide(args)
    elif args.command == "complete":
        handle_complete(args)
    elif args.command == "export":
        handle_export(args)
    elif args.command == "status":
        handle_status(args)
    elif args.command == "import-json":
        handle_import_json(args)
    elif args.command == "server":
        handle_server(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
