"""Command-line interface for mc-ha-bridge."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import load_config
from .datapack_gen import generate as generate_datapack
from .watcher import run as run_watcher


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mc-ha-bridge",
        description="Trigger Home Assistant automations from buttons pressed in a cheats-off vanilla Minecraft world.",
    )
    parser.add_argument("--version", action="version", version=f"mc-ha-bridge {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Generate the datapack from your config")
    init_parser.add_argument("--config", default="config.yaml", help="Path to config.yaml (default: config.yaml)")

    watch_parser = subparsers.add_parser("watch", help="Watch the log and fire HA webhooks")
    watch_parser.add_argument("--config", default="config.yaml", help="Path to config.yaml (default: config.yaml)")

    args = parser.parse_args()

    if args.command == "init":
        config = load_config(args.config)
        out_path = generate_datapack(config)
        print(f"Datapack written to: {out_path}")
        print("Reload your Minecraft world (title screen -> re-enter) for it to load.")
    elif args.command == "watch":
        config = load_config(args.config)
        run_watcher(config)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
