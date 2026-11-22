# Arquitectura del monolito

## Punto de entrada y red

Nginx funciona como único punto de entrada del sistema. Los navegadores, la app
Android, la app de escritorio y las integraciones consumen un solo origen por
HTTP/HTTPS; Nginx dirige `/` al sistema web y cada prefijo `/api/v1/...` al
microservicio propietario. Los contenedores de negocio permanecen en la red
interna `orvia_backend` y no publican puertos en el host.

Esta decisión evita que los clientes conozcan la topología interna, centraliza
TLS, límites de peticiones, encabezados de proxy y correlation IDs, y permite
cambiar o escalar un servicio sin modificar las aplicaciones consumidoras. La
configuración y matriz de rutas están en `infra/nginx/` y
`docs/REVERSE_PROXY.md`.

## Ampliacion distribuida del segundo parcial

| Puerto | Servicio | Responsabilidad | Persistencia |
|---:|---|---|---|
| 8001 | auth | JWT, sesiones y revocacion | PostgreSQL + Redis |
| 8002 | devoluciones | Registro y autorizacion | PostgreSQL + MongoDB + Redis |
| 8003 | logistica | Recoleccion y recepcion | PostgreSQL + Redis |
| 8004 | inspecciones | Inspeccion, disposicion e inventario | PostgreSQL + MongoDB + Redis |
| 8005 | reembolsos-costos | Reembolso unico y costos | PostgreSQL + Redis |
| 8006 | ventas-catalogos | Ventas, productos, lotes y catalogos | PostgreSQL + Redis |
| 8007 | evidencias | Archivos privados y metadatos | PostgreSQL + MongoDB + volumen |
| 8008 | analisis-auditoria | Pareto, snapshots y auditoria | PostgreSQL + MongoDB + Redis |

El flujo implementado es `ventas-catalogos -> devoluciones -> logistica ->
inspecciones -> reembolsos-costos -> analisis-auditoria`, con `evidencias`
disponible durante solicitud e inspeccion. Todos validan el mismo JWT y comprueban en Redis que la
sesion siga activa y que el token no haya sido revocado. La ficha individual y
el guion de evidencias estan en `docs/MICROSERVICIOS_AVANCE_ROBERTO.md`.

El web conserva un modo de contingencia independiente y expone
`/integracion/servicios` para que un administrador consulte los health
checks (ocho en el segundo parcial; en el tercero se suman los de la tabla de la
seccion siguiente). En la rama `roberto/integracion-web-microservicios`, el login, las
consultas de ventas/devoluciones y las mutaciones del proceso completo se
ejecutan por HTTP contra las API. El cliente comun (`apps/web/app/api_client.py`) conserva
JWT en la sesion Redis, renueva access tokens y propaga correlation ids. La
matriz exacta esta en `docs/INTEGRACION_WEB_MICROSERVICIOS.md`.

## Ampliacion del tercer parcial: calidad y causa raiz

Persona 4 agrega los servicios que llevan una devolucion repetida hasta su causa
y hasta la correccion comprobada. Los puertos y el reparto entre integrantes estan
en `docs/PUERTOS.md`; la ficha de cada servicio, en `docs/FICHAS_MICROSERVICIOS.md`.

| Puerto | Servicio | Responsabilidad | Persistencia | Migracion |
|---:|---|---|---|---|
| 8006 | ventas-catalogos (ampliado) | Ademas de ventas y catalogos: lotes, numeros de serie, trazabilidad hasta tienda, venta y recorrido, y tasas de devolucion | PostgreSQL + Redis | 040 |
| 8008 | analisis-auditoria | Queda **solo auditoria** (bitacora y eventos). El analisis que tenia esta aislado y obsoleto | PostgreSQL + MongoDB + Redis | 045 |
| 8010 | clasificacion-motivos | Categorias de origen de la falla y submotivos con versiones; la sugerencia automatica la revisa una persona | PostgreSQL + Redis | 041 |
| 8011 | causa-raiz | Alertas, investigaciones, hipotesis, evidencias, acciones CAPA y medicion de su eficacia | PostgreSQL + Redis | 043, 044 |
| 8013 | proveedores | Indicadores de calidad por proveedor y reclamaciones con seguimiento | PostgreSQL + Redis | 042 |
| 8018 | reportes-analitica | Reportes (JSON, XML, CSV, Excel, PDF), datos para Highcharts, tendencias, pronosticos, anomalias y analisis de varios factores. Solo lectura | PostgreSQL + Redis | ninguna |

