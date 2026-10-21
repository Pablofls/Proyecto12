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
> depende de la sesion de notificaciones y reportes (RF-28, RF-29) ya se
> integro en `main` (Pull Request 5) y se refleja en el texto. El orden sigue el listado de 20
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
| Migraciones SQL | 13 | `db/migrations/` |
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
| RF (funcionales) | 32 | 29 | 1: RF-19 | 2: RF-02, RF-14 |
| RNF (no funcionales) | 30 | 21 | 5: RNF-13, RNF-14, RNF-15, RNF-21, RNF-28 | 4: RNF-17, RNF-20, RNF-24, RNF-29 |
| RN (reglas de negocio) | 15 | 14 | 1: RN-14 | 0 |

RF-28 (exportacion CSV) y RF-29 (campanita y bandeja por rol) entraron con la sesion 01 y estan implementados; UC-24 y UC-25 tambien.

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

---

## 11. Seguridad, JWT y control de acceso

Flujo completo con secuencias en
[`diagramas/secuencia_login_jwt.md`](diagramas/secuencia_login_jwt.md).

### 11.1 Tokens

| Aspecto | Implementacion | Archivo |
|---|---|---|
| Algoritmo y emisor | HS256, `iss = devoluciones-auth` | `shared/seguridad.py` |
| Claims | `iss`, `sub`, `rol`, `nombre`, `sid`, `jti`, `typ`, `iat`, `exp` (todos exigidos al decodificar, salvo `rol` y `nombre`) | `services/auth/app.py:_token` |
| Access token | 15 min (`JWT_MINUTOS_ACCESO`), `typ = access` | `services/auth/app.py` |
| Refresh token | 8 h (`JWT_HORAS_REFRESH`), `typ = refresh`; un access no sirve como refresh ni al reves | `shared/seguridad.py:decodificar` |
| Secreto | `JWT_SECRET` del `.env`, minimo 32 caracteres; el servicio **no arranca** si falta o es corto | `shared/seguridad.py:secreto` |
| Sesion | `sesion_api:<sid>` en Redis durante 8 h; un token solo vale mientras su sesion exista | `services/auth/app.py:_abrir_sesion` |
| Revocacion | `jwt_revocado:<jti>` con el tiempo restante del token (logout) y borrado de sesiones (logout y revocacion global del Administrador) | `services/auth/app.py` |
| Verificacion | firma, emisor, vigencia, tipo, revocacion, sesion y rol, en ese orden | `shared/seguridad.py:requiere_jwt` |
| Redis caido | `503 seguridad_no_disponible` (falla cerrada) | `shared/seguridad.py:comprobar_en_redis` |

### 11.2 Control de acceso en dos niveles

1. **Por rol**: `requiere_jwt(*roles)` en cada endpoint; un rol no permitido
   recibe `403 sin_permiso` con `rol` y `roles_permitidos`.
2. **Por recurso**: `devoluciones._exigir_visible`, `evidencias.contexto`,
   `ventas.detalle_venta` y `ventas.permiso_lectura`. Un cliente que conoce el
   identificador de otro cliente recibe 403 y queda `acceso_denegado` en la
   bitacora.

### 11.3 Requisitos de seguridad del enunciado y su estado real

| Requisito (`docs/enunciado/Requisitos.md`) | Estado | Evidencia en el codigo |
|---|---|---|
| Contrasenas con hash seguro | Implementado | `werkzeug.security` en `auth` y `usuarios` |
| JWT de acceso de corta duracion | Implementado | 15 min |
| Token de renovacion | Implementado | `POST /auth/refresh` |
| Revocacion mediante Redis | Implementado | `jwt_revocado:*`, `sesion_api:*` |
| Control de acceso por roles | Implementado | `requiere_jwt` en los 8 servicios |
| Autorizacion por recurso | Implementado | ver 11.2 |
| Separacion de tenants | No aplica en el alcance (RNF-17 pendiente) | sistema de una sola organizacion |
| Proteccion contra inyeccion SQL | Implementado | parametros ligados; listas blancas para nombres de tabla |
| Validacion de JSON y XML | Implementado | validacion por endpoint y XSD |
| Proteccion contra XXE | Implementado en el parser, **sin prueba dedicada** | `shared/xsd.py` (`resolve_entities=False`, `no_network=True`, `load_dtd=False`) |
| Limitacion de peticiones | **Parcial** | `limitar` solo en `auth` y `devoluciones` |
| Registro de intentos fallidos | Implementado | `intentos_acceso` |
| Bloqueo temporal | Implementado | 5 intentos, 15 min, Redis + PostgreSQL |
| Cifrado de comunicaciones | **No implementado**: todo corre en HTTP | pendiente de TLS (apartado 19) |
| Secretos fuera del codigo | Implementado | `.env` fuera de git, `.env.example` versionado |
| URLs firmadas para objetos privados | **Parcial**: HMAC de 15 min sobre volumen local, sin GCS | `services/evidencias` |
| Bitacoras de auditoria | Implementado | `registrar_bitacora`, `GET /auditoria` |
| Ocultamiento de datos sensibles | Implementado | errores genericos, `/health` sin detalle, sin trazas al cliente |
| Politicas de retencion | **Parcial**: eliminacion logica sin politica de purga definida | migracion 005 |
| Eliminacion logica | Implementado | `eliminado_en` |

### 11.4 Limitaciones de seguridad conocidas

- El secreto HS256 es **compartido** por los ocho servicios y el web puede
  conocerlo solo a traves del `.env`; comprometer un servicio permitiria
  falsificar tokens. Un esquema asimetrico (RS256) lo evitaria.
- El enlace firmado de evidencias reutiliza `JWT_SECRET` como clave HMAC.
- Los puertos 8001-8008 se publican en `0.0.0.0`; el acceso real depende de las
  reglas de firewall de GCP.
- El rate limit del web y de seis servicios no existe; en `auth` el sujeto es la
  IP de origen.

## 12. Documentacion de endpoints

Codigos comunes a todo endpoint protegido: `401` (`no_autenticado`,
`token_expirado`, `token_invalido`, `token_revocado`, `sesion_inactiva`), `403`
(`sin_permiso`), `503` (`seguridad_no_disponible`). A todo endpoint con cuerpo:
`400` (`validacion`, `json_invalido`, `xml_invalido`, `xml_no_cumple_xsd`) y
`415`. Se omiten en las tablas salvo cuando son el codigo de negocio relevante.
Todos los servicios exponen ademas `GET /health` (200 o 503, publico),
`GET /docs`, `GET /openapi.json` y `GET /contratos/<archivo>.xsd`.

