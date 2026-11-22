# Koolnova for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![release](https://img.shields.io/github/v/release/thcuba/homeassistant-koolnova)](https://github.com/thcuba/homeassistant-koolnova/releases)

Custom integration that controls **Koolnova** HVAC systems from Home Assistant through their cloud
API. Zones, the project as a whole, and (on legacy accounts) the physical hub are exposed as
`climate` entities, plus a connectivity binary sensor per project.

Requires Home Assistant 2026.11.0 or newer and a Koolnova app account.

> ⚠️ Koolnova bans your IP automatically if their API receives more than one request every
> 30 seconds, and also on repeated failed logins. The integration never sends two requests less
> than 10 s apart and backs off for 300 s after a failed login — do not force these lower.

## Features

- ❄️ **HVAC modes per zone and globally** (COOL / HEAT / OFF), plus the five modes the official app
  offers — cool air, hot air, heat floor, cool floor + cool air, heat floor + hot air — selectable as
  **presets** on the project entity
- 🎛️ **`koolnova.set_all_zones_mode` service** to set the mode of every zone at once
- 🌡️ **Target temperature** per zone and global median across zones
- 🌬️ **Fan speed** per zone (LOW / MEDIUM / HIGH / AUTO)
- 🏠 **Global project control** (mode, ECO, stop) on a single `climate` entity
- 🧊 **Hub control** on legacy accounts: one `climate` entity per hub with ON/OFF and the behavior
  mode (manual / auto / planning)
- 📶 **Connectivity binary sensor** per project (online/offline)
- 💧 **Per-zone humidity and CO₂**: a `sensor` per room that reports one
  (`sensor.koolnova_<room>_humidity`, `sensor.koolnova_<room>_co2`)
- 🔌 **Per-zone on/off**: a `switch` per room (`switch.koolnova_<room>_power`) toggles the zone
  straight from the dashboard; zone `climate` modes display as **On/Off** instead of Auto/Off (the
  codes sent to the API are unchanged)
- 🛡️ **Robust against the brittle API**: retries with exponential backoff on timeouts, network
  errors, rate limiting (429) and server errors (5xx); auto-refreshes the session token on 401;
  a 50 s per-request timeout, floored at 45 s; falls back to the `/devices/` endpoint when the
  main ones fail
- ⏱️ **Request throttle**: two API calls never leave less than 10 s apart, shared by the whole
  process. A full refresh (3 + N requests) and a multi-zone command (one PATCH per zone) reach
  Koolnova spread out instead of in the same instant — which is what triggers the IP ban
- 🔄 **Staggered polling**: sensors every cycle, the more expensive project list cached
- 🎛️ **Setup and intervals configurable from the UI**
- 🌍 Translations: English, Spanish, Italian

## Entities

| Entity | Domain | Purpose |
|---|---|---|
| `climate.koolnova_*` (project) | climate | Global control: target temperature (median of zones), project HVAC mode, ECO/stop, and the five app modes as **presets**; exposes `project_mode_raw`, `heat_source`, `configured_heat_source` |
| `climate.koolnova_*` (zone) | climate | One per room: temperature, setpoint, HVAC mode, fan speed |
| `climate.koolnova_hub_*` | climate | Legacy hub, one per hub: ON/OFF + manual / auto / planning |
| `switch.koolnova_<room>_power` | switch | One per room: power on/off toggle |
| `sensor.koolnova_<room>_humidity` | sensor | One per room that reports humidity: relative humidity (%) |
| `sensor.koolnova_<room>_co2` | sensor | One per room that reports CO₂ (ppm) |
| `sensor.koolnova_connectivity_status` | sensor | Online/offline + WiFi signal, last sync, per-room last update |
| `binary_sensor.koolnova_connectivity_status` | binary_sensor | Online/offline per project, ready for automations |

The integration also fires a `koolnova_update_completed` event after every poll with counts and a
`lastsync` timestamp — handy for automation triggers. See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Dashboards

