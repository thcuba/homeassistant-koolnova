# The Koolnova API

Reference for the REST API this integration consumes. **It is neither public nor documented**:
everything here was reverse-engineered from the `app.koolnova.com` webapp and verified against the
client code in `custom_components/koolnova/koolnova_api/`.

Base: `https://api.koolnova.com` (Django REST framework).

> If you change the client, update this document in the same commit. It is the only description of
> this API that exists.

## Rules that break everything when ignored

1. **Browser-like headers on every request.** Since May 2026 the API answers `404` (not `401`, not
   `403`) to requests without them, which makes it look like the endpoint is gone. See
   `COMMON_HEADERS` in `koolnova_api/const.py`.
2. **Trailing slash on every path.** `projects/` yes, `projects` no.
3. **At most one request every 30 s.** Koolnova bans your IP automatically above that rate, and
   also on repeated failed logins. The client enforces a minimum distance of
   `MIN_REQUEST_INTERVAL` (10 s) between any two HTTP calls, login included, and the brake is
   shared by the whole process (`KoolnovaClientSession._wait_for_request_slot`), so parallel
   callers leave one at a time. This removes the bursts — a full refresh issues 3 + N requests,
   `koolnova.set_all_zones_mode` fires one PATCH per zone at the same instant — but 10 s is
   **not** by itself the 30 s ban threshold: what keeps the account safe is the low average
   (180 s polling, a full cycle every 20). Raise `MIN_REQUEST_INTERVAL` to 30 if a ban is ever
   observed on a real account.
4. **45 s minimum request timeout.** Requests to the Koolnova servers never time out below 45 s
   — the value Koolnova support recommends. The integration default is 50 s, configurable via
   `request_timeout` in the options flow (range 45-300 s): even a lower configured value is
   floored to 45 s. A hung request without a timeout would otherwise block a polling cycle
   forever.

## Common headers

```
accept: application/json, text/plain, */*
accept-language: en
origin: https://app.koolnova.com
referer: https://app.koolnova.com/
cache-control: no-cache
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36
sec-ch-ua: "Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
sec-fetch-dest: empty
sec-fetch-mode: cors
sec-fetch-site: same-site
```

Requests with a body add `content-type: application/json` (`PATCH_HEADERS`).
Authenticated requests add `Authorization: Bearer ******`

## Authentication

### `POST /auth/v2/login/`

The identifier goes in the **`email`** field. This is the most fragile detail in the whole
integration:

| Payload | Response |
|---|---|
| `{"email": "...", "password": "..."}` | `200` + token |
| `{"username": "...", "password": "..."}` | `400 "Unable to log in with provided credentials"` |

Do not change it without checking against the live API: sending `username` broke login in v1.3.0
and had to be reverted in v1.3.1.

```json
{ "email": "user@example.com", "password": "..." }
```

The response carries the token in `access_token` (the client also accepts `token` and
`accessToken`). It lives for roughly one hour; the client renews it after **50 minutes**
(`TOKEN_LIFETIME` in `client.py`).

On `429` the client retries with exponential backoff (5 attempts, capped at 60 s), honouring the
`Retry-After` header when present. After a failed login it waits `AUTH_FAILURE_COOLDOWN` (300 s)
before retrying.

## Endpoints

### `GET /projects/`

List of projects. The same query parameters as the webapp are sent:

```
page=1  page_size=25  ordering=-start_date  search=  is_oem=false
```

From each item in `data[]` the client uses `name` and, inside `topic`: `id`, `name`, `mode`,
`is_stop`, `is_online`, `eco`, `last_sync`.

### `GET /topics/sensors/`

List of sensors (zones). From each item in `data[]` the client uses `id`, `name`, `status`,
`temperature`, `setpoint_temperature`, `humidity`, `speed`, `updated_at` and the `topic_info` block
(which provides the topic `id` and the connectivity data: RSSI, online, sync).

Fields seen on each zone as of November 2026:

| Field | Meaning |
|---|---|
| `humidity` | Relative humidity in %, e.g. `54.0`. `null` when the zone has no humidity probe |
| `co2` | CO₂ reading in ppm; `null` on zones without a CO₂ probe |
| `room` / `floor` | `{id, name}` grouping (not consumed) |
| `control_unit`, `zone` | Control unit number and zone index, as shown in the webapp (`uc: 31 / zone: 04`) |
| `is_trv`, `is_removed`, `image` | Not consumed |

`topic_info.humidity` is a **different, project-level boolean** (it reads `false` on accounts whose
zones do report humidity), so don't use it to decide whether a zone has a humidity reading.

### `PUT /topics/sensors/{sensor_id}/`

Updates one zone. **It is `PUT`, not `PATCH`** � unlike the topics endpoint.

| Payload | Effect |
|---|---|
| `{"setpoint_temperature": 24.5}` | Target temperature |
| `{"status": "00"}` | Zone mode (see table) |
| `{"speed": "2"}` | Fan speed (see table) |

### `PATCH /topics/{topic_id}/`

Updates the whole project.

| Payload | Effect |
|---|---|
| `{"mode": "1"}` | Global mode (see table) |
| `{"eco": true}` | ECO mode |
| `{"is_stop": true}` | Global stop |
| `{"is_online": true}` | Online state |

## Hub / legacy controller endpoints

