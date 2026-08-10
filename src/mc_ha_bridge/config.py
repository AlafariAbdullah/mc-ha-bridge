"""Config loading and validation for mc-ha-bridge."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml


@dataclass
class ButtonConfig:
    name: str
    coords: tuple  # (x, y, z)
    webhook_id: str


@dataclass
class BridgeConfig:
    save_path: Path
    log_path: Path
    ha_base_url: str
    buttons: List[ButtonConfig]


def load_config(path: str) -> BridgeConfig:
    config_path = Path(path).expanduser()
    if not config_path.exists():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        print("Copy config.example.yaml to config.yaml and edit it first.", file=sys.stderr)
        sys.exit(1)

    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    try:
        mc = raw["minecraft"]
        ha = raw["home_assistant"]
        buttons_raw = raw["buttons"]
    except KeyError as e:
        print(f"Missing required config section: {e}", file=sys.stderr)
        sys.exit(1)

    if not buttons_raw:
        print("Config has no buttons defined.", file=sys.stderr)
        sys.exit(1)

    buttons = []
    seen_names = set()
    seen_webhooks = set()
    for entry in buttons_raw:
        name = entry["name"]
        coords = tuple(entry["coords"])
        webhook_id = entry["webhook_id"]

        if len(coords) != 3:
            print(f"Button '{name}' has invalid coords (need exactly 3): {coords}", file=sys.stderr)
            sys.exit(1)
        if name in seen_names:
            print(f"Duplicate button name in config: {name}", file=sys.stderr)
            sys.exit(1)
        if webhook_id in seen_webhooks:
            print(f"Duplicate webhook_id in config: {webhook_id}", file=sys.stderr)
            sys.exit(1)
        seen_names.add(name)
        seen_webhooks.add(webhook_id)

        buttons.append(ButtonConfig(name=name, coords=coords, webhook_id=webhook_id))

    return BridgeConfig(
        save_path=Path(mc["save_path"]).expanduser(),
        log_path=Path(mc["log_path"]).expanduser(),
        ha_base_url=ha["base_url"].rstrip("/"),
        buttons=buttons,
    )
