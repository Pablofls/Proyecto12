# Documento tecnico integral — Segundo parcial

**Plataforma distribuida para la gestion y analisis de devoluciones de productos refrigerados y no refrigerados mediante logistica inversa y analisis de causa raiz**

| | |
|---|---|
| Proyecto | 12 — Devoluciones y logistica inversa con analisis de causa raiz |
| Equipo | 02 |
| Materia | Integracion de Aplicaciones Computacionales |
| Institucion | Universidad de Monterrey (UDEM) |
| Entrega | Segundo parcial: monolito web ampliado y ocho microservicios |
| Integrantes | Josue Berdeal, Roberto Sandoval, David Munoz, Pablo Flores |
| Repositorio | `git@github.com:Pablofls/Proyecto12.git` |
| Version del documento | 21 de octubre de 2026, redactado sobre `main` en el commit `2a52f76` |

> **Como leer este documento.** Describe lo que **esta implementado en el
> repositorio**, verificado contra `services/*/app.py`, `shared/`,
> `docker-compose.yml`, `db/migrations/` y `apps/web/`. Lo que no se puede
> demostrar desde el codigo (ejecuciones en la VM, capturas, resultados de
> pruebas) queda marcado como **EVIDENCIA PENDIENTE** con un identificador
> `EV-nn`; el indice de pendientes esta al final del apartado 13. Lo que
> depende de la sesion de notificaciones y reportes (RF-28, RF-29) lleva
> `<!-- ACTUALIZAR tras sesion 01 -->`. El orden sigue el listado de 20
> apartados del plan de documentacion del equipo; el documento del curso
> (`docs/enunciado/`) no contiene una seccion numerada 13 con esa estructura,
> asi que se tomo ese listado como guia.

## Indice