### El flujo de causa raiz

1. El sistema detecta un patron raro (por ejemplo, muchas devoluciones de un mismo lote)
   y genera una **alerta**. La alerta solo *propone* investigar.
2. Una persona abre la investigacion, junta evidencia y escribe hipotesis (5 porques,
   Ishikawa), que luego verifica.
3. Marca la causa como confirmada o inconclusa. Confirmar exige evidencia y una
   hipotesis verificada.
4. Crea acciones CAPA con responsable y fecha, y mide si funcionaron.
5. Un supervisor, distinto del analista, la cierra reconfirmando su contrasena.

Los estados y los servicios que intervienen estan en
[docs/diagramas/causa_raiz.md](diagramas/causa_raiz.md); el uso de la API, en
`docs/GUIA_CAUSA_RAIZ.md`. **El analisis apoya la decision, nunca la toma**
(RN-09, RN-11): una sugerencia de motivo no modifica la devolucion y una alerta no
abre una investigacion por si sola.

### Quien escribe cada dato

Cada tabla nueva tiene **un solo servicio** que escribe en ella, aunque todos
comparten el mismo PostgreSQL:

| Servicio | Escribe | Solo lee |
|---|---|---|
| ventas-catalogos | `series_producto` (ademas de los catalogos y ventas de siempre) | devoluciones, recolecciones, inspecciones, disposiciones |
| clasificacion-motivos | `submotivos`, `submotivos_versiones`, `clasificaciones_motivo` | `categorias_motivo` (catalogo fijo que carga la migracion 041), `devoluciones`, `motivos` |
| proveedores | `reclamaciones_proveedor`, `reclamacion_devoluciones`, `seguimiento_reclamacion` | proveedores, lotes, devoluciones, inspecciones, costos |
| causa-raiz | `alertas_patron`, `investigaciones`, `hipotesis`, `evidencias_investigacion`, `seguimiento_investigacion`, `acciones_capa`, `mediciones_eficacia` | ventas, lotes, devoluciones, politicas de devolucion |
| reportes-analitica | nada | ventas, lotes, devoluciones, costos |
| analisis-auditoria | nada (el analisis obsoleto aun escribe sus snapshots en MongoDB) | `bitacora`, eventos de MongoDB |

La excepcion es `bitacora`: la escriben todos los servicios y la base solo admite
agregar (migracion 045: `UPDATE`, `DELETE` y `TRUNCATE` fallan). Esa proteccion es del
esquema; frena a la aplicacion o a una inyeccion SQL, no a quien administre PostgreSQL
y desactive el trigger a proposito.

### Reglas de diseno de esta ampliacion

- **La auditoria no depende del analisis.** `auditoria.py` no importa nada del analisis y
  solo tiene rutas GET; pruebas lo hacen cumplir. El analisis se retiro por completo
  (`docs/MIGRACION_ANALISIS_8008.md`): `retirado.py` solo responde 410 con los sucesores.
- **Una tasa solo se compara con ventas que ya pudieron devolverse.** Las ventas de los
  ultimos dias aun pueden recibir devoluciones (plazo de `politicas_devolucion`, RN-16);
  contarlas haria parecer que la tasa baja. Lo aplican la medicion de eficacia de
  `causa-raiz` y las series de `reportes-analitica`, y ninguna da un veredicto con
  menos de 20 unidades vendidas.
- **Cerrar una investigacion es una operacion critica.** `causa-raiz` consume el permiso
  de un solo uso que emite `auth` (`cerrar_investigacion`), guardado en Redis, y valida
  las reglas de negocio antes de consumirlo.
- **Los servicios no se llaman entre si.** Se coordinan por la base y por Redis, de modo
  que la caida de uno no apaga a los demas.
