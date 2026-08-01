# Solución de problemas

Problemas habituales al usar la integración. Si vas a tocar el código, mira antes
[DEVELOPMENT.md](DEVELOPMENT.md) y [API.md](API.md).

## Antes de nada: no reintentes en bucle

Koolnova **banea tu IP automáticamente** si su API recibe más de una consulta cada 30 segundos, o
si detecta logins fallidos repetidos. Si algo falla, no recargues la integración una y otra vez ni
bajes el intervalo de actualización: espera unos minutos entre intentos. Un ban se manifiesta como
errores de conexión que no se arreglan aunque las credenciales sean correctas.

## La integración no se conecta / errores 404 en los logs

Un `404` de esta API casi nunca significa que la ruta no exista: significa que la petición no
parecía venir de un navegador. La API exige un `User-Agent` de Chrome moderno y los headers
`sec-ch-ua*` / `sec-fetch-*` (ver `koolnova_api/const.py`).

Si empieza a fallar de golpe sin haber cambiado nada, lo más probable es que Koolnova haya vuelto
a endurecer ese filtro — pasó en mayo de 2026 (issue #4). Abre una incidencia.

## "Authentication failed" al configurar

- Comprueba usuario y contraseña entrando en la app oficial de Koolnova.
- El login usa el campo `email`; si has tocado el cliente y lo has cambiado a `username`, la API
  responde `400 "Unable to log in with provided credentials"` (ver [API.md](API.md#autenticación)).
- Tras un fallo de login la integración espera 5 minutos antes de reintentar, a propósito. No es
  un cuelgue.

## "No projects found"

La cuenta no tiene ningún proyecto activo. Créalo primero en la app de Koolnova.

## Las entidades aparecen como "unavailable"

Por orden de probabilidad:

1. El proyecto está offline (`is_online: false`) — compruébalo en la app oficial.
2. El coordinator no consigue actualizar: mira los logs.
3. Problema de autenticación o token caducado; reinicia Home Assistant.

Si persiste, elimina la integración desde la UI, reinicia HA y vuelve a añadirla.

## Los cambios no se aplican

- **Temperatura fuera de rango**: ajusta `min_temp` / `max_temp` en las opciones de la integración.
- El estado que muestra HA viene de la última lectura cacheada; con el intervalo en 30 s puede
  tardar en reflejar un cambio hecho desde la app oficial.

## HACS: "No content to download"

El tag de la release y el campo `"version"` de `manifest.json` no coinciden. Es un fallo de
empaquetado, no tuyo: repórtalo. Ver [DEVELOPMENT.md](DEVELOPMENT.md#publicar-una-release).

## Recoger información para un issue

Activa el log de depuración en `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.koolnova: debug
```

Reinicia HA, reproduce el problema y adjunta al
[issue](https://github.com/luisgsluis/homeassistant-koolnova/issues) la versión de Home Assistant,
la de la integración y los logs relevantes.

> Los logs de depuración no incluyen la contraseña ni el token desde la v1.3.0, pero **sí** los
> nombres de tus proyectos y zonas. Revísalos antes de publicarlos.
