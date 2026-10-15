# mc-ha-bridge

Trigger Home Assistant automations from physical buttons/levers pressed in a
**vanilla, cheats-off** Minecraft world. No mods, no command blocks, no
server plugins — just a datapack (which loads without cheats being enabled)
and a small watcher process outside the game.

## How it works

Vanilla Minecraft has no way to make an HTTP request from inside the game,
so this uses a two-part bridge:

1. A **datapack** watches your in-game buttons every tick and, on each
   press, writes a line like `BUTTON:hidden:PRESSED` into the game's log
   (`latest.log`) via `/say`. Datapacks run automatically when a world
   loads and are unaffected by the "Allow Cheats" world setting — only
   *player-typed* commands are gated by that.
2. A small **watcher** process (this tool) tails that log file on your
   computer, and fires a Home Assistant webhook for each press.

```
[in-game button] → [datapack, /say to log] → [watcher tails log] → [HA webhook] → [your automation]
```

## Requirements

- Python 3.9+
- A Home Assistant instance reachable from the machine running the watcher
- A vanilla Minecraft world (singleplayer is fine) with cheats off

## Install
From inside the folder (From Source):
```bash
pip install -e .
```

## Setup

### 1. Build your circuit(s) in-game

Place a button (or lever) for each device you want to control. Note each
one's coordinates by standing next to it and pressing `F3`.

### 2. Write your config

Copy `config.example.yaml` to `config.yaml` and fill in your paths, your
Home Assistant URL, and one entry per button:

```yaml
minecraft:
  save_path: ~/.local/share/PrismLauncher/instances/26.2/minecraft/saves/CurrentWorld
  log_path: ~/.local/share/PrismLauncher/instances/26.2/minecraft/logs/latest.log

home_assistant:
  base_url: http://192.168.1.175:8123

buttons:
  - name: hidden
    coords: [-133, 128, -795]
    webhook_id: mc_hidden
  - name: spots2
    coords: [-131, 128, -795]
    webhook_id: mc_spots2
```

`save_path` and `log_path` support `~`. `log_path` is usually at the
*instance* level (shared across all worlds in that instance), not inside
the save folder itself — check your launcher if unsure.

### 3. Generate and install the datapack

```bash
mc-ha-bridge init --config config.yaml
```

This writes a complete datapack into
`<save_path>/datapacks/mc_ha_bridge/`. Fully re-run this any time you
change your config — it overwrites the generated files cleanly.

Then, in-game: return to the title screen and re-enter the world so the
datapack loads. Press a button and confirm you see e.g. `BUTTON:hidden:PRESSED`
appear in chat.

If your Minecraft version needs a different `pack_format`, edit the
generated `pack.mcmeta` — see the
[Minecraft Wiki's Data Pack format table](https://minecraft.wiki/w/Data_pack#Pack_format)
for your version.

### 4. Set up Home Assistant

For each button, you need a webhook trigger in HA whose ID matches the
`webhook_id` in your config. The simplest approach is one automation with
one trigger per button, routed with `choose:`. Example for two buttons —
extend the pattern for the rest of yours:

```yaml
alias: mc-ha-bridge buttons
trigger:
  - platform: webhook
    webhook_id: mc_hidden
    local_only: false
    id: hidden
  - platform: webhook
    webhook_id: mc_spots2
    local_only: false
    id: spots2
action:
  - choose:
      - conditions:
          - condition: trigger
            id: hidden
        sequence:
          - service: switch.toggle
            target:
              entity_id: switch.your_entity_here
      - conditions:
          - condition: trigger
            id: spots2
        sequence:
          - service: switch.toggle
            target:
              entity_id: switch.your_other_entity_here
mode: parallel
```

Add this via Settings → Automations & Scenes → Create Automation → ⋮ →
Edit in YAML.

### 5. Run the watcher

```bash
mc-ha-bridge watch --config config.yaml
```

Press your buttons in-game — you should see confirmation in the terminal
and your Home Assistant devices respond.

### 6. (Optional) Run it as a background service

See `systemd/mc-ha-bridge.service.example` for a template to run the
watcher automatically on login, instead of manually in a terminal.

## Troubleshooting

- **Nothing shows up in chat when I press a button** — double check the
  coordinates in the generated `tick.mcfunction`, and that you reloaded
  the world after running `init`.
- **Chat shows the press but the terminal shows nothing** — check
  `log_path` in your config points at the *live* `latest.log` for the
  instance you're actually playing.
- **Terminal shows the webhook fired but HA doesn't respond** — check the
  `webhook_id` matches exactly between your config and the HA automation,
  and that `base_url` is reachable from the machine running the watcher.

## License

MIT - see `LICENSE`.
