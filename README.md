# Sprinter - SEOSprint Task Analyzer & Goal Runner Bot

Sprinter is a modular Python-based task scraper, analyzer, and progress tracker built for automated micro-task workflows. It filters and shortlists high-efficiency tasks towards a custom payout goal (e.g. $100) while strictly enforcing speed and safety criteria.

## Core Features

- Target Goal Tracking: Monitors accumulated task earnings towards a target dollar goal.
- Strict Rule Enforcement:
  - Email signup only.
  - Mobile/phone friendly tasks only.
  - Strict exclusion of KYC, passport, ID, and selfie verification.
  - Strict exclusion of phone number and SMS verification.
  - Strict exclusion of deposits, payments, and multi-day grinds.
  - Prioritizes tasks with 2-3 minute completion windows.
- Persistent Session & Cookie Management: Update PHPSESSID, language, or Cloudflare tokens dynamically.
- SQLite Database Storage: Keeps track of shortlisted, active, and completed tasks.
- Dual Ingestion: Run live scans directly from Python or import JSON captures from browser sessions.
- Execution Guide Generator: Step-by-step assistance for fast report submissions.

## Architecture

- config.py: Manages persistent credentials, user agents, endpoints, and targets.
- filter.py: Rule-based regex scoring engine detecting KYC, SMS, and signup criteria.
- crawler.py: Automated multi-page fetcher with real-time CLI terminal progress.
- database.py: SQLite storage for task records, payouts, and scan logs.
- analyzer.py: Report generation, task guides, and export utilities.
- main.py: Unified CLI entrypoint.

## Installation & Setup

```bash
cd ~/sprinter
chmod +x main.py
```

## CLI Usage

### 1. Configure Cookies
```bash
python3 main.py cookies --set "PHPSESSID=your_session_cookie; lang=en"
python3 main.py cookies --show
```

### 2. Run Automated Task Scanner
```bash
python3 main.py scan --goal 100 --pages 50
```

### 3. Review Shortlist & Status
```bash
python3 main.py list
python3 main.py status
```

### 4. Get Task Execution Guide
```bash
python3 main.py guide <task_id>
```

### 5. Mark Completed Task
```bash
python3 main.py complete <task_id>
```

### 6. Export Shortlist
```bash
python3 main.py export --format json
python3 main.py export --format txt
```

### 7. Import Browser Captured JSON
```bash
python3 main.py import-json ~/downloads/seosprint_tasks.json
```

## Integration with Antigravity AI

Antigravity operates Sprinter autonomously via CLI commands:
1. Update tokens: `python3 main.py cookies --set <token>`
2. Execute scans: `python3 main.py scan`
3. Analyze pipeline: `python3 main.py status`
4. Guide user: `python3 main.py guide <task_id>`