Tablas verificadas contra los decoradores de cada `app.py`. "Todos" significa
cualquier rol autenticado.

### auth (`/api/v1/auth`)

| Metodo | Ruta | Rol | Codigos de negocio |
|---|---|---|---|
| POST | `/login` | publico | 200, 400, 401 `credenciales_invalidas`, 423 `cuenta_bloqueada`, 429 |
| POST | `/refresh` | publico (refresh token en el cuerpo) | 200, 400, 401, 429 |
| POST | `/logout` | Todos | 200, 401 |
| GET | `/sesion` | Todos | 200, 401 |
| DELETE | `/usuarios/{id}/sesiones` | Administrador | 200, 404 |

### devoluciones (`/api/v1/devoluciones`)

| Metodo | Ruta | Rol | Codigos de negocio |
|---|---|---|---|
| POST | `` | Cliente, Analista | 201, 400, 403, 404, 409 `cantidad_excedida`/`sin_disponible`, 429 |
| GET | `` (filtros `estado`, `q`; paginado) | Todos (el Cliente solo ve lo suyo) | 200, 400 |
| GET | `/{id}` | Todos (recurso) | 200, 403, 404 |
| PUT | `/{id}` | Cliente | 200, 400, 403, 404, 409 `estado_no_permite` |
| PATCH | `/{id}/resolucion` | Analista | 200, 400, 404, 409 |
| DELETE | `/{id}` | Cliente | 200, 403, 404, 409 |

### logistica (`/api/v1/logistica`)

| Metodo | Ruta | Rol | Codigos de negocio |
|---|---|---|---|
| POST | `/recolecciones` | Coordinador | 201, 400, 404, 409 |
| GET | `/recolecciones` (filtro `estado`) | Coordinador, Encargado del Centro | 200, 400 |
| PATCH | `/recolecciones/{id}/asignacion` | Coordinador | 200, 400, 404, 409 |
| PATCH | `/recolecciones/{id}/estado` | Coordinador | 200, 404, 409 `transicion_invalida` |
| POST | `/recepciones` | Encargado del Centro | 201, 400, 404, 409 |

### inspecciones (`/api/v1/inspecciones`)

| Metodo | Ruta | Rol | Codigos de negocio |
|---|---|---|---|
| POST | `` | Inspector | 201, 400, 404, 409 `inspeccion_duplicada`/`estado_no_permite` |
| GET | `/{devolucion_id}` | Inspector, Analista, Encargado del Centro | 200, 404 |
| PATCH | `/{devolucion_id}` | Inspector | 200, 400, 404 |
| POST | `/{devolucion_id}/disposicion` | Analista | 201, 400, 404, 409 `sin_inspeccion`/`no_apto_inventario`/`disposicion_duplicada` |
| POST | `/inventario/{disposicion_id}/etiqueta` | Encargado del Centro | 201, 404, 409 `destino_no_etiquetable` |

### reembolsos-costos (`/api/v1/reembolsos-costos`)

| Metodo | Ruta | Rol | Codigos de negocio |
|---|---|---|---|
| POST | `/reembolsos` | Encargado de Reembolsos | 201, 400, 404, 409 `reembolso_en_proceso`/`reembolso_duplicado`/`monto_excedido`/`estado_no_permite` |
| GET | `/reembolsos` | Encargado de Reembolsos, Analista | 200 |
| POST | `/costos` | Coordinador, Encargado del Centro, Inspector, Analista, Encargado de Reembolsos (cada uno solo su etapa) | 201, 400, 403, 404 |
| GET | `/costos/{devolucion_id}` | Encargado de Reembolsos, Analista | 200, 404 |

### ventas-catalogos (`/api/v1`)

| Metodo | Ruta | Rol | Codigos de negocio |
|---|---|---|---|
| GET | `/ventas` (filtro `q`; paginado) | Todos (el Cliente solo las suyas) | 200, 400 |
| GET | `/ventas/{id}` | Todos (recurso) | 200, 403, 404 |
| GET | `/catalogos` | Administrador, Analista | 200 |
| GET | `/catalogos/{nombre}` (paginado, `solo_activos`) | Todos (el Cliente solo `motivos`) | 200, 403, 404 |
| GET | `/catalogos/{nombre}/{id}` | Todos (el Cliente solo `motivos`) | 200, 403, 404 |
| POST | `/catalogos/{nombre}` | Administrador | 201, 400, 404, 409 `referencia_inactiva` |
| PUT | `/catalogos/{nombre}/{id}` | Administrador | 200, 400, 404, 409 |
| PATCH | `/catalogos/{nombre}/{id}/estado` | Administrador | 200, 400, 404 |
| DELETE | `/catalogos/{nombre}/{id}` | Administrador | 200 (desactiva), 404 |

### evidencias (`/api/v1/evidencias`)

| Metodo | Ruta | Rol | Codigos de negocio |
|---|---|---|---|
| POST | `` (multipart o comentario JSON/XML) | Cliente, Inspector | 201, 400, 403, 404, 409, 413, 415 |
| GET | `` (`devolucion_id` obligatorio; paginado) | Todos (recurso) | 200, 400, 403, 404 |
| GET | `/{id}` | Todos (recurso) | 200, 403, 404 |
| GET | `/{id}/enlace` | Todos (recurso) | 200, 403, 404, 409 `sin_archivo` |
| GET | `/{id}/archivo` | Enlace firmado vigente o JWT con acceso al recurso | 200, 401, 403, 404 |
| DELETE | `/{id}` | Cliente, Inspector (solo evidencia propia) | 200, 403, 404, 409 |

### analisis-auditoria (`/api/v1`)

| Metodo | Ruta | Rol | Codigos de negocio |
|---|---|---|---|
| POST | `/analisis/clasificar-motivo` | Cliente, Administrador, Analista | 200, 400 |
| GET | `/analisis/alertas-fraude` | Administrador, Analista | 200 |
| POST | `/analisis/sincronizar` | Administrador, Analista | 200 |
| GET | `/analisis/pareto` | Administrador, Analista | 200, 400, 409 `analisis_sin_datos` |
| GET | `/analisis/resumen` | Administrador, Analista | 200 |
| GET | `/analisis/eventos` | Administrador, Analista | 200, 400 |
| GET | `/auditoria` (filtros `accion`, `entidad`, `correlation_id`; paginado) | Administrador, Analista | 200, 400 |

