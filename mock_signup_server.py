"""Local mock signup server for testing Account Farming Bot offline.

Serves a minimal registration form that mimics a real AI-platform signup page:
  - GET  /register  -> HTML form with email + password inputs and a submit button
  - POST /register  -> "success" page containing a success indicator ("welcome")

This lets you validate the bot's full pipeline (email -> DB -> browser -> fill ->
submit -> validate -> registered) WITHOUT any external service, proxy, or CAPTCHA.

Run:     python mock_signup_server.py
Point:   TARGET_URL=http://127.0.0.1:8899/register  (use the "mock" platform entry)
This is for LOCAL TESTING ONLY -- not part of production.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import html

HOST = "127.0.0.1"
PORT = 8899

FORM_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Mock AI Platform - Sign Up</title></head>
<body>
  <h1>Create your account</h1>
  <form method="POST" action="/register">
    <label>Email:<br><input type="email" name="email" placeholder="you@example.com" required></label><br><br>
    <label>Password:<br><input type="password" name="password" placeholder="********" required></label><br><br>
    <button type="submit">Sign Up</button>
  </form>
</body>
</html>"""

SUCCESS_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Mock AI Platform - Welcome</title></head>
<body>
  <h1>Welcome!</h1>
  <p>Your account has been created successfully. Please check your email to verify.</p>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if urlparse(self.path).path in ("/", "/register"):
            self._send(200, FORM_HTML)
        else:
            self._send(404, "<h1>404 Not Found</h1>")

    def do_POST(self):
        if urlparse(self.path).path != "/register":
            self._send(404, "<h1>404 Not Found</h1>")
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8", "ignore")
        try:
            data = {k: v[0] for k, v in parse_qs(body).items()}
            email = html.escape(data.get("email", ""))
            print(f"[mock] Registration received for: {email}", flush=True)
        except Exception:
            pass
        self._send(200, SUCCESS_HTML)

    def _send(self, code, content):
        payload = content.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Mock signup server running at http://{HOST}:{PORT}/register (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