No dashboard ships with the integration — you build one from the entities above. Two starting
points are documented in [docs/DASHBOARDS.md](docs/DASHBOARDS.md): a **plain Home Assistant** one
(core `thermostat` + `tile` cards, no extra dependency) and a
**[Mushroom](https://github.com/piitaya/lovelace-mushroom)** one (more compact). That doc also
covers other patterns, like grouping fan control by floor instead of by zone.

## Installation

### HACS (recommended)

1. HACS → ⋮ menu → **Custom repositories** → add
   `https://github.com/thcuba/homeassistant-koolnova` with category *Integration*.
2. Search for **Koolnova**, download it and restart Home Assistant.

### Manual

Copy `custom_components/koolnova/` into the `custom_components` directory of your configuration
and restart Home Assistant.

## Configuration

**Settings → Devices & services → Add integration → Koolnova**, using your Koolnova app
credentials.

Options available afterwards through *Configure*:

| Option | Default | Range |
|---|---|---|
| Update interval | 30 s | 30–3600 s |
| Project refresh frequency | every 10 cycles | 1–300 |
| Project HVAC modes | COOL, HEAT | COOL / HEAT / OFF / AUTO |
| Zone HVAC modes | OFF, AUTO | COOL / HEAT / OFF / AUTO |
| Temperature range | 21–27 °C | 15–35 °C |
| Temperature precision | 0.5 °C | 0.5 or 1 °C |
| API request timeout | 50 s | 45–300 s |
| Project heat source | air | air / floor / both |

`Project heat source` tells the integration which circuit(s) your installation drives. The app lists
the circuits as separate entries — cool air, hot air, heat floor, heat floor + hot air, cool floor +
cool air — while Home Assistant only has one `heat` and one `cool`, so this option decides which entry
is sent. Pick `air` for ducted units only (the default), `floor` for an underfloor circuit alone
(heating only: the app has no cool-floor-only entry), or `both` when the two work together — see
[docs/API.md](docs/API.md#project-mode-mode).

The five entries are also exposed as **presets** on the project entity (`cool_air`, `hot_air`,
`heat_floor`, `cool_both`, `heat_both`): a preset sends its own code straight away and does not read
this option, which is the simplest way to get exactly what the app shows.

## Services

### `koolnova.set_all_zones_mode`

Set the HVAC mode of every zone of a project in one call — the action that used to live in the
presets of the project entity.

| Field | Required | Values |
|---|---|---|
| `mode` | yes | `cool` / `heat` / `off` / `auto` |
| `target` | no | any Koolnova `climate` entity; omitted means every project |

```yaml
action: koolnova.set_all_zones_mode
target:
  entity_id: climate.koolnova_ac_casa_controllo_globale
data:
  mode: "off"
```

The call reports how many zones were updated in the log. Zone modes use their own encoding
(`00` cool, `01` heat, `02` off, `03` auto), which is not the project `mode` table.

## Documentation

- [CHANGELOG.md](CHANGELOG.md) — version history
- [docs/DASHBOARDS.md](docs/DASHBOARDS.md) — example Lovelace dashboards
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — common problems
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) — architecture, test environment and releases
- [docs/API.md](docs/API.md) — the Koolnova API, documented by reverse engineering

## Disclaimer

Unofficial project, not affiliated with Koolnova. It relies on an undocumented API that the
manufacturer may change or shut down at any time. The REST client bundled in `koolnova_api/` is a
fork of the `koolnova-api` package, with credit to its original author.

MIT licensed · [Issues](https://github.com/thcuba/homeassistant-koolnova/issues)

## Looking for Contributors

Koolnova for Home Assistant is a side project I maintain solo, and I'm looking for people to bring
into it as contributors — not a queue for feature requests. If you want to actually work on
something, open an issue to introduce yourself and what you'd want to tackle.
