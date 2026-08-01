# Desarrollo

Cómo está construida la integración, cómo probarla y cómo publicar una versión.
Para la API de Koolnova ver [API.md](API.md); para problemas de uso, [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Arquitectura

```
custom_components/koolnova/
├── __init__.py        setup/unload del config entry, crea el coordinator
├── config_flow.py     alta por UI (credenciales) y opciones
├── const.py           DOMAIN, límites, mapeos código Koolnova <-> modo HA
├── coordinator.py     DataUpdateCoordinator: hace el polling
├── climate.py         entidades: proyecto (global) y zona (por habitación)
├── manifest.json      la versión debe coincidir con el tag de git
├── brand/             icono y logo servidos por HA (ver su README)
└── koolnova_api/      cliente REST vendorizado
    ├── client.py      get_project, get_sensors, update_sensor, update_project
    ├── session.py     login y ciclo de vida del token
    ├── const.py       URLs y headers obligatorios
    └── exceptions.py  KoolnovaError
```

### Cliente API vendorizado — regla de imports

`koolnova_api/` es un fork local del cliente `koolnova-api` (crédito al autor original). Vive
dentro del repositorio y **no** es una dependencia PyPI, porque el paquete `koolnova-api` (con
guión) colisionaba con el módulo local, que antes se llamaba `koolnovaapi` (sin guión), y provocaba
errores 404 en todas las llamadas.

```python
from .koolnova_api.client import KoolnovaAPIRestClient   # ✅
from koolnovaapi.client import KoolnovaAPIRestClient     # ❌ rompe la integración
```

Nunca reintroduzcas un import absoluto de `koolnova_api` ni añadas el paquete PyPI a
`manifest.json`. Tras tocar imports, limpia la caché de Python (`__pycache__`) antes de probar.

### Dos ámbitos de entidad

`climate.py` expone dos clases que traducen a través de los mapeos de `const.py`
(`KOOLNOVA_TO_HVAC_MODE`, `KOOLNOVA_ZONE_STATUS_TO_HVAC`, `KOOLNOVA_TO_FAN` y sus inversos
autogenerados):

- `KoolnovaProjectEntity` — el proyecto completo: modo HVAC global, ECO, parada.
- `KoolnovaZoneEntity` — una por sensor/habitación: consigna, estado, velocidad de ventilador.

### Polling a dos ritmos

El coordinator refresca los **sensores** en cada ciclo, pero la lista de **proyectos** (más cara)
solo cada `project_update_frequency` ciclos, cacheando el resto (`DEFAULT_PROJECT_UPDATE_FREQUENCY`
= 10 en `const.py`).

Los cambios de opciones (intervalo, modos ofrecidos, rango de temperatura) recargan la
configuración del coordinator sin recargar el config entry entero (`async_reload_entry` en
`__init__.py`).

### Límites impuestos por Koolnova

Koolnova banea la IP automáticamente si se consulta más de una vez cada 30 s, y también ante
logins fallidos repetidos. De ahí que `MIN_UPDATE_INTERVAL` sea 30 s (el coordinator recorta a
ese valor las configuraciones antiguas más agresivas) y que exista un cooldown de 300 s tras un
login fallido. **No bajes estos límites.**

## Entorno de pruebas

No hay suite de tests: la integración solo se ejercita de verdad contra una instancia real de Home
Assistant y una cuenta Koolnova real.

Hubo un directorio `tests/` con scripts de exploración de la API que llevaban credenciales en
texto plano; se purgó del historial en la v1.2.6. **No recrees ese patrón**: si añades tests, usa
respuestas HTTP mockeadas, nunca credenciales reales.

El desarrollo se hace contra una instancia de HA en Docker, editando la integración directamente
en su directorio de configuración:

```bash
$HOME/docker/homeassistant/config/custom_components/koolnova
docker restart homeassistant
```

### Antes de hacer push

1. `docker restart homeassistant`
2. Sin errores en `docker logs homeassistant` ni en `home-assistant.log`.
3. El alta desde la UI funciona.
4. Las entidades `climate.koolnova_*` responden: temperatura, modo y ventilador.

## Publicar una release

HACS instala directamente desde el repositorio de GitHub, así que la raíz tiene que mantener la
forma estándar: `custom_components/koolnova/`, `hacs.json` y `README.md` en su sitio, sin ZIPs ni
`zip_release`.

> **El tag y el campo `"version"` de `manifest.json` deben ser idénticos.** Si no coinciden, HACS
> falla con `Downloading … failed with (No content to download)`. Tag `v1.3.2` ↔ versión `1.3.2`
> (el prefijo `v` solo va en el tag). No publiques releases cuyo nombre o tag no correspondan a la
> versión del manifest: quedan como "latest" y rompen la instalación.

1. Actualiza `"version"` en `custom_components/koolnova/manifest.json`.
2. Añade la entrada correspondiente en [CHANGELOG.md](../CHANGELOG.md).
3. `git commit -m "vX.Y.Z: …"`
4. `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
5. `git push origin main --tags`
6. Crea la release en GitHub desde ese tag, sin assets propios.

### `hacs.json`

Solo admite un conjunto reducido de claves. Los metadatos de la integración (`domain`,
`config_flow`, `iot_class`, `integration_type`…) van en `manifest.json`; si se ponen aquí, el
check `hacsjson` falla con *extra keys not allowed*.

```json
{
  "name": "Koolnova",
  "homeassistant": "2025.12.0",
  "render_readme": true,
  "country": ["ES"],
  "hide_default_branch": false
}
```
