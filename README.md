# Koolnova for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![release](https://img.shields.io/github/v/release/luisgsluis/homeassistant-koolnova)](https://github.com/luisgsluis/homeassistant-koolnova/releases)

Custom integration that controls **Koolnova** HVAC systems from Home Assistant through their cloud
API. Every zone, plus the project as a whole, is exposed as a `climate` entity.

- ❄️ HVAC modes per zone and globally (COOL / HEAT / AUTO / OFF)
- 🌡️ Target temperature per zone
- 🌬️ Fan speed per zone
- 🏠 Global project control (mode, ECO, stop)
- 🔄 Staggered polling: sensors every cycle, projects cached
- 🎛️ Setup and intervals configurable from the UI

Requires Home Assistant 2025.12.0 or newer and a Koolnova app account.

> ⚠️ Koolnova bans your IP automatically if their API receives more than one request every
> 30 seconds. That is why the minimum interval is 30 s — do not force it lower.

## Installation

### HACS (recommended)

1. HACS → ⋮ menu → **Custom repositories** → add
   `https://github.com/luisgsluis/homeassistant-koolnova` with category *Integration*.
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

## Documentation

- [CHANGELOG.md](CHANGELOG.md) — version history
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — common problems
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) — architecture, test environment and releases
- [docs/API.md](docs/API.md) — the Koolnova API, documented by reverse engineering

## Disclaimer

Unofficial project, not affiliated with Koolnova. It relies on an undocumented API that the
manufacturer may change or shut down at any time. The REST client bundled in `koolnova_api/` is a
fork of the `koolnova-api` package, with credit to its original author.

MIT licensed · [Issues](https://github.com/luisgsluis/homeassistant-koolnova/issues)
