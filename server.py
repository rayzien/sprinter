import http.server
import socketserver
import os
import json
import urllib.parse
from database import save_task, get_summary, get_tasks, update_task_status, get_task_by_id

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class SprinterHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/bulk-shortlist':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8')
                data = json.loads(body)
                tasks = data if isinstance(data, list) else data.get("tasks", [])
                
                saved_count = 0
                for t in tasks:
                    tid = str(t.get("id") or t.get("taskId") or "").strip()
                    if not tid:
                        continue
                    save_task({
                        "task_id": tid,
                        "title": str(t.get("title") or f"Task {tid}").strip(),
                        "url": str(t.get("url") or f"https://seosprint.net/taskread/{tid}").strip(),
                        "price_usd": float(t.get("priceUSD") or t.get("price_usd") or 0.0),
                        "category": str(t.get("category") or "Email Signup").strip(),
                        "emp_name": str(t.get("empName") or t.get("emp_name") or "Employer").strip(),
                        "page_found": int(t.get("page", 1)),
                        "score": int(t.get("score", 75))
                    })
                    saved_count += 1
                
                summary = get_summary()
                print(f"[SERVER] Received & saved {saved_count} tasks. Total Shortlist: ${summary['total_shortlisted_value']:.2f}")

                resp = json.dumps({"status": "ok", "saved_count": saved_count, "summary": summary}).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                err = json.dumps({"status": "error", "message": str(e)}).encode('utf-8')
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(err)))
                self.end_headers()
                self.wfile.write(err)
        elif parsed.path == '/api/complete':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
                data = json.loads(body)
                task_id = data.get("task_id")
                if task_id:
                    update_task_status(task_id, 'completed')
                    summary = get_summary()
                    resp = json.dumps({"status": "ok", "summary": summary}).encode('utf-8')
                else:
                    resp = json.dumps({"status": "error", "message": "Missing task_id"}).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                err = json.dumps({"status": "error", "message": str(e)}).encode('utf-8')
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(err)))
                self.end_headers()
                self.wfile.write(err)
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/status':
            summary = get_summary()
            resp = json.dumps(summary).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
        elif parsed.path == '/api/tasks':
            params = urllib.parse.parse_qs(parsed.query)
            status = params.get('status', ['shortlisted'])[0]
            limit = int(params.get('limit', [100])[0])
            tasks = get_tasks(status=status, limit=limit)
            resp = json.dumps(tasks).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
        else:
            super().do_GET()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def start_server(port=PORT):
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", port), SprinterHandler) as httpd:
        print(f"[SERVER] Sprinter sync server listening on http://127.0.0.1:{port}")
        print("[SERVER] Real-time task receiver endpoint: http://127.0.0.1:8080/api/bulk-shortlist")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[SERVER] Shutting down.")

if __name__ == '__main__':
    start_server()
