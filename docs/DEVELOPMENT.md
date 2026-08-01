# Development

How the integration is built, how to test it, and how to publish a version.
For the Koolnova API see [API.md](API.md); for usage problems, [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Architecture

```
custom_components/koolnova/
├── __init__.py        config entry setup/unload, creates the coordinator
├── config_flow.py     UI setup (credentials) and options
├── const.py           DOMAIN, limits, Koolnova code <-> HA mode mappings
├── coordinator.py     DataUpdateCoordinator: does the polling
├── climate.py         entities: project (global) and zone (per room)
├── manifest.json      version must match the git tag
├── brand/             icon and logo served by HA (see its README)
└── koolnova_api/      vendored REST client
    ├── client.py      get_project, get_sensors, update_sensor, update_project
    ├── session.py     login and token lifecycle
    ├── const.py       URLs and required headers
    └── exceptions.py  KoolnovaError
```

### Vendored API client — the import rule

`koolnova_api/` is a local fork of the `koolnova-api` client (credit to the original author). It
lives inside the repository and is **not** a PyPI dependency, because the `koolnova-api` package
(hyphen) collided with the local module — previously named `koolnovaapi` (no separator) — and
caused 404 errors on every call.

```python
from .koolnova_api.client import KoolnovaAPIRestClient   # ✅
from koolnovaapi.client import KoolnovaAPIRestClient     # ❌ breaks the integration
```

Never reintroduce an absolute `koolnova_api` import, and never add the PyPI package to
`manifest.json`. After touching imports, clear the Python cache (`__pycache__`) before testing.

### Two entity scopes

`climate.py` exposes two classes that translate through the mappings in `const.py`
(`KOOLNOVA_TO_HVAC_MODE`, `KOOLNOVA_ZONE_STATUS_TO_HVAC`, `KOOLNOVA_TO_FAN` and their
auto-generated inverses):

- `KoolnovaProjectEntity` — the whole project: global HVAC mode, ECO, stop.
- `KoolnovaZoneEntity` — one per sensor/room: setpoint, status, fan speed.

### Two polling rates

The coordinator refreshes **sensors** every cycle, but the (more expensive) **project** list only
every `project_update_frequency` cycles, caching the rest (`DEFAULT_PROJECT_UPDATE_FREQUENCY` = 10
in `const.py`).

Option changes (interval, offered modes, temperature range) reload the coordinator's configuration
without reloading the whole config entry (`async_reload_entry` in `__init__.py`).

### Limits imposed by Koolnova

Koolnova bans your IP automatically if their API is polled more often than once every 30 s, and
also on repeated failed logins. Hence `MIN_UPDATE_INTERVAL` is 30 s (the coordinator clamps older,
more aggressive configurations to it) and a 300 s cooldown exists after a failed login. **Do not
lower these limits.**

## Test environment

There is no test suite: the integration can only really be exercised against a live Home Assistant
instance and a real Koolnova account.

A `tests/` directory once held API exploration scripts with plaintext credentials; it was purged
from history in v1.2.6. **Do not recreate that pattern** — if you add tests, use mocked HTTP
responses, never real credentials.

Development happens against a Home Assistant instance in Docker, editing the integration directly
in its configuration directory:

```bash
$HOME/docker/homeassistant/config/custom_components/koolnova
docker restart homeassistant
```

### Before pushing

1. `docker restart homeassistant`
2. No errors in `docker logs homeassistant` or in `home-assistant.log`.
3. Setup from the UI works.
4. The `climate.koolnova_*` entities respond: temperature, mode and fan.

## Publishing a release

HACS installs straight from the GitHub repository, so the root must keep the standard shape:
`custom_components/koolnova/`, `hacs.json` and `README.md` where they are, with no ZIPs and no
`zip_release`.

> **The tag and the `"version"` field in `manifest.json` must be identical.** If they differ, HACS
> fails with `Downloading … failed with (No content to download)`. Tag `v1.3.2` ↔ version `1.3.2`
> (the `v` prefix belongs to the tag only). Never publish a release whose tag or name does not
> match the manifest version: it becomes "latest" and breaks installs for everyone.

1. Bump `"version"` in `custom_components/koolnova/manifest.json`.
2. Add the matching entry to [CHANGELOG.md](../CHANGELOG.md).
3. `git commit -m "vX.Y.Z: …"`
4. `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
5. `git push origin main --tags`
6. Create the GitHub release from that tag, with no custom assets.

### `hacs.json`

Only a small set of keys is allowed. Integration metadata (`domain`, `config_flow`, `iot_class`,
`integration_type`…) belongs in `manifest.json`; putting it here makes the `hacsjson` check fail
with *extra keys not allowed*.

```json
{
  "name": "Koolnova",
  "homeassistant": "2025.12.0",
  "render_readme": true,
  "country": ["ES"],
  "hide_default_branch": false
}
```
