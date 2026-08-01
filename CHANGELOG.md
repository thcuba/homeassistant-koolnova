# Changelog

Todas las versiones publicadas de la integración. El formato sigue
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el versionado es
[SemVer](https://semver.org/lang/es/): el tag de git y el campo `"version"` de
`manifest.json` son siempre idénticos (ver [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md#publicar-una-release)).

## [1.3.2] — 2026-07-06

### Añadido
- Icono y logo de marca servidos por la propia integración desde
  `custom_components/koolnova/brand/`. Desde HA 2026.3 estas imágenes locales tienen prioridad
  sobre el CDN de marcas, así que la integración muestra su logo sin depender de
  `home-assistant/brands` — que **ya no acepta integraciones custom** (su bot cierra el PR
  automáticamente desde el cambio de `brands-proxy-api` de febrero de 2026).

## [1.3.1] — 2026-07-05

### Corregido
- **Regresión de login introducida en 1.3.0.** La 1.3.0 pasó el identificador del usuario en el
  campo `username` del payload de `/auth/v2/login/`; la API responde `400 "Unable to log in with
  provided credentials"` con `username` y `200` con `email`. Se vuelve a `email`.

  El `404` original del issue #4 nunca lo causó el nombre del campo, sino la falta de headers de
  navegador — que la 1.3.0 sí añadió correctamente y aquí se conservan.

## [1.3.0] — 2026-07-04

### Corregido
- **Autenticación rota (issue #4).** Desde mayo de 2026 la API responde `404` en
  `/auth/v2/login/` a las peticiones que no parecen venir de un navegador. Se envían ahora
  `User-Agent` de Chrome moderno y los headers `sec-ch-ua*` / `sec-fetch-*`.
- `hacs.json` contenía claves no admitidas que hacían fallar el check `hacsjson`; el workflow de
  validación vuelve a pasar (`brands` se ignora por tratarse de un repositorio custom).

### Seguridad
- Protección anti-ban: Koolnova banea la IP automáticamente si se consulta más de una vez cada
  30 s (confirmado por su soporte). El intervalo mínimo y por defecto pasan a 30 s, y el
  coordinator recorta los valores de configuraciones anteriores a este límite.
- Protección anti-ban: cooldown de 5 minutos tras un login fallido antes de reintentar; los
  logins fallidos repetidos también provocan ban de IP.
- Los logs de debug ya no incluyen el payload de login (contenía la contraseña) ni el token.

### Eliminado
- Código muerto heredado del proyecto original (métodos de piscinas y hubs, ~110 líneas) y la
  dependencia implícita de `dateutil`.

### Sin cambios
- Los modos HVAC por defecto se mantienen.

## [1.2.6] — 2026-07-04

### Seguridad
- Eliminado el directorio `tests/` y purgado del historial de git: contenía scripts de
  exploración de la API con credenciales en texto plano. El historial de commits fue reescrito.

### Añadido
- Workflow de validación HACS/hassfest (`.github/workflows/validate.yml`).
- `CLAUDE.md` con las reglas de trabajo del repositorio.

### Corregido
- Enlace roto a la documentación de troubleshooting en el README.

## [1.2.0]

### Corregido
- **Errores 404 en todas las llamadas a la API.** El módulo local se llamaba `koolnovaapi` y
  colisionaba con el paquete PyPI `koolnova-api`. Se renombra a `koolnova_api` (con guión bajo),
  se vendoriza dentro del repositorio, se le añade `__init__.py` y pasa a importarse siempre con
  imports relativos. La integración deja de tener dependencias externas.

## [1.1.0]

### Añadido
- Control global del proyecto además del control por zona.

### Corregido
- Errores en la actualización de sensores.
- Mapeos HVAC y polling del coordinator optimizados.

## [1.0.0]

Versión inicial: proyectos y zonas como entidades `climate`, con control de temperatura y modo.

[1.3.2]: https://github.com/luisgsluis/homeassistant-koolnova/releases/tag/v1.3.2
[1.3.1]: https://github.com/luisgsluis/homeassistant-koolnova/releases/tag/v1.3.1
[1.3.0]: https://github.com/luisgsluis/homeassistant-koolnova/releases/tag/v1.3.0
[1.2.6]: https://github.com/luisgsluis/homeassistant-koolnova/releases/tag/v1.2.6
[1.2.0]: https://github.com/luisgsluis/homeassistant-koolnova/commits/main
[1.1.0]: https://github.com/luisgsluis/homeassistant-koolnova/commits/main
[1.0.0]: https://github.com/luisgsluis/homeassistant-koolnova/commits/main