Las rutas de este apartado coinciden con los `openapi.yaml` de cada servicio
(revisados ruta por ruta el 21 de octubre de 2026). Las fichas previas decian
que `devoluciones` tenia `GET /{id}/historial`; ese endpoint no existe: el
historial viene dentro de `GET /{id}` y la ficha ya se corrigio.

## 13. Evidencias request/response

> **Estado: estructura lista, evidencia no capturada.** Este repositorio no
> contiene capturas ni respuestas reales de los servicios, y este documento no
> las inventa. Las colecciones de Postman existentes cubren auth y devoluciones
> (`docs/postman/`) y un avance de tres servicios; no hay captura de ninguna
> ejecucion. Cada bloque de abajo indica **que escenarios** se deben ejecutar en
> la VM, tomados de los codigos de error que el propio servicio devuelve.

Para cada escenario se debe anexar (`docs/FICHAS_MICROSERVICIOS.md`): metodo y
URL, objetivo, parametros, headers (incluido `Authorization` y
`X-Correlation-ID`), cuerpo JSON o XML, respuesta completa, codigo HTTP,
captura de Swagger o Postman, el efecto en PostgreSQL, MongoDB o Redis, y al
menos un error controlado.

### 13.1 auth

| Escenario | JSON | XML | Efecto a mostrar |
|---|---|---|---|
| Login correcto | pendiente | pendiente | `sesion_api:*` en Redis, `intentos_acceso` y bitacora `login_api` |
| Credenciales invalidas (401) y bloqueo al quinto intento (423) | pendiente | — | `intentos:*`, `bloqueo:*`, `usuarios.bloqueado_hasta` |
| Rate limit (429 con `Retry-After`) | pendiente | — | `limite:IP:login` con TTL |
| Refresh | pendiente | pendiente | access nuevo, misma sesion |
| Logout y reuso del token (401 `token_revocado`) | pendiente | — | `jwt_revocado:*` |
| Revocacion global por Administrador | pendiente | — | sesiones borradas |

> **EVIDENCIA PENDIENTE [EV-10]:** request/response, capturas de Swagger
> (`:8001/docs`) y de Redis/PostgreSQL para los escenarios de auth.
> <!-- EVIDENCIA PENDIENTE: EV-10 auth -->

### 13.2 devoluciones

| Escenario | JSON | XML | Efecto a mostrar |
|---|---|---|---|
| Alta (201) y folio `DEV-AAAA-NNNN` | pendiente | pendiente | fila en `devoluciones`, evento en `eventos` |
| Cantidad excedida (409) y compra ajena (403) | pendiente | — | bitacora `acceso_denegado` |
| Listado con filtro y paginacion | pendiente | pendiente | — |
| Detalle con `historial` y `eventos` | pendiente | — | consulta cruzada PostgreSQL-MongoDB |
| Correccion (PUT) y cancelacion logica (DELETE) | pendiente | pendiente | `eliminado_en` |
| Resolucion: autorizar, rechazar sin justificacion (400), pedir informacion | pendiente | pendiente | `notificaciones`, `fecha_cierre` si rechaza |
| XML que no cumple el XSD (400 `xml_no_cumple_xsd`) | — | pendiente | — |

> **EVIDENCIA PENDIENTE [EV-11]:** request/response, Swagger (`:8002/docs`) y
> efectos en PostgreSQL y MongoDB. <!-- EVIDENCIA PENDIENTE: EV-11 devoluciones -->

### 13.3 logistica

| Escenario | JSON | XML | Efecto a mostrar |
|---|---|---|---|
| Programar sobre devolucion autorizada (201) y sobre no autorizada (409) | pendiente | pendiente | estado `en_recoleccion` |
| Fecha pasada o con formato invalido (400) | pendiente | — | sin fila en PostgreSQL |
| Asignar ruta y transportista; avanzar de estado; transicion invalida (409) | pendiente | pendiente | `recolecciones.estado` |
| Confirmar recepcion y recepcion duplicada (409) | pendiente | pendiente | estado `recibida` |

> **EVIDENCIA PENDIENTE [EV-12]:** request/response y Swagger (`:8003/docs`).
> <!-- EVIDENCIA PENDIENTE: EV-12 logistica -->

### 13.4 inspecciones

| Escenario | JSON | XML | Efecto a mostrar |
|---|---|---|---|
| Inspeccion de producto refrigerado, apta (201) | pendiente | pendiente | documento en `inspecciones` y `mongo_doc_id` en `inspecciones_ref` |
| Refrigerado sin temperatura o minutos (400) | pendiente | — | — |
| Mas de 30 min fuera de refrigeracion: `apto_para_inventario = false` | pendiente | — | documento y fila |
| Disposicion `inventario` sobre producto no apto (409) | pendiente | — | sin fila en `disposiciones` |
| Disposicion valida y etiqueta `REC-...` | pendiente | pendiente | `disposiciones`, `inventario_recuperado` |
| PATCH del detalle | pendiente | pendiente | `update_one` en Mongo |

> **EVIDENCIA PENDIENTE [EV-13]:** request/response, Swagger (`:8004/docs`),
> documento Mongo y fila PostgreSQL enlazados. <!-- EVIDENCIA PENDIENTE: EV-13 inspecciones -->

### 13.5 reembolsos-costos

| Escenario | JSON | XML | Efecto a mostrar |
|---|---|---|---|
| Reembolso aprobado (201) y cierre de la devolucion | pendiente | pendiente | `reembolsos`, `costos`, estado `cerrada` |
| Segundo intento (409 `reembolso_duplicado`) y lock | pendiente | — | `lock:reembolso:*` mientras se procesa |
| Monto mayor al valor devuelto (409 `monto_excedido`) | pendiente | — | — |
| Monto negativo o NaN (400) | pendiente | — | — |
| Costo por etapa y por rol equivocado (403) | pendiente | pendiente | `costos`, `vista_costo_devolucion` |

