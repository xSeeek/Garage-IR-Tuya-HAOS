# 🏠 Garage IR Tuya

Convierte un portón de garage controlado por **radiofrecuencia (RF)** en un accesorio nativo de **Apple HomeKit**, usando un emisor IR/RF compatible con **Tuya** y **Home Assistant** como puente.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1+-41BDF5?logo=homeassistant&logoColor=white)
![HomeKit](https://img.shields.io/badge/Apple%20HomeKit-Compatible-000000?logo=apple&logoColor=white)
![Tuya](https://img.shields.io/badge/Tuya-IR%2FRF%20Bridge-FF4800?logo=tuya&logoColor=white)

## ✨ Características

- 🚗 **Garage door nativo en Apple Home** — Se muestra con el ícono correcto de puerta de garage via HomeKit Bridge
- 🛡️ **Safeguard de doble-pulsación** — Maneja automáticamente el comportamiento del motor cuando se interrumpe un movimiento en curso
- ⚙️ **Configuración desde la UI** — Sin editar YAML. Selecciona entidades y ajusta el timer desde la interfaz de Home Assistant
- 🔄 **Forzar estado** — Corrige el estado desde las opciones si se desfasó con la puerta física
- 📡 **Sin sensor necesario** — Funciona con estado asumido basado en timers, con persistencia entre reinicios
- 🌐 **Bilingüe** — Interfaz en español e inglés

## 📐 Arquitectura

```
Apple Home (HomeKit) → Home Assistant (Cover Entity) → Escenas/Scripts Tuya → Caja IR/RF → Portón RF
```

## 📋 Requisitos

- [Home Assistant](https://www.home-assistant.io/) 2024.1 o superior
- [HACS](https://hacs.xyz/) instalado
- Integración de **Tuya** configurada en Home Assistant
- Escenas o scripts funcionando para abrir/cerrar el portón
- Integración **HomeKit Bridge** de Home Assistant ([documentación](https://www.home-assistant.io/integrations/homekit/))

## 🚀 Instalación

### Paso 1: Agregar repositorio en HACS

1. Abre **HACS** en Home Assistant
2. Ve a **Integraciones**
3. Haz clic en el menú **⋮** (tres puntos, arriba a la derecha) → **Repositorios personalizados**
4. Agrega:
   - **URL**: `https://github.com/TU_USUARIO/garage-ir-tuya`
   - **Categoría**: `Integración`
5. Haz clic en **Agregar**

### Paso 2: Instalar la integración

1. Busca **"Garage IR Tuya"** en HACS
2. Haz clic en **Descargar**
3. **Reinicia Home Assistant**

### Paso 3: Configurar la integración

1. Ve a **Ajustes → Dispositivos y servicios → + Agregar integración**
2. Busca **"Garage IR Tuya"**
3. Completa el formulario:

| Campo | Descripción |
|-------|-------------|
| **Nombre del cover** | Nombre que aparecerá en HA y HomeKit (ej: "Puerta del Garage") |
| **Entidad para abrir** | La escena, script o botón que abre el portón |
| **Entidad para cerrar** | La escena, script o botón que cierra el portón |
| **Entidad para detener** | *(Opcional)* Entidad para detener el movimiento |
| **Duración del movimiento** | Segundos que tarda el portón en abrir/cerrar (5-120s) |

4. Haz clic en **Enviar** ✅

### Paso 4: Exponer a HomeKit (opcional)

Si usas **HomeKit Bridge** con filtro de entidades, agrega el cover:

```yaml
homekit:
  - filter:
      include_entities:
        - cover.puerta_del_garage
```

Si expones todas las entidades, el cover aparecerá automáticamente.

## ⚙️ Configuración Posterior

Para modificar la configuración después de la instalación:

1. Ve a **Ajustes → Dispositivos y servicios**
2. Encuentra **Garage IR Tuya** → haz clic en **Configurar**
3. Modifica los campos que necesites
4. Usa **"Forzar estado actual"** si el estado se desfasó:
   - **Sin cambios** — No modifica el estado
   - **Abierto** — Fuerza el estado a abierto
   - **Cerrado** — Fuerza el estado a cerrado

> El valor de "Forzar estado" se resetea automáticamente después de aplicarse.

## 🛡️ Safeguard: Doble-Pulsación

Este componente maneja automáticamente el comportamiento peculiar de muchos motores de portón:

> Si el portón se está **abriendo** y pides **cerrar**, la primera señal actúa como **"detener"**. Se necesita una segunda señal para que realmente **cierre**.

### Lógica implementada

| Acción | Estado actual | Comportamiento |
|--------|---------------|----------------|
| **Abrir** | Cerrado | ✅ Abre normalmente (1 señal) |
| **Abrir** | Cerrándose | 🛡️ Safeguard: detiene + abre (2 señales, 2s delay) |
| **Abrir** | Abierto/Abriéndose | ⏭️ Ignora |
| **Cerrar** | Abierto | ✅ Cierra normalmente (1 señal) |
| **Cerrar** | Abriéndose | 🛡️ Safeguard: detiene + cierra (2 señales, 2s delay) |
| **Cerrar** | Cerrado/Cerrándose | ⏭️ Ignora |

## ⚠️ Limitaciones

- **Sin sensor físico**: El estado se basa en timers. Si alguien usa el control RF físico, Home Assistant no lo detectará.
  - **Solución**: Usa "Forzar estado" en las opciones para corregirlo.
  - **Solución permanente**: Instalar un sensor de contacto (~$5 USD).
- **Estado al reiniciar**: Se restaura el último estado conocido. Si HA se reinició durante un movimiento, se asume que el movimiento terminó.

## 📁 Estructura

```
garage-ir-tuya/
├── custom_components/
│   └── garage_ir_tuya/
│       ├── __init__.py           # Setup de la integración
│       ├── manifest.json         # Metadatos HA
│       ├── config_flow.py        # UI de configuración
│       ├── cover.py              # Cover entity con safeguard
│       ├── const.py              # Constantes
│       ├── strings.json          # Strings (inglés)
│       └── translations/
│           ├── en.json           # Inglés
│           └── es.json           # Español
├── hacs.json                     # Metadatos HACS
├── README.md
├── LICENSE
└── .gitignore
```

## 📄 Licencia

MIT — Usa, modifica y comparte libremente.
