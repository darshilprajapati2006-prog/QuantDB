"""
QuantDB Public Sharing Utility.
Generates a secure, temporary public HTTPS link using Cloudflare Tunnel
so your friends, teammates, or professors can access the app from anywhere.
"""

import os
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path


def find_active_streamlit_port(ports=(8501, 8502, 8503)) -> int:
    """Finds which local port has an active Streamlit server running."""
    for p in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", p)) == 0:
                return p
    return 8501


CLOUDFLARED_BIN = Path(sys.prefix) / "Lib" / "site-packages" / "pycloudflared" / "cloudflared-windows-amd64.exe"

if not CLOUDFLARED_BIN.exists():
    print("cloudflared binary not found. Please install pycloudflared:")
    print("python -m pip install pycloudflared")
    sys.exit(1)

port = find_active_streamlit_port()
local_url = f"http://127.0.0.1:{port}"

print("=" * 65)
print("  QUANTDB — GENERATING PUBLIC SHARING LINK")
print("=" * 65)
print(f"Connecting Cloudflare Tunnel to local Streamlit ({local_url})...")

proc = subprocess.Popen(
    [str(CLOUDFLARED_BIN), "tunnel", "--url", local_url, "--no-autoupdate"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
)

tunnel_url = None
stop_event = threading.Event()


def log_reader():
    global tunnel_url
    for line in iter(proc.stdout.readline, ""):
        if not line:
            break
        if not tunnel_url:
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match:
                tunnel_url = match.group(0)
        if stop_event.is_set():
            break


reader_thread = threading.Thread(target=log_reader, daemon=True)
reader_thread.start()

start_time = time.time()
while time.time() - start_time < 30 and not tunnel_url:
    time.sleep(0.3)

if tunnel_url:
    try:
        Path("tunnel_url.txt").write_text(tunnel_url.strip(), encoding="utf-8")
    except Exception:
        pass
    print("\n" + "=" * 65, flush=True)
    print(">>> PUBLIC LINK READY! SEND THIS TO YOUR FRIEND:", flush=True)
    print(f"\n   URL: {tunnel_url}\n", flush=True)
    print("=" * 65, flush=True)
    print("Academic Demo Login Credentials:", flush=True)
    print("  * Admin:      admin01      / Admin01@QuantDB", flush=True)
    print("  * Researcher: researcher01 / Researcher01@QuantDB", flush=True)
    print("  * Trader:     trader01     / Trader01@QuantDB", flush=True)
    print("  * Standard:   user01       / User01@QuantDB", flush=True)
    print("  * Or they can click 'CREATE ACCOUNT' to register their own!", flush=True)
    print("=" * 65, flush=True)
    print("[ACTIVE] Tunnel is LIVE and healthy. Keep this window open!", flush=True)
    print("Press Ctrl + C when you want to stop sharing.\n", flush=True)

    try:
        while proc.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Cloudflare Tunnel...")
        stop_event.set()
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        print("Tunnel closed safely.")
else:
    print("Failed to capture public URL within 30 seconds.")
    proc.terminate()
