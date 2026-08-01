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
   also on repeated failed logins.

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
Authenticated requests add `Authorization: Bearer <token>`.

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
{ "email": "user@example.com", "password": "…" }
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
`temperature`, `setpoint_temperature`, `speed`, `updated_at` and the `topic_info` block (which
provides the topic `id` and the connectivity data: RSSI, online, sync).

### `PUT /topics/sensors/{sensor_id}/`

Updates one zone. **It is `PUT`, not `PATCH`** — unlike the topics endpoint.

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

## Code tables

Defined in `custom_components/koolnova/const.py`. **Project modes and zone modes use different
encodings** — an easy mistake to make.

### Project mode (`mode`)

| Code | HA mode |
|---|---|
| `"1"` | `cool` |
| `"2"` | `off` |
| `"4"` | `heat` |
| `"6"` | `auto` |

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
| `404` | **Almost always missing browser-like headers** — not a missing route. Also a path without a trailing slash, or a non-existent ID |
| `429` | Rate limited; the client retries with backoff |
| `5xx` | API down; the client retries with a short backoff |
