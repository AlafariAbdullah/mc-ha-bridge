"""Generates a Minecraft datapack from a BridgeConfig.

The generated datapack logs `BUTTON:<name>:PRESSED` to the game log every
time the corresponding button is pressed, using rising-edge detection so
one physical press produces exactly one log line.
"""

from __future__ import annotations

from pathlib import Path

from .config import BridgeConfig

PACK_MCMETA = """{
  "pack": {
    "pack_format": 48,
    "description": "mc-ha-bridge button press logger"
  }
}
"""

DATAPACK_NAME = "mc_ha_bridge"


def generate(config: BridgeConfig) -> Path:
    base = config.save_path / "datapacks" / DATAPACK_NAME
    func_dir = base / "data" / "mcbtn" / "function"
    tags_dir = base / "data" / "minecraft" / "tags" / "function"

    func_dir.mkdir(parents=True, exist_ok=True)
    tags_dir.mkdir(parents=True, exist_ok=True)

    (base / "pack.mcmeta").write_text(PACK_MCMETA, encoding="utf-8")
    (tags_dir / "load.json").write_text('{ "values": ["mcbtn:load"] }\n', encoding="utf-8")
    (tags_dir / "tick.json").write_text('{ "values": ["mcbtn:tick"] }\n', encoding="utf-8")

    load_lines = ["scoreboard objectives add raw dummy"]
    tick_lines = []

    for btn in config.buttons:
        x, y, z = btn.coords
        load_lines.append(f"scoreboard players set {btn.name} raw 0")

        tick_lines.append(
            f"execute if block {x} {y} {z} #minecraft:buttons[powered=true] "
            f"if score {btn.name} raw matches 0 run function mcbtn:press_{btn.name}"
        )
        tick_lines.append(
            f"execute if block {x} {y} {z} #minecraft:buttons[powered=true] "
            f"run scoreboard players set {btn.name} raw 1"
        )
        tick_lines.append(
            f"execute unless block {x} {y} {z} #minecraft:buttons[powered=true] "
            f"run scoreboard players set {btn.name} raw 0"
        )

        (func_dir / f"press_{btn.name}.mcfunction").write_text(
            f"say BUTTON:{btn.name}:PRESSED\n", encoding="utf-8"
        )

    (func_dir / "load.mcfunction").write_text("\n".join(load_lines) + "\n", encoding="utf-8")
    (func_dir / "tick.mcfunction").write_text("\n".join(tick_lines) + "\n", encoding="utf-8")

    return base
