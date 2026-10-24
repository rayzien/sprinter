import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "base_url": "https://seosprint.run",
    "task_endpoint": "/earn-task/2",
    "phpsessid": "j8dhaab0fssdltl7gj58518arn",
    "lang": "en",
    "cf_clearance": "",
    "user_agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "target_goal_usd": 100.0,
    "max_scan_pages": 50,
    "delay_seconds": 1.2
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(cfg)
            return merged
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def get_cookie_header(cfg=None):
    if cfg is None:
        cfg = load_config()
    cookies = []
    if cfg.get("phpsessid"):
        cookies.append(f"PHPSESSID={cfg['phpsessid']}")
    if cfg.get("lang"):
        cookies.append(f"lang={cfg['lang']}")
    if cfg.get("cf_clearance"):
        cookies.append(f"cf_clearance={cfg['cf_clearance']}")
    return "; ".join(cookies)

def get_headers(cfg=None):
    if cfg is None:
        cfg = load_config()
    return {
        "User-Agent": cfg.get("user_agent", DEFAULT_CONFIG["user_agent"]),
        "Cookie": get_cookie_header(cfg),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"{cfg.get('base_url', 'https://seosprint.run')}/",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document"
    }

def update_cookies_from_raw(raw_input):
    cfg = load_config()
    raw = raw_input.strip()
    if "=" not in raw and len(raw) > 15:
        cfg["phpsessid"] = raw
        save_config(cfg)
        return {"phpsessid": raw}

    parts = [p.strip() for p in raw.split(";") if p.strip()]
    updated = {}
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k.upper() == "PHPSESSID":
                cfg["phpsessid"] = v
                updated["phpsessid"] = v
            elif k.lower() == "lang":
                cfg["lang"] = v
                updated["lang"] = v
            elif k.lower() == "cf_clearance":
                cfg["cf_clearance"] = v
                updated["cf_clearance"] = v
    if updated:
        save_config(cfg)
    return updated