- **PDF y Excel sin librerias nuevas.** `reportes-analitica` los escribe con la
  biblioteca estandar porque `CLAUDE.md` pide acordar las dependencias con el equipo; si
  se prefiere `reportlab` y `openpyxl`, solo cambia `formatos.py`.

## Por que un monolito ahora

El primer parcial pide un sistema web ejecutable, no una arquitectura
distribuida. Construir microservicios desde el inicio habria significado
resolver descubrimiento de servicios, comunicacion y despliegue antes de tener
siquiera el flujo del negocio funcionando.

La decision fue construir un **monolito modular**: una sola aplicacion que se
despliega junta, pero cuyo codigo esta separado por area de negocio de modo que
cada modulo pueda convertirse despues en un microservicio sin reescribir la
logica. Esto es lo que declara la seccion 5.2 del documento.

## Capas

```
Navegador
    |
    v
Plantillas Jinja2  (apps/web/app/templates)          <- presentacion
    |
    v
Blueprints         (apps/web/app/blueprints)         <- controladores y reglas del caso de uso
    |
    v
db.py / cache.py   (app)                    <- acceso a datos
    |
    v
PostgreSQL   Redis                          <- contenedores en la VM
```

Las plantillas nunca consultan la base de datos. Los blueprints nunca abren
conexiones a mano: usan `consultar` y `ejecutar` de `apps/web/app/db.py`. Esa separacion
es lo que permite mover un modulo a un microservicio mas adelante cambiando solo
la capa de acceso.

## Modulos

| Blueprint | Prefijo | Responsabilidad |
|---|---|---|
| `auth` | `/login`, `/logout` | Autenticacion, intentos fallidos, bloqueo |
| `panel` | `/panel`, `/bitacora` | Tableros, causas, costos, auditoria |
| `usuarios` | `/usuarios` | Cuentas, roles y bajas logicas |
| `catalogos` | `/catalogos` | Productos, lotes, proveedores, tiendas, rutas, transportistas, motivos |
| `ventas` | `/ventas` | Consulta de ventas y su detalle |
| `devoluciones` | `/devoluciones` | Expediente, evidencias, autorizacion |
| `logistica` | `/logistica` | Recoleccion y recepcion |
| `inspecciones` | `/inspecciones` | Inspeccion, disposicion e inventario recuperado |
| `reembolsos` | `/reembolsos` | Gestion del reembolso |
| `reportes` | `/reportes` | Descarga CSV de los reportes (RF-28); `app/exportacion.py` hace el streaming y el escape de formulas |
| `notificaciones` | `/notificaciones` | Campanita y bandeja por usuario (RF-29); `app/notificaciones.py` decide los destinatarios |

Cada blueprint corresponde a un microservicio del catalogo declarado en el
documento. La correspondencia es intencional: al partir el monolito, cada uno se
convierte en un servicio.

## Reglas de negocio en la base de datos, no solo en el codigo

Esta es la decision de diseno mas importante del proyecto. Las reglas criticas
estan implementadas como **triggers de PostgreSQL**, no solo como validaciones
del formulario:

| Trigger | Que impide |
|---|---|
| `trg_validar_destino_inventario` | Mandar a inventario un producto que la inspeccion marco como no apto (RN-06, RN-07) |
| `trg_validar_inspeccion_vs_disposicion` | Marcar una inspeccion como no apta cuando ya existe una disposicion a inventario |
| `trg_validar_reembolso` | Reembolsar mas que el valor devuelto, o aprobar sobre una devolucion sin autorizar (RN-04, RF-25) |

El motivo: cuando el sistema se parta en microservicios, varios servicios
escribiran sobre las mismas tablas. Si la regla vive solo en el codigo de la
aplicacion web, el primer servicio con un error la rompe. En la base de datos,
la regla se cumple sin importar quien escriba.

## Distribucion de los datos

