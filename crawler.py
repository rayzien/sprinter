import re
import time
import urllib.request
import urllib.error
from config import load_config, get_headers
from filter import parse_price, evaluate_task, estimate_time_minutes
from database import save_task, get_summary, record_scan_log, save_account_info

def fetch_page(page_num, cfg):
    base_url = cfg.get("base_url", "https://seosprint.run").rstrip("/")
    endpoint = cfg.get("task_endpoint", "/earn-task/2")
    sep = "&" if "?" in endpoint else "?"
    url = f"{base_url}{endpoint}{sep}page={page_num}"
    headers = get_headers(cfg)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            return content, resp.status
    except urllib.error.HTTPError as e:
        return None, e.code
    except Exception as e:
        return None, str(e)

def extract_account_info(html):
    """Parses user account statistics if available on page"""
    if not html or "ss_id = false" in html:
        return None
    uid_match = re.search(r'let ss_id\s*=\s*(\d+);', html)
    if not uid_match:
        return None
    uid = uid_match.group(1)
    # Check for balance
    bal_match = re.search(r'class="[^"]*(?:user-balance|balance|my-balance)[^"]*"[^>]*>([\d\.,]+)', html)
    balance = float(bal_match.group(1).replace(',', '.')) if bal_match else 0.0
    # Rating
    rat_match = re.search(r'class="[^"]*user-rating[^"]*"[^>]*>([\d\.,]+)', html)
    rating = float(rat_match.group(1).replace(',', '.')) if rat_match else 0.0

    acc = {
        "user_id": uid,
        "username": f"User #{uid}",
        "balance_usd": balance,
        "rating": rating,
        "status": "Active"
    }
    save_account_info(acc)
    return acc

def parse_tasks_from_html(html, page_num, base_url):
    tasks = []
    if not html:
        return tasks

    rows = re.findall(r'<tr[^>]*data-task-id="?(\d+)"?[^>]*>(.*?)</tr>', html, re.S)
    if not rows:
        rows = re.findall(r'<tr[^>]*class="[^"]*table-rtask[^"]*"[^>]*>(.*?)</tr>', html, re.S)

    for r in rows:
        r_text = r[1] if isinstance(r, tuple) else r
        link = re.search(r'href=["\'](/taskread/(\d+))["\']', r_text)
        if not link:
            continue
        t_id = link.group(2)
        t_url = f"{base_url.rstrip('/')}/taskread/{t_id}"

        title_match = re.search(r'<a[^>]*href=["\']/taskread/\d+["\'][^>]*>(.*?)</a>', r_text, re.S)
        raw_title = title_match.group(1) if title_match else f"Task #{t_id}"
        title = re.sub(r'<[^>]+>', '', raw_title).strip()

        emp_match = re.search(r'class=["\'][^"\']*(?:mem-nickname|emp-rating)[^"\']*["\'][^>]*>(.*?)<', r_text)
        emp_name = emp_match.group(1).strip() if emp_match else "Employer"

        price = parse_price(r_text)
        tasks.append({
            "task_id": t_id,
            "title": title,
            "url": t_url,
            "price_usd": price,
            "emp_name": emp_name,
            "page_found": page_num,
            "raw_text": r_text
        })
    return tasks

def run_scan(max_pages=None, target_goal=None, on_progress=None):
    cfg = load_config()
    max_pages = max_pages or cfg.get("max_scan_pages", 50)
    target_goal = target_goal or cfg.get("target_goal_usd", 100.0)
    delay = cfg.get("delay_seconds", 1.2)
    base_url = cfg.get("base_url", "https://seosprint.run")
    endpoint = cfg.get("task_endpoint", "/earn-task/2")

    print(f"[SCAN] Initializing scan for goal: ${target_goal:.2f} across up to {max_pages} pages")
    print(f"[SCAN] Target URL: {base_url}{endpoint}")
    print(f"[SCAN] Session: {cfg.get('phpsessid', 'none')[:10]}...")
    print("-" * 65)

    accumulated = get_summary(target_goal)["total_shortlisted_value"]
    matched_count = 0
    total_scanned_tasks = 0

    for page in range(1, max_pages + 1):
        html, status = fetch_page(page, cfg)
        if html is None:
            print(f"[SCAN] Page {page:02d}: Failed to fetch (Status: {status})")
            time.sleep(2)
            continue

        if "ss_id = false" in html or "Oops ... Sorry generously" in html:
            print(f"[WARN] Page {page:02d}: Session cookie is not active (Returned Guest mode / Denied).")
            print("[INFO] SEOSprint blocks expired/external sessions from raw CLI.")
            print("[ACTION] Run the realtime in-browser scanner on Kiwi Browser or update cookie via:")
            print("         python3 main.py cookies --set \"PHPSESSID=<fresh_cookie>\"")
            break

        # Check account info on first successful page
        extract_account_info(html)

        tasks = parse_tasks_from_html(html, page, base_url)
        if not tasks:
            print(f"[SCAN] Page {page:02d}: No more tasks found. Reached end of catalog.")
            break

        total_scanned_tasks += len(tasks)
        page_matches = 0

        for t in tasks:
            eval_res = evaluate_task(t["title"], t["raw_text"], t["price_usd"])
            if eval_res["valid"]:
                t["score"] = eval_res["score"]
                t["category"] = eval_res["category"]
                t["est_minutes"] = eval_res.get("est_minutes", 2.5)
                save_task(t)
                accumulated += t["price_usd"]
                matched_count += 1
                page_matches += 1

                pct = min(100.0, (accumulated / target_goal) * 100.0) if target_goal > 0 else 0.0
                print(f"[MATCH] Task #{t['task_id']} | ~{t['est_minutes']:.1f}m | +${t['price_usd']:.3f} | {t['title'][:30]} | Total: ${accumulated:.2f} ({pct:.1f}%)")

                if accumulated >= target_goal:
                    print("-" * 65)
                    print(f"[SUCCESS] Target goal reached: ${accumulated:.2f} / ${target_goal:.2f}")
                    record_scan_log(page, matched_count, accumulated)
                    return True

        pct = min(100.0, (accumulated / target_goal) * 100.0) if target_goal > 0 else 0.0
        print(f"[SCAN] Page {page:02d}/{max_pages} complete | Page Matches: {page_matches} | Total Shortlist: ${accumulated:.2f} ({pct:.1f}%)")

        if on_progress:
            on_progress(page, max_pages, accumulated, target_goal)

        time.sleep(delay)

    print("-" * 65)
    print(f"[COMPLETE] Scan finished | Tasks evaluated: {total_scanned_tasks} | Qualified: {matched_count} | Value: ${accumulated:.2f}")
    record_scan_log(page, matched_count, accumulated)
    return False