1. [Portada e integrantes](#1-portada-e-integrantes)
2. [Resumen ejecutivo y problema](#2-resumen-ejecutivo-y-problema)
3. [Objetivos y alcance actualizado](#3-objetivos-y-alcance-actualizado)
4. [Requerimientos funcionales y no funcionales](#4-requerimientos-funcionales-y-no-funcionales)
5. [Correcciones respecto del primer parcial](#5-correcciones-respecto-del-primer-parcial)
6. [Procesos de negocio, actores y roles](#6-procesos-de-negocio-actores-y-roles)
7. [Arquitectura general y diagramas](#7-arquitectura-general-y-diagramas)
8. [Diseno de PostgreSQL, MongoDB y Redis](#8-diseno-de-postgresql-mongodb-y-redis)
9. [Diseno individual de cada microservicio](#9-diseno-individual-de-cada-microservicio)
10. [Contratos JSON, XML y XSD](#10-contratos-json-xml-y-xsd)
11. [Seguridad, JWT y control de acceso](#11-seguridad-jwt-y-control-de-acceso)
12. [Documentacion de endpoints](#12-documentacion-de-endpoints)
13. [Evidencias request/response](#13-evidencias-requestresponse)
14. [Integracion del web con los servicios](#14-integracion-del-web-con-los-servicios)
15. [Docker](#15-docker)
16. [Pruebas unitarias y de integracion](#16-pruebas-unitarias-y-de-integracion)
17. [Resultados, problemas identificados y soluciones](#17-resultados-problemas-identificados-y-soluciones)
18. [Matriz de trazabilidad y cumplimiento](#18-matriz-de-trazabilidad-y-cumplimiento)
19. [Conclusiones tecnicas y trabajo pendiente](#19-conclusiones-tecnicas-y-trabajo-pendiente)
20. [Anexo: que cambio en este parcial y reparto](#20-anexo-que-cambio-en-este-parcial-y-reparto)

---

## 1. Portada e integrantes

La portada y la tabla de datos estan al inicio. Integrantes segun
`README.md`:

| Integrante | Usuario de GitHub | Rama de trabajo |
|---|---|---|
| Pablo Flores | `Pablofls` | `pablo/...` |
| Roberto Sandoval | `BobbySandoval122` | `roberto/...` |
| David Munoz | `Thedavidzavala6` (tambien `thedavidzavala6`) | `david/...` |
| Josue Berdeal | sin commits en el historial (ver apartado 20) | `josue/...` |

<!-- COMPLETAR: matriculas y apellidos completos tal como los pide la portada oficial -->

## 2. Resumen ejecutivo y problema

**Problema.** Las devoluciones suelen tratarse como casos aislados, aunque
varias provengan del mismo lote, proveedor, empaque, ruta o tienda. En productos
refrigerados el tiempo fuera de la cadena de frio decide si el producto puede
volver a inventario. La solucion debe conectar la evidencia no estructurada
(fotos, comentarios, detalle de inspeccion) con la informacion transaccional
(ventas, lotes, reembolsos, costos) para detectar problemas sistemicos
(`docs/enunciado/Descripcion.md`).

**Solucion entregada en este parcial.** Un sistema web (Flask + Jinja2) que
conserva todo el proceso del primer parcial y ahora delega sus operaciones
criticas en **ocho microservicios REST** versionados (`/api/v1`), cada uno en su
propio contenedor Docker, con autenticacion comun por JWT, respuestas en JSON o
XML segun `Accept`, contratos XSD, documentacion Swagger y `/health`. Los datos
se reparten entre PostgreSQL (expediente transaccional), MongoDB (detalle
semiestructurado, eventos y resultados de analisis) y Redis (sesiones,
revocacion, limites, bloqueo y cache). Todo se ejecuta con Docker Compose en la
maquina virtual de GCP del equipo.

**Cifras verificables en el repositorio.**

| Elemento | Cantidad | Fuente |
|---|---:|---|
| Microservicios | 8 | `services/` |
| Contenedores en Compose | 12 (8 servicios, web, PostgreSQL, Redis, MongoDB) | `docker-compose.yml` |
| Migraciones SQL | 12 | `db/migrations/` |
| Esquemas XSD | 22 (21 por servicio y 1 comun de error) | `services/*/contratos`, `shared/contratos` |
| Patrones de clave en Redis | 10 | `docs/diagramas/redis_claves.md` |
| Colecciones MongoDB | 4 | `db/mongo/init.js` |
| Requerimientos funcionales | 32: 27 implementados, 2 parciales, 3 pendientes | `docs/TRAZABILIDAD.md` |
| Requerimientos no funcionales | 30: 21 implementados, 5 parciales, 4 pendientes | `docs/TRAZABILIDAD.md` |

## 3. Objetivos y alcance actualizado

**Objetivo general.** Entregar una plataforma distribuida que registre
devoluciones ligadas a una venta, coordine su logistica inversa, inspeccione y
decida el destino de cada producto, controle un reembolso unico, y permita
analizar causas recurrentes con apoyo de patrones (nunca como decision
automatica, RN-09).

**Objetivos del segundo parcial.**

1. Ampliar el web sin perder su operacion independiente (`USE_MICROSERVICES=false`).
2. Construir ocho microservicios con responsabilidad unica, contenedor propio,
   rutas versionadas, validacion, autenticacion, autorizacion, JSON/XML, errores
   uniformes, registro de actividad, `/health` y OpenAPI.
3. Definir y validar contratos JSON y XML (XSD).
4. Usar MongoDB y Redis de forma funcional, no solo declarada.
5. Dejar todo reproducible con Docker Compose en la VM.

**Dentro del alcance.** Web ampliado, ocho microservicios, JWT con renovacion y
revocacion, JSON y XML, PostgreSQL, MongoDB, Redis, Swagger y Docker Compose
(`CLAUDE.md`, "Alcance de esta entrega").

**Fuera del alcance acordado por el equipo.** Las aplicaciones Android y de
escritorio. Los **contratos** que esos clientes consumirian si estan
implementados (JSON para movil, XML para escritorio). Ademas quedan para el
tercer parcial el almacenamiento en Google Cloud Storage, HTTPS, pruebas de
carga y respaldo (apartado 19).

> **Nota de cumplimiento.** El documento de entregables del curso lista la
> aplicacion movil y la de escritorio como entregables del segundo parcial
> (`docs/enunciado/Entregables.md`). El alcance de este repositorio las excluye
> por decision del equipo registrada en `CLAUDE.md`; conviene que el equipo
> confirme esa decision con el profesor antes de la entrega.

## 4. Requerimientos funcionales y no funcionales

La matriz completa, con el archivo que implementa cada identificador y su
estado, esta en [`docs/TRAZABILIDAD.md`](TRAZABILIDAD.md). Resumen:

| Grupo | Total | Implementados | Parciales | Pendientes |
|---|---:|---:|---:|---|
| RF (funcionales) | 32 | 27 | 2: RF-19, RF-29 | 3: RF-02, RF-14, RF-28 |
| RNF (no funcionales) | 30 | 21 | 5: RNF-13, RNF-14, RNF-15, RNF-21, RNF-28 | 4: RNF-17, RNF-20, RNF-24, RNF-29 |
| RN (reglas de negocio) | 15 | 14 | 1: RN-14 | 0 |

<!-- ACTUALIZAR tras sesion 01: RF-28 (exportar reportes) y RF-29 (notificaciones visibles en el web) cambian de estado si la sesion 01 entra a main; revisar tambien UC-24 y UC-25 -->

**Reglas de negocio** y donde se hacen cumplir:

| Regla | Resumen | Donde |
|---|---|---|
| RN-01 | Toda devolucion nace de una linea de venta | `devoluciones.venta_detalle_id NOT NULL` y `409 cantidad_excedida` |
| RN-02 | Folio unico | `seq_folio_devolucion` + `UNIQUE` (migracion 007) |
| RN-03 | Un reembolso valido por devolucion | `UNIQUE (devolucion_id)` + lock Redis |
| RN-04 | Reembolso solo sobre devolucion autorizada | `trg_validar_reembolso` + validacion en el servicio |
| RN-05 a RN-07 | Datos de cadena de frio y bloqueo a inventario | `evaluar_aptitud` + triggers de las migraciones 001 y 006 |
| RN-09, RN-11 | Analisis y clasificacion son apoyo | `requiere_confirmacion = true`, `interpretacion` en el Pareto |
| RN-12, RN-13 | Bitacora y permisos por rol | `registrar_bitacora`, `requiere_jwt(...)` |

## 5. Correcciones respecto del primer parcial

Salen de `docs/BITACORA.md`, de `docs/AUDITORIA_SEGUNDO_PARCIAL.md` y del
historial de git (`git log`). El hash identifica el commit que lo contiene.

| # | Que se corrigio | Por que | Donde / commit |
|---|---|---|---|
| 1 | Se agrego `venta_detalle`; `devoluciones.venta_id` paso a `venta_detalle_id` | Una venta con varios articulos no se podia representar y el valor devuelto no era exacto (base del control antifraude) | migracion 002; `7282d8f` |
| 2 | Triggers de reembolso y de coherencia inspeccion-disposicion | Nada impedia reembolsar mas de lo pagado ni aprobar sobre una devolucion no autorizada (RN-04, RF-25) | migracion 006; `7282d8f` |
| 3 | Folio por secuencia | Contar filas duplica folios con usuarios concurrentes (RN-02, RNF-19) | migracion 007; `7282d8f` |
| 4 | Roles como parte del contrato del sistema | Los nombres de rol definen permisos; se unifico "Encargado del Centro de Devoluciones" | migracion 008; `7282d8f` |
| 5 | Costos por etapa y vista de costo total | La retroalimentacion senalo que el costo total no se podia calcular; se amplio el CHECK y se creo `vista_costo_devolucion` en lugar de una columna redundante | migraciones 009 y 010; `e125f6e` |
| 6 | Destino `donacion` | La retroalimentacion lo pide y faltaba en el catalogo | migracion 011; `e125f6e` |
| 7 | Panel de causa raiz y KPIs | RF-23, RF-24 y RF-26 se adelantaron al monolito por instruccion de la retroalimentacion | `bb5a171`, `a04dfcb` |
| 8 | `fecha_cierre` tambien en el rechazo inicial | Sin ello el KPI de tiempo de resolucion ignoraba las devoluciones rechazadas en la primera revision | migracion 012; `a04dfcb` |
| 9 | Orden de `DROP CONSTRAINT`/`UPDATE` en la migracion 009 y seed con `transporte` | El `UPDATE` violaba el CHECK viejo; el seed fallaba en una base limpia (RNF-27) | `60d7c90`, `04dfc46` |
| 10 | Contrasena de demostracion fuera del repositorio | El repositorio es publico; la contrasena anterior se considera comprometida | `527f2dc` |
| 11 | Puertos `55432`/`56379` y etiqueta `:z` | La VM ya tiene un PostgreSQL nativo en 5432 y SELinux en `Enforcing` | `039304a` |
| 12 | `ip_origen()` ya no lee `X-Forwarded-For` | Un cliente podia saltarse el rate limit variando ese header | `dd0cc68` (base comun de `shared/`); la verificacion en la VM esta narrada en `BITACORA.md` |
| 13 | Un 500 ya no confirma la transaccion | El manejador de errores hacia que el teardown viera `exc=None` y hiciera commit a medias | `dd0cc68` |
| 14 | `/health` ya no devuelve el texto de la excepcion | Evita filtrar host y usuario de la base (RNF-16) | `dd0cc68` |
| 15 | Fechas en ISO 8601 y NUMERIC como numero | `jsonify` usaba RFC 822 | `2f750a7` |
| 16 | Validaciones de fecha, booleano estricto, minutos negativos y montos no finitos (NaN/Infinity) | La auditoria las detecto en logistica, inspecciones y reembolsos | `docs/AUDITORIA_SEGUNDO_PARCIAL.md` |
| 17 | Etapas de costo autorizadas por rol | Cada rol solo registra costos de su propia etapa | `e184986`, `ETAPAS_POR_ROL` |
| 18 | Estado real de MongoDB en la trazabilidad | La matriz afirmaba un uso que no existia | `aaf7b23` |

## 6. Procesos de negocio, actores y roles

### 6.1 Proceso principal

```
Cliente solicita (linea de venta + motivo + evidencia)
  -> Analista autoriza / rechaza / pide informacion
  -> Coordinador programa y asigna recoleccion (ruta, transportista)
  -> Transito -> recoleccion completada
  -> Encargado del Centro confirma recepcion
  -> Inspector registra condiciones (cadena de frio, danos, caducidad)
  -> Analista decide el destino (inventario, reparacion, reacondicionamiento,
     reciclaje, devolucion a proveedor, desecho, donacion)
  -> Encargado del Centro etiqueta el inventario recuperable
  -> Encargado de Reembolsos aprueba o rechaza el reembolso (una sola vez)
  -> La devolucion se cierra
  -> Analista y Administrador consultan costos, Pareto, fraude y bitacora
```

El diagrama de secuencia del flujo completo, con las llamadas reales a los
servicios, esta en
[`diagramas/secuencia_proceso_completo.md`](diagramas/secuencia_proceso_completo.md).
Estados de `devoluciones.estado`: `solicitada`, `en_revision`, `autorizada`,
`rechazada`, `en_recoleccion`, `recibida`, `en_inspeccion`, `resuelta`,
`cerrada`.

### 6.2 Los siete roles

Los nombres son los de la tabla `roles` (migracion 008) y las constantes de
`shared/seguridad.py`. La aplicacion de origen y las restricciones vienen de la
seccion 3.5 del documento del primer parcial.

| Rol | Responsabilidad | Restriccion clave |
|---|---|---|
| Cliente | Solicitar devoluciones, adjuntar evidencia, consultar sus casos | Solo ve y modifica lo propio |
| Inspector | Inspeccionar y registrar condiciones | No autoriza ni decide destino |
| Encargado del Centro de Devoluciones | Confirmar recepcion, etiquetas, inventario recuperado | No aprueba reembolsos ni edita catalogos |
| Coordinador de Logistica | Programar y asignar recolecciones | No accede a la inspeccion ni al destino |
| Analista de Devoluciones | Autorizar, decidir destino, revisar causas, fraude y reportes | No administra usuarios ni catalogos |
| Encargado de Reembolsos | Aprobar o rechazar reembolsos | Solo sobre devoluciones autorizadas |
| Administrador | Usuarios, roles, catalogos y monitoreo | No participa en la operacion diaria |

### 6.3 Matriz de permisos por modulo (documento del primer parcial)

`G` gestiona, `C` consulta, `C*` consulta solo lo propio, `-` sin acceso.

| Modulo | Cliente | Inspector | Enc. Centro | Coordinador | Analista | Enc. Reembolsos | Admin |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Usuarios y catalogos | - | - | - | - | C | - | G |
| Registro de solicitud | G* | - | - | - | C | - | - |
| Autorizacion de solicitud | C* | - | - | - | G | - | - |
| Recoleccion | C* | - | - | G | C | - | - |
| Inspeccion y recepcion | - | G | G (recepcion) | - | C | - | - |
| Disposicion del producto | C* | - | C | - | G | - | - |
| Reembolsos | C* | - | - | - | C | G | - |
| Analisis de causas y fraude | - | - | - | - | G | - | C |
| Reportes y costos | - | - | - | - | G | C | C |
| Auditoria y monitoreo | - | - | - | - | C | - | C |

### 6.4 Operaciones de la API por rol (segun los decoradores `requiere_jwt`)

| Rol | Puede ejecutar por API |
|---|---|
| Cliente | alta, correccion y cancelacion de sus devoluciones; evidencias propias; ventas propias; catalogo de motivos; sugerir motivo |
| Inspector | registrar y corregir inspeccion; consultarla; evidencias de la etapa de inspeccion; costo de inspeccion |
| Encargado del Centro | consultar recolecciones; confirmar recepcion; consultar inspeccion; etiquetar inventario; costo de almacenamiento |
| Coordinador de Logistica | programar, asignar y avanzar recolecciones; consultarlas; costo de transporte |
| Analista | registrar y resolver devoluciones; disposicion; consultar reembolsos y costos; todo `analisis` y `auditoria`; costos de reacondicionamiento, destruccion y otros; leer catalogos |
| Encargado de Reembolsos | resolver reembolsos (una vez); consultar reembolsos y costos; costo de reembolso |
| Administrador | revocar sesiones; CRUD de los siete catalogos; `analisis` y `auditoria`; panel de salud (web) |

**Diferencias conocidas entre la matriz y la API** (el web lee PostgreSQL
directamente para varias consultas compuestas, por lo que el usuario si ve esa
informacion en pantalla):

- El Analista puede **registrar** una devolucion por API (`POST /devoluciones`
  acepta `Cliente` y `Analista`); la matriz le asigna solo consulta.
- `GET /logistica/recolecciones` solo admite Coordinador y Encargado del
  Centro; Cliente y Analista consultan la recoleccion desde el web.
- `GET /reembolsos-costos/costos/{id}` no admite Administrador, aunque la
  matriz le da consulta de costos.

## 7. Arquitectura general y diagramas

La arquitectura es un **monolito web modular** que conserva sus capas
(plantillas -> blueprints -> acceso a datos) y **ocho microservicios Flask** que
comparten la libreria `shared/` (JWT, respuestas JSON/XML, errores,
paginacion, MongoDB, validacion XSD) copiada en cada imagen. El web es un cliente
HTTP de los servicios (`apps/web/app/api_client.py`) y conserva un modo de
contingencia. Detalle y decisiones en
[`ARQUITECTURA.md`](ARQUITECTURA.md); justificacion del enfoque modular en ese
mismo archivo ("Por que un monolito ahora").

Los ocho diagramas, versionados como Mermaid (renderizan en GitHub):

| # | Diagrama | Contenido |
|---|---|---|
| 1 | [Componentes](diagramas/componentes.md) | Web, 8 servicios, PostgreSQL, MongoDB, Redis, volumen; protocolo de cada flecha |
| 2 | [Despliegue](diagramas/despliegue.md) | VM de GCP, red de Compose, puertos 8000-8008, volumenes, `127.0.0.1` frente a `0.0.0.0` |
| 3 | [Secuencia: login y JWT](diagramas/secuencia_login_jwt.md) | Login, emision, verificacion en otro servicio, refresh, logout y revocacion |
| 4 | [Secuencia: proceso completo](diagramas/secuencia_proceso_completo.md) | Auth -> venta -> devolucion -> evidencia -> logistica -> inspeccion -> reembolso con lock y 409 -> Pareto con cache |
| 5 | [Comunicacion web-servicios](diagramas/comunicacion_web_servicios.md) | JWT, refresh, `X-Correlation-ID`, negociacion JSON/XML |
| 6 | [Datos PostgreSQL](diagramas/datos_postgresql.md) | ER logico y fisico, triggers, vista |
| 7 | [Datos MongoDB](diagramas/datos_mongodb.md) | Colecciones, documentos, indices, enlace con PostgreSQL |
| 8 | [Claves Redis](diagramas/redis_claves.md) | Patron, finalidad, TTL, quien escribe y lee |

**Decisiones de arquitectura relevantes** (verificables en el codigo):

1. **Reglas criticas en la base de datos.** Los triggers de las migraciones 001
   y 006 protegen RN-04, RN-06 y RN-07 aunque un servicio con un error las
   omita.
2. **Base de datos compartida.** Los ocho servicios usan la misma base
   PostgreSQL y no se llaman entre si por HTTP: cada uno valida el JWT
   localmente (`JWT_SECRET` comun) y consulta Redis. La orquestacion del
   proceso la hace el cliente (hoy el web). Es una simplificacion consciente
   (apartado 19).
3. **Falla cerrada.** Si Redis no responde, los endpoints protegidos devuelven
   503: sin poder consultar la revocacion no se sabe si un token sigue vigente.
4. **Transaccion por peticion** con rollback ante un 500 (`shared/infra.py`).
5. **El bloqueo de cuenta vive en Redis y en PostgreSQL** para sobrevivir a un
   reinicio de Redis (RNF-21).

## 8. Diseno de PostgreSQL, MongoDB y Redis

### 8.1 PostgreSQL 16

Diagramas ER logico y fisico en
[`diagramas/datos_postgresql.md`](diagramas/datos_postgresql.md). Resumen:

- 23 tablas de dominio y soporte, mas `schema_migrations` (control de
  `scripts/migrate.py`, que guarda un checksum por migracion y avisa si una ya
  aplicada se edito).
- Normalizacion a 3FN: `devoluciones` no guarda `cliente_id` (se obtiene por
  `venta_detalle -> ventas`), y el costo total es una **vista**, no una columna.
- Triggers: `trg_validar_destino_inventario` (001), `trg_validar_reembolso` y
  `trg_validar_inspeccion_vs_disposicion` (006).
- Eliminacion logica (`eliminado_en`) en usuarios, ventas, devoluciones,
  evidencias y reembolsos (migracion 005).
- `inspecciones_ref.mongo_doc_id` enlaza con MongoDB.
- Todo SQL usa parametros ligados (`psycopg2`); no hay ORM (RNF-11).
  Las unicas interpolaciones (`ventas-catalogos`) usan nombres tomados de una
  lista blanca fija.

Justificacion de PostgreSQL: el expediente exige integridad referencial,
restricciones (`CHECK`, `UNIQUE`) y transacciones con bloqueo de filas
(`SELECT ... FOR UPDATE`) para que dos solicitudes simultaneas no superen la
cantidad comprada.

### 8.2 MongoDB 7

Diseno en [`diagramas/datos_mongodb.md`](diagramas/datos_mongodb.md). Cuatro
colecciones (`inspecciones`, `evidencias_metadatos`, `eventos`,
`resultados_analisis`) creadas por `db/mongo/init.js`, con usuario de aplicacion
`readWrite` limitado a su base.

Justificacion: la inspeccion cambia de forma segun el tipo de producto
(refrigerado o no), los metadatos de un archivo varian por tipo, los eventos
crecen sin esquema fijo y los resultados de analisis son proyecciones derivadas.
Operaciones demostradas en el codigo: insercion, consulta, actualizacion,
agregacion (Pareto), indexacion, filtrado y recuperacion por identificadores
relacionados.

### 8.3 Redis 7

Diseno en [`diagramas/redis_claves.md`](diagramas/redis_claves.md): diez
patrones de clave para sesiones, revocacion, bloqueo por intentos, rate limit,
lock de reembolso y cache de Pareto, con TTL y responsables. Persistencia AOF
(`--appendonly yes`) sobre el volumen `redis_data`.

## 9. Diseno individual de cada microservicio

Todos comparten: Flask 3.0.3, gunicorn con 2 workers, imagen `python:3.11-slim`,
contenedor en el puerto interno 8000, prefijo `/api/v1`, `GET /health` publico
(200 o 503 con el estado de cada dependencia), `GET /docs` (Swagger UI desde
CDN), `GET /openapi.json`, `GET /contratos/<archivo>.xsd`, errores uniformes
con `X-Correlation-ID`, paginacion `?pagina=&por_pagina=` (maximo 100) en los
listados paginados, y JWT validado por `shared/seguridad.py:requiere_jwt`. Las
fichas resumidas previas estan en
[`FICHAS_MICROSERVICIOS.md`](FICHAS_MICROSERVICIOS.md); aqui se amplian con el
formato del apartado 4 del enunciado.

### 9.1 auth — puerto 8001

| Elemento | Detalle |
|---|---|
| Identificacion | `services/auth`, prefijo `/api/v1/auth`, host `:8001` |
| Justificacion | Unico emisor de JWT. Concentra el ciclo de vida de la sesion para que el resto de servicios solo verifique (RF-01, RF-04, RNF-08, RNF-12) |
| Endpoints | `POST /login`, `POST /refresh`, `POST /logout`, `GET /sesion`, `DELETE /usuarios/{id}/sesiones` |
| Entrada | JSON o XML; los XML se validan contra `login.xsd` y `refresh.xsd` |
| Salida | JSON o XML; tokens (`tokens.xsd`), sesion (`sesion.xsd`); errores 400, 401, 403, 404, 415, 423, 429, 503 |
| Seguridad | Hash `werkzeug`; mensaje generico en credenciales invalidas; 5 intentos y bloqueo de 15 min (423); rate limit 10 por minuto en login y 30 en refresh; access de 15 min y refresh de 8 h; revocacion por `jti` y por sesion |
| Persistencia | PostgreSQL (`usuarios`, `roles`, `intentos_acceso`, `bitacora`); Redis (sesion, lista de sesiones, revocados, intentos, bloqueo, limite). No usa MongoDB |
| Integracion | El web lo llama para login, logout y refresh. Los demas servicios no lo llaman: comparten `JWT_SECRET` y consultan las mismas claves Redis |
| Despliegue | `services/auth/Dockerfile`; Compose `auth`, `0.0.0.0:8001`, con `healthcheck`; `requirements.txt` sin `pymongo` |

### 9.2 devoluciones — puerto 8002

| Elemento | Detalle |
|---|---|
| Identificacion | `services/devoluciones`, prefijo `/api/v1/devoluciones`, host `:8002` |
| Justificacion | Inicio del proceso: alta ligada a una linea de venta, correccion, resolucion y cancelacion (RF-06 a RF-11, RF-29, RN-01, RN-02) |
| Endpoints | `POST ""`, `GET ""`, `GET /{id}`, `PUT /{id}`, `PATCH /{id}/resolucion`, `DELETE /{id}` |
| Entrada | JSON o XML; `devolucion_nueva.xsd`, `devolucion_edicion.xsd`, `resolucion.xsd`; filtros `estado`, `q`, paginacion |
| Salida | JSON o XML; el detalle incluye `historial` (bitacora) y `eventos` (MongoDB); `Location` en el 201; errores 400, 401, 403, 404, 409, 429 |
| Seguridad | Alta: Cliente y Analista; correccion y cancelacion: Cliente; resolucion: Analista; el Cliente solo accede a lo suyo (403 + bitacora `acceso_denegado`); rate limit de 20 altas por minuto por usuario |
| Persistencia | PostgreSQL (expediente, `notificaciones`, `bitacora`) con `FOR UPDATE`; MongoDB (`eventos`, indice `idx_devolucion_fecha`); Redis (verificacion JWT y limite) |
| Integracion | Es la unica que publica eventos en MongoDB. Al resolver inserta una notificacion para el cliente |
| Despliegue | `services/devoluciones/Dockerfile`; Compose `devoluciones`, `0.0.0.0:8002`, con `healthcheck`; depende de PostgreSQL, Redis y MongoDB sanos |

### 9.3 logistica — puerto 8003

| Elemento | Detalle |
|---|---|
| Identificacion | `services/logistica`, prefijo `/api/v1/logistica`, host `:8003` |
| Justificacion | Recoleccion y recepcion (RF-12, RF-13, RF-15, RN-08) |
| Endpoints | `POST /recolecciones`, `GET /recolecciones`, `PATCH /recolecciones/{id}/asignacion`, `PATCH /recolecciones/{id}/estado`, `POST /recepciones` |
| Entrada | JSON o XML; `recoleccion.xsd`, `asignacion.xsd`, `estado_recoleccion.xsd`, `recepcion.xsd`; fecha `AAAA-MM-DD` no pasada; booleano estricto |
| Salida | JSON o XML; errores 400, 401, 403, 404, 409 (`transicion_invalida`, `recoleccion_duplicada`, `recepcion_duplicada`, `estado_no_permite`) |
| Seguridad | Coordinador programa, asigna y avanza; Encargado del Centro recibe; ambos consultan |
| Persistencia | PostgreSQL (`recolecciones`, `recepciones`, `devoluciones`, `rutas`, `transportistas`); Redis solo para JWT. Sin MongoDB |
| Integracion | Requiere devolucion `autorizada` para programar y recoleccion `completada` para recibir; cambia `devoluciones.estado` a `en_recoleccion` y `recibida` |
| Despliegue | `services/logistica/Dockerfile`; Compose `logistica`, `0.0.0.0:8003`, **sin** `healthcheck` en Compose (el endpoint `/health` si existe) |

Maquina de estados de la recoleccion: `programada` -> `asignada` ->
`en_transito` -> `completada`; desde `asignada` y `en_transito` tambien a
`fallida`.

### 9.4 inspecciones — puerto 8004

| Elemento | Detalle |
|---|---|
| Identificacion | `services/inspecciones`, prefijo `/api/v1/inspecciones`, host `:8004` |
| Justificacion | Inspeccion con cadena de frio, destino del producto e inventario recuperable (RF-16 a RF-19, RN-05 a RN-07) |
| Endpoints | `POST ""`, `GET /{devolucion_id}`, `PATCH /{devolucion_id}`, `POST /{devolucion_id}/disposicion`, `POST /inventario/{disposicion_id}/etiqueta` |
| Entrada | JSON o XML; `inspeccion.xsd`, `inspeccion_actualizacion.xsd`, `disposicion.xsd`; temperatura y minutos obligatorios si es refrigerado |
| Salida | JSON o XML; el alta devuelve la referencia de PostgreSQL y el `detalle` de MongoDB; errores 400, 401, 403, 404, 409 (`inspeccion_duplicada`, `sin_inspeccion`, `no_apto_inventario`, `disposicion_duplicada`) |
| Seguridad | Inspector registra y corrige; Analista decide el destino; Encargado del Centro etiqueta; Inspector, Analista y Encargado consultan |
| Persistencia | MongoDB (`inspecciones`, detalle); PostgreSQL (`inspecciones_ref`, `disposiciones`, `inventario_recuperado`); Redis solo para JWT |
| Integracion | `evaluar_aptitud` marca no apto con danos, caducidad vencida, cadena de frio rota o mas de 30 minutos fuera de refrigeracion; el trigger de la base repite la regla para el destino `inventario`. Si falla el INSERT en PostgreSQL se borra el documento de Mongo |
| Despliegue | `services/inspecciones/Dockerfile`; Compose `inspecciones`, `0.0.0.0:8004`, sin `healthcheck` en Compose; depende de MongoDB sano |

### 9.5 reembolsos-costos — puerto 8005

| Elemento | Detalle |
|---|---|
| Identificacion | `services/reembolsos_costos` (servicio `reembolsos-costos`), prefijo `/api/v1/reembolsos-costos`, host `:8005` |
| Justificacion | Un solo reembolso por devolucion y costo por etapa (RF-20, RF-21, RF-27, RN-03, RN-04) |
| Endpoints | `POST /reembolsos`, `GET /reembolsos`, `POST /costos`, `GET /costos/{devolucion_id}` |
| Entrada | JSON o XML; `reembolso.xsd`, `costo.xsd`; monto decimal finito y no negativo; metodo `transferencia`, `tarjeta`, `efectivo` o `vale` |
| Salida | JSON o XML; errores 400, 401, 403, 404, 409 (`reembolso_en_proceso`, `reembolso_duplicado`, `monto_excedido`, `estado_no_permite`) |
| Seguridad | Solo el Encargado de Reembolsos resuelve; los costos se limitan por rol a su etapa (`ETAPAS_POR_ROL`) |
| Persistencia | PostgreSQL (`reembolsos`, `costos`, `notificaciones`); Redis (JWT y lock `lock:reembolso:<id>`, 30 s, liberado con compare-and-delete en Lua). Sin MongoDB |
| Integracion | Cierra la devolucion si estaba `resuelta`; notifica al cliente; el trigger `fn_validar_reembolso` repite las reglas |
| Despliegue | `services/reembolsos_costos/Dockerfile`; Compose `reembolsos-costos`, `0.0.0.0:8005`, sin `healthcheck` en Compose |

### 9.6 ventas-catalogos — puerto 8006

| Elemento | Detalle |
|---|---|
| Identificacion | `services/ventas_catalogos`, prefijos `/api/v1/ventas` y `/api/v1/catalogos`, host `:8006` |
| Justificacion | Fuente de ventas y de siete catalogos (proveedores, productos, lotes, tiendas, rutas, transportistas, motivos); RF-05, RF-06 |
| Endpoints | `GET /ventas`, `GET /ventas/{id}`; `GET /catalogos`, `GET/POST /catalogos/{nombre}`, `GET/PUT/DELETE /catalogos/{nombre}/{id}`, `PATCH /catalogos/{nombre}/{id}/estado` |
| Entrada | JSON o XML en escritura; `catalogo.xsd`, `estado.xsd`; campos y tipos por lista blanca (`CATALOGOS`) |
| Salida | JSON o XML; las lineas de venta incluyen `ya_devuelto` y `disponible`; errores 400, 401, 403, 404, 409 (`referencia_inactiva`) |
| Seguridad | Lectura autenticada; Cliente solo ve sus ventas y el catalogo `motivos` activo; escritura solo Administrador; `DELETE` desactiva (no borra) |
| Persistencia | PostgreSQL; Redis solo para JWT. Sin MongoDB |
| Integracion | El web consulta ventas por aqui; la linea de venta que muestra es la que despues usa `devoluciones` |
| Despliegue | `services/ventas_catalogos/Dockerfile`; Compose `ventas-catalogos`, `0.0.0.0:8006`, con `healthcheck` |

### 9.7 evidencias — puerto 8007

| Elemento | Detalle |
|---|---|
| Identificacion | `services/evidencias`, prefijo `/api/v1/evidencias`, host `:8007` |
| Justificacion | Fotos, documentos y comentarios del caso sin publicar archivos como contenido estatico (RF-09, RNF-15, RN-14) |
| Endpoints | `POST ""`, `GET ""?devolucion_id=`, `GET /{id}`, `GET /{id}/enlace`, `GET /{id}/archivo`, `DELETE /{id}` |
| Entrada | `multipart/form-data` con `archivo` (JPG, PNG o PDF reales, maximo 10 MB) o JSON/XML (`comentario.xsd`) solo para comentarios |
| Salida | JSON o XML; descarga con `Content-Disposition: attachment`; errores 400, 401, 403, 404, 409, 413, 415 |
| Seguridad | Tipo real por bytes iniciales; nombre interno aleatorio; archivo en volumen privado con permisos `0600`; propiedad y asignacion (Cliente solo durante `solicitada` o `en_revision`; Inspector solo de su inspeccion); enlace HMAC-SHA256 de 15 min o JWT en la descarga; retiro logico |
| Persistencia | PostgreSQL (`evidencias`, referencia oficial); MongoDB (`evidencias_metadatos`); volumen `evidencias_data` en `/srv/evidencias_privadas`; Redis solo para JWT |
| Integracion | Una falla en cualquier paso borra el archivo y el documento de Mongo y hace rollback |
| Despliegue | `services/evidencias/Dockerfile`; Compose `evidencias`, `0.0.0.0:8007`, con `healthcheck` que ademas comprueba escritura en el almacen |

### 9.8 analisis-auditoria — puerto 8008

| Elemento | Detalle |
|---|---|
| Identificacion | `services/analisis_auditoria`, prefijos `/api/v1/analisis` y `/api/v1/auditoria`, host `:8008` |
| Justificacion | Causa raiz como apoyo (RN-09): Pareto, clasificacion de motivo, senales de fraude, eventos y consulta de bitacora (RF-22 a RF-26, RF-30) |
| Endpoints | `POST /analisis/sincronizar`, `GET /analisis/pareto`, `GET /analisis/resumen`, `GET /analisis/eventos`, `POST /analisis/clasificar-motivo`, `GET /analisis/alertas-fraude`, `GET /auditoria` |
| Entrada | `dimension` (`motivo`, `producto`, `lote`, `proveedor`, `tienda`, `ruta`, `transportista`, `estado`), `medida` (`frecuencia`, `cantidad`, `costo`), `desde`/`hasta`; `clasificacion.xsd` |
| Salida | JSON o XML; el Pareto incluye porcentaje, acumulado, `cache` (`hit` o `miss`) y una nota de interpretacion; errores 400, 401, 403, 409 (`analisis_sin_datos`) |
| Seguridad | Administrador y Analista; el Cliente solo puede pedir la sugerencia de motivo |
| Persistencia | Lee PostgreSQL y no modifica el negocio; MongoDB (`resultados_analisis`, `eventos`); Redis (cache 600 s y version de datos) |
| Integracion | Debe ejecutarse `sincronizar` antes del primer Pareto; las alertas de fraude exigen revision humana y no bloquean nada |
| Despliegue | `services/analisis_auditoria/Dockerfile`; Compose `analisis-auditoria`, `0.0.0.0:8008`, con `healthcheck` |

### 9.9 Justificacion de la separacion de responsabilidades

| Servicio | Por que es un servicio aparte |
|---|---|
| auth | Una sola fuente de identidad y revocacion; si cambia la politica de sesiones solo cambia este servicio |
| devoluciones | Es el expediente y su maquina de estados inicial; tiene las reglas de propiedad mas estrictas |
| logistica | Actores distintos (Coordinador, Encargado del Centro) y un ciclo propio (recoleccion) |
| inspecciones | Es el unico con datos semiestructurados dominantes y las reglas RN-05 a RN-07 |
| reembolsos-costos | Aislar el dinero: concurrencia con lock, monto maximo y unicidad se pueden endurecer sin tocar el resto |
| ventas-catalogos | Datos maestros de lectura intensiva, escritos solo por Administrador |
| evidencias | Manejo de archivos (tamano, tipo, enlaces) con riesgos propios; no mezclar bytes con la logica de negocio |
| analisis-auditoria | Es de solo lectura sobre el negocio y su carga (agregaciones, cache) puede escalar aparte |

Limite de la separacion: todos escriben en la misma base PostgreSQL y, por eso,
no son independientes en datos; la independencia es de despliegue, de codigo y
de responsabilidad (apartado 19).

## 10. Contratos JSON, XML y XSD

**Negociacion** (`shared/respuestas.py`). La respuesta usa JSON salvo que
`Accept` pida `application/xml` o `text/xml`. El cuerpo se acepta como
`application/json` o `application/xml`; otro tipo devuelve `415
formato_no_soportado`.

**Regla de conversion a XML.** Un diccionario es un elemento con hijos; una
lista es un elemento cuyos hijos se llaman `item`; `null` es un elemento vacio;
los booleanos son `true`/`false`; la declaracion es UTF-8.

**Formato de error comun** (JSON; en XML la raiz es `error`, validada por
`shared/contratos/error.xsd`):

```json
{"error": {"codigo": 404, "tipo": "no_encontrado", "mensaje": "...",
           "detalles": null, "correlation_id": "..."}}
```

Nunca contiene trazas ni datos internos (RNF-16); la traza va al log del
contenedor. Los `tipo` usados en el codigo incluyen `validacion`,
`no_autenticado`, `token_expirado`, `token_invalido`, `token_revocado`,
`sesion_inactiva`, `sin_permiso`, `no_encontrado`, `credenciales_invalidas`,
`cuenta_bloqueada` (423), `demasiadas_peticiones` (429), `json_invalido`,
`xml_invalido`, `xml_no_cumple_xsd`, `formato_no_soportado` (415),
`archivo_grande` (413), `seguridad_no_disponible` (503) y `error_interno` (500).

**Paginacion.** `?pagina=1&por_pagina=20` (maximo 100). Respuesta:

```json
{"datos": [], "paginacion": {"pagina": 1, "por_pagina": 20, "total": 0, "paginas": 0}}
```

`GET /logistica/recolecciones` y `GET /reembolsos-costos/reembolsos` devuelven
`{"datos": [...]}` sin bloque de paginacion (este ultimo con tope de 100 filas).

**Versionamiento.** Prefijo `/api/v1` en todos los servicios; `GET /health`
devuelve `"version": "v1"`.

**Validacion XML.** `leer_cuerpo(xsd=...)` valida el XML recibido contra el XSD
del endpoint (`shared/xsd.py`) con un parser que no resuelve entidades ni
accede a la red, y responde `400 xml_no_cumple_xsd` con linea y problema. Los
esquemas usan `xs:all` (los campos pueden llegar en cualquier orden), no usan
espacio de nombres y estan en UTF-8. Se publican en
`GET /contratos/<archivo>.xsd`.

### Los 22 XSD

| Servicio | Esquemas |
|---|---|
| auth | `login`, `refresh`, `sesion`, `tokens` |
| devoluciones | `devolucion_nueva`, `devolucion_edicion`, `devolucion_creada`, `resolucion` |
| logistica | `recoleccion`, `asignacion`, `estado_recoleccion`, `recepcion` |
| inspecciones | `inspeccion`, `inspeccion_actualizacion`, `disposicion` |
| reembolsos-costos | `reembolso`, `costo` |
| ventas-catalogos | `catalogo`, `estado` |
| evidencias | `comentario` |
| analisis-auditoria | `clasificacion` |
| comun (`shared/contratos`) | `error` |

Total: 21 + 1 = 22. La auditoria del 21 de octubre registra que los 22 compilan
con `lxml`.

> **EVIDENCIA PENDIENTE [EV-09]:** ejecucion real de un request y un response
> XML por cada servicio con body, y de un `400 xml_no_cumple_xsd`, en la VM.
> <!-- EVIDENCIA PENDIENTE: EV-09 XML real por servicio y error de XSD -->

**Brechas de contrato detectadas.** Los `openapi.yaml` de `logistica`,
`inspecciones`, `reembolsos-costos`, `ventas-catalogos` y `evidencias` no
incluyen ejemplos (`example`) de JSON ni XML, que el enunciado pide mostrar en
Swagger; `auth`, `devoluciones` y `analisis-auditoria` si los traen.
