"""Tails Minecraft's latest.log and fires the matching Home Assistant
webhook for each configured button."""

from __future__ import annotations

import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

from .config import BridgeConfig

PATTERN = re.compile(r"BUTTON:(\w+):PRESSED")

CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"


def _follow(path: Path):
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, 2)  # start at end of file, ignore existing history
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.25)
                continue
            yield line


def run(config: BridgeConfig) -> None:
    if not config.log_path.exists():
        print(f"Log file not found: {config.log_path}", file=sys.stderr)
        print("Check minecraft.log_path in your config.", file=sys.stderr)
        sys.exit(1)

    webhook_by_name = {b.name: b.webhook_id for b in config.buttons}

    print(f"Watching {config.log_path} for button presses... (Ctrl+C to stop)")

    try:
        for line in _follow(config.log_path):
            match = PATTERN.search(line)
            if not match:
                continue

            name = match.group(1)
            webhook_id = webhook_by_name.get(name)
            ts = datetime.now().strftime("%H:%M:%S")

            if not webhook_id:
                print(f"[{ts}] {RED}Unrecognized button '{name}' — not in config{RESET}")
                continue

            url = f"{config.ha_base_url}/api/webhook/{webhook_id}"
            try:
                resp = requests.post(url, timeout=3)
                if resp.ok:
                    print(f"[{ts}] {CYAN}[{name}] webhook fired -> {webhook_id} ({resp.status_code}){RESET}")
                else:
                    print(f"[{ts}] {RED}[{name}] webhook failed -> {webhook_id} ({resp.status_code}){RESET}")
            except requests.RequestException as e:
                print(f"[{ts}] {RED}[{name}] webhook error: {e}{RESET}")
    except KeyboardInterrupt:
        print("\nStopped.")
