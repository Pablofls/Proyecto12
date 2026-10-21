# Cambios de la integracion web con microservicios

Fecha de corte: 21 de octubre de 2026  
Rama: `roberto/integracion-web-microservicios`  
Base estable: `roberto/tres-microservicios` (`7dca3ad`)

## Proposito de esta rama

La version estable ya contenia el monolito web y ocho microservicios
desplegables, pero el flujo principal del sistema web todavia ejecutaba la
mayoria de sus operaciones directamente contra PostgreSQL.

Esta rama conserva la interfaz y el modo monolitico como contingencia, pero
conecta las operaciones principales del sitio mediante HTTP con los
microservicios responsables. No existe fallback silencioso: si el modo
distribuido esta activo y un servicio falla, la web informa el error y no
repite la escritura directamente en la base de datos.

## Cambios principales

### Cliente comun para microservicios

Se agrego `app/api_client.py` para centralizar:

- requests HTTP en JSON;
- encabezado `Authorization: Bearer <JWT>`;
- propagacion de `X-Correlation-ID`;
- timeout configurable;
- manejo uniforme de errores HTTP y de disponibilidad;
- renovacion automatica del access token una sola vez;
- eliminacion de la sesion local si el refresh token deja de ser valido.

Los access y refresh tokens permanecen en la sesion Flask respaldada por
Redis. No se guardan en `localStorage` ni en una cookie legible por JavaScript.

### Configuracion

Se agregaron las siguientes variables:

```dotenv
USE_MICROSERVICES=true
MICROSERVICE_TIMEOUT=5
AUTH_SERVICE_URL=http://auth:8000
DEVOLUCIONES_SERVICE_URL=http://devoluciones:8000
LOGISTICA_SERVICE_URL=http://logistica:8000
INSPECCIONES_SERVICE_URL=http://inspecciones:8000
REEMBOLSOS_SERVICE_URL=http://reembolsos-costos:8000
VENTAS_SERVICE_URL=http://ventas-catalogos:8000
EVIDENCIAS_SERVICE_URL=http://evidencias:8000
ANALISIS_SERVICE_URL=http://analisis-auditoria:8000
```

`USE_MICROSERVICES=true` habilita el flujo distribuido. La barra superior
muestra la insignia **API distribuida**. Con `false`, el mismo artefacto puede
operar temporalmente con la logica del monolito.

### Operaciones web conectadas

| Accion del sistema web | Microservicio |
|---|---|
| Inicio, renovacion y cierre de sesion | `auth` |
| Consulta de ventas y sus lineas | `ventas-catalogos` |
| Listado, registro y resolucion de solicitudes | `devoluciones` |
| Registro de comentarios como evidencia | `evidencias` |
| Programacion, asignacion y estados de recoleccion | `logistica` |
| Confirmacion de recepcion | `logistica` |
| Registro y actualizacion de inspecciones | `inspecciones` |
| Disposicion y etiquetado de inventario | `inspecciones` |
| Registro de costos y resolucion del reembolso | `reembolsos-costos` |
| Resumen, sincronizacion y Pareto del panel de causas | `analisis-auditoria` |

Las consultas compuestas del expediente y algunos tableros conservan lectura
relacional directa porque combinan varios dominios en una sola plantilla. Las
mutaciones del proceso distribuido pasan por la API responsable.

### Reembolsos y costos

Se ajusto la autorizacion de costos para que cada etapa corresponda a un rol:

- Coordinador de Logistica: transporte.
- Encargado del Centro: almacenamiento.
- Inspector: inspeccion.
- Analista: reacondicionamiento, destruccion y otros.
- Encargado de Reembolsos: reembolso.

El servicio mantiene el lock distribuido de Redis para impedir que una misma
devolucion sea pagada dos veces.

### Panel de causas

El panel ahora puede:

1. solicitar el resumen al servicio `analisis-auditoria`;
2. sincronizar los datos oficiales de PostgreSQL hacia snapshots derivados en
   MongoDB;
3. solicitar el Pareto de motivos;
4. reutilizar el resultado desde la cache Redis;
5. mostrar cantidad de snapshots, reportes generados, version de datos y si la
   respuesta fue `cache miss` o `cache hit`.

El analisis continua siendo apoyo para revision humana y no asigna una causa o
responsabilidad automaticamente.

## Verificacion realizada

En la VM de GCP se comprobo:

- web y ocho microservicios con respuesta HTTP 200 en `/health`;
- Swagger UI accesible en los puertos 8001 a 8008;
- flujo real iniciado desde formularios web;
- alta y autorizacion de `DEV-2026-0033`;
- programacion, asignacion, transito, entrega y recepcion;
- inspeccion refrigerada con documento real en MongoDB;
- disposicion, inventario y etiqueta `REC-2026-0033`;
- reembolso de 32.24 y cierre automatico del expediente;
- liberacion del lock Redis al terminar;
- sincronizacion de 33 casos en MongoDB;
- primer Pareto con `cache miss` y segunda consulta con `cache hit`;
- usuario y correlation id visibles en los logs de cada API.

Resultado de pruebas locales de la version actual:

- 88 pruebas aprobadas;
- 4 pruebas de integracion de devoluciones omitidas cuando `INTEGRACION` no
  vale `1`;
- 8 documentos OpenAPI validos con 55 operaciones documentadas;
- 22 contratos XSD validos;
- Compose resuelve 12 servicios y 4 volumenes.

## Commits de esta integracion

| Commit | Contenido |
|---|---|
| `820a512` | Cliente HTTP, JWT/refresh y flujo web conectado con los servicios. |
| `e184986` | Autorizacion de costos por rol y documentacion del E2E. |
| `92adaec` | Sincronizacion y Pareto distribuido en el panel de causas. |

## Como obtener la version

Repositorio del fork:

`https://github.com/BobbySandoval122/Proyecto12.git`

Para agregarlo como remoto y traer la rama:

```bash
git remote add roberto https://github.com/BobbySandoval122/Proyecto12.git
git fetch roberto
git switch --track -c roberto/integracion-web-microservicios \
  roberto/roberto/integracion-web-microservicios
```

Si la rama local ya existe:

```bash
git switch roberto/integracion-web-microservicios
git pull roberto roberto/integracion-web-microservicios
```

## Como levantarla

No se debe reemplazar un `.env` ya configurado. Si es una instalacion nueva,
se copia `.env.example` a `.env` y se sustituyen todos los valores de ejemplo.

```bash
docker compose up -d --build
docker compose exec app python scripts/migrate.py
docker compose ps
```

Para comprobar el despliegue:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8002/health
# continuar hasta el puerto 8008
```

La web queda en el puerto 8000 del host. Los puertos 8001 a 8008 se utilizan
para las API y Swagger de cada microservicio.

## Contrasenas y secretos

Esta integracion no modifica el mecanismo de contrasenas ni incorpora
credenciales al codigo. La contrasena de las cuentas demo se toma de
`PASSWORD_DEMO` en el `.env` privado de la VM. Los secretos de PostgreSQL,
MongoDB, Redis, Flask y JWT tambien deben permanecer fuera de Git.

No se debe copiar ni sobrescribir el `.env` de la VM al actualizar la rama.

## Pendientes del equipo

La arquitectura y el flujo integrado estan implementados. Antes de entregar,
el equipo debe terminar la documentacion integral, capturas request/response,
colecciones Postman restantes, pruebas de integracion con `INTEGRACION=1`,
evidencias de PostgreSQL/MongoDB/Redis/volumen, presentacion y video.