> **EVIDENCIA PENDIENTE [EV-14]:** request/response, Swagger (`:8005/docs`) y
> `redis-cli` con el lock. <!-- EVIDENCIA PENDIENTE: EV-14 reembolsos-costos -->

### 13.6 ventas-catalogos

| Escenario | JSON | XML | Efecto a mostrar |
|---|---|---|---|
| Venta propia con `disponible` por linea; venta ajena (403) | pendiente | — | — |
| Listado de catalogos con paginacion y busqueda | pendiente | pendiente | — |
| Alta con campo no permitido (400) y con referencia inactiva (409) | pendiente | pendiente | — |
| Cliente leyendo un catalogo distinto de `motivos` (403) | pendiente | — | — |
| Cambio de estado y desactivacion | pendiente | pendiente | `activo` |

> **EVIDENCIA PENDIENTE [EV-15]:** request/response y Swagger (`:8006/docs`).
> <!-- EVIDENCIA PENDIENTE: EV-15 ventas-catalogos -->

### 13.7 evidencias

| Escenario | JSON | XML | Efecto a mostrar |
|---|---|---|---|
| Comentario | pendiente | pendiente | fila en `evidencias` y documento en `evidencias_metadatos` |
| Fotografia JPG o PNG (multipart) | pendiente | — | archivo con nombre aleatorio en el volumen privado |
| Archivo `.exe` renombrado (415) y mayor a 10 MB (413) | pendiente | — | sin archivo ni fila |
| Enlace firmado, descarga con enlace vigente y con enlace vencido | pendiente | — | — |
| Cliente ajeno (403) y retiro logico | pendiente | — | `eliminado_en` |

> **EVIDENCIA PENDIENTE [EV-16]:** request/response, Swagger (`:8007/docs`),
> `ls` del volumen y los tres efectos (archivo, PostgreSQL, MongoDB).
> <!-- EVIDENCIA PENDIENTE: EV-16 evidencias -->

### 13.8 analisis-auditoria

| Escenario | JSON | XML | Efecto a mostrar |
|---|---|---|---|
| Pareto antes de sincronizar (409 `analisis_sin_datos`) | pendiente | — | — |
| Sincronizar | pendiente | pendiente | `snapshot_devolucion` y `sincronizacion` en Mongo, `analisis:version` |
| Pareto: primera llamada `miss`, segunda `hit` | pendiente | pendiente | `cache:causas:*` con TTL de 600 s y documento `pareto` |
| Sugerencia de motivo | pendiente | pendiente | `requiere_confirmacion = true` |
| Alertas de fraude, eventos por `correlation_id`, auditoria | pendiente | pendiente | — |

> **EVIDENCIA PENDIENTE [EV-17]:** request/response, Swagger (`:8008/docs`) y
> la agregacion en Mongo. <!-- EVIDENCIA PENDIENTE: EV-17 analisis-auditoria -->

### 13.9 Indice de evidencias pendientes

| ID | Que debe capturarse | Se llena en |
|---|---|---|
| EV-01 | `docker compose ps` con los 12 contenedores | `diagramas/despliegue.md`, apartado 15 |
| EV-02 | Firewall de GCP y consola de la VM | `diagramas/despliegue.md`, apartado 15 |
| EV-03 | Login real, `sesion_api` con TTL y `jwt_revocado` tras el logout | `diagramas/secuencia_login_jwt.md` |
| EV-04 | Flujo E2E completo con capturas | `diagramas/secuencia_proceso_completo.md`, apartado 17 |
| EV-05 | Mismo `correlation_id` en dos servicios desde una accion del web | `diagramas/comunicacion_web_servicios.md` |
| EV-06 | Esquema real de PostgreSQL y migraciones aplicadas | `diagramas/datos_postgresql.md` |
| EV-07 | Colecciones, indices y documentos de MongoDB (incluye `getIndexes()` de `inspecciones`) | `diagramas/datos_mongodb.md` |
| EV-08 | Claves de Redis con TTL | `diagramas/redis_claves.md` |
| EV-09 | XML real por servicio y un `xml_no_cumple_xsd` | apartado 10 |
| EV-10 a EV-17 | Request/response, Swagger y efecto en BD de cada servicio | apartados 13.1 a 13.8 |
| EV-20 | Resultado de las pruebas unitarias dentro de los contenedores | apartado 16 |
| EV-21 | Pruebas de integracion `INTEGRACION=1` | apartado 16 |
| EV-22 | Caida de PostgreSQL, MongoDB y Redis; servicio no disponible | apartado 16 |
| EV-23 | Concurrencia (doble reembolso, doble alta) y archivo mayor a 10 MB | apartado 16 |
| EV-24 | Prueba de XXE contra un endpoint con XML | apartado 16 |
| EV-25 | Build y arranque de Compose con todos los servicios sanos | apartado 15 |
| EV-26 | Panel `/integracion/servicios` con 8 de 8 disponibles | apartado 14 |
| EV-27 | Capturas del web: login, panel de causas con Highcharts, bitacora | apartado 14 |
| EV-28 | Suite E2E y su resultado | apartado 17 |

## 14. Integracion del web con los servicios

Detalle en
[`INTEGRACION_WEB_MICROSERVICIOS.md`](INTEGRACION_WEB_MICROSERVICIOS.md) y
[`CAMBIOS_INTEGRACION_MICROSERVICIOS.md`](CAMBIOS_INTEGRACION_MICROSERVICIOS.md);
secuencia en
[`diagramas/comunicacion_web_servicios.md`](diagramas/comunicacion_web_servicios.md).

- **Cliente comun** `apps/web/app/api_client.py`: JSON, `Authorization: Bearer`,
  `X-Correlation-ID`, timeout de 5 s, un reintento tras renovar el token, y
  conversion de fallos de red en `503 servicio_no_disponible`.
- **Sesion**: los JWT viven en la sesion de Flask-Session respaldada por Redis
  (`devoluciones:sesion:<id>`), con cookie `HttpOnly` y `SameSite=Lax`; nunca en
  `localStorage`.
- **Operaciones conectadas por API**: login y logout; ventas; alta y resolucion
  de devoluciones; comentarios de evidencia; programar, asignar, avanzar y
  recibir en logistica; inspeccion, disposicion y etiqueta; costos y
  reembolso; sincronizacion y Pareto.
- **Lecturas compuestas**: el expediente y los paneles conservan consultas
  relacionales directas a PostgreSQL porque cruzan varios dominios en una
  plantilla.