Legacy Koolnova controllers (a physical hub instead of per-zone devices) expose a few extra
endpoints. These were contributed from a community fork and are covered by mocked unit tests only �
**not verified against the live API**; if your account has no hub, `/modules/` answers nothing
usable and the integration simply creates no hub entities.

### `GET /modules/`

Lists the modules on the account, one dict per module. The client classifies them by
`ModuleType_Id` (`1` => koolnova zone device, `2` => hub) and uses `Serial` as the id:

```json
[{"Serial": "KN1234", "ModuleType_Id": 2, "...": "..."}]
```

### `GET /hub/{hub_id}/state`

Current state of one hub:

| Field | Meaning |
|---|---|
| `stateEquipment` | Hub is on (`true`/`false`) |
| `behavior` | Behavior mode: `manual`, `auto`, `planning` |

### `PUT /hub/{hub_id}/mode/{target}`

Sets the hub behavior mode. `target` is one of `manual`, `auto`, `planning`. The response mirrors
`/hub/{id}/state`.

### `POST /hub/{hub_id}/Manual/{bool}`

Turns the hub on/off (`True`/`False`). The client then re-reads `/hub/{id}/state` to return the
new state.

### `GET /devices/`

Used as fallback data source: flat list of devices with a nested `sensor` dict, and by the
coordinator only when the `topics` endpoints fail, so the integration degrades instead of
going `unavailable`.

On most Koolnova cloud accounts this endpoint does **not** carry a usable room humidity: the
device's `sensor.topic_info.humidity` field is reported as the boolean `false` (or is absent),
not as a percentage. `get_sensor_humidity_map()` therefore only accepts a **real numeric**
value (`int`/`float`, never a boolean) and skips everything else — so a device without an
exposed humidity simply never produces a `Room_humidity` entry and no bogus sensor is created.

> **Note on local humidity (Modbus, no cloud).** A real physical humidity sensor wired to the
> 100-CPND00 controller (its "humidity sensor input") is **not** exposed through this cloud
> API. Reading it requires local Modbus access (RS485 on the controller), outside the scope of
> this cloud-only integration.

### `GET /notifications/`

Lists notifications. Currently not consumed by the integration; exposed for tooling.

## Code tables

Defined in `custom_components/koolnova/const.py`. **Project modes and zone modes use different
encodings** � an easy mistake to make.

### Project mode (`mode`)

The cloud drives **two circuits** — air and underfloor — and the app lists their combinations as
separate entries, so "heat" and "cool" on their own are ambiguous.

| Code | HA mode | What it actually drives |
|---|---|---|
| `"1"` | `cool` | cool **air** only (ducted units) |
| `"2"` | `heat` | **hot air** only (ducted units) |
| `"3"` | `heat` | **heat floor** only (underfloor circuit) |
| `"4"` | — | *not identified yet: deliberately left unmapped* |
| `"5"` | `cool` | **cool floor + cool air** together |
| `"6"` | `heat` | **heat floor + hot air** together |

Two consequences:

- The mapping is **not invertible** — three codes collapse onto `heat` and two onto `cool` — so the
  code to send also depends on the configured heat source. `KOOLNOVA_PROJECT_MODE_CODE` in `const.py`
  is keyed by `(hvac mode, heat source)`, the source being `air`, `floor` or `both`.
- **There is neither an "auto" nor an "off" code.** Code `6` looks like auto but it is the "heat
  floor + hot air" combination; the installation is stopped by setting the separate `is_stop` flag,
  because off is a flag and not a mode. A stopped project keeps reporting whatever `mode` was set
  before, which is why the entity reads `is_stop` first.

Code `4` has not been identified: it appears in the app's list, but no observation ties it to a mode
yet. It is left out of the table on purpose, so it is logged with its raw value instead of being
silently translated into something plausible.

There is no **cool-floor-only** entry either: cooling exists on air (`1`) or on both circuits (`5`),
never on the underfloor circuit alone. That combination fails loudly instead of silently falling back
to another circuit.

> **These codes come from the official app and are not yet verified against the cloud.** Only `1` and
> `2` have been observed in a real payload. The raw value is exposed as the `project_mode_raw`
> attribute and an unmapped code logs a warning carrying its value, so the table can be confirmed —
> or corrected — from Home Assistant, without reading the API by hand.
>
> **Why the old table was wrong.** Until 2.0.11 it read `1 cool, 2 off, 4 heat, 6 auto`, with the
> inverse map generated automatically. That made `off` send `2`, which the app reads as **hot air**:
> switching the installation off switched the heating *on*. `heat` sent `4`, which also implied the
> underfloor circuit, so an installation with ducted air only never blew hot air (issue #96). Code
> `6` turned out not to exist in the app at all.

### Zone status (`status`)

| Code | HA mode |
|---|---|
| `"00"` | `cool` |
| `"01"` | `heat` |
| `"02"` | `off` |
| `"03"` | `auto` |

### Fan speed (`speed`)

| Code | HA speed |
|---|---|
| `"1"` | `low` |
| `"2"` | `medium` |
| `"3"` | `high` |
| `"4"` | `auto` |

## Error codes

| Code | Usual cause |
|---|---|
| `400` | Malformed payload, value out of range, or `username` instead of `email` on login |
| `404` | **Almost always missing browser-like headers** � not a missing route. Also a path without a trailing slash, or a non-existent ID |
| `429` | Rate limited; the client retries with backoff |
| `5xx` | API down; the client retries with a short backoff |