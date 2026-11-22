# Orvia Campo — Android (Persona 2)

**Proyecto Android Studio** independiente de Orvia-Oficial. Kotlin + Jetpack Compose + Material 3, conectado a los contratos reales del repositorio `Pablofls/Proyecto12` (commit `5690365`, 21 de noviembre de 2026).

## 1. Cómo abrirlo (Windows)

1. Descomprime `Orvia_Campo_Android.zip`.
2. Abre la carpeta `Orvia_Campo_Android` en **Android Studio**, con **JDK 17**, **SDK 36** y conexión a internet para descargar dependencias.
3. Ejecuta una sola vez, desde PowerShell en esa carpeta:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\preparar-wrapper.ps1
   ```
   Este script obtiene `gradle-wrapper.jar` directamente del GitHub **oficial de Gradle** (versión 8.13.0). El archivo binario no se incluyó porque no estaba disponible en el entorno de generación.
4. En Android Studio selecciona **Sync Project with Gradle Files**. Luego **Run ▶** en un emulador Android o teléfono.
5. Para compilar por terminal:
   ```powershell
   .\gradlew.bat assembleDebug
   ```
   APK de depuración esperado: `app/build/outputs/apk/debug/app-debug.apk`.

## 2. Conexión al backend real

El login muestra un campo **Servidor Orvia**. Introduce solo la base del host (sin puerto):

- **Emulador y Docker en tu misma PC:** `http://10.0.2.2`.
- **Emulador con la VM de Orvia en otro equipo:** usa el dominio o una IP privada que permita alcanzar el reverse proxy por HTTP/HTTPS.
- **Teléfono físico:** una IP/dominio accesible desde el teléfono.

**Importante:** `10.0.2.2` significa *la máquina que ejecuta el emulador*, no una VM remota. Si Orvia corre en otra VM, `10.0.2.2` **no** apunta mágicamente a esa VM.

**Seguridad:** HTTP se admite solo en el build `debug` para desarrollo controlado; la versión `release` deshabilita tráfico HTTP sin cifrar. En un escenario real usa HTTPS en el reverse proxy. Los puertos internos de los microservicios no deben publicarse.

## 3. Qué está implementado realmente

| Perfil | Función | API existente |
| --- | --- | --- |
| Todos los roles autorizados | Login JWT, refresh, logout | `/api/v1/auth` mediante Nginx |
| Cliente | Lista de ventas reales; selección de línea de venta | `/api/v1/ventas` |
| Cliente | Motivos, elegibilidad y creación de devolución | `/api/v1/catalogos` + `/api/v1/devoluciones` |
| Cliente | Adjuntar fotografía JPEG real al expediente | `/api/v1/evidencias` |
| Recolector / Coordinador | Captura de avance de recolección e identificación por QR/ID numérico | `/api/v1/sincronizacion` |
| Recolector | Captura puntual de GPS (con permiso) | `/api/v1/sincronizacion` |
| Recolector / Operador / Centro | Foto/comentario de evidencia de campo | `/api/v1/sincronizacion` |
| Operador / Centro | Recepción con cotejo y control de duplicados | `/api/v1/sincronizacion` |
| Roles de campo | Cola cifrada offline con UUID constante, reintentos y resolución de conflicto | `/api/v1/sincronizacion` |

La cola guarda **un UUID por operación**, timestamp con zona, y opcionalmente fotografía JPEG junto a su SHA-256. Nunca se marca como confirmada hasta `estado: aceptada` del servidor. `conflicto` y `rechazada` se conservan en pantalla para revisión manual, sin reintentos automáticos con ID modificado.

El proyecto no tiene datos inventados: los indicadores muestran cifras reales de respuestas API o la cola local.

## 4. Funciones deliberadamente no simuladas

- **Notificaciones push/correo (8017):** el repositorio tiene campanita web, pero no un servicio API 8017 independiente. La app indica este pendiente en Perfil.
- **Mis recolecciones asignadas al Recolector:** la API de logística `8003` solo permite listar al Coordinador o Encargado del Centro. Se captura el **ID real** mediante QR numérico o entrada manual; hay que crear un endpoint por recolector con validación de pertenencia antes de mostrar lista de tareas.
- **Videos, firma digital, QR propio generado por Orvia, rutas optimizadas y GPS en segundo plano:** no implementados. No se presentan botones decorativos que finjan funcionar.
- **Cierre financiero o disposición offline:** nunca se ofrecen, porque requieren autorización en línea.

## 5. Arquitectura del código

- `MainActivity.kt`: cámara real, selector de imágenes, GPS, escáner Google Code Scanner y detección de reconexión.
- `OrviaViewModel.kt`: lógica de casos de uso y estados reales, gestión de la cola, llamadas HTTP.
- `network/OrviaApi.kt`: cliente OkHttp y decodificación de errores de negocio.
- `data/SecureStore.kt`: AES-GCM con clave Android Keystore; la cola se separa por `usuario_id`.
- `data/PhotoProcessor.kt`: compresión JPEG y SHA-256.
- `ui/Screens.kt`: pantallas Compose según rol y navegación sin rutas ficticias.

## 6. Verificar la VM antes de abrir la app

```bash
cd ~/Orvia-Oficial
docker compose ps
python scripts/probar_proxy.py --base http://localhost
```

Cada servicio debe responder 200 si se encuentra saludable. Tener un servicio `Up` sin un HTTP saludable no prueba su funcionalidad.

## 7. Estado de verificación

Este ZIP contiene **código fuente de la app**, no un APK compilado. Se inspeccionó la estructura y contratos reales de Orvia, pero el entorno de creación no dispone del SDK de Android ni de Gradle para ejecutar `assembleDebug` o probar cámara/GPS/emulador. Tras abrirlo es necesario compilar y corregir cualquier incompatibilidad que señale la versión instalada de Android Studio.

Consulta `docs/PRUEBAS_Y_PENDIENTES.md` para los casos manuales de aceptación y los límites actuales.
