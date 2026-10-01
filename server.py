"""Tiny local web server for the Interactive Globe System.

The camera only works on http://localhost (or https), so the page must be
served rather than opened as a file. Run:  python server.py

It also exposes POST /key?k=left|right, which presses a real (OS-level)
arrow key on Windows so other programs can react to it.
"""
import http.server
import socketserver
import webbrowser
import os
import sys
import time
from urllib.parse import urlparse, parse_qs

PORT = 8000
os.chdir(os.path.dirname(os.path.abspath(__file__)))

VK = {"left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28}
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002


def press_key(name):
    if sys.platform != "win32" or name not in VK:
        return False
    import ctypes
    user32 = ctypes.windll.user32
    vk = VK[name]
    scan = user32.MapVirtualKeyW(vk, 0)
    user32.keybd_event(vk, scan, KEYEVENTF_EXTENDEDKEY, 0)
    time.sleep(0.03)
    user32.keybd_event(vk, scan, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
    return True


class Handler(http.server.SimpleHTTPRequestHandler):
    # Windows' registry often maps these wrong, which breaks ES modules / wasm.
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".mjs": "text/javascript",
        ".js": "text/javascript",
        ".wasm": "application/wasm",
        ".mp4": "video/mp4",
        ".task": "application/octet-stream",
    }

    def do_POST(self):
        url = urlparse(self.path)
        if url.path == "/key":
            name = parse_qs(url.query).get("k", [""])[0].lower()
            ok = press_key(name)
            print(f"key press: {name} -> {'sent' if ok else 'not sent'}")
            self.send_response(200 if ok else 400)
            self.end_headers()
            return
        self.send_error(404)

    def log_message(self, *args):
        pass


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    with Server(("127.0.0.1", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}/index.html"
        print(f"Interactive Globe running at {url}  (Ctrl+C to stop)")
        if os.environ.get("NO_BROWSER") != "1":
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
