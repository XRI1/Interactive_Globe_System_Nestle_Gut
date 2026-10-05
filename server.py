"""Tiny local web server for the Interactive Globe System.

The camera only works on http://localhost (or https), so the page must be
served rather than opened as a file. Run:  python server.py

It also exposes:
  POST /key?k=left|right  presses a real (OS-level) arrow key on Windows
  POST /zone              saves the detection zone (from setup.html) to zone.json

When an arrow key is pressed, the same command ("LEFT" / "RIGHT") is also sent
to the ESP32 over USB serial, e.g. to switch its light on.
"""
import http.server
import socketserver
import webbrowser
import os
import sys
import time
import json
import socket
import threading
from urllib.parse import urlparse, parse_qs

PORT = 8000
ZONE_FILE = "zone.json"
LOG_FILE = "server.log"
os.chdir(os.path.dirname(os.path.abspath(__file__)))

VK = {"left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28}
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

def log(msg):
    """Print to the server window and append to server.log (useful for checking what happened)."""
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


# ---------- ESP32 (USB serial) ----------
ESP32_PORT = os.environ.get("ESP32_PORT", "auto")   # "auto", or e.g. "COM3"; "off" disables it
ESP32_BAUD = 115200
# USB-serial chips used on ESP32 boards: CH340/CH9102, CP210x, FTDI, Espressif native USB
ESP32_USB_VIDS = {0x1A86, 0x10C4, 0x0403, 0x303A}


class Esp32:
    """Keeps one serial connection open (opening the port can reset the ESP32)."""

    def __init__(self):
        self.ser = None
        self.lock = threading.Lock()

    def _find_port(self):
        if ESP32_PORT.lower() != "auto":
            return ESP32_PORT
        from serial.tools import list_ports
        for p in list_ports.comports():
            if p.vid in ESP32_USB_VIDS:
                return p.device
        return None

    def _connect(self):
        try:
            import serial
        except ImportError:
            log("ESP32: pyserial not installed (run: python -m pip install pyserial)")
            return False
        port = self._find_port()
        if not port:
            log("ESP32: no board found")
            return False
        try:
            ser = serial.Serial()
            ser.port, ser.baudrate, ser.timeout, ser.write_timeout = port, ESP32_BAUD, 0, 1
            ser.dtr = ser.rts = False          # don't reset the board when opening
            ser.open()
            self.ser = ser
            log(f"ESP32: connected on {port}")
            return True
        except Exception as e:
            log(f"ESP32: could not open {port}: {e}")
            return False

    def send(self, command):
        if ESP32_PORT.lower() == "off":
            return False
        with self.lock:
            for _ in range(2):                 # retry once after a reconnect
                if not self.ser and not self._connect():
                    return False
                try:
                    self.ser.write((command + "\n").encode())
                    self.ser.flush()
                    log(f"ESP32: sent {command}")
                    time.sleep(0.2)
                    reply = self.ser.read(500).decode(errors="replace").strip()
                    if reply:
                        log(f"ESP32 replied: {reply}")
                    return True
                except Exception as e:
                    log(f"ESP32: write failed ({e}), reconnecting")
                    try:
                        self.ser.close()
                    except Exception:
                        pass
                    self.ser = None
            return False


esp32 = Esp32()


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
            log(f"key press: {name} -> {'sent' if ok else 'not sent'}")
            if name in ("left", "right"):
                esp32.send(name.upper())
            self.send_response(200 if ok else 400)
            self.end_headers()
            return
        if url.path == "/zone":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length))
                zone = {k: round(float(data[k]), 4) for k in ("x0", "x1", "y0", "y1")}
                if not (0 <= zone["x0"] < zone["x1"] <= 1 and 0 <= zone["y0"] < zone["y1"] <= 1):
                    raise ValueError("zone out of range")
            except (ValueError, KeyError, TypeError) as e:
                self.send_error(400, str(e))
                return
            with open(ZONE_FILE, "w", encoding="utf-8") as f:
                json.dump(zone, f, indent=2)
            log(f"zone saved: {zone}")
            self.send_response(200)
            self.end_headers()
            return
        self.send_error(404)

    def end_headers(self):
        # Always re-check files, so replaced videos/images show up after a reload.
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, *args):
        pass


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    # HTTPServer enables SO_REUSEADDR, which on Windows lets a second server share
    # the port while the OLD one keeps answering. Demand exclusive use instead.
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


if __name__ == "__main__":
    try:
        httpd = Server(("127.0.0.1", PORT), Handler)
    except OSError as e:
        log(f"Port {PORT} is already in use ({e}). Close the other 'Globe Server' window and try again.")
        time.sleep(10)
        sys.exit(1)
    with httpd:
        page = sys.argv[1] if len(sys.argv) > 1 else "index.html"
        url = f"http://localhost:{PORT}/{page}"
        log(f"Interactive Globe running at {url}  (Ctrl+C to stop)")
        if ESP32_PORT.lower() != "off":
            esp32.send("HELLO")                # connect at startup; the ESP32 ignores this
        if os.environ.get("NO_BROWSER") != "1":
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
