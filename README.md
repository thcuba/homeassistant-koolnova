# Koolnova para Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![release](https://img.shields.io/github/v/release/luisgsluis/homeassistant-koolnova)](https://github.com/luisgsluis/homeassistant-koolnova/releases)

Integración personalizada que controla sistemas HVAC **Koolnova** desde Home Assistant, a través de
su API cloud. Cada zona y el proyecto completo se exponen como entidades `climate`.

- ❄️ Modos HVAC por zona y globales (COOL / HEAT / AUTO / OFF)
- 🌡️ Consigna de temperatura por zona
- 🌬️ Velocidad de ventilador por zona
- 🏠 Control global del proyecto (modo, ECO, parada)
- 🔄 Polling escalonado: sensores en cada ciclo, proyectos cacheados
- 🎛️ Configuración e intervalos ajustables desde la UI

Requiere Home Assistant 2025.12.0 o superior y una cuenta de la app Koolnova.

> ⚠️ Koolnova banea la IP automáticamente si su API recibe más de una consulta cada 30 segundos.
> Por eso el intervalo mínimo es de 30 s; no lo fuerces por debajo.

## Instalación

### HACS (recomendado)

1. HACS → menú ⋮ → **Repositorios personalizados** → añade
   `https://github.com/luisgsluis/homeassistant-koolnova` como categoría *Integration*.
2. Busca **Koolnova**, descárgala y reinicia Home Assistant.

### Manual

Copia `custom_components/koolnova/` dentro del directorio `custom_components` de tu configuración
y reinicia Home Assistant.

## Configuración

**Ajustes → Dispositivos y servicios → Añadir integración → Koolnova**, con las credenciales de la
app Koolnova.

Opciones disponibles después, desde *Configurar*:

| Opción | Por defecto | Rango |
|---|---|---|
| Intervalo de actualización | 30 s | 30–3600 s |
| Frecuencia de refresco de proyectos | cada 10 ciclos | 1–300 |
| Modos HVAC del proyecto | COOL, HEAT | COOL / HEAT / OFF / AUTO |
| Modos HVAC de zona | OFF, AUTO | COOL / HEAT / OFF / AUTO |
| Rango de temperatura | 21–27 °C | 15–35 °C |
| Precisión de temperatura | 0,5 °C | 0,5 o 1 °C |

## Documentación

- [CHANGELOG.md](CHANGELOG.md) — historial de versiones
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — problemas frecuentes
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) — arquitectura, entorno de pruebas y releases
- [docs/API.md](docs/API.md) — la API de Koolnova, documentada por ingeniería inversa

## Aviso

Proyecto no oficial, sin relación con Koolnova. Usa una API no documentada que su fabricante puede
cambiar o cerrar en cualquier momento. El cliente REST incluido en `koolnova_api/` es un fork del
paquete `koolnova-api`, con crédito a su autor original.

Licencia MIT · [Issues](https://github.com/luisgsluis/homeassistant-koolnova/issues)