- **Contingencia**: `USE_MICROSERVICES=false` regresa las rutas a la logica de
  monolito. No hay fallback automatico: si un servicio falla en modo
  distribuido el web muestra el error y no repite la escritura en la base.
- **Monitoreo**: `/integracion/servicios` (solo Administrador) consulta los ocho
  `/health` con timeout de 2 s y muestra disponibilidad, latencia y
  dependencias; el web tiene su propio `/health`.
- **Formato**: el web usa JSON. El XML queda para clientes de escritorio, fuera
  del alcance de esta entrega.

Estado reportado por el equipo (sin captura en el repositorio): el 21 de octubre
de 2026 se recorrio desde formularios web el caso `DEV-2026-0033` hasta el
estado `cerrada`, y los nueve `/health` respondieron 200
(`docs/INTEGRACION_WEB_MICROSERVICIOS.md`, `docs/BITACORA.md`).

> **EVIDENCIA PENDIENTE [EV-26]:** captura del panel `/integracion/servicios`
> con 8 de 8 servicios disponibles. <!-- EVIDENCIA PENDIENTE: EV-26 panel de servicios 8/8 -->

> **EVIDENCIA PENDIENTE [EV-27]:** capturas del web: inicio de sesion con la
> insignia "API distribuida", panel de causas con Highcharts y bitacora.
> <!-- EVIDENCIA PENDIENTE: EV-27 capturas del web -->

- **Notificaciones y reportes (sesion 01)**: campanita y bandeja por rol (`apps/web/app/notificaciones.py`, RF-29) y exportacion CSV de listados y panel (`apps/web/app/exportacion.py`, RF-28). Detalle en `docs/TRAZABILIDAD.md`.

## 15. Docker

### 15.1 Contenedores

Doce servicios en `docker-compose.yml` (diagrama en
[`diagramas/despliegue.md`](diagramas/despliegue.md)):

| Contenedor | Imagen / build | Dependencias (`depends_on` sano) |
|---|---|---|
| `devoluciones_postgres` | `postgres:16-alpine`, volumen `postgres_data` | — |
| `devoluciones_redis` | `redis:7-alpine --appendonly yes`, volumen `redis_data` | — |
| `devoluciones_mongo` | `mongo:7`, volumen `mongo_data`, `./db/mongo` como init | — |
| `devoluciones_app` (web) | `apps/web/Dockerfile`, 3 workers de gunicorn | postgres, redis |
| `devoluciones_auth`, `_logistica`, `_reembolsos_costos`, `_ventas_catalogos` | `services/<servicio>/Dockerfile`, 2 workers | postgres, redis |
| `devoluciones_devoluciones`, `_inspecciones`, `_analisis_auditoria` | idem | postgres, redis, mongo |
| `devoluciones_evidencias` | idem, volumen `evidencias_data` | postgres, redis, mongo |

El contexto de build de cada imagen es la raiz del repositorio para poder copiar
`shared/`. Todos usan `restart: unless-stopped`; healthchecks de Compose en
postgres, redis, mongo, auth, devoluciones, ventas-catalogos, evidencias y
analisis-auditoria.

### 15.2 Variables de entorno

Se copian de `.env.example` a `.env` **en la VM**; el `.env` nunca se versiona.

| Grupo | Variables |
|---|---|
| Aplicacion | `FLASK_SECRET_KEY`, `FLASK_ENV`, `APP_PORT`, `USE_MICROSERVICES`, `MICROSERVICE_TIMEOUT` |
| PostgreSQL | `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` |
| Redis | `REDIS_HOST`, `REDIS_PORT` |
| MongoDB | `MONGO_ROOT_USER`, `MONGO_ROOT_PASSWORD` (solo para crear la base), `MONGO_HOST`, `MONGO_PORT`, `MONGO_DB`, `MONGO_APP_USER`, `MONGO_APP_PASSWORD` |
| JWT | `JWT_SECRET` (minimo 32 caracteres, igual en todos), `JWT_MINUTOS_ACCESO`, `JWT_HORAS_REFRESH`, `LOGIN_MAX_POR_MINUTO` |
| Acceso | `MAX_INTENTOS_FALLIDOS`, `MINUTOS_BLOQUEO` |
| Datos de demostracion | `PASSWORD_DEMO` |
| Direcciones de servicios (web) | `AUTH_SERVICE_URL`, `DEVOLUCIONES_SERVICE_URL`, `LOGISTICA_SERVICE_URL`, `INSPECCIONES_SERVICE_URL`, `REEMBOLSOS_SERVICE_URL`, `VENTAS_SERVICE_URL`, `EVIDENCIAS_SERVICE_URL`, `ANALISIS_SERVICE_URL` |
| Opcionales | `DEVOLUCIONES_MAX_POR_MINUTO` (default 20), `EVIDENCIAS_DIR` (lo fija Compose), `GCS_BUCKET` (sin uso hoy) |

### 15.3 Levantar, detener y reconstruir (en la VM)

| Tarea | Comando |
|---|---|
| Actualizar el codigo | `git pull origin main` |
| Preparar el entorno | `cp .env.example .env` y completar los valores |
| Construir y levantar todo | `docker compose up -d --build` |
| Estado | `docker compose ps` |
| Migraciones | `docker compose exec app python scripts/migrate.py` (estado: `--estado`) |
| Catalogos y datos de demostracion | `docker compose exec -T postgres psql -U devoluciones_app -d devoluciones < db/seeds/001_catalogos.sql` y `docker compose exec app python scripts/seed_demo.py` |
| Salud de un servicio | `curl -s localhost:8001/health` (puertos 8001 a 8008; web en 8000) |
| Reconstruir un servicio | `docker compose up -d --build auth` |
| Aplicar cambios del `.env` | `docker compose up -d <servicio>` (`restart` no relee el `.env`) |
| Logs | `docker compose logs --tail=100 <servicio>` |
| Detener sin borrar datos | `docker compose stop` o `docker compose down` |
| Borrar tambien los datos | `docker compose down -v` (destruye los cuatro volumenes) |
| Validar Compose sin secretos | `APP_ENV_FILE=.env.example docker compose --env-file .env.example config` |

Procedimiento completo y guion de demostracion: [`SETUP.md`](SETUP.md).

