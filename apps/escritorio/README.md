# Aplicacion de escritorio del centro de devoluciones

## Ejecutable para el centro de devoluciones

Instala las dependencias de construcción y ejecuta `construir.ps1`. El resultado
es `dist/CentroDevoluciones.exe` y utiliza el `config.json` situado junto a él.
Los XSD requeridos se empaquetan dentro del ejecutable.
El ejecutable y sus ventanas utilizan la hoja verde de Orvia como identidad visual.

```powershell
python -m pip install -r apps/escritorio/requirements.txt -r apps/escritorio/requirements-build.txt
powershell -ExecutionPolicy Bypass -File apps/escritorio/construir.ps1
```

Cliente PySide6 de Roberto para centros de devolución. No accede directamente
a PostgreSQL, MongoDB ni Redis y no repite reglas del negocio: consume los
microservicios desplegados. La interfaz comparte colores, tarjetas, tablas y
jerarquía visual con el sistema web.
Todas sus peticiones y respuestas usan `application/xml`; los cuerpos se
validan localmente con XSD antes de enviarse y nuevamente en el servicio.

1. Copiar `config.example.json` como `config.json` y poner en `base` la URL del
   reverse proxy (por ejemplo `http://IP-DE-LA-VM:8000`, o sin puerto si el proxy
   esta en el 80/443). Ya no se configura un puerto por microservicio: Nginx es
   la unica entrada y enruta por `/api/v1/...`. El formato anterior (un URL por
   servicio) sigue aceptandose.
2. Instalar: `python -m pip install -r apps/escritorio/requirements.txt`.
3. Ejecutar desde la raiz: `python apps/escritorio/main.py`.

Los tokens viven solo en memoria durante la sesion. Las decisiones críticas
requieren un token de operación de un solo uso emitido por `auth`.

## Flujo y perfiles

- **Inspector:** consulta pendientes y registra el dictamen técnico.
- **Analista/Supervisor:** revisa el dictamen y autoriza la disposición.
- **Encargado del centro (Roberto):** recibe en cuarentena y controla la
  reincorporación autorizada al inventario recuperable.
- **Encargado de reembolsos:** aprueba o rechaza un reembolso único.
- **Administrador/Analista:** consulta auditoría e investigaciones sin poder
  modificarlas.

Los menús son específicos por rol, pero la autorización definitiva siempre la
aplica cada microservicio. Ocultar un botón nunca sustituye un permiso del API.

## Pruebas

```powershell
$env:QT_QPA_PLATFORM='offscreen'
python -m pytest -q apps/escritorio/tests/test_cliente_xml.py apps/escritorio/tests/test_interfaz.py

$env:INTEGRACION_ESCRITORIO='1'
$env:PASSWORD_DEMO='DemoRoberto2026!'
python -m pytest -q apps/escritorio/tests/test_integracion_real.py
```

La segunda suite requiere Docker Compose levantado y valida inicio de sesión y
consultas XML reales para cada perfil, además del rechazo 403 por rol incorrecto.
