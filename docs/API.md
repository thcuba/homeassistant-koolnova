# API de Koolnova

Referencia de la API REST que consume esta integración. **No es una API pública ni documentada**:
todo lo que hay aquí está obtenido por ingeniería inversa de la webapp `app.koolnova.com` y
verificado contra el código del cliente en `custom_components/koolnova/koolnova_api/`.

Base: `https://api.koolnova.com` (Django REST framework).

> Si cambias algo del cliente, actualiza este documento en el mismo commit. Es la única
> descripción que existe de esta API.

## Reglas que hacen fallar todo si no se respetan

1. **Headers de navegador en todas las peticiones.** Desde mayo de 2026 la API responde `404`
   (no `401`, no `403`) a las peticiones que no los llevan, lo que hace parecer que el endpoint
   ha desaparecido. Ver `COMMON_HEADERS` en `koolnova_api/const.py`.
2. **Barra final en las rutas.** `projects/` sí, `projects` no.
3. **Máximo una consulta cada 30 s.** Koolnova banea la IP automáticamente por encima de ese
   ritmo (confirmado por su soporte), y también ante logins fallidos repetidos.

## Headers comunes

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

Las peticiones con cuerpo añaden `content-type: application/json` (`PATCH_HEADERS`).
Las peticiones autenticadas añaden `Authorization: Bearer <token>`.

## Autenticación

### `POST /auth/v2/login/`

El identificador va en el campo **`email`**. Es el detalle más frágil de toda la integración:

| Payload | Respuesta |
|---|---|
| `{"email": "...", "password": "..."}` | `200` + token |
| `{"username": "...", "password": "..."}` | `400 "Unable to log in with provided credentials"` |

No lo cambies sin comprobarlo contra la API real: enviar `username` rompió el login en la v1.3.0
y hubo que revertirlo en la v1.3.1.

```json
{ "email": "usuario@ejemplo.com", "password": "…" }
```

La respuesta trae el token en `access_token` (el cliente acepta también `token` y `accessToken`).
Vive alrededor de 1 hora; el cliente lo renueva a los **50 minutos** (`TOKEN_LIFETIME` en
`client.py`).

Ante `429` el cliente reintenta con backoff exponencial (5 intentos, tope de 60 s), respetando la
cabecera `Retry-After` si viene. Tras un login fallido espera `AUTH_FAILURE_COOLDOWN` (300 s)
antes de reintentar.

## Endpoints

### `GET /projects/`

Lista de proyectos. Se envían los mismos parámetros que la webapp:

```
page=1  page_size=25  ordering=-start_date  search=  is_oem=false
```

De cada elemento de `data[]` el cliente usa `name` y, dentro de `topic`: `id`, `name`, `mode`,
`is_stop`, `is_online`, `eco`, `last_sync`.

### `GET /topics/sensors/`

Lista de sensores (zonas). De cada elemento de `data[]` se usan `id`, `name`, `status`,
`temperature`, `setpoint_temperature`, `speed`, `updated_at` y el bloque `topic_info` (que aporta
el `id` del topic y los datos de conectividad: RSSI, online, sincronización).

### `PUT /topics/sensors/{sensor_id}/`

Actualiza una zona. **Es `PUT`, no `PATCH`** — a diferencia del endpoint de topics.

| Payload | Efecto |
|---|---|
| `{"setpoint_temperature": 24.5}` | Temperatura objetivo |
| `{"status": "00"}` | Modo de la zona (ver tabla) |
| `{"speed": "2"}` | Velocidad del ventilador (ver tabla) |

### `PATCH /topics/{topic_id}/`

Actualiza el proyecto completo.

| Payload | Efecto |
|---|---|
| `{"mode": "1"}` | Modo global (ver tabla) |
| `{"eco": true}` | Modo ECO |
| `{"is_stop": true}` | Parada global |
| `{"is_online": true}` | Estado online |

## Tablas de códigos

Definidas en `custom_components/koolnova/const.py`. **Los modos de proyecto y los de zona usan
codificaciones distintas**; confundirlas es un error fácil de cometer.

### Modo de proyecto (`mode`)

| Código | Modo HA |
|---|---|
| `"1"` | `cool` |
| `"2"` | `off` |
| `"4"` | `heat` |
| `"6"` | `auto` |

### Estado de zona (`status`)

| Código | Modo HA |
|---|---|
| `"00"` | `cool` |
| `"01"` | `heat` |
| `"02"` | `off` |
| `"03"` | `auto` |

### Velocidad de ventilador (`speed`)

| Código | Velocidad HA |
|---|---|
| `"1"` | `low` |
| `"2"` | `medium` |
| `"3"` | `high` |
| `"4"` | `auto` |

## Códigos de error

| Código | Causa habitual |
|---|---|
| `400` | Payload mal formado, valor fuera de rango, o `username` en vez de `email` al hacer login |
| `404` | **Casi siempre, headers de navegador ausentes** — no que la ruta no exista. También ruta sin barra final o ID inexistente |
| `429` | Límite de peticiones; el cliente reintenta con backoff |
| `5xx` | API caída; el cliente reintenta con backoff corto |