Aviso: `db/mongo/init.js` solo se ejecuta con el volumen `mongo_data` vacio; si
se cambia hay que aplicarlo a mano o recrear el volumen.

> **EVIDENCIA PENDIENTE [EV-25]:** salida del build y de `docker compose ps`
> con los servicios sanos, y `curl` a los nueve `/health`.
> <!-- EVIDENCIA PENDIENTE: EV-25 build, ps y health de los nueve endpoints -->

## 16. Pruebas unitarias y de integracion

### 16.1 Estado real

Conteo de funciones `test_*` por archivo (contado en el codigo; las pruebas
parametrizadas se expanden al ejecutarse). Las pruebas unitarias usan dobles
(por ejemplo Redis en memoria) y no requieren servidores locales; las de
integracion usan las bases reales de la VM.

| Archivo | Funciones | Cubre |
|---|---:|---|
| `services/auth/tests/test_auth.py` | 27 | login JSON/XML, 401 generico, bloqueo, rate limit, refresh, logout y revocacion, token falso y expirado, 403, Redis caido, XSD de respuestas |
| `services/devoluciones/tests/test_reglas.py` | 11 | validaciones de entrada y de resolucion |
| `services/devoluciones/tests/test_api.py` | 13 | 401, token revocado, 403 por rol, validacion, XML contra XSD, paginacion, rate limit |
| `services/devoluciones/tests/test_integracion.py` | 4 | flujo real con auth, PostgreSQL, MongoDB y Redis; **solo en la VM** |
| `services/logistica/tests/test_api.py` | 5 | 401, 403, XML invalido, fecha invalida, booleano estricto |
| `services/inspecciones/tests/test_reglas.py` | 5 | `evaluar_aptitud` (danos, cadena de frio, 30 min) y booleano ambiguo |
| `services/reembolsos_costos/tests/test_api.py` | 6 | 401, rol sin permiso, monto negativo y no finito, XML invalido, etapas por rol |
| `services/ventas_catalogos/tests/test_reglas.py` | 5 | catalogos iguales al monolito, producto y lote validos e invalidos |
| `services/evidencias/tests/test_seguridad_archivos.py` | 3 | tipo por contenido, enlace firmado, rechazo de `.exe` |
| `services/analisis_auditoria/tests/test_pareto.py` | 4 | Pareto, division por cero, clasificador explicable |
| `apps/web/app/tests/test_api_client.py` | 3 | JWT solo en sesion, 503 por red, renovacion con un reintento |
| `apps/web/app/tests/test_microservicios.py` | 3 | salud del servicio, timeout y JSON invalido degradan sin romper |
| **Total** | **89** | |

`docs/AUDITORIA_SEGUNDO_PARCIAL.md` reporta 84 pruebas aprobadas y 4 de
integracion omitidas en una corrida local; esa cifra no pudo reproducirse al
redactar este documento (no hay dependencias instaladas en la maquina de
redaccion y las bases viven solo en la VM). Los resultados reales deben
tomarse de la VM.

> **EVIDENCIA PENDIENTE [EV-20]:** salida de `pytest` de cada servicio y del
> web dentro de los contenedores (por ejemplo `docker compose run --rm --no-deps
> auth python -m pytest -v`). <!-- EVIDENCIA PENDIENTE: EV-20 pytest por servicio -->

> **EVIDENCIA PENDIENTE [EV-21]:** `docker compose run --rm -e INTEGRACION=1
> devoluciones python -m pytest -v tests/test_integracion.py` (comando del
> encabezado del archivo). <!-- EVIDENCIA PENDIENTE: EV-21 pruebas de integracion -->

### 16.2 Cobertura frente a las pruebas que pide el enunciado

| Prueba obligatoria | Estado |
|---|---|
| Unitarias | Existen (tabla anterior); resultado en VM pendiente |
| De integracion | Parcial: 4 de `devoluciones`; no hay suite de los 8 servicios |
| Contratos JSON | Parcial: validacion de campos; no hay suite dedicada |
| Esquemas XML | Parcial: auth valida sus respuestas contra XSD; devoluciones prueba XML invalido |
| Autenticacion, autorizacion, expiracion y revocacion | Cubiertas en `auth` y 401/403 en varios servicios |
| Recuperacion ante fallos | Solo Redis caido en `auth` (con dobles) y microservicio no disponible en el web |
| Caida de PostgreSQL y de MongoDB | **No hay prueba** |
| Concurrencia | **No hay prueba** (existen `FOR UPDATE` y el lock de reembolso como mecanismos) |
| Archivos grandes | Parcial: el 413 no tiene prueba |
| Grandes volumenes | **No hay prueba** |
| Seguridad basica y XXE | Parcial: firma falsa, enlace firmado, rate limit; **sin prueba de XXE** |
| Carga con Locust y perfiles (RNF-29) | **No existe**; corresponde al tercer parcial |

> **EVIDENCIA PENDIENTE [EV-22]:** detener el contenedor de PostgreSQL, el de
> MongoDB y el de Redis y mostrar la respuesta de `/health` y de un endpoint de
> negocio en cada caso; apagar un microservicio y mostrar el panel del web.
> <!-- EVIDENCIA PENDIENTE: EV-22 caida de dependencias -->

> **EVIDENCIA PENDIENTE [EV-23]:** dos solicitudes simultaneas de reembolso y
> de alta sobre la misma linea de venta, y una subida mayor a 10 MB (413).
> <!-- EVIDENCIA PENDIENTE: EV-23 concurrencia y archivo grande -->

> **EVIDENCIA PENDIENTE [EV-24]:** un XML con entidad externa contra un endpoint
> de un servicio, para demostrar que no se resuelve.
> <!-- EVIDENCIA PENDIENTE: EV-24 prueba de XXE -->

## 17. Resultados, problemas identificados y soluciones

### 17.1 Resultados reportados por el equipo

Fuentes: `docs/BITACORA.md`, `docs/AUDITORIA_SEGUNDO_PARCIAL.md`,
`docs/INTEGRACION_WEB_MICROSERVICIOS.md`. Ninguno tiene captura en el
repositorio.