| Motor | Que guarda | Por que ahi |
|---|---|---|
| PostgreSQL | Expediente completo: ventas, devoluciones, inspecciones, reembolsos, costos, bitacora | Datos relacionales con reglas de integridad y consultas de agregacion |
| Redis | Sesiones, conteo de intentos fallidos, bloqueo temporal | Datos efimeros con expiracion automatica, escritos en cada peticion |
| MongoDB | Detalle de la inspeccion, metadatos de evidencias, eventos y resultados de analisis | Estructura variable. **En uso desde el segundo parcial** (`inspecciones`, `evidencias`, `devoluciones`, `analisis-auditoria`); `inspecciones_ref.mongo_doc_id` apunta al documento |
| Volumen `evidencias_data` | Fotografias y documentos de evidencia | Archivos binarios que no deben vivir en la base; enlaces firmados de 15 min. Google Cloud Storage queda para el tercer parcial |

El bloqueo de cuenta se escribe en **los dos** motores a proposito: Redis lleva
el conteo vivo con expiracion automatica, y PostgreSQL conserva el bloqueo si
Redis se reinicia. Si se guardara solo en Redis, reiniciar el contenedor
levantaria todos los bloqueos (RNF-21).

## Autorizacion en dos niveles

1. **Por rol** — el decorador `roles_required(...)` en cada vista. Responde 403
   y deja el intento en la bitacora (RNF-09, RN-13).
2. **Por recurso** — `exigir_devolucion_visible(...)`. Un cliente que conoce el
   identificador de la devolucion de otro cliente recibe 403 igualmente. Esto es
   lo que la seccion 5.3 del documento describe como autorizacion por recurso.

## Vistas de solo lectura

`vista_costo_devolucion` (migracion 010) agrega, por devolucion, el total de
`costos` desglosado por etapa (transporte, inspeccion, almacenamiento,
reacondicionamiento, destruccion, reembolso, otros). Es una vista y no una
columna en `devoluciones` para no duplicar un dato que ya vive en `costos`:
guardarlo aparte obligaria a mantenerlo sincronizado a mano cada vez que se
inserta un costo, lo que rompe la normalizacion y es una fuente comun de
datos desincronizados. `panel.costos` y el analisis de causa raiz la
consultan directamente.

## Preparacion para los siguientes parciales

El monolito ya incluye piezas que solo tienen sentido en la arquitectura
distribuida, para no tener que reconstruir despues:

- **`/health`** devuelve el estado de cada dependencia por separado y responde
  503 si alguna falla (RNF-22, RF-32).
- **Identificador de correlacion** en cada registro de bitacora, que permitira
  seguir una peticion entre servicios (RNF-23).
- **`inspecciones_ref`** ya esta separada del detalle de la inspeccion,
  anticipando que ese detalle vivira en MongoDB.
- **`evidencias`** guarda bucket y objeto, nunca una URL publica, para que el
  enlace firmado se genere al consultar (RNF-15).
- **Configuracion por variables de entorno**, sin ningun valor en el codigo.

## Diagramas y documento tecnico (segundo parcial)

Los diagramas viven como Mermaid en `docs/diagramas/` y renderizan en GitHub:

| Diagrama | Archivo |
|---|---|
| Componentes | [docs/diagramas/componentes.md](diagramas/componentes.md) |
| Despliegue | [docs/diagramas/despliegue.md](diagramas/despliegue.md) |
| Secuencia: login, JWT y revocacion | [docs/diagramas/secuencia_login_jwt.md](diagramas/secuencia_login_jwt.md) |
| Secuencia: proceso completo | [docs/diagramas/secuencia_proceso_completo.md](diagramas/secuencia_proceso_completo.md) |
| Comunicacion web-servicios | [docs/diagramas/comunicacion_web_servicios.md](diagramas/comunicacion_web_servicios.md) |
| Datos PostgreSQL (logico y fisico) | [docs/diagramas/datos_postgresql.md](diagramas/datos_postgresql.md) |
| Datos MongoDB | [docs/diagramas/datos_mongodb.md](diagramas/datos_mongodb.md) |
| Claves de Redis | [docs/diagramas/redis_claves.md](diagramas/redis_claves.md) |
| Causa raiz: estados y servicios (tercer parcial) | [docs/diagramas/causa_raiz.md](diagramas/causa_raiz.md) |

El documento tecnico integral, que los reune con el diseno de cada servicio, los
contratos, la seguridad y las evidencias pendientes, es
[docs/DOCUMENTO_TECNICO.md](DOCUMENTO_TECNICO.md).
