# 🏠 Garage IR Tuya — Portón de Garage para HomeKit

Convierte un portón de garage controlado por **radiofrecuencia (RF)** en un accesorio nativo de **Apple HomeKit**, usando un emisor IR/RF compatible con **Tuya** y **Home Assistant** como puente.

![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025+-41BDF5?logo=homeassistant&logoColor=white)
![HomeKit](https://img.shields.io/badge/Apple%20HomeKit-Compatible-000000?logo=apple&logoColor=white)
![Tuya](https://img.shields.io/badge/Tuya-Scenes-FF4800?logo=tuya&logoColor=white)

## ✨ Características

- 🚗 **Garage door nativo en Apple Home** — Se muestra con el ícono correcto de puerta de garage
- 🛡️ **Safeguard de doble-pulsación** — Maneja automáticamente el comportamiento del motor cuando se interrumpe un movimiento en curso
- 📡 **Sin sensor necesario** — Funciona con estado asumido basado en timers
- 🎯 **Abrir, Cerrar y Detener** — Las tres acciones soportadas
- ⚙️ **Instalación simple** — Un solo archivo YAML como paquete de Home Assistant

## 📐 Arquitectura

```
Apple Home (HomeKit) → Home Assistant (Template Cover) → Escenas Tuya → Caja IR/RF → Portón RF
```

## 📋 Requisitos

- [Home Assistant](https://www.home-assistant.io/) 2025.1 o superior
- Integración de **Tuya** configurada en Home Assistant
- Escenas de Tuya funcionando para abrir/cerrar el portón
- Integración **HomeKit Bridge** de Home Assistant ([documentación](https://www.home-assistant.io/integrations/homekit/))

## 🚀 Instalación

### Paso 1: Habilitar Packages en Home Assistant

> [!NOTE]  
> Si ya tienes `packages` habilitado, salta al **Paso 2**.

Edita tu archivo `/config/configuration.yaml` y agrega lo siguiente dentro de la sección `homeassistant:`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Si ya tienes la sección `homeassistant:`, solo agrega la línea de `packages:`.

### Paso 2: Crear la carpeta `packages`

Si no existe, crea la carpeta `packages` dentro de tu directorio de configuración de Home Assistant:

```bash
mkdir -p /config/packages
```

### Paso 3: Descargar el paquete

**Opción A — Desde la terminal de Home Assistant (SSH o Terminal Add-on):**

```bash
cd /config/packages
curl -O https://raw.githubusercontent.com/TU_USUARIO/garage-ir-tuya/main/garage_door.yaml
```

**Opción B — Manualmente:**

1. Descarga el archivo [`garage_door.yaml`](garage_door.yaml)
2. Cópialo a `/config/packages/garage_door.yaml` usando:
   - **Samba Share** — Accede a `\\HOMEASSISTANT\config\packages\` desde tu PC
   - **File Editor Add-on** — Crea el archivo y pega el contenido
   - **VS Code Add-on** — Abre la carpeta packages y crea el archivo

### Paso 4: Personalizar las escenas (si es necesario)

Abre `garage_door.yaml` y verifica que los `entity_id` de las escenas coincidan con los tuyos:

```yaml
# Busca estas líneas y ajusta si tus escenas tienen nombres diferentes:
entity_id: scene.abre_el_estacionamiento     # ← Escena para ABRIR
entity_id: scene.cierra_el_estacionamiento    # ← Escena para CERRAR
```

También puedes ajustar el **timer** si tu portón tarda más o menos de 15 segundos:

```yaml
timer:
  garage_door:
    duration: "00:00:15"    # ← Ajusta el tiempo aquí
```

### Paso 5: Configurar HomeKit Bridge

> [!NOTE]
> Si ya tienes HomeKit Bridge configurado y exponiendo todas las entidades, el cover se agregará automáticamente. Solo necesitas seguir este paso si filtras entidades manualmente.

Agrega la entidad del cover a tu configuración de HomeKit en `/config/configuration.yaml`:

```yaml
homekit:
  - filter:
      include_entities:
        - cover.puerta_del_garage
        # ... tus otras entidades ...
```

### Paso 6: Reiniciar Home Assistant

1. Ve a **Ajustes → Sistema → Reiniciar**
2. Después del reinicio, verifica que la entidad `cover.puerta_del_garage` aparezca en **Herramientas para desarrolladores → Estados**

### Paso 7: Agregar a Apple Home

1. Abre la app **Home** en tu iPhone/iPad
2. Si es la primera vez con HomeKit Bridge, escanea el código QR o ingresa el código de emparejamiento que aparece en las notificaciones de HA
3. La **Puerta del Garage** debería aparecer automáticamente como accesorio

## 🛡️ Safeguard: Doble-Pulsación

Este paquete maneja automáticamente el comportamiento peculiar de muchos motores de portón:

> Si el portón se está **abriendo** y pides **cerrar**, la primera señal de cierre actúa como **"detener"**. Se necesita una segunda señal para que realmente **cierre**.

### Lógica implementada:

| Acción | Estado actual | Comportamiento |
|--------|---------------|----------------|
| **Abrir** | Cerrado | ✅ Abre normalmente (1 señal) |
| **Abrir** | Cerrándose | 🛡️ Safeguard: detiene + abre (2 señales, 2s delay) |
| **Abrir** | Abierto/Abriéndose | ⏭️ Ignora (ya abierto) |
| **Cerrar** | Abierto | ✅ Cierra normalmente (1 señal) |
| **Cerrar** | Abriéndose | 🛡️ Safeguard: detiene + cierra (2 señales, 2s delay) |
| **Cerrar** | Cerrado/Cerrándose | ⏭️ Ignora (ya cerrado) |

## ⚠️ Limitaciones

- **Sin sensor físico**: El estado del portón se basa en timers. Si alguien usa el control RF físico, Home Assistant no lo detectará y el estado podría desincronizarse.
- **Solución futura**: Instalar un sensor de contacto ($5-10 USD) para tener feedback real del estado.
- **Estado al reiniciar**: El portón siempre inicia como `closed` al reiniciar HA. Si estaba abierto, puedes corregirlo manualmente desde **Herramientas para desarrolladores → Estados**.

## 📁 Estructura

```
garage-ir-tuya/
├── garage_door.yaml          # Paquete de Home Assistant (el archivo principal)
├── README.md                 # Este archivo
└── .gitignore
```

## 📄 Licencia

MIT — Usa, modifica y comparte libremente.