| Resultado | Fuente |
|---|---|
| Compose construido en la VM; nueve `/health` en 200 y 8 de 8 servicios en el panel (21 de octubre) | `BITACORA.md`, `AUDITORIA_SEGUNDO_PARCIAL.md` |
| Caso `DEV-2026-0033` recorrido desde el web hasta `cerrada`; reembolso de 32.24; lock liberado (`TTL=-2`); etiqueta `REC-2026-0033`; Pareto con cache | `INTEGRACION_WEB_MICROSERVICIOS.md` |
| Con 12 IPs falsas en `X-Forwarded-For`, la peticion 11 recibe 429 | `BITACORA.md` |
| Ocho servicios compilan; ocho OpenAPI cargan; 22 XSD compilan; `docker compose config` resuelve 12 servicios y 4 volumenes | `AUDITORIA_SEGUNDO_PARCIAL.md` |

> **EVIDENCIA PENDIENTE [EV-04 / EV-28]:** capturas del caso E2E y una suite E2E
> automatizada de los ocho servicios (auth -> venta -> devolucion ->
> logistica -> inspeccion -> evidencia -> reembolso -> Pareto).
> <!-- EVIDENCIA PENDIENTE: EV-28 suite E2E -->

### 17.2 Problemas encontrados y como se resolvieron

| Problema | Solucion | Referencia |
|---|---|---|
| PostgreSQL nativo de la VM ocupaba el 5432 | Mapeo del contenedor a 55432 y 56379/57017 para Redis/Mongo, solo en `127.0.0.1` | `BITACORA.md` |
| SELinux impedia leer el codigo montado | Etiqueta `:z` en el volumen | `BITACORA.md` |
| Una migracion fallaba al reclasificar datos | Quitar el CHECK antes del `UPDATE` | `60d7c90` |
| El seed no funcionaba en base limpia | Usar la etapa `transporte` | `04dfc46` |
| Rate limit evadible con `X-Forwarded-For` | No leer ese header | `shared/infra.py:ip_origen` |
| Un 500 confirmaba la transaccion | Marca `g.error_interno` y rollback | `shared/respuestas.py` |
| Dos solicitudes podian devolver mas de lo comprado | `SELECT ... FOR UPDATE` en linea y devolucion | `services/devoluciones/app.py` |
| Doble reembolso concurrente | Lock Redis `NX EX 30` + `UNIQUE` + trigger | `services/reembolsos_costos/app.py` |
| Archivo huerfano si fallaba Mongo o PostgreSQL | Compensacion: borrar archivo y metadatos y `rollback` | `services/evidencias/app.py` |

### 17.3 Problemas abiertos detectados al redactar este documento

| # | Hallazgo | Impacto | Accion sugerida |
|---|---|---|---|
| 1 | Posible conflicto de indices en MongoDB: `init.js` crea `idx_devolucion` sobre `inspecciones.devolucion_id` y el servicio pide otro indice unico sobre la misma llave | Podria fallar el alta de inspecciones en una base creada desde cero | Comprobar `getIndexes()` en la VM (EV-07) |
| 2 | Solo `devoluciones` publica eventos en `eventos` | La trazabilidad por `correlation_id` en Mongo no cubre el resto del flujo (la bitacora de PostgreSQL si) | Publicar eventos tambien desde los demas servicios o documentarlo como limite |
| 3 | `limitar` solo en `auth` y `devoluciones` | RNF-13 parcial | Aplicarlo a los demas servicios |
| 4 | `openapi.yaml` de cinco servicios sin ejemplos JSON/XML | El enunciado lo exige en Swagger | Agregar ejemplos |
| 5 | Sin `healthcheck` de Compose en logistica, inspecciones y reembolsos-costos | `docker compose ps` no mostrara su salud | Copiar el bloque de los demas servicios |
| 6 | Todo en HTTP | Credenciales y tokens sin cifrar en la red | TLS en el tercer parcial |
| 7 | Base de datos compartida y `JWT_SECRET` simetrico en todos | Acoplamiento y radio de dano ante una fuga | Documentado como limite (apartados 7 y 11) |
| 8 | `README.md` describia solo el primer parcial | Documentacion desactualizada | Corregido en este mismo trabajo |
| 9 | Las fichas tenian cifras de pruebas y un endpoint que no coinciden con el codigo | Documentacion contradictoria | Corregido en este mismo trabajo |
| 10 | Josue Berdeal no aparece en el historial de git | La rubrica exige evidencia de los cuatro integrantes | Ver apartado 20 |

## 18. Matriz de trazabilidad y cumplimiento

La matriz vigente esta en [`TRAZABILIDAD.md`](TRAZABILIDAD.md): una fila por RF
(32), RNF (30) y RN (15), la lista de casos de uso, y una tabla de ampliacion
del segundo parcial que apunta a archivo y prueba. En este trabajo se
corrigieron contra el codigo RNF-13 (de pendiente a parcial), RNF-15 y RN-14
(de pendiente a parcial por los enlaces firmados HMAC), RNF-28, la cuenta de
XSD, el lugar de los triggers de RN-07 y los casos de uso UC-18 a UC-21 y UC-27.

RF-28, RF-29, UC-24 y UC-25 pasaron a implementados al integrar la sesion 01.

Cumplimiento por rubro, segun `AUDITORIA_SEGUNDO_PARCIAL.md` y lo verificado
aqui:

| Rubro | Estado |
|---|---|
| Microservicios (8) | Implementados; falta evidencia en VM por endpoint |
| Contratos JSON/XML/XSD | 22 XSD y 8 OpenAPI; faltan ejemplos en 5 y evidencia de XML real |
| Web + PostgreSQL + MongoDB + Redis + JWT + Docker | Integrado; falta E2E automatizado y capturas |
| Pruebas | 89 funciones de prueba; faltan caidas, concurrencia, carga y E2E |
| Documentacion | Este documento, 8 diagramas, trazabilidad; faltan las evidencias del apartado 13 |
| Aplicaciones movil y de escritorio | Fuera del alcance acordado (ver apartado 3) |

## 19. Conclusiones tecnicas y trabajo pendiente

### 19.1 Conclusiones

1. La separacion en ocho servicios con una libreria `shared/` comun permitio
   que seguridad, formato de errores, paginacion y negociacion JSON/XML se
   comportaran igual en todos, con pocas lineas por servicio.
2. Llevar las reglas criticas a triggers de PostgreSQL y a un lock de Redis
   hizo que RN-03, RN-04, RN-06 y RN-07 se cumplan aunque un servicio falle.
3. Se usan las tres bases con una razon cada una (transaccion, estructura
   variable y datos efimeros) y los enlaces entre ellas son por identificador,
   no por llave foranea.
4. La decision de compartir la base de datos simplifico la integracion pero
   limita la independencia de los servicios.
5. Lo mas debil es la **evidencia**, no el codigo: faltan ejecuciones y capturas
   reproducibles en la VM.

### 19.2 Requerimientos no implementados o parciales

La justificacion se limita a lo que el repositorio o el documento del curso
permite afirmar.

| ID | Estado | Justificacion | Que falta |
|---|---|---|---|
| RF-02 | Pendiente | Sin implementar y sin una decision registrada en `BITACORA.md`; no bloquea el proceso principal porque el Administrador gestiona las cuentas (RF-03). Requiere definir un canal de entrega (correo) que el proyecto no tiene | Flujo de recuperacion con token de un solo uso |
| RF-14 | Pendiente | Requiere la aplicacion movil (escaneo de QR o codigo de barras), fuera del alcance acordado | App movil |
| RF-19 | Parcial | El codigo de etiqueta y el inventario existen; la **impresion** requiere la aplicacion de escritorio e impresora | Impresion de etiquetas |
| RN-14 / RNF-15 | Parcial | Hay enlaces firmados de 15 min sobre volumen local; el almacenamiento en Google Cloud Storage esta planeado para el tercer parcial (`Entregables.md`) | Bucket de GCS y URLs firmadas del proveedor |
| RNF-13 | Parcial | Solo `auth` y `devoluciones` limitan peticiones | Aplicarlo al resto y al web |
| RNF-14 | Parcial | Secretos fuera del codigo; falta cifrado de comunicaciones | HTTPS con proxy TLS |
| RNF-17 | Pendiente | El sistema opera para una sola organizacion; no hay separacion de tenants | Solo si el alcance lo requiere |
| RNF-20 | Pendiente | Hay una instancia por servicio; no se probo ni se configuro escalado horizontal | Balanceador y pruebas |
| RNF-21 | Parcial | El bloqueo sobrevive a Redis y `/health` degrada, pero falta probar la caida de las demas dependencias | EV-22 |
| RNF-24 | Pendiente | Respaldo y recuperacion pertenecen al tercer parcial (`Entregables.md`, "Recuperacion ante fallos") | Respaldos de volumenes y prueba de restauracion |
| RNF-28 | Parcial | Faltan E2E, caidas y carga | Suite E2E |
| RNF-29 | Pendiente | Las pruebas de carga con Locust son del tercer parcial | Perfiles de Locust |

Otros pendientes del entregable del curso: aplicaciones Android y de
escritorio (fuera de alcance acordado), ejemplos en Swagger de cinco servicios,
healthchecks de Compose en tres, eventos de MongoDB en los demas servicios,
pruebas de XXE y de caidas de dependencias, y la verificacion en la VM de la migracion 013 y de la campanita.

## 20. Anexo: que cambio en este parcial y reparto

### 20.1 Funcionalidades corregidas, ampliadas y nuevas

| Tipo | Elemento |
|---|---|
| Corregido | Modelo de datos (`venta_detalle`, triggers, folio, roles, costos, destino `donacion`, `fecha_cierre`); seguridad de la contrasena de demostracion; puertos y SELinux; ver apartado 5 |
| Ampliado | Web: panel de causas con cruce producto-lote-proveedor-ruta-tienda, Pareto, tendencia mensual y KPIs; captura de costos por etapa; panel `/integracion/servicios`; modo distribuido con `api_client.py` |
| Nuevo | `shared/` (JWT, JSON/XML, XSD, paginacion, MongoDB, Swagger); los ocho microservicios; MongoDB en Compose con `init.js`; 22 XSD; 8 `openapi.yaml`; claves Redis de sesion, revocacion, limites, lock y cache; colecciones de Postman; 8 diagramas Mermaid y este documento |

### 20.2 Reparto de responsabilidades (segun el historial de git)

Obtenido con `git shortlog -sn --all` y `git log --all` sobre el repositorio
(47 commits en `main` al 21 de octubre, incluidos 2 merges de Pull Request). Es evidencia de autoria en
git, no una valoracion del esfuerzo.

| Integrante | Identidad en git | Commits | Periodo | Trabajo principal |
|---|---|---:|---|---|
| Pablo Flores | `Pablofls` | 31 | 2 sep al 21 oct | Estructura del repositorio y Compose; migraciones 001 a 013 (la 013 con la sesion de notificaciones); monolito del primer parcial; panel de causas, KPIs y costos; seguridad del seed; reglas del proyecto; integracion final y reestructura del monorepo (PR #3 y #4) |
| David Munoz | `Thedavidzavala6` (8) y `thedavidzavala6` (1) | 9 | 6 sep, 18 oct | MongoDB en Compose; `shared/`; microservicio `auth`; microservicio `devoluciones`; bitacora de decisiones del segundo parcial; correcciones del seed |
| Roberto Sandoval | `BobbySandoval122` | 7 | 21 oct | `logistica`, `inspecciones`, `reembolsos-costos`, `ventas-catalogos`, `evidencias`, `analisis-auditoria`; panel de salud; consumo de los servicios desde el web; etapas de costo por rol; documentacion de la integracion |
| Josue Berdeal | — | **0** | — | **Sin commits en el historial** |

> **ACCION REQUERIDA antes de la entrega:** `CLAUDE.md` indica que el parcial
> exige evidencia de participacion de los cuatro integrantes y que el historial
> de git es esa evidencia. El historial actual no contiene commits atribuibles a
> Josue Berdeal (la cuenta `thedavidzavala6` con otro correo parece una segunda
> identidad de David y no se le asigno a Josue). Si Josue trabajo en una rama sin
> subir o con otra identidad de git, debe subirse a `josue/...` y entrar por
> Pull Request; este documento no le atribuye trabajo que git no muestra.
> <!-- COMPLETAR: confirmar con Josue Berdeal su aportacion y su evidencia en git -->

Documentos de apoyo por integrante: `docs/MICROSERVICIOS_AVANCE_ROBERTO.md`
(servicios de Roberto), `docs/CAMBIOS_INTEGRACION_MICROSERVICIOS.md`
(integracion del web) y `docs/BITACORA.md` (decisiones).
