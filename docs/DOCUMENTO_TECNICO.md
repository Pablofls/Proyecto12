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
| Version del documento | 21 de octubre de 2026 (redaccion sobre `2a52f76`); evidencia real de la VM incorporada el 22 de octubre sobre `main` en `83e130b` |

> **Como leer este documento.** Describe lo que **esta implementado en el
> repositorio**, verificado contra `services/*/app.py`, `shared/`,
> `docker-compose.yml`, `db/migrations/` y `apps/web/`. Lo que no se puede
> demostrar desde el codigo (ejecuciones en la VM, capturas, resultados de
> pruebas) queda marcado como **EVIDENCIA PENDIENTE** con un identificador
> `EV-nn`; el estado de cada una esta en el apartado 13.9 y lo que sigue
> pendiente, con quien y como obtenerlo, en el apartado 19.3. Las evidencias que
> ya existen en el repositorio (`docs/evidencias/`, `docs/pruebas/`) se resumen y
> enlazan en el texto; las transcripciones largas quedan en esos archivos. Lo que
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
| Requerimientos funcionales | 32: 29 implementados, 1 parcial, 2 pendientes | `docs/TRAZABILIDAD.md` |
| Requerimientos no funcionales | 30: 20 implementados, 6 parciales, 4 pendientes | `docs/TRAZABILIDAD.md` |

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
| RNF (no funcionales) | 30 | 20 | 6: RNF-13, RNF-14, RNF-15, RNF-21, RNF-22, RNF-28 | 4: RNF-17, RNF-20, RNF-24, RNF-29 |
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

**Evidencia real del XML (VM, 22 de octubre).** Los casos de cada servicio con
cuerpo o respuesta en XML, de las ocho colecciones de Newman (peticion y
respuesta completas en cada enlace):

| Servicio | Exito en XML | Error de contrato o de esquema |
|---|---|---|
| auth | [004](evidencias/ejecuciones/auth.md#004_auth_post_login_200_xml), [011](evidencias/ejecuciones/auth.md#011_auth_get_sesion_200_xml) | [008](evidencias/ejecuciones/auth.md#008_auth_post_login_400_xml), [009](evidencias/ejecuciones/auth.md#009_auth_post_login_400_xml) (XML mal formado o fuera del XSD, 400) |
| devoluciones | [029](evidencias/ejecuciones/devoluciones.md#029_devoluciones_post_raiz_201_xml), [036](evidencias/ejecuciones/devoluciones.md#036_devoluciones_get_raiz_200_xml), [048](evidencias/ejecuciones/devoluciones.md#048_devoluciones_patch_id_resolucion_200_xml) | [031](evidencias/ejecuciones/devoluciones.md#031_devoluciones_post_raiz_400_xml) (`xml_no_cumple_xsd`) |
| logistica | [064](evidencias/ejecuciones/logistica.md#064_logistica_get_recolecciones_200_xml), [072](evidencias/ejecuciones/logistica.md#072_logistica_patch_recolecciones_id_asignacion_200_xml), [077](evidencias/ejecuciones/logistica.md#077_logistica_patch_recolecciones_id_estado_200_xml) | [060](evidencias/ejecuciones/logistica.md#060_logistica_post_recolecciones_400_xml) |
| inspecciones | [095](evidencias/ejecuciones/inspecciones.md#095_inspecciones_get_id_200_xml), [102](evidencias/ejecuciones/inspecciones.md#102_inspecciones_patch_id_200_xml), [106](evidencias/ejecuciones/inspecciones.md#106_inspecciones_post_id_disposicion_201_xml) | [089](evidencias/ejecuciones/inspecciones.md#089_inspecciones_post_raiz_400_xml) |
| reembolsos-costos | [121](evidencias/ejecuciones/reembolsos_costos.md#121_reembolsos_costos_post_costos_201_xml), [131](evidencias/ejecuciones/reembolsos_costos.md#131_reembolsos_costos_get_reembolsos_200_xml), [135](evidencias/ejecuciones/reembolsos_costos.md#135_reembolsos_costos_get_costos_id_200_xml) | [118](evidencias/ejecuciones/reembolsos_costos.md#118_reembolsos_costos_post_costos_400_xml); 409 en XML: [129](evidencias/ejecuciones/reembolsos_costos.md#129_reembolsos_costos_post_reembolsos_409_xml) |
| ventas-catalogos | [140](evidencias/ejecuciones/ventas_catalogos.md#140_ventas_catalogos_get_raiz_200_xml), [145](evidencias/ejecuciones/ventas_catalogos.md#145_ventas_catalogos_get_id_200_xml), [151](evidencias/ejecuciones/ventas_catalogos.md#151_ventas_catalogos_get_catalogos_nombre_200_xml), [159](evidencias/ejecuciones/ventas_catalogos.md#159_ventas_catalogos_post_catalogos_nombre_201_xml) | — |
| evidencias | [175](evidencias/ejecuciones/evidencias.md#175_evidencias_post_raiz_201_xml), [190](evidencias/ejecuciones/evidencias.md#190_evidencias_get_raiz_200_xml) | — |
| analisis-auditoria | [211](evidencias/ejecuciones/analisis_auditoria.md#211_analisis_auditoria_post_clasificar_motivo_200_xml), [220](evidencias/ejecuciones/analisis_auditoria.md#220_analisis_auditoria_get_pareto_200_xml), [229](evidencias/ejecuciones/analisis_auditoria.md#229_analisis_auditoria_get_alertas_fraude_200_xml), [232](evidencias/ejecuciones/analisis_auditoria.md#232_analisis_auditoria_get_eventos_200_xml), [237](evidencias/ejecuciones/analisis_auditoria.md#237_analisis_auditoria_get_auditoria_200_xml) | — |

El error `xml_no_cumple_xsd` real, con linea y problema del validador (caso 031):

**031_devoluciones_post_raiz_400_xml** — registrar 400 XML no cumple XSD ([caso completo](evidencias/ejecuciones/devoluciones.md#031_devoluciones_post_raiz_400_xml))

```
POST http://{{vm_host}}:8002/api/v1/devoluciones
Content-Type: application/xml

<devolucion>
  <motivo_id>1</motivo_id>
</devolucion>

--> 400 BAD REQUEST
<?xml version='1.0' encoding='utf-8'?>
<error><codigo>400</codigo><tipo>xml_no_cumple_xsd</tipo><mensaje>El XML no cumple el contrato del endpoint.</mensaje><detalles><item><linea>1</linea><problema>Element 'devolucion': Missing child element(s). Expected is one of ( venta_detalle_id, descripcion_problema, cantidad_devuelta ).</problema></item></detalles><correlation_id>7cc61646aaa342b1</correlation_id></error>
```

La suite E2E lo repite sin Newman: FMT-05 (XML sin `motivo_id`, 400
`xml_no_cumple_xsd`), FMT-06 (XML mal formado, 400 `xml_invalido`) y FMT-07 (XXE,
apartado 16.2) pasan en la VM ([`PRUEBAS.md`](PRUEBAS.md)).

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
| Proteccion contra XXE | Implementado y probado: E2E FMT-07 responde 400 `xml_invalido` sin resolver la entidad (apartado 16.2) | `shared/xsd.py` (`resolve_entities=False`, `no_network=True`, `load_dtd=False`) |
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

> **Estado: evidencia real capturada en la VM el 22 de octubre de 2026.** Se
> ejecutaron las ocho colecciones de Postman con Newman contra la VM: 238 casos
> documentados con su peticion y respuesta reales (JSON, XML, 400, 401, 403, 404,
> 409, 415) y 767 verificaciones, 0 fallidas (suma de los encabezados de
> `evidencias/ejecuciones/*.md`; el resumen propio de Newman, con sus 271
> peticiones, no esta versionado). Los efectos en PostgreSQL, MongoDB, Redis,
> Docker y el volumen privado se capturaron el mismo dia con
> `scripts/evidencias_vm.sh` (`evidencias/bases/*.txt`). Tokens, contrasenas e IP
> de la VM aparecen ocultos desde la fuente y no se reintroducen aqui.
>
> Lo que **no** se capturo queda como `pendiente` en cada tabla y en el apartado
> 13.9; no se rellena con texto inventado.

Fuentes enlazadas desde este apartado:

| Fuente | Contenido |
|---|---|
| [`evidencias/ejecuciones/<servicio>.md`](evidencias/ejecuciones/auth.md) | Una seccion por caso: URL, cuerpo, respuesta completa, codigo y verificaciones de Newman |
| [`evidencias/bases/postgresql.txt`](evidencias/bases/postgresql.txt) | Filas del proceso completo de la devolucion 81 (`DEV-2026-0081`, `cerrada`), bitacora de 17 eventos, notificaciones y migraciones |
| [`evidencias/bases/mongodb.txt`](evidencias/bases/mongodb.txt) | Insercion, consulta, actualizacion, filtro, agregacion, `getIndexes()` y `explain` |
| [`evidencias/bases/redis.txt`](evidencias/bases/redis.txt) | Claves, TTL, cache del Pareto y candado con 409 `reembolso_en_proceso` |
| [`evidencias/bases/docker.txt`](evidencias/bases/docker.txt), [`volumen.txt`](evidencias/bases/volumen.txt) | `docker compose ps`, recursos, volumenes, nueve `/health` y volumen privado |
| [`EVIDENCIAS.md`](EVIDENCIAS.md) | Plantilla del apartado 5 por endpoint, enlazada a cada ejecucion |
| [`pruebas/salida_2026-10-21.txt`](pruebas/salida_2026-10-21.txt) | Salida completa de la suite E2E y de la integracion por servicio (lineas `[E2E]` por peticion) |

Cada servicio tiene su coleccion en `postman/<servicio>.postman_collection.json`
y su Swagger en `:800N/docs`. **No hay capturas de pantalla de Swagger en el
repositorio** (`evidencias/capturas/` esta vacia); queda en 13.9.

Las colecciones de devoluciones, logistica, inspecciones y reembolsos-costos
trabajan sobre la misma devolucion 81 (alta, autorizacion, recoleccion, recepcion,
inspeccion, disposicion, etiqueta, costos, reembolso y cierre), por lo que sus
respuestas se pueden contrastar con las filas de [`postgresql.txt`](evidencias/bases/postgresql.txt).

### 13.1 auth

| Escenario | Casos reales | Efecto verificado |
|---|---|---|
| Login correcto, JSON y XML | [003](evidencias/ejecuciones/auth.md#003_auth_post_login_200), [004](evidencias/ejecuciones/auth.md#004_auth_post_login_200_xml) | `devoluciones:sesion_api:*` con TTL 28132 s de 28800 en [`redis.txt`](evidencias/bases/redis.txt); filas `exitoso` en `intentos_acceso` ([`postgresql.txt`](evidencias/bases/postgresql.txt)) |
| Login invalido: datos incompletos (400), credenciales (401), tipo de contenido (415), XML mal formado o fuera del XSD (400) | [005](evidencias/ejecuciones/auth.md#005_auth_post_login_400), [006](evidencias/ejecuciones/auth.md#006_auth_post_login_401), [007](evidencias/ejecuciones/auth.md#007_auth_post_login_415), [008](evidencias/ejecuciones/auth.md#008_auth_post_login_400_xml), [009](evidencias/ejecuciones/auth.md#009_auth_post_login_400_xml) | El 401 no revela si el correo existe (RNF-16) |
| Sesion actual con token valido y sin token (401) | [010](evidencias/ejecuciones/auth.md#010_auth_get_sesion_200), [011](evidencias/ejecuciones/auth.md#011_auth_get_sesion_200_xml), [012](evidencias/ejecuciones/auth.md#012_auth_get_sesion_401), [013](evidencias/ejecuciones/auth.md#013_auth_get_sesion_401) | — |
| Refresh | [014](evidencias/ejecuciones/auth.md#014_auth_post_refresh_200), [015](evidencias/ejecuciones/auth.md#015_auth_post_refresh_401), [016](evidencias/ejecuciones/auth.md#016_auth_post_refresh_400) | El 401 (`token_invalido`) es un access token usado como refresh |
| Logout y reuso del token (401 `token_revocado`) | [019](evidencias/ejecuciones/auth.md#019_auth_post_logout_200), [020](evidencias/ejecuciones/auth.md#020_auth_get_sesion_401), [021](evidencias/ejecuciones/auth.md#021_auth_post_refresh_401), [023](evidencias/ejecuciones/auth.md#023_auth_get_sesion_401) | La clave `jwt_revocado:<jti>` existe en Redis con TTL de 898 s ([`jwt_revocado.txt`](evidencias/bases/jwt_revocado.txt)): logout 200 y el mismo token 401 `token_revocado` |
| Cierre global de sesiones por Administrador (403, 404, 200) | [017](evidencias/ejecuciones/auth.md#017_auth_delete_usuarios_id_sesiones_403), [018](evidencias/ejecuciones/auth.md#018_auth_delete_usuarios_id_sesiones_404), [022](evidencias/ejecuciones/auth.md#022_auth_delete_usuarios_id_sesiones_200) | `sesiones_cerradas: 1` en la respuesta |
| Rate limit (429 con `demasiadas_peticiones`) | Salida E2E, caso SEG-23: [`salida_2026-10-21.txt`](pruebas/salida_2026-10-21.txt) lineas 301 a 312 | Las dos ultimas peticiones respondieron 429 ("Limite de 10 peticiones en 60 s"). Sin caso en Newman |
| Bloqueo al quinto intento (423) | [`bloqueo_423.txt`](evidencias/bases/bloqueo_423.txt) | Cinco 401 `credenciales_invalidas` y el sexto 423 `cuenta_bloqueada`; Redis `intentos:<correo>`=5 y `bloqueo:<correo>` con TTL 899 s; la cuenta se desbloquea al terminar |

<details>
<summary>Auth: peticion y respuesta copiadas tal cual (tokens y contrasenas ya ocultos en la fuente)</summary>

**003_auth_post_login_200** — login 200 exitoso ([caso completo](evidencias/ejecuciones/auth.md#003_auth_post_login_200))

```
POST http://{{vm_host}}:8001/api/v1/auth/login
Content-Type: application/json

{
  "email": "josue.analista@demo.mx",
  "password": "***"
}

--> 200 OK
{
  "token_type": "Bearer",
  "access_token": "***jwt***",
  "expires_in": 900,
  "refresh_token": "***jwt***",
  "refresh_expires_in": 28800,
  "usuario": {
    "id": 16,
    "nombre": "Josue Berdeal",
    "email": "josue.analista@demo.mx",
    "rol": "Analista de Devoluciones"
  }
}
```

**004_auth_post_login_200_xml** — login 200 XML (admin) ([caso completo](evidencias/ejecuciones/auth.md#004_auth_post_login_200_xml))

```
POST http://{{vm_host}}:8001/api/v1/auth/login
Content-Type: application/xml

<login>
  <email>pablo.admin@demo.mx</email>
  <password>***</password>
</login>

--> 200 OK
<?xml version='1.0' encoding='utf-8'?>
<respuesta><token_type>Bearer</token_type><access_token>***jwt***</access_token><expires_in>900</expires_in><refresh_token>***jwt***</refresh_token><refresh_expires_in>28800</refresh_expires_in><usuario><id>18</id><nombre>Pablo Flores</nombre><email>pablo.admin@demo.mx</email><rol>Administrador</rol></usuario></respuesta>
```

**006_auth_post_login_401** — login 401 credenciales invalidas ([caso completo](evidencias/ejecuciones/auth.md#006_auth_post_login_401))

```
POST http://{{vm_host}}:8001/api/v1/auth/login
Content-Type: application/json

{
  "email": "nadie@demo.mx",
  "password": "***"
}

--> 401 UNAUTHORIZED
{
  "error": {
    "codigo": 401,
    "tipo": "credenciales_invalidas",
    "mensaje": "Correo o contrasena incorrectos.",
    "detalles": null,
    "correlation_id": "0f5be23fde49497a"
  }
}
```

**014_auth_post_refresh_200** — refresh 200 exitoso ([caso completo](evidencias/ejecuciones/auth.md#014_auth_post_refresh_200))

```
POST http://{{vm_host}}:8001/api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "***jwt***"
}

--> 200 OK
{
  "token_type": "Bearer",
  "access_token": "***jwt***",
  "expires_in": 900
}
```

**019_auth_post_logout_200** — logout 200 exitoso ([caso completo](evidencias/ejecuciones/auth.md#019_auth_post_logout_200))

```
POST http://{{vm_host}}:8001/api/v1/auth/logout
Content-Type: application/json

--> 200 OK
{
  "mensaje": "Sesion cerrada. El token ya no es valido."
}
```

**020_auth_get_sesion_401** — sesion 401 token revocado ([caso completo](evidencias/ejecuciones/auth.md#020_auth_get_sesion_401))

```
GET http://{{vm_host}}:8001/api/v1/auth/sesion

--> 401 UNAUTHORIZED
{
  "error": {
    "codigo": 401,
    "tipo": "token_revocado",
    "mensaje": "El token fue revocado. Inicia sesion de nuevo.",
    "detalles": null,
    "correlation_id": "1da89e8b24af4344"
  }
}
```

**022_auth_delete_usuarios_id_sesiones_200** — cerrar sesiones 200 admin ([caso completo](evidencias/ejecuciones/auth.md#022_auth_delete_usuarios_id_sesiones_200))

```
DELETE http://{{vm_host}}:8001/api/v1/auth/usuarios/16/sesiones

--> 200 OK
{
  "usuario_id": 16,
  "sesiones_cerradas": 1
}
```

</details>

### 13.2 devoluciones

| Escenario | Casos reales | Efecto verificado |
|---|---|---|
| Alta 201 con folio `DEV-AAAA-NNNN`, en JSON y XML | [028](evidencias/ejecuciones/devoluciones.md#028_devoluciones_post_raiz_201), [029](evidencias/ejecuciones/devoluciones.md#029_devoluciones_post_raiz_201_xml) | Fila `DEV-2026-0081` en `devoluciones` y `alta_devolucion` en bitacora ([`postgresql.txt`](evidencias/bases/postgresql.txt)); evento `devolucion_registrada` en Mongo ([`mongodb.txt`](evidencias/bases/mongodb.txt)) |
| Cantidad excedida (409), compra ajena (403), linea inexistente (404), datos invalidos (400), XML que no cumple el XSD (400) | [027](evidencias/ejecuciones/devoluciones.md#027_devoluciones_post_raiz_409), [033](evidencias/ejecuciones/devoluciones.md#033_devoluciones_post_raiz_403), [034](evidencias/ejecuciones/devoluciones.md#034_devoluciones_post_raiz_404), [030](evidencias/ejecuciones/devoluciones.md#030_devoluciones_post_raiz_400), [031](evidencias/ejecuciones/devoluciones.md#031_devoluciones_post_raiz_400_xml) | La bitacora de la devolucion 81 trae `acceso_denegado` |
| Listado con paginacion y filtro, JSON y XML; estado invalido (400) | [035](evidencias/ejecuciones/devoluciones.md#035_devoluciones_get_raiz_200), [036](evidencias/ejecuciones/devoluciones.md#036_devoluciones_get_raiz_200_xml), [037](evidencias/ejecuciones/devoluciones.md#037_devoluciones_get_raiz_400) | — |
| Detalle con `historial` y `eventos`; ajeno (403); inexistente (404) | [040](evidencias/ejecuciones/devoluciones.md#040_devoluciones_get_id_200), [050](evidencias/ejecuciones/devoluciones.md#050_devoluciones_get_id_200), [041](evidencias/ejecuciones/devoluciones.md#041_devoluciones_get_id_403), [042](evidencias/ejecuciones/devoluciones.md#042_devoluciones_get_id_404) | Consulta cruzada PostgreSQL-MongoDB en una sola respuesta |
| Correccion (PUT), cancelacion logica (DELETE) y cancelacion de una ya revisada (409) | [046](evidencias/ejecuciones/devoluciones.md#046_devoluciones_put_id_200), [051](evidencias/ejecuciones/devoluciones.md#051_devoluciones_delete_id_200), [047](evidencias/ejecuciones/devoluciones.md#047_devoluciones_delete_id_409), [052](evidencias/ejecuciones/devoluciones.md#052_devoluciones_get_id_404) | `devolucion_cancelada` en Mongo; el 404 posterior confirma el retiro logico |
| Resolucion: pedir informacion, autorizar (JSON y XML), rechazar sin justificacion (400), doble resolucion (409), cliente sin permiso (403) | [045](evidencias/ejecuciones/devoluciones.md#045_devoluciones_patch_id_resolucion_200), [048](evidencias/ejecuciones/devoluciones.md#048_devoluciones_patch_id_resolucion_200_xml), [044](evidencias/ejecuciones/devoluciones.md#044_devoluciones_patch_id_resolucion_400), [049](evidencias/ejecuciones/devoluciones.md#049_devoluciones_patch_id_resolucion_409), [043](evidencias/ejecuciones/devoluciones.md#043_devoluciones_patch_id_resolucion_403) | `notificaciones` de la devolucion 81 (cliente y coordinador) en [`postgresql.txt`](evidencias/bases/postgresql.txt) |
| Sin token (401) | [032](evidencias/ejecuciones/devoluciones.md#032_devoluciones_post_raiz_401), [038](evidencias/ejecuciones/devoluciones.md#038_devoluciones_get_raiz_401), [039](evidencias/ejecuciones/devoluciones.md#039_devoluciones_get_raiz_401) | — |

<details>
<summary>Devoluciones: peticion y respuesta copiadas tal cual (tokens y contrasenas ya ocultos en la fuente)</summary>

**028_devoluciones_post_raiz_201** — registrar 201 exitoso ([caso completo](evidencias/ejecuciones/devoluciones.md#028_devoluciones_post_raiz_201))

```
POST http://{{vm_host}}:8002/api/v1/devoluciones
Content-Type: application/json

{
  "venta_detalle_id": 72,
  "motivo_id": 1,
  "descripcion_problema": "El empaque llego roto y el producto derramado.",
  "cantidad_devuelta": 1
}

--> 201 CREATED
{
  "id": 81,
  "folio_devolucion": "DEV-2026-0081",
  "estado": "solicitada",
  "fecha_solicitud": "2026-10-22T00:37:25.634753+00:00",
  "venta_detalle_id": 72,
  "motivo_id": 1,
  "descripcion_problema": "El empaque llego roto y el producto derramado.",
  "cantidad_devuelta": 1
}
```

**029_devoluciones_post_raiz_201_xml** — registrar 201 XML ([caso completo](evidencias/ejecuciones/devoluciones.md#029_devoluciones_post_raiz_201_xml))

```
POST http://{{vm_host}}:8002/api/v1/devoluciones
Content-Type: application/xml

<devolucion>
  <venta_detalle_id>72</venta_detalle_id>
  <motivo_id>1</motivo_id>
  <descripcion_problema>Caja golpeada, el producto llego aplastado.</descripcion_problema>
</devolucion>

--> 201 CREATED
<?xml version='1.0' encoding='utf-8'?>
<respuesta><id>82</id><folio_devolucion>DEV-2026-0082</folio_devolucion><estado>solicitada</estado><fecha_solicitud>2026-10-22T00:37:25.789330+00:00</fecha_solicitud><venta_detalle_id>72</venta_detalle_id><motivo_id>1</motivo_id><descripcion_problema>Caja golpeada, el producto llego aplastado.</descripcion_problema><cantidad_devuelta>1</cantidad_devuelta></respuesta>
```

**027_devoluciones_post_raiz_409** — registrar 409 cantidad excedida ([caso completo](evidencias/ejecuciones/devoluciones.md#027_devoluciones_post_raiz_409))

```
POST http://{{vm_host}}:8002/api/v1/devoluciones
Content-Type: application/json

{
  "venta_detalle_id": 72,
  "motivo_id": 1,
  "descripcion_problema": "El empaque llego roto y el producto derramado.",
  "cantidad_devuelta": 999
}

--> 409 CONFLICT
{
  "error": {
    "codigo": 409,
    "tipo": "cantidad_excedida",
    "mensaje": "Solo se pueden devolver 3 articulo(s) de esta linea.",
    "detalles": {
      "disponible": 3,
      "solicitada": 999
    },
    "correlation_id": "ef767389cf774f09"
  }
}
```

**033_devoluciones_post_raiz_403** — registrar 403 compra de otro cliente ([caso completo](evidencias/ejecuciones/devoluciones.md#033_devoluciones_post_raiz_403))

```
POST http://{{vm_host}}:8002/api/v1/devoluciones
Content-Type: application/json

{
  "venta_detalle_id": 85,
  "motivo_id": 1,
  "descripcion_problema": "El empaque llego roto y el producto derramado.",
  "cantidad_devuelta": 1
}

--> 403 FORBIDDEN
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "La compra no pertenece a tu cuenta.",
    "detalles": null,
    "correlation_id": "588610a405a8410c"
  }
}
```

**031_devoluciones_post_raiz_400_xml** — registrar 400 XML no cumple XSD ([caso completo](evidencias/ejecuciones/devoluciones.md#031_devoluciones_post_raiz_400_xml))

```
POST http://{{vm_host}}:8002/api/v1/devoluciones
Content-Type: application/xml

<devolucion>
  <motivo_id>1</motivo_id>
</devolucion>

--> 400 BAD REQUEST
<?xml version='1.0' encoding='utf-8'?>
<error><codigo>400</codigo><tipo>xml_no_cumple_xsd</tipo><mensaje>El XML no cumple el contrato del endpoint.</mensaje><detalles><item><linea>1</linea><problema>Element 'devolucion': Missing child element(s). Expected is one of ( venta_detalle_id, descripcion_problema, cantidad_devuelta ).</problema></item></detalles><correlation_id>7cc61646aaa342b1</correlation_id></error>
```

**042_devoluciones_get_id_404** — detalle 404 inexistente ([caso completo](evidencias/ejecuciones/devoluciones.md#042_devoluciones_get_id_404))

```
GET http://{{vm_host}}:8002/api/v1/devoluciones/999999

--> 404 NOT FOUND
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe la devolucion 999999.",
    "detalles": null,
    "correlation_id": "02a7c9202e7244af"
  }
}
```

</details>

### 13.3 logistica

| Escenario | Casos reales | Efecto verificado |
|---|---|---|
| Programar 201; repetir sobre una devolucion que ya no esta autorizada (409 `estado_no_permite`) | [061](evidencias/ejecuciones/logistica.md#061_logistica_post_recolecciones_201), [062](evidencias/ejecuciones/logistica.md#062_logistica_post_recolecciones_409) | Recoleccion 29 en `recolecciones` ([`postgresql.txt`](evidencias/bases/postgresql.txt)) |
| Programar sobre una devolucion **no autorizada** (409) | Sin captura en Newman; lo cubren E2E SEG-18 e INT-LOG-2 ([`PRUEBAS.md`](PRUEBAS.md)) | — |
| Fecha pasada (400), devolucion invalida (400), inexistente (404), rol sin permiso (403), XML que no cumple el XSD (400) | [059](evidencias/ejecuciones/logistica.md#059_logistica_post_recolecciones_400), [057](evidencias/ejecuciones/logistica.md#057_logistica_post_recolecciones_400), [058](evidencias/ejecuciones/logistica.md#058_logistica_post_recolecciones_404), [056](evidencias/ejecuciones/logistica.md#056_logistica_post_recolecciones_403), [060](evidencias/ejecuciones/logistica.md#060_logistica_post_recolecciones_400_xml) | — |
| Asignar ruta y transportista (JSON invalido, XML 200), transicion invalida (409), estado `en_transito` y `completada` (JSON y XML) | [069](evidencias/ejecuciones/logistica.md#069_logistica_patch_recolecciones_id_asignacion_400), [070](evidencias/ejecuciones/logistica.md#070_logistica_patch_recolecciones_id_asignacion_400), [072](evidencias/ejecuciones/logistica.md#072_logistica_patch_recolecciones_id_asignacion_200_xml), [073](evidencias/ejecuciones/logistica.md#073_logistica_patch_recolecciones_id_estado_409), [075](evidencias/ejecuciones/logistica.md#075_logistica_patch_recolecciones_id_estado_200), [076](evidencias/ejecuciones/logistica.md#076_logistica_patch_recolecciones_id_asignacion_409), [077](evidencias/ejecuciones/logistica.md#077_logistica_patch_recolecciones_id_estado_200_xml) | Ruta 4 y transportista 4; `estado_recoleccion` `completada` en la bitacora |
| Recepcion 201, duplicada (409), rol sin permiso (403), cuerpo invalido (400) | [082](evidencias/ejecuciones/logistica.md#082_logistica_post_recepciones_201), [083](evidencias/ejecuciones/logistica.md#083_logistica_post_recepciones_409), [078](evidencias/ejecuciones/logistica.md#078_logistica_post_recepciones_403), [079](evidencias/ejecuciones/logistica.md#079_logistica_post_recepciones_400), [081](evidencias/ejecuciones/logistica.md#081_logistica_post_recepciones_400) | Fila 23 en `recepciones` con `coincide_expediente = t` |

<details>
<summary>Logistica: peticion y respuesta copiadas tal cual (tokens y contrasenas ya ocultos en la fuente)</summary>

**061_logistica_post_recolecciones_201** — programar 201 exitoso ([caso completo](evidencias/ejecuciones/logistica.md#061_logistica_post_recolecciones_201))

```
POST http://{{vm_host}}:8003/api/v1/logistica/recolecciones
Content-Type: application/json

{
  "devolucion_id": 81,
  "fecha_programada": "2026-10-29",
  "lugar": "Domicilio del cliente"
}

--> 201 CREATED
{
  "id": 29,
  "devolucion_id": 81,
  "fecha_programada": "2026-10-29",
  "lugar": "Domicilio del cliente",
  "estado": "programada"
}
```

**077_logistica_patch_recolecciones_id_estado_200_xml** — estado 200 completada XML ([caso completo](evidencias/ejecuciones/logistica.md#077_logistica_patch_recolecciones_id_estado_200_xml))

```
PATCH http://{{vm_host}}:8003/api/v1/logistica/recolecciones/29/estado
Content-Type: application/xml

<estado_recoleccion>
  <estado>completada</estado>
</estado_recoleccion>

--> 200 OK
<?xml version='1.0' encoding='utf-8'?>
<respuesta><id>29</id><estado>completada</estado></respuesta>
```

**059_logistica_post_recolecciones_400** — programar 400 fecha en el pasado ([caso completo](evidencias/ejecuciones/logistica.md#059_logistica_post_recolecciones_400))

```
POST http://{{vm_host}}:8003/api/v1/logistica/recolecciones
Content-Type: application/json

{
  "devolucion_id": 81,
  "fecha_programada": "2020-01-01",
  "lugar": "Domicilio del cliente"
}

--> 400 BAD REQUEST
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "fecha_programada no puede estar en el pasado.",
    "detalles": null,
    "correlation_id": "f96b48cded3544de"
  }
}
```

**062_logistica_post_recolecciones_409** — programar 409 ya programada ([caso completo](evidencias/ejecuciones/logistica.md#062_logistica_post_recolecciones_409))

```
POST http://{{vm_host}}:8003/api/v1/logistica/recolecciones
Content-Type: application/json

{
  "devolucion_id": 81,
  "fecha_programada": "2026-10-29",
  "lugar": "Domicilio del cliente"
}

--> 409 CONFLICT
{
  "error": {
    "codigo": 409,
    "tipo": "estado_no_permite",
    "mensaje": "Solo se programan devoluciones autorizadas.",
    "detalles": {
      "estado_actual": "en_recoleccion"
    },
    "correlation_id": "37b28b8a67214c72"
  }
}
```

**073_logistica_patch_recolecciones_id_estado_409** — estado 409 transicion invalida ([caso completo](evidencias/ejecuciones/logistica.md#073_logistica_patch_recolecciones_id_estado_409))

```
PATCH http://{{vm_host}}:8003/api/v1/logistica/recolecciones/29/estado
Content-Type: application/json

{
  "estado": "completada"
}

--> 409 CONFLICT
{
  "error": {
    "codigo": 409,
    "tipo": "transicion_invalida",
    "mensaje": "No se puede pasar de asignada a completada.",
    "detalles": null,
    "correlation_id": "1f57a087fc844914"
  }
}
```

**056_logistica_post_recolecciones_403** — programar 403 centro sin permiso ([caso completo](evidencias/ejecuciones/logistica.md#056_logistica_post_recolecciones_403))

```
POST http://{{vm_host}}:8003/api/v1/logistica/recolecciones
Content-Type: application/json

{
  "devolucion_id": 81,
  "fecha_programada": "2026-10-29",
  "lugar": "Domicilio del cliente"
}

--> 403 FORBIDDEN
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "Tu rol no tiene permiso para esta operacion.",
    "detalles": {
      "rol": "Encargado del Centro de Devoluciones",
      "roles_permitidos": [
        "Coordinador de Logistica"
      ]
    },
    "correlation_id": "9ad226928f12444e"
  }
}
```

</details>

### 13.4 inspecciones

| Escenario | Casos reales | Efecto verificado |
|---|---|---|
| Inspeccion de producto refrigerado, apta (201) | [092](evidencias/ejecuciones/inspecciones.md#092_inspecciones_post_raiz_201) | `inspecciones_ref` 21 con `mongo_doc_id` `6ad95b4fdc019a2bc7393ae6` ([`postgresql.txt`](evidencias/bases/postgresql.txt)) y el mismo documento en Mongo ([`mongodb.txt`](evidencias/bases/mongodb.txt)) |
| Duplicada (409), booleano ambiguo (400), empaque sin describir (400), devolucion invalida (400), inexistente (404), rol sin permiso (403), XML que no cumple el XSD (400) | [093](evidencias/ejecuciones/inspecciones.md#093_inspecciones_post_raiz_409), [091](evidencias/ejecuciones/inspecciones.md#091_inspecciones_post_raiz_400), [090](evidencias/ejecuciones/inspecciones.md#090_inspecciones_post_raiz_400), [087](evidencias/ejecuciones/inspecciones.md#087_inspecciones_post_raiz_400), [088](evidencias/ejecuciones/inspecciones.md#088_inspecciones_post_raiz_404), [086](evidencias/ejecuciones/inspecciones.md#086_inspecciones_post_raiz_403), [089](evidencias/ejecuciones/inspecciones.md#089_inspecciones_post_raiz_400_xml) | — |
| Refrigerado sin temperatura o minutos (400) y mas de 30 min fuera de refrigeracion (`apto_para_inventario = false`) | Sin captura en Newman; lo cubren la prueba unitaria `evaluar_aptitud`, E2E SEG-20 e INT-INS-2/3 ([`PRUEBAS.md`](PRUEBAS.md)) | — |
| Disposicion valida (XML), duplicada (409), destino invalido (400), rol sin permiso (403) | [106](evidencias/ejecuciones/inspecciones.md#106_inspecciones_post_id_disposicion_201_xml), [107](evidencias/ejecuciones/inspecciones.md#107_inspecciones_post_id_disposicion_409), [104](evidencias/ejecuciones/inspecciones.md#104_inspecciones_post_id_disposicion_400), [103](evidencias/ejecuciones/inspecciones.md#103_inspecciones_post_id_disposicion_403) | Fila 16 en `disposiciones` (destino `inventario`) |
| Disposicion `inventario` sobre producto no apto (409) | Sin captura en Newman; E2E SEG-19 e INT-INS-2 | — |
| Etiqueta `REC-...` | [110](evidencias/ejecuciones/inspecciones.md#110_inspecciones_post_inventario_id_etiqueta_201), [108](evidencias/ejecuciones/inspecciones.md#108_inspecciones_post_inventario_id_etiqueta_403), [109](evidencias/ejecuciones/inspecciones.md#109_inspecciones_post_inventario_id_etiqueta_404) | `inventario_recuperado` 5 con `REC-2026-0081` |
| PATCH del detalle (XML 200, sin cambios 400, rol sin permiso 403) | [102](evidencias/ejecuciones/inspecciones.md#102_inspecciones_patch_id_200_xml), [099](evidencias/ejecuciones/inspecciones.md#099_inspecciones_patch_id_400), [100](evidencias/ejecuciones/inspecciones.md#100_inspecciones_patch_id_403) | `updateOne` y lectura posterior en [`mongodb.txt`](evidencias/bases/mongodb.txt) |
| Detalle JSON y XML | [094](evidencias/ejecuciones/inspecciones.md#094_inspecciones_get_id_200), [095](evidencias/ejecuciones/inspecciones.md#095_inspecciones_get_id_200_xml), [096](evidencias/ejecuciones/inspecciones.md#096_inspecciones_get_id_403), [097](evidencias/ejecuciones/inspecciones.md#097_inspecciones_get_id_404) | — |

<details>
<summary>Inspecciones: peticion y respuesta copiadas tal cual (tokens y contrasenas ya ocultos en la fuente)</summary>

**092_inspecciones_post_raiz_201** — registrar 201 exitoso ([caso completo](evidencias/ejecuciones/inspecciones.md#092_inspecciones_post_raiz_201))

```
POST http://{{vm_host}}:8004/api/v1/inspecciones
Content-Type: application/json

{
  "devolucion_id": 81,
  "estado_empaque": "Empaque intacto, sello cerrado",
  "danos": false,
  "caducidad_vencida": false,
  "cadena_frio_rota": false,
  "minutos_fuera_refrigeracion": 10,
  "temperatura_recepcion": 4.5,
  "observaciones": "Inspeccion de prueba desde Postman"
}

--> 201 CREATED
{
  "id": 21,
  "devolucion_id": 81,
  "resultado_general": "apto",
  "mongo_doc_id": "6ad95b4fdc019a2bc7393ae6",
  "apto_para_inventario": true,
  "fecha_inspeccion": "2026-10-22T00:39:43.019119+00:00",
  "detalle": {
    "devolucion_id": 81,
    "inspector_id": 13,
    "fecha": "2026-10-22T00:39:43.025668+00:00",
    "producto": {
      "clasificacion_temperatura": "refrigerado"
    },
    "condiciones": {
      "estado_empaque": "Empaque intacto, sello cerrado",
      "danos": false,
      "caducidad_vencida": false,
      "cadena_frio_rota": false,
      "minutos_fuera_refrigeracion": 10,
      "temperatura_recepcion": 4.5
    },
    "observaciones": "Inspeccion de prueba desde Postman",
    "resultado": {
      "apto_para_inventario": true,
      "motivos": []
    },
    "id": "6ad95b4fdc019a2bc7393ae6"
  }
}
```

**106_inspecciones_post_id_disposicion_201_xml** — disposicion 201 XML ([caso completo](evidencias/ejecuciones/inspecciones.md#106_inspecciones_post_id_disposicion_201_xml))

```
POST http://{{vm_host}}:8004/api/v1/inspecciones/81/disposicion
Content-Type: application/xml

<disposicion>
  <destino>inventario</destino>
  <justificacion>Producto apto, regresa a inventario.</justificacion>
</disposicion>

--> 201 CREATED
<?xml version='1.0' encoding='utf-8'?>
<respuesta><id>16</id><devolucion_id>81</devolucion_id><analista_id>16</analista_id><destino>inventario</destino><justificacion>Producto apto, regresa a inventario.</justificacion><fecha_decision>2026-10-22T00:39:44.746378+00:00</fecha_decision></respuesta>
```

**093_inspecciones_post_raiz_409** — registrar 409 duplicada ([caso completo](evidencias/ejecuciones/inspecciones.md#093_inspecciones_post_raiz_409))

```
POST http://{{vm_host}}:8004/api/v1/inspecciones
Content-Type: application/json

{
  "devolucion_id": 81,
  "estado_empaque": "Empaque intacto, sello cerrado",
  "danos": false,
  "caducidad_vencida": false,
  "cadena_frio_rota": false,
  "minutos_fuera_refrigeracion": 10,
  "temperatura_recepcion": 4.5,
  "observaciones": "Inspeccion de prueba desde Postman"
}

--> 409 CONFLICT
{
  "error": {
    "codigo": 409,
    "tipo": "inspeccion_duplicada",
    "mensaje": "La devolucion ya tiene inspeccion.",
    "detalles": null,
    "correlation_id": "8e14860c86a744fc"
  }
}
```

**091_inspecciones_post_raiz_400** — registrar 400 booleano invalido ([caso completo](evidencias/ejecuciones/inspecciones.md#091_inspecciones_post_raiz_400))

```
POST http://{{vm_host}}:8004/api/v1/inspecciones
Content-Type: application/json

{
  "devolucion_id": 81,
  "estado_empaque": "Empaque intacto, sello cerrado",
  "danos": "quizas",
  "caducidad_vencida": false,
  "cadena_frio_rota": false,
  "minutos_fuera_refrigeracion": 10,
  "temperatura_recepcion": 4.5,
  "observaciones": "Inspeccion de prueba desde Postman"
}

--> 400 BAD REQUEST
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "danos debe ser booleano.",
    "detalles": null,
    "correlation_id": "36f6c2c883214fa1"
  }
}
```

**107_inspecciones_post_id_disposicion_409** — disposicion 409 duplicada ([caso completo](evidencias/ejecuciones/inspecciones.md#107_inspecciones_post_id_disposicion_409))

```
POST http://{{vm_host}}:8004/api/v1/inspecciones/81/disposicion
Content-Type: application/json

{
  "destino": "reciclaje"
}

--> 409 CONFLICT
{
  "error": {
    "codigo": 409,
    "tipo": "disposicion_duplicada",
    "mensaje": "Ya existe una disposicion.",
    "detalles": null,
    "correlation_id": "4697c0604dd94792"
  }
}
```

**110_inspecciones_post_inventario_id_etiqueta_201** — etiqueta 201 exitoso ([caso completo](evidencias/ejecuciones/inspecciones.md#110_inspecciones_post_inventario_id_etiqueta_201))

```
POST http://{{vm_host}}:8004/api/v1/inspecciones/inventario/16/etiqueta
Content-Type: application/json

--> 201 CREATED
{
  "id": 5,
  "disposicion_id": 16,
  "producto_id": 7,
  "etiqueta_codigo": "REC-2026-0081",
  "fecha_ingreso": "2026-10-22T00:39:45.250034+00:00",
  "estado": "disponible"
}
```

</details>

### 13.5 reembolsos-costos

| Escenario | Casos reales | Efecto verificado |
|---|---|---|
| Reembolso aprobado (201) y cierre de la devolucion | [128](evidencias/ejecuciones/reembolsos_costos.md#128_reembolsos_costos_post_reembolsos_201) | Fila 11 en `reembolsos`; `DEV-2026-0081` en estado `cerrada` con `fecha_cierre` ([`postgresql.txt`](evidencias/bases/postgresql.txt)) |
| Segundo intento (409 `reembolso_duplicado`, en XML) | [129](evidencias/ejecuciones/reembolsos_costos.md#129_reembolsos_costos_post_reembolsos_409_xml) | Sigue una sola fila |
| Lock en Redis (409 `reembolso_en_proceso`) | [`redis.txt`](evidencias/bases/redis.txt): `SET ... NX EX 30` devuelve OK, `TTL = 30`, el POST responde 409 y `DEL` libera el candado | Candado puesto a mano sobre `devolucion_id` 999999 |
| Monto mayor al valor devuelto (409 `monto_excedido`, con `detalles.maximo`) | [127](evidencias/ejecuciones/reembolsos_costos.md#127_reembolsos_costos_post_reembolsos_409) | — |
| Monto negativo (400), estado, metodo e id invalidos (400), inexistente (404), XML invalido (400) | [115](evidencias/ejecuciones/reembolsos_costos.md#115_reembolsos_costos_post_costos_400), [123](evidencias/ejecuciones/reembolsos_costos.md#123_reembolsos_costos_post_reembolsos_400), [124](evidencias/ejecuciones/reembolsos_costos.md#124_reembolsos_costos_post_reembolsos_400), [125](evidencias/ejecuciones/reembolsos_costos.md#125_reembolsos_costos_post_reembolsos_400), [126](evidencias/ejecuciones/reembolsos_costos.md#126_reembolsos_costos_post_reembolsos_404), [118](evidencias/ejecuciones/reembolsos_costos.md#118_reembolsos_costos_post_costos_400_xml) | `monto no finito` (NaN) solo tiene prueba unitaria (`test_montos_no_finitos`) |
| Costo por etapa, JSON y XML; etapa de otro rol (403); cliente (403) | [120](evidencias/ejecuciones/reembolsos_costos.md#120_reembolsos_costos_post_costos_201), [121](evidencias/ejecuciones/reembolsos_costos.md#121_reembolsos_costos_post_costos_201_xml), [114](evidencias/ejecuciones/reembolsos_costos.md#114_reembolsos_costos_post_costos_403), [113](evidencias/ejecuciones/reembolsos_costos.md#113_reembolsos_costos_post_costos_403) | `costos` por etapa y `vista_costo_devolucion` con `costo_total` 196.50 |
| Consultas: reembolsos, desglose de costos, 401 y 403 | [130](evidencias/ejecuciones/reembolsos_costos.md#130_reembolsos_costos_get_reembolsos_200), [131](evidencias/ejecuciones/reembolsos_costos.md#131_reembolsos_costos_get_reembolsos_200_xml), [132](evidencias/ejecuciones/reembolsos_costos.md#132_reembolsos_costos_get_reembolsos_403), [133](evidencias/ejecuciones/reembolsos_costos.md#133_reembolsos_costos_get_reembolsos_401), [134](evidencias/ejecuciones/reembolsos_costos.md#134_reembolsos_costos_get_costos_id_200), [135](evidencias/ejecuciones/reembolsos_costos.md#135_reembolsos_costos_get_costos_id_200_xml), [136](evidencias/ejecuciones/reembolsos_costos.md#136_reembolsos_costos_get_costos_id_403), [137](evidencias/ejecuciones/reembolsos_costos.md#137_reembolsos_costos_get_costos_id_404) | — |

<details>
<summary>Reembolsos y costos: peticion y respuesta copiadas tal cual (tokens y contrasenas ya ocultos en la fuente)</summary>

**128_reembolsos_costos_post_reembolsos_201** — reembolso 201 aprobado ([caso completo](evidencias/ejecuciones/reembolsos_costos.md#128_reembolsos_costos_post_reembolsos_201))

```
POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/reembolsos
Content-Type: application/json

{
  "devolucion_id": 81,
  "estado": "aprobado",
  "metodo": "transferencia",
  "monto": 1.0
}

--> 201 CREATED
{
  "id": 11,
  "devolucion_id": 81,
  "monto": 1.0,
  "metodo": "transferencia",
  "estado": "aprobado",
  "fecha_resolucion": "2026-10-22T00:42:03.019623+00:00"
}
```

**121_reembolsos_costos_post_costos_201_xml** — costo 201 almacenamiento XML ([caso completo](evidencias/ejecuciones/reembolsos_costos.md#121_reembolsos_costos_post_costos_201_xml))

```
POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos
Content-Type: application/xml

<costo>
  <devolucion_id>81</devolucion_id>
  <etapa>almacenamiento</etapa>
  <monto>45.00</monto>
</costo>

--> 201 CREATED
<?xml version='1.0' encoding='utf-8'?>
<respuesta><id>47</id><devolucion_id>81</devolucion_id><etapa>almacenamiento</etapa><monto>45.0</monto><fecha>2026-10-22</fecha></respuesta>
```

**127_reembolsos_costos_post_reembolsos_409** — reembolso 409 monto excedido ([caso completo](evidencias/ejecuciones/reembolsos_costos.md#127_reembolsos_costos_post_reembolsos_409))

```
POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/reembolsos
Content-Type: application/json

{
  "devolucion_id": 81,
  "estado": "aprobado",
  "metodo": "transferencia",
  "monto": 9999999.99
}

--> 409 CONFLICT
{
  "error": {
    "codigo": 409,
    "tipo": "monto_excedido",
    "mensaje": "El reembolso excede el valor devuelto.",
    "detalles": {
      "maximo": 193.77
    },
    "correlation_id": "5fc7df7722014db0"
  }
}
```

**129_reembolsos_costos_post_reembolsos_409_xml** — reembolso 409 duplicado XML ([caso completo](evidencias/ejecuciones/reembolsos_costos.md#129_reembolsos_costos_post_reembolsos_409_xml))

```
POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/reembolsos
Content-Type: application/xml

<reembolso>
  <devolucion_id>81</devolucion_id>
  <monto>1.00</monto>
  <metodo>transferencia</metodo>
  <estado>aprobado</estado>
</reembolso>

--> 409 CONFLICT
<?xml version='1.0' encoding='utf-8'?>
<error><codigo>409</codigo><tipo>reembolso_duplicado</tipo><mensaje>La devolucion ya tiene un reembolso valido.</mensaje><detalles /><correlation_id>38448f016c7449dc</correlation_id></error>
```

**115_reembolsos_costos_post_costos_400** — costo 400 monto negativo ([caso completo](evidencias/ejecuciones/reembolsos_costos.md#115_reembolsos_costos_post_costos_400))

```
POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos
Content-Type: application/json

{
  "devolucion_id": 81,
  "etapa": "transporte",
  "monto": -5
}

--> 400 BAD REQUEST
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "monto debe ser un monto decimal finito no negativo.",
    "detalles": null,
    "correlation_id": "73051ed6d3a34227"
  }
}
```

**114_reembolsos_costos_post_costos_403** — costo 403 etapa de otro rol ([caso completo](evidencias/ejecuciones/reembolsos_costos.md#114_reembolsos_costos_post_costos_403))

```
POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos
Content-Type: application/json

{
  "devolucion_id": 81,
  "etapa": "reembolso",
  "monto": 150.5
}

--> 403 FORBIDDEN
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "Tu rol no puede registrar costos de esta etapa.",
    "detalles": null,
    "correlation_id": "19f8712ddd35468d"
  }
}
```

</details>

### 13.6 ventas-catalogos

| Escenario | Casos reales | Efecto verificado |
|---|---|---|
| Venta propia con `disponible` por linea (JSON y XML); venta ajena (403); inexistente (404) | [144](evidencias/ejecuciones/ventas_catalogos.md#144_ventas_catalogos_get_id_200), [145](evidencias/ejecuciones/ventas_catalogos.md#145_ventas_catalogos_get_id_200_xml), [146](evidencias/ejecuciones/ventas_catalogos.md#146_ventas_catalogos_get_id_403), [147](evidencias/ejecuciones/ventas_catalogos.md#147_ventas_catalogos_get_id_404) | La respuesta trae `ya_devuelto` y `disponible` por linea (insumo de RN-01) |
| Listado con paginacion (JSON y XML), paginacion invalida (400), sin token (401) | [139](evidencias/ejecuciones/ventas_catalogos.md#139_ventas_catalogos_get_raiz_200), [140](evidencias/ejecuciones/ventas_catalogos.md#140_ventas_catalogos_get_raiz_200_xml), [141](evidencias/ejecuciones/ventas_catalogos.md#141_ventas_catalogos_get_raiz_400), [142](evidencias/ejecuciones/ventas_catalogos.md#142_ventas_catalogos_get_raiz_401), [143](evidencias/ejecuciones/ventas_catalogos.md#143_ventas_catalogos_get_raiz_401) | — |
| Catalogos: lista (solo roles permitidos), motivos, rutas, transportistas, registro por id | [148](evidencias/ejecuciones/ventas_catalogos.md#148_ventas_catalogos_get_catalogos_200), [150](evidencias/ejecuciones/ventas_catalogos.md#150_ventas_catalogos_get_catalogos_nombre_200), [151](evidencias/ejecuciones/ventas_catalogos.md#151_ventas_catalogos_get_catalogos_nombre_200_xml), [154](evidencias/ejecuciones/ventas_catalogos.md#154_ventas_catalogos_get_catalogos_nombre_200), [155](evidencias/ejecuciones/ventas_catalogos.md#155_ventas_catalogos_get_catalogos_nombre_200), [156](evidencias/ejecuciones/ventas_catalogos.md#156_ventas_catalogos_get_catalogos_nombre_registro_id_200) | — |
| Cliente leyendo un catalogo distinto de `motivos` (403) y catalogo inexistente (404) | [149](evidencias/ejecuciones/ventas_catalogos.md#149_ventas_catalogos_get_catalogos_403), [152](evidencias/ejecuciones/ventas_catalogos.md#152_ventas_catalogos_get_catalogos_nombre_403), [153](evidencias/ejecuciones/ventas_catalogos.md#153_ventas_catalogos_get_catalogos_nombre_404) | — |
| Alta (JSON y XML), alta con datos invalidos (400), con referencia inactiva (409), rol sin permiso (403) | [158](evidencias/ejecuciones/ventas_catalogos.md#158_ventas_catalogos_post_catalogos_nombre_201), [159](evidencias/ejecuciones/ventas_catalogos.md#159_ventas_catalogos_post_catalogos_nombre_201_xml), [160](evidencias/ejecuciones/ventas_catalogos.md#160_ventas_catalogos_post_catalogos_nombre_400), [164](evidencias/ejecuciones/ventas_catalogos.md#164_ventas_catalogos_post_catalogos_nombre_409), [162](evidencias/ejecuciones/ventas_catalogos.md#162_ventas_catalogos_post_catalogos_nombre_403) | — |
| Edicion, cambio de estado y baja logica | [165](evidencias/ejecuciones/ventas_catalogos.md#165_ventas_catalogos_put_catalogos_nombre_registro_id_200), [168](evidencias/ejecuciones/ventas_catalogos.md#168_ventas_catalogos_patch_catalogos_nombre_id_estado_200), [171](evidencias/ejecuciones/ventas_catalogos.md#171_ventas_catalogos_delete_catalogos_nombre_registro_id_200) | `activo` cambia en la respuesta; no hay captura de la fila en PostgreSQL |

<details>
<summary>Ventas y catalogos: peticion y respuesta copiadas tal cual (tokens y contrasenas ya ocultos en la fuente)</summary>

**144_ventas_catalogos_get_id_200** — venta 200 detalle ([caso completo](evidencias/ejecuciones/ventas_catalogos.md#144_ventas_catalogos_get_id_200))

```
GET http://{{vm_host}}:8006/api/v1/ventas/29

--> 200 OK
{
  "id": 29,
  "folio_venta": "VTA-2026-0004",
  "fecha_venta": "2026-08-31",
  "cliente_id": 11,
  "cliente": "Miguel Ramos Soto",
  "tienda": "Tienda Valle Oriente",
  "lineas": [
    {
      "id": 69,
      "lote_id": 11,
      "cantidad": 2,
      "precio_unitario": 253.06,
      "numero_lote": "L-2026-312",
      "fecha_caducidad": "2027-01-01",
      "producto_id": 10,
      "producto": "Galletas surtidas 600 g",
      "sku": "ABA-003",
      "clasificacion_temperatura": "no_refrigerado",
      "proveedor": "Abarrotes Monterrey",
      "ya_devuelto": 1,
      "disponible": 1
    }
  ]
}
```

**145_ventas_catalogos_get_id_200_xml** — venta 200 detalle XML ([caso completo](evidencias/ejecuciones/ventas_catalogos.md#145_ventas_catalogos_get_id_200_xml))

```
GET http://{{vm_host}}:8006/api/v1/ventas/29

--> 200 OK
<?xml version='1.0' encoding='utf-8'?>
<venta><id>29</id><folio_venta>VTA-2026-0004</folio_venta><fecha_venta>2026-08-31</fecha_venta><cliente_id>11</cliente_id><cliente>Miguel Ramos Soto</cliente><tienda>Tienda Valle Oriente</tienda><lineas><item><id>69</id><lote_id>11</lote_id><cantidad>2</cantidad><precio_unitario>253.06</precio_unitario><numero_lote>L-2026-312</numero_lote><fecha_caducidad>2027-01-01</fecha_caducidad><producto_id>10</producto_id><producto>Galletas surtidas 600 g</producto><sku>ABA-003</sku><clasificacion_temperatura>no_refrigerado</clasificacion_temperatura><proveedor>Abarrotes Monterrey</proveedor><ya_devuelto>1</ya_devuelto><disponible>1</disponible></item></lineas></venta>
```

**146_ventas_catalogos_get_id_403** — venta 403 de otro cliente ([caso completo](evidencias/ejecuciones/ventas_catalogos.md#146_ventas_catalogos_get_id_403))

```
GET http://{{vm_host}}:8006/api/v1/ventas/29

--> 403 FORBIDDEN
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "La venta no te pertenece.",
    "detalles": null,
    "correlation_id": "546730f466bd4f13"
  }
}
```

**160_ventas_catalogos_post_catalogos_nombre_400** — alta 400 sin nombre ([caso completo](evidencias/ejecuciones/ventas_catalogos.md#160_ventas_catalogos_post_catalogos_nombre_400))

```
POST http://{{vm_host}}:8006/api/v1/catalogos/motivos
Content-Type: application/json

{
  "nombre": ""
}

--> 400 BAD REQUEST
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Campos invalidos.",
    "detalles": [
      {
        "campo": "nombre",
        "problema": "obligatorio"
      }
    ],
    "correlation_id": "0f58c6f58a064cc2"
  }
}
```

**164_ventas_catalogos_post_catalogos_nombre_409** — alta 409 referencia inactiva ([caso completo](evidencias/ejecuciones/ventas_catalogos.md#164_ventas_catalogos_post_catalogos_nombre_409))

```
POST http://{{vm_host}}:8006/api/v1/catalogos/productos
Content-Type: application/json

{
  "sku": "PM-1792629378",
  "nombre": "Producto Postman",
  "clasificacion_temperatura": "refrigerado",
  "proveedor_id": 999999
}

--> 409 CONFLICT
{
  "error": {
    "codigo": 409,
    "tipo": "referencia_inactiva",
    "mensaje": "El campo proveedor_id no referencia un registro activo.",
    "detalles": null,
    "correlation_id": "6c3f4825d3794973"
  }
}
```

**149_ventas_catalogos_get_catalogos_403** — catalogos 403 cliente ([caso completo](evidencias/ejecuciones/ventas_catalogos.md#149_ventas_catalogos_get_catalogos_403))

```
GET http://{{vm_host}}:8006/api/v1/catalogos

--> 403 FORBIDDEN
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "Tu rol no tiene permiso para esta operacion.",
    "detalles": {
      "rol": "Cliente",
      "roles_permitidos": [
        "Administrador",
        "Analista de Devoluciones"
      ]
    },
    "correlation_id": "bc9302e35c6a46e3"
  }
}
```

</details>

### 13.7 evidencias

| Escenario | Casos reales | Efecto verificado |
|---|---|---|
| Comentario JSON y XML | [174](evidencias/ejecuciones/evidencias.md#174_evidencias_post_raiz_201), [175](evidencias/ejecuciones/evidencias.md#175_evidencias_post_raiz_201_xml) | Fila en `evidencias` y documento en `evidencias_metadatos` ([`postgresql.txt`](evidencias/bases/postgresql.txt), [`mongodb.txt`](evidencias/bases/mongodb.txt)) |
| Fotografia PNG (multipart) | [176](evidencias/ejecuciones/evidencias.md#176_evidencias_post_raiz_201) | Archivo con nombre aleatorio y permisos `-rw-------` en el volumen privado ([`volumen.txt`](evidencias/bases/volumen.txt)); `GET /uploads/` responde 404 |
| Archivo que no es imagen ni PDF (415) | [188](evidencias/ejecuciones/evidencias.md#188_evidencias_post_raiz_415) | Sin archivo ni fila nuevos |
| Archivo mayor a 10 MB (413) | **pendiente** | Ver EV-23 |
| Enlace firmado de 15 min, descarga con enlace y con Bearer, sin firma ni token (401) | [197](evidencias/ejecuciones/evidencias.md#197_evidencias_get_id_enlace_200), [199](evidencias/ejecuciones/evidencias.md#199_evidencias_get_evidencia_id_archivo_200), [200](evidencias/ejecuciones/evidencias.md#200_evidencias_get_id_archivo_200), [201](evidencias/ejecuciones/evidencias.md#201_evidencias_get_id_archivo_401) | La respuesta incluye una firma de corta vida; no se transcribe aqui |
| Enlace de un comentario sin archivo (409) | [198](evidencias/ejecuciones/evidencias.md#198_evidencias_get_id_enlace_409) | — |
| Enlace **vencido** | **pendiente** | Requiere esperar 15 min o ajustar el reloj |
| Cliente ajeno (403), analista (403), retiro logico, ya retirada (404) | [184](evidencias/ejecuciones/evidencias.md#184_evidencias_post_raiz_403), [196](evidencias/ejecuciones/evidencias.md#196_evidencias_get_id_403), [183](evidencias/ejecuciones/evidencias.md#183_evidencias_post_raiz_403), [205](evidencias/ejecuciones/evidencias.md#205_evidencias_delete_id_200), [206](evidencias/ejecuciones/evidencias.md#206_evidencias_delete_id_404) | Evidencia 15 con `eliminado_en` en `postgresql.txt` |

<details>
<summary>Evidencias: peticion y respuesta copiadas tal cual (tokens y contrasenas ya ocultos en la fuente)</summary>

**174_evidencias_post_raiz_201** — alta 201 comentario JSON ([caso completo](evidencias/ejecuciones/evidencias.md#174_evidencias_post_raiz_201))

```
POST http://{{vm_host}}:8007/api/v1/evidencias
Content-Type: application/json

{
  "devolucion_id": 83,
  "tipo": "comentario",
  "etapa": "solicitud",
  "comentario": "El sello del empaque llego roto."
}

--> 201 CREATED
{
  "id": 14,
  "devolucion_id": 83,
  "tipo": "comentario",
  "metadatos_id": "6ad95b931f4384d46cf80035"
}
```

**175_evidencias_post_raiz_201_xml** — alta 201 comentario XML ([caso completo](evidencias/ejecuciones/evidencias.md#175_evidencias_post_raiz_201_xml))

```
POST http://{{vm_host}}:8007/api/v1/evidencias
Content-Type: application/xml

<evidencia>
  <devolucion_id>83</devolucion_id>
  <tipo>comentario</tipo>
  <etapa>solicitud</etapa>
  <comentario>Segundo comentario en XML.</comentario>
</evidencia>

--> 201 CREATED
<?xml version='1.0' encoding='utf-8'?>
<evidencia><id>15</id><devolucion_id>83</devolucion_id><tipo>comentario</tipo><metadatos_id>6ad95b93c703a34b44966136</metadatos_id></evidencia>
```

**176_evidencias_post_raiz_201** — alta 201 archivo PNG ([caso completo](evidencias/ejecuciones/evidencias.md#176_evidencias_post_raiz_201))

```
POST http://{{vm_host}}:8007/api/v1/evidencias

devolucion_id: 83
etapa: solicitud
archivo: (archivo) evidencia_prueba.png

--> 201 CREATED
{
  "id": 16,
  "devolucion_id": 83,
  "tipo": "fotografia",
  "metadatos_id": "6ad95b931f4384d46cf80036"
}
```

**188_evidencias_post_raiz_415** — alta 415 archivo no soportado ([caso completo](evidencias/ejecuciones/evidencias.md#188_evidencias_post_raiz_415))

```
POST http://{{vm_host}}:8007/api/v1/evidencias

devolucion_id: 83
etapa: solicitud
archivo: (archivo) no_es_imagen.txt

--> 415 UNSUPPORTED MEDIA TYPE
{
  "error": {
    "codigo": 415,
    "tipo": "formato_no_soportado",
    "mensaje": "Solo se permiten JPG, PNG o PDF reales.",
    "detalles": null,
    "correlation_id": "878e4e26b2ef4160"
  }
}
```

**198_evidencias_get_id_enlace_409** — enlace 409 comentario sin archivo ([caso completo](evidencias/ejecuciones/evidencias.md#198_evidencias_get_id_enlace_409))

```
GET http://{{vm_host}}:8007/api/v1/evidencias/14/enlace

--> 409 CONFLICT
{
  "error": {
    "codigo": 409,
    "tipo": "sin_archivo",
    "mensaje": "Un comentario no tiene archivo asociado.",
    "detalles": null,
    "correlation_id": "bf3169d97cd04c20"
  }
}
```

**196_evidencias_get_id_403** — detalle 403 otro cliente ([caso completo](evidencias/ejecuciones/evidencias.md#196_evidencias_get_id_403))

```
GET http://{{vm_host}}:8007/api/v1/evidencias/14

--> 403 FORBIDDEN
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "No tienes acceso a esa devolucion.",
    "detalles": null,
    "correlation_id": "5246b7c32df64bd4"
  }
}
```

**205_evidencias_delete_id_200** — retiro 200 exitoso ([caso completo](evidencias/ejecuciones/evidencias.md#205_evidencias_delete_id_200))

```
DELETE http://{{vm_host}}:8007/api/v1/evidencias/15

--> 200 OK
{
  "id": 15,
  "eliminada": true
}
```

</details>

### 13.8 analisis-auditoria

| Escenario | Casos reales | Efecto verificado |
|---|---|---|
| Pareto antes de sincronizar (409 `analisis_sin_datos`) | **pendiente** (la base ya estaba sincronizada) | Solo hay prueba de division por cero (`test_pareto_vacio_sin_division_por_cero`) |
| Sincronizar (200: 38 casos, version 7) | [217](evidencias/ejecuciones/analisis_auditoria.md#217_analisis_auditoria_post_sincronizar_200) | `analisis:version = 7` y `solo_lectura_postgresql: true` ([`redis.txt`](evidencias/bases/redis.txt)) |
| Pareto primera llamada `miss`, segunda `hit`; XML por proveedor y costo | [218](evidencias/ejecuciones/analisis_auditoria.md#218_analisis_auditoria_get_pareto_200), [219](evidencias/ejecuciones/analisis_auditoria.md#219_analisis_auditoria_get_pareto_200), [220](evidencias/ejecuciones/analisis_auditoria.md#220_analisis_auditoria_get_pareto_200_xml) | `cache:causas:*` con TTL 142 s al capturar; la agregacion de Mongo suma los mismos 38 casos |
| Pareto: dimension, fecha o rango invalidos (400), cliente (403), token invalido (401) | [221](evidencias/ejecuciones/analisis_auditoria.md#221_analisis_auditoria_get_pareto_400), [222](evidencias/ejecuciones/analisis_auditoria.md#222_analisis_auditoria_get_pareto_400), [223](evidencias/ejecuciones/analisis_auditoria.md#223_analisis_auditoria_get_pareto_400), [224](evidencias/ejecuciones/analisis_auditoria.md#224_analisis_auditoria_get_pareto_403), [225](evidencias/ejecuciones/analisis_auditoria.md#225_analisis_auditoria_get_pareto_401) | — |
| Sugerencia de motivo (`requiere_confirmacion = true`) | [210](evidencias/ejecuciones/analisis_auditoria.md#210_analisis_auditoria_post_clasificar_motivo_200), [211](evidencias/ejecuciones/analisis_auditoria.md#211_analisis_auditoria_post_clasificar_motivo_200_xml), [212](evidencias/ejecuciones/analisis_auditoria.md#212_analisis_auditoria_post_clasificar_motivo_400), [213](evidencias/ejecuciones/analisis_auditoria.md#213_analisis_auditoria_post_clasificar_motivo_401), [214](evidencias/ejecuciones/analisis_auditoria.md#214_analisis_auditoria_post_clasificar_motivo_403) | La clasificacion no modifica `devoluciones` (RN-11) |
| Resumen, alertas de fraude, eventos por `correlation_id`, auditoria | [226](evidencias/ejecuciones/analisis_auditoria.md#226_analisis_auditoria_get_resumen_200), [228](evidencias/ejecuciones/analisis_auditoria.md#228_analisis_auditoria_get_alertas_fraude_200), [229](evidencias/ejecuciones/analisis_auditoria.md#229_analisis_auditoria_get_alertas_fraude_200_xml), [231](evidencias/ejecuciones/analisis_auditoria.md#231_analisis_auditoria_get_eventos_200), [232](evidencias/ejecuciones/analisis_auditoria.md#232_analisis_auditoria_get_eventos_200_xml), [236](evidencias/ejecuciones/analisis_auditoria.md#236_analisis_auditoria_get_auditoria_200), [237](evidencias/ejecuciones/analisis_auditoria.md#237_analisis_auditoria_get_auditoria_200_xml) | — |

La agregacion de Mongo (`resultados_analisis`, snapshots vigentes por motivo) da
Cadena de frio rota 12, Caducidad proxima 8, Etiqueta incorrecta 7, Caducidad
vencida 3, Calidad inferior 3, Producto danado 3 y Error en el pedido 2: la misma
distribucion del Pareto con `cache: miss` ([`mongodb.txt`](evidencias/bases/mongodb.txt)).

<details>
<summary>Analisis y auditoria: peticion y respuesta copiadas tal cual (tokens y contrasenas ya ocultos en la fuente)</summary>

**210_analisis_auditoria_post_clasificar_motivo_200** — clasificar 200 cliente ([caso completo](evidencias/ejecuciones/analisis_auditoria.md#210_analisis_auditoria_post_clasificar_motivo_200))

```
POST http://{{vm_host}}:8008/api/v1/analisis/clasificar-motivo
Content-Type: application/json

{
  "descripcion": "El producto llego roto y el empaque aplastado por el golpe."
}

--> 200 OK
{
  "sugerencias": [
    {
      "motivo": "Producto danado",
      "puntaje": 3,
      "coincidencias": [
        "aplastado",
        "golpe",
        "roto"
      ],
      "motivo_id": 1
    }
  ],
  "requiere_confirmacion": true,
  "explicacion": "La clasificacion orienta; el usuario confirma el motivo."
}
```

**217_analisis_auditoria_post_sincronizar_200** — sincronizar 200 exitoso ([caso completo](evidencias/ejecuciones/analisis_auditoria.md#217_analisis_auditoria_post_sincronizar_200))

```
POST http://{{vm_host}}:8008/api/v1/analisis/sincronizar
Content-Type: application/json

--> 200 OK
{
  "casos_sincronizados": 38,
  "version_cache": 7,
  "fecha": "2026-10-22T00:43:11.774152+00:00",
  "solo_lectura_postgresql": true
}
```

**220_analisis_auditoria_get_pareto_200_xml** — pareto 200 XML por proveedor y costo ([caso completo](evidencias/ejecuciones/analisis_auditoria.md#220_analisis_auditoria_get_pareto_200_xml))

```
GET http://{{vm_host}}:8008/api/v1/analisis/pareto?dimension=proveedor&medida=costo

--> 200 OK
<?xml version='1.0' encoding='utf-8'?>
<pareto><dimension>proveedor</dimension><medida>costo</medida><total_general>4003.78</total_general><categorias><item><etiqueta>Lacteos del Norte</etiqueta><total>1705.93</total><casos>16</casos><porcentaje>42.61</porcentaje><porcentaje_acumulado>42.61</porcentaje_acumulado></item><item><etiqueta>Abarrotes Monterrey</etiqueta><total>1408.79</total><casos>9</casos><porcentaje>35.19</porcentaje><porcentaje_acumulado>77.79</porcentaje_acumulado></item><item><etiqueta>CampoVerde Agricola</etiqueta><total>542.68</total><casos>10</casos><porcentaje>13.55</porcentaje><porcentaje_acumulado>91.35</porcentaje_acumulado></item><item><etiqueta>Avicola Real</etiqueta><total>346.38</total><casos>3</casos><porcentaje>8.65</porcentaje><porcentaje_acumulado>100.0</porcentaje_acumulado></item></categorias><interpretacion>Patrones para revision humana; no confirman causalidad.</interpretacion><cache>miss</cache><version_datos>7</version_datos></pareto>
```

**221_analisis_auditoria_get_pareto_400** — pareto 400 dimension desconocida ([caso completo](evidencias/ejecuciones/analisis_auditoria.md#221_analisis_auditoria_get_pareto_400))

```
GET http://{{vm_host}}:8008/api/v1/analisis/pareto?dimension=color

--> 400 BAD REQUEST
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Dimension o medida desconocida.",
    "detalles": null,
    "correlation_id": "5e1f748fa7b9434f"
  }
}
```

**215_analisis_auditoria_post_sincronizar_403** — sincronizar 403 cliente ([caso completo](evidencias/ejecuciones/analisis_auditoria.md#215_analisis_auditoria_post_sincronizar_403))

```
POST http://{{vm_host}}:8008/api/v1/analisis/sincronizar
Content-Type: application/json

--> 403 FORBIDDEN
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "Tu rol no tiene permiso para esta operacion.",
    "detalles": {
      "rol": "Cliente",
      "roles_permitidos": [
        "Administrador",
        "Analista de Devoluciones"
      ]
    },
    "correlation_id": "9f4121c5c634409d"
  }
}
```

</details>

### 13.9 Estado de cada evidencia (EV-nn)

| ID | Que debia capturarse | Estado | Donde esta |
|---|---|---|---|
| EV-01 | `docker compose ps` con los 12 contenedores | Hecha | [`docker.txt`](evidencias/bases/docker.txt); apartado 15 |
| EV-02 | Firewall de GCP y consola de la VM | Hecha (solo `gcloud`; sin captura de la consola web) | [`gcp.txt`](evidencias/bases/gcp.txt) |
| EV-03 | Login real, `sesion_api` con TTL y `jwt_revocado` | Hecha | 13.1; [`redis.txt`](evidencias/bases/redis.txt); [`jwt_revocado.txt`](evidencias/bases/jwt_revocado.txt) |
| EV-04 | Flujo E2E completo | Hecha como salida de texto (sin capturas de pantalla) | Apartado 17.1; [`salida_2026-10-21.txt`](pruebas/salida_2026-10-21.txt) |
| EV-05 | Mismo `correlation_id` en dos servicios desde una accion del web | **Pendiente** | Tabla del apartado 19.3 |
| EV-06 | Esquema real de PostgreSQL y migraciones aplicadas | Hecha: las 13 migraciones y `\dt` | [`migraciones.txt`](evidencias/bases/migraciones.txt); [`postgresql.txt`](evidencias/bases/postgresql.txt) |
| EV-07 | Colecciones, indices y documentos de MongoDB | Hecha | [`mongodb.txt`](evidencias/bases/mongodb.txt); apartado 8.2 |
| EV-08 | Claves de Redis con TTL | Hecha | [`redis.txt`](evidencias/bases/redis.txt) |
| EV-09 | XML real por servicio y un `xml_no_cumple_xsd` | Hecha | Apartado 10 |
| EV-10 a EV-17 | Peticion y respuesta de cada servicio y efecto en BD | Hecha, salvo los escenarios marcados `pendiente` en 13.1 a 13.8 y las capturas de Swagger | 13.1 a 13.8 |
| EV-20 | Pruebas unitarias | Hecha: 119 en la laptop y 84 dentro de los contenedores de la VM | Apartado 16; [`unitarias_contenedores.txt`](evidencias/bases/unitarias_contenedores.txt) |
| EV-21 | Pruebas de integracion `INTEGRACION=1` | Hecha: 8 servicios, 34 pruebas | Apartado 16; [`salida_2026-10-21_servicios.txt`](pruebas/salida_2026-10-21_servicios.txt) |
| EV-22 | Caida de PostgreSQL, MongoDB y Redis | **Pendiente** | Tabla del apartado 19.3 |
| EV-23 | Concurrencia y archivo mayor a 10 MB | **Pendiente** | Tabla del apartado 19.3 |
| EV-24 | Prueba de XXE | Hecha | Apartado 16.2 |
| EV-25 | Build y arranque de Compose | Hecha | Apartado 15; [`build.txt`](evidencias/bases/build.txt) |
| EV-26 | Panel `/integracion/servicios` 8 de 8 | **Pendiente** | Tabla del apartado 19.3 |
| EV-27 | Capturas del web | **Pendiente** | Tabla del apartado 19.3 |
| EV-28 | Suite E2E y su resultado | Hecha: 100 passed in 5.84 s | Apartado 17.1 |

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
> con 8 de 8 servicios disponibles. Hay evidencia parcial: los nueve `/health`
> que consulta el panel respondieron 200 desde la VM ([`docker.txt`](evidencias/bases/docker.txt))
> y el paso 6b del E2E inicia sesion en el web por su formulario real
> ([`salida_2026-10-21.txt`](pruebas/salida_2026-10-21.txt)). Falta la captura del
> panel; como obtenerla: apartado 19.3.
> <!-- EVIDENCIA PENDIENTE: EV-26 panel de servicios 8/8 -->

> **EVIDENCIA PENDIENTE [EV-27]:** capturas del web: inicio de sesion con la
> insignia "API distribuida", panel de causas con Highcharts y bitacora. No hay
> capturas de pantalla en el repositorio (`docs/evidencias/capturas/` esta vacia);
> como obtenerlas: apartado 19.3.
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

**Evidencia EV-01 y EV-25 (VM, 22 de octubre).** `docker compose ps` lista los
doce contenedores `Up`; ocho con `(healthy)` (`postgres`, `redis`, `mongo`,
`auth`, `devoluciones`, `evidencias`, `ventas-catalogos` y `analisis-auditoria`)
y cuatro sin healthcheck de Compose (`app`, `logistica`, `inspecciones` y
`reembolsos-costos`, ver apartado 17.3). La salida completa, junto con
`docker stats`, los volumenes y los logs con el `X-Correlation-ID`, esta en
[`evidencias/bases/docker.txt`](evidencias/bases/docker.txt) y el volumen privado en
[`evidencias/bases/volumen.txt`](evidencias/bases/volumen.txt). Los nueve `/health` (web en 8000,
servicios en 8001 a 8008), copiados tal cual:

```
8000: 200
8001: 200
8002: 200
8003: 200
8004: 200
8005: 200
8006: 200
8007: 200
8008: 200
```

**Evidencia EV-25.** Salida real del propio `docker compose up -d --build` y del estado
posterior en [`evidencias/bases/build.txt`](evidencias/bases/build.txt) (22 de octubre).

## 16. Pruebas unitarias y de integracion

### 16.1 Estado real

El catalogo completo de casos (ID, entradas, resultado esperado, resultado
obtenido, estado y evidencia) esta en [`PRUEBAS.md`](PRUEBAS.md). Aqui se resume
lo que hay y lo que se ejecuto.

**Pruebas unitarias: 119 casos.** Usan dobles (por ejemplo Redis en memoria) y no
requieren servidores. Conteo por archivo, tal como lo reporta `pytest -v` en
[`pruebas/resultado_2026-10-21_local.md`](pruebas/resultado_2026-10-21_local.md):

| Archivo | Casos | Cubre |
|---|---:|---|
| `services/auth/tests/test_auth.py` | 27 | login JSON/XML, 401 generico, bloqueo, rate limit, refresh, logout y revocacion, token falso y expirado, 403, Redis caido, XSD de respuestas |
| `services/devoluciones/tests/test_reglas.py` | 11 | validaciones de entrada y de resolucion |
| `services/devoluciones/tests/test_api.py` | 13 | 401, token revocado, 403 por rol, validacion, XML contra XSD, paginacion, rate limit |
| `services/logistica/tests/test_api.py` | 5 | 401, 403, XML invalido, fecha invalida, booleano estricto |
| `services/inspecciones/tests/test_reglas.py` | 5 | `evaluar_aptitud` (danos, cadena de frio, 30 min) y booleano ambiguo |
| `services/reembolsos_costos/tests/test_api.py` | 6 | 401, rol sin permiso, monto negativo y no finito, XML invalido, etapas por rol |
| `services/ventas_catalogos/tests/test_reglas.py` | 8 | catalogos iguales al monolito, producto y lote validos e invalidos (con parametros) |
| `services/evidencias/tests/test_seguridad_archivos.py` | 3 | tipo por contenido, enlace firmado, rechazo de `.exe` |
| `services/analisis_auditoria/tests/test_pareto.py` | 4 | Pareto, division por cero, clasificador explicable |
| `apps/web/app/tests/test_api_client.py` | 3 | JWT solo en sesion, 503 por red, renovacion con un reintento |
| `apps/web/app/tests/test_microservicios.py` | 3 | salud del servicio, timeout y JSON invalido degradan sin romper |
| `apps/web/app/tests/test_exportacion.py` | 16 | CSV con BOM, bloques, escape de formulas, 403 por rol (RF-28) |
| `apps/web/app/tests/test_notificaciones.py` | 15 | matriz de destinatarios, bandeja y campanita (RF-29) |
| **Total** | **119** | |

**Pruebas de integracion y E2E: se ejecutan solo en la VM** (`INTEGRACION=1`,
`bash scripts/correr_e2e.sh`):

| Grupo | Casos | Resultado en la VM (21 de octubre) |
|---|---:|---|
| Integracion por servicio (`services/*/tests/test_integracion.py`) | 34 | 8 de 8 servicios sin fallos: auth 5, ventas-catalogos 4, evidencias 4, devoluciones 4, logistica 3, inspecciones 5, reembolsos-costos 5, analisis-auditoria 4 |
| E2E (`tests/e2e/`): proceso de 11 pasos mas el 6b (campanita), seguridad y errores, JSON/XML y rate limit | 100 | **100 passed in 5.84 s** |

Los 119 unitarios se corrieron en la laptop del equipo (Python 3.13, sin bases
de datos) y, ademas, dentro de los contenedores de la VM.

**Evidencia EV-20.** Local: 119 casos en
[`pruebas/resultado_2026-10-21_local.md`](pruebas/resultado_2026-10-21_local.md). En la VM,
`pytest` dentro de cada contenedor de servicio
([`evidencias/bases/unitarias_contenedores.txt`](evidencias/bases/unitarias_contenedores.txt)):
auth 27, ventas-catalogos 8, devoluciones 24, evidencias 3, logistica 5, inspecciones 5,
reembolsos-costos 8 y analisis-auditoria 4 (84 passed; los casos `skipped` son las pruebas
de integracion, que solo corren con `INTEGRACION=1`). Con los 37 del web suman 121; los 119 de la corrida local son anteriores a las dos pruebas del monto maximo de reembolso.

**Evidencia EV-21.** Salida real de la VM, tomada de
[`pruebas/salida_2026-10-21.txt`](pruebas/salida_2026-10-21.txt) (bloque
`reembolsos-costos`, comando `docker compose run --rm -e INTEGRACION=1
reembolsos-costos python -m pytest -v -p no:cacheprovider
tests/test_integracion.py`):

```
tests/test_integracion.py::IntegracionReembolsos::test_costos_por_etapa_y_total PASSED [ 20%]
tests/test_integracion.py::IntegracionReembolsos::test_el_cliente_no_reembolsa PASSED [ 40%]
tests/test_integracion.py::IntegracionReembolsos::test_lock_de_redis_bloquea_la_resolucion_concurrente PASSED [ 60%]
tests/test_integracion.py::IntegracionReembolsos::test_no_reembolsa_si_no_esta_autorizada_ni_mas_del_valor PASSED [ 80%]
tests/test_integracion.py::IntegracionReembolsos::test_un_solo_reembolso_por_devolucion PASSED [100%]

============================== 5 passed in 1.43s ===============================
```

La salida completa de los ocho servicios esta en esa misma carpeta
(`salida_2026-10-21.txt` y `salida_2026-10-21_servicios.txt`).

### 16.2 Cobertura frente a las pruebas que pide el enunciado

| Prueba obligatoria | Estado |
|---|---|
| Unitarias | 119 passed (laptop, sin bases); falta la corrida en contenedores de la VM |
| De integracion | Hechas en la VM para los ocho servicios (34 casos, todos pasan) |
| Contratos JSON | E2E SEG-10 (400 `validacion`, 9 casos) y los casos 400 de cada servicio en [`EVIDENCIAS.md`](EVIDENCIAS.md); 767 verificaciones de Newman sin fallos |
| Esquemas XML | E2E FMT-01 a FMT-06 pasan; los casos `*_xml` de cada servicio (apartado 10); los 22 XSD compilan con `lxml` |
| Autenticacion, autorizacion, expiracion y revocacion | E2E SEG-01 a SEG-08 (8 servicios cada uno), E2E-11 e INT-AUTH-1 a 5 pasan |
| Recuperacion ante fallos | Parcial: Redis caido en `auth` (con dobles) y microservicio no disponible en el web (unitaria). **Sin prueba real** de caida de contenedores (EV-22) |
| Caida de PostgreSQL y de MongoDB | **No hay prueba** (EV-22) |
| Concurrencia | Parcial: INT-REE-2 prueba el lock de Redis tomado manualmente y E2E-09 el segundo reembolso (409 `reembolso_duplicado`); **no hay dos solicitudes simultaneas reales** (EV-23) |
| Archivos grandes | Parcial: el 415 por contenido falso pasa (INT-EVI-2); **el 413 por mas de 10 MB no tiene prueba** (EV-23) |
| Grandes volumenes | **No hay prueba** |
| Seguridad basica y XXE | XXE: E2E FMT-07 pasa; inyeccion SQL en la busqueda (SEG-22), rate limit (SEG-23), bitacora sin tokens (SEG-21) y firma falsa, expirado y revocado (SEG-03 a SEG-05) pasan. Sin escaner de vulnerabilidades |
| Carga con Locust y perfiles (RNF-29) | **No existe**; corresponde al tercer parcial |

> **Evidencia EV-24 (XXE).** La prueba `test_xml_no_resuelve_entidades_externas`
> (FMT-07) envia un XML con `<!ENTITY x SYSTEM "file:///etc/passwd">` al login. El
> parser (`shared/xsd.py`, `lxml` sin entidades ni red) no resuelve la entidad y
> responde 400, sin contenido del archivo. Linea tomada tal cual de
> [`pruebas/salida_2026-10-21.txt`](pruebas/salida_2026-10-21.txt):
>
> ```
> tests/e2e/test_03_json_y_xml.py::test_xml_no_resuelve_entidades_externas [E2E] POST /api/v1/auth/login -> 400 {"error": {"codigo": 400, "tipo": "xml_invalido", "mensaje": "El cuerpo no es un documento XML bien formado.", "detalles": ["undefined entity &x;: line 1, column 93"], "correlation_id": "0ae936c3ba8c4250"}}
> ```

> **Evidencia del rate limit (429).** Caso SEG-23: diez logins fallidos
> responden 401 y el siguiente 429 (linea de la misma salida):
>
> ```
> [E2E] POST /api/v1/auth/login -> 429 {"error": {"codigo": 429, "tipo": "demasiadas_peticiones", "mensaje": "Limite de 10 peticiones en 60 s. Intenta de nuevo en 60 s.", "detalles": null, "correlation_id": "c6bd3744d3c9432f"}}
> ```

> **EVIDENCIA PENDIENTE [EV-22]:** detener el contenedor de PostgreSQL, el de
> MongoDB y el de Redis y mostrar la respuesta de `/health` y de un endpoint de
> negocio en cada caso; apagar un microservicio y mostrar el panel del web.
> Como obtenerla: apartado 19.3. <!-- EVIDENCIA PENDIENTE: EV-22 caida de dependencias -->

> **EVIDENCIA PENDIENTE [EV-23]:** dos solicitudes simultaneas de reembolso y
> de alta sobre la misma linea de venta, y una subida mayor a 10 MB (413).
> Como obtenerla: apartado 19.3. <!-- EVIDENCIA PENDIENTE: EV-23 concurrencia y archivo grande -->

## 17. Resultados, problemas identificados y soluciones

### 17.1 Resultados

Todo lo de esta tabla tiene salida en el repositorio.

| Resultado | Fuente |
|---|---|
| Suite E2E en la VM: **100 passed in 5.84 s** (12 del proceso completo, 23 de seguridad y errores, 8 de JSON/XML y el resto con parametros) | [`pruebas/salida_2026-10-21.txt`](pruebas/salida_2026-10-21.txt), [`PRUEBAS.md`](PRUEBAS.md) |
| Integracion por servicio en la VM: **8 de 8**, 34 casos | [`pruebas/salida_2026-10-21.txt`](pruebas/salida_2026-10-21.txt), [`pruebas/salida_2026-10-21_servicios.txt`](pruebas/salida_2026-10-21_servicios.txt) |
| Unitarias: 119 passed en la laptop, sin bases | [`pruebas/resultado_2026-10-21_local.md`](pruebas/resultado_2026-10-21_local.md) |
| Ocho colecciones de Newman contra la VM: 238 casos documentados, 767 verificaciones, 0 fallidas | [`evidencias/ejecuciones/`](evidencias/ejecuciones/auth.md) |
| Doce contenedores arriba (ocho con `(healthy)` en Compose) y los nueve `/health` en 200 | [`evidencias/bases/docker.txt`](evidencias/bases/docker.txt) |
| Devolucion `DEV-2026-0081` recorrida hasta `cerrada` con 17 eventos de bitacora, reembolso 1.00 y `costo_total` 196.50 | [`evidencias/bases/postgresql.txt`](evidencias/bases/postgresql.txt) |
| Candado de reembolso: 409 `reembolso_en_proceso` con el lock puesto | [`evidencias/bases/redis.txt`](evidencias/bases/redis.txt) |
| Caso `DEV-2026-0033` recorrido desde formularios web hasta `cerrada`; reembolso de 32.24; etiqueta `REC-2026-0033` | Reportado por el equipo en `INTEGRACION_WEB_MICROSERVICIOS.md`; sin captura |
| Con 12 IPs falsas en `X-Forwarded-For`, la peticion 11 recibe 429 | Reportado por el equipo en `BITACORA.md`; sin salida versionada |
| Ocho servicios compilan; ocho OpenAPI cargan; 22 XSD compilan; `docker compose config` resuelve 12 servicios y 4 volumenes | `AUDITORIA_SEGUNDO_PARCIAL.md` |

**Las cuatro corridas en la VM (21 de octubre).** El detalle de cada fallo y su
causa esta en [`pruebas/resultado_2026-10-21.md`](pruebas/resultado_2026-10-21.md):

| Corrida | Resultado |
|---|---|
| 1a (`main` con las sesiones 01 a 03) | E2E 91 de 100: 2 fallos reales (E2E-06 prueba desactualizada, E2E-09 bug H-11) y 7 en cascada porque la suite agoto la linea de venta. Integracion: logistica, inspecciones, reembolsos y analisis sin resultado por 429 (H-07) |
| 1b (limite de login subido temporalmente) | logistica 3/3, inspecciones 5/5 y analisis 4/4; reembolsos 4/5 (H-11 otra vez); devoluciones con 401 al iniciar (cuenta real, sin contrasena demo) |
| 2a (tras PR #8) | **E2E 100 de 100**; integracion 7 de 8, devoluciones con un fallo porque la imagen aun traia la prueba vieja |
| 3a (tras PR #9 e imagen de `devoluciones` reconstruida) | devoluciones **4 passed in 1.33 s** |

Resultado final: **E2E 100/100 e integracion 8/8**. La leccion operativa: la
suite de cada servicio corre con el archivo que esta dentro de su imagen, asi que
hay que reconstruir (`docker compose up -d --build <servicio>`) cada servicio
cuyas pruebas cambian.

**Evidencia EV-04 / EV-28 (proceso completo).** Los once pasos del proceso mas el
6b (campanita) estan en `tests/e2e/test_01_proceso_completo.py` y pasan en la
VM. Como ejemplo, el paso 9 (reembolso unico con lock de Redis), lineas tomadas
tal cual de [`pruebas/salida_2026-10-21.txt`](pruebas/salida_2026-10-21.txt):

```
tests/e2e/test_01_proceso_completo.py::test_paso_09_reembolso_unico_con_lock [E2E] POST /api/v1/reembolsos-costos/reembolsos -> 201 {"id": 9, "devolucion_id": 56, "monto": 227.17, "metodo": "transferencia", "estado": "aprobado", "fecha_resolucion": "2026-10-21T18:22:07.439922+00:00"}
[E2E] POST /api/v1/reembolsos-costos/reembolsos -> 409 {"error": {"codigo": 409, "tipo": "reembolso_duplicado", "mensaje": "La devolucion ya tiene un reembolso valido.", "detalles": null, "correlation_id": "ed6cf17d34d9489d"}}
[E2E] POST /api/v1/reembolsos-costos/reembolsos -> 409 {"error": {"codigo": 409, "tipo": "reembolso_en_proceso", "mensaje": "Otro proceso esta resolviendo este reembolso.", "detalles": null, "correlation_id": "81df657514e94f88"}}
```

Es salida de texto, no capturas de pantalla. Cada paso, su resultado esperado y
la evidencia estan en la tabla E2E-01 a E2E-11 de [`PRUEBAS.md`](PRUEBAS.md).

### 17.2 Problemas encontrados y como se resolvieron

| Problema | Solucion | Referencia |
|---|---|---|
| PostgreSQL nativo de la VM ocupaba el 5432 | Mapeo del contenedor a 55432 y 56379/57017 para Redis/Mongo, solo en `127.0.0.1` | `BITACORA.md`; [`docker.txt`](evidencias/bases/docker.txt) |
| SELinux impedia leer el codigo montado | Etiqueta `:z` en el volumen | `BITACORA.md` |
| Una migracion fallaba al reclasificar datos | Quitar el CHECK antes del `UPDATE` | `60d7c90` |
| El seed no funcionaba en base limpia | Usar la etapa `transporte` | `04dfc46` |
| Rate limit evadible con `X-Forwarded-For` | No leer ese header | `shared/infra.py:ip_origen` |
| Un 500 confirmaba la transaccion | Marca `g.error_interno` y rollback | `shared/respuestas.py` |
| Dos solicitudes podian devolver mas de lo comprado | `SELECT ... FOR UPDATE` en linea y devolucion | `services/devoluciones/app.py` |
| Doble reembolso concurrente | Lock Redis `NX EX 30` + `UNIQUE` + trigger | `services/reembolsos_costos/app.py` |
| Archivo huerfano si fallaba Mongo o PostgreSQL | Compensacion: borrar archivo y metadatos y `rollback` | `services/evidencias/app.py` |
| **H-11:** un reembolso por el monto maximo exacto se rechazaba con 409 `monto_excedido` (comparaba `Decimal` contra `float`; `Decimal("227.17") > float(227.17)`). Lo detecto E2E-09 en la 1a corrida | Se compara `Decimal` con `Decimal` y se agregaron dos pruebas unitarias (PR #8). El paso 9 aprobo despues 227.17 con 201 | [`PRUEBAS.md`](PRUEBAS.md) (H-11); [`pruebas/resultado_2026-10-21.md`](pruebas/resultado_2026-10-21.md) |
| **H-07:** el rate limit de login (10 por minuto por IP) dejo sin login a cuatro servicios en la 1a corrida, porque `test_99` llega al limite a proposito y la red del compose comparte IP | `scripts/correr_e2e.sh` borra las claves `devoluciones:limite:*:login` antes de cada bloque; `auth` no se modifico | [`PRUEBAS.md`](PRUEBAS.md) (H-07) |
| La suite agotaba la linea de venta (`sin_disponible` en cascada, 7 fallos) | Un fixture `autouse` marca como `rechazada` las devoluciones de cada prueba de error y `cantidad_excedida` lee lo disponible en ese momento | `tests/e2e/conftest.py`; [`pruebas/resultado_2026-10-21.md`](pruebas/resultado_2026-10-21.md) |
| La prueba de `devoluciones` elegia como "otro cliente" a `prueba@gmail.com`, una cuenta real sin la contrasena demo (401 al iniciar) | La prueba usa solo cuentas demo (PR #9) | [`pruebas/resultado_2026-10-21.md`](pruebas/resultado_2026-10-21.md) |
| Pruebas desactualizadas: esperaban solo la notificacion `autorizacion` y ahora tambien se inserta `autorizacion_logistica` para el Coordinador | Se acepta la segunda notificacion; el paso 6b verifica el reparto | [`pruebas/resultado_2026-10-21.md`](pruebas/resultado_2026-10-21.md) |
| La imagen de un servicio no se reconstruyo y corrio la prueba vieja | Reconstruir cada servicio cuyas pruebas cambian antes de correr su integracion | [`pruebas/resultado_2026-10-21.md`](pruebas/resultado_2026-10-21.md) |

### 17.3 Problemas abiertos

| # | Hallazgo | Impacto | Accion sugerida |
|---|---|---|---|
| 1 | ~~Posible conflicto de indices en MongoDB~~ **Descartado con evidencia real:** `getIndexes()` de `inspecciones` muestra `idx_devolucion` (no unico) y `uq_inspeccion_devolucion` (unico) sobre la misma llave, y la inspeccion se crea con 201 ([caso 092](evidencias/ejecuciones/inspecciones.md#092_inspecciones_post_raiz_201)) | Ninguno; hay un indice redundante | Opcional: quitar `idx_devolucion` en una migracion de Mongo (`mongodb.txt`) |
| 2 | Solo `devoluciones` publica eventos en `eventos` (la captura de Mongo filtra por `servicio: 'devoluciones'`) | La trazabilidad por `correlation_id` en Mongo no cubre el resto del flujo (la bitacora de PostgreSQL si) | Publicar eventos tambien desde los demas servicios o documentarlo como limite |
| 3 | `limitar` solo en `auth` y `devoluciones` | RNF-13 parcial | Aplicarlo a los demas servicios |
| 4 | `openapi.yaml` de cinco servicios sin ejemplos JSON/XML | El enunciado lo exige en Swagger | Agregar ejemplos |
| 5 | **Confirmado en la VM:** `docker compose ps` no muestra `(healthy)` en `app`, `logistica`, `inspecciones` ni `reembolsos-costos` ([`docker.txt`](evidencias/bases/docker.txt)); los cuatro responden 200 en `/health` | RNF-22 parcial en Compose | Agregar el bloque `healthcheck` a esos servicios |
| 6 | Todo en HTTP | Credenciales y tokens sin cifrar en la red | TLS en el tercer parcial |
| 7 | Base de datos compartida y `JWT_SECRET` simetrico en todos | Acoplamiento y radio de dano ante una fuga | Documentado como limite (apartados 7 y 11) |
| 8 | `README.md` describia solo el primer parcial | Documentacion desactualizada | Corregido en este mismo trabajo |
| 9 | Las fichas tenian cifras de pruebas y un endpoint que no coinciden con el codigo | Documentacion contradictoria | Corregido en este mismo trabajo |
| 10 | Josue Berdeal no aparece en el historial de git | La rubrica exige evidencia de los cuatro integrantes | Ver apartado 20 |
| 11 | Hallazgos de la suite sin corregir (H-01 a H-06, H-08 y H-10: etapas de evidencia inalcanzables, XSD de respuesta solo en `auth`, orden de validacion en logistica, notificaciones por API incompletas, entre otros) | Ver la severidad de cada uno | Tabla "Hallazgos" de [`PRUEBAS.md`](PRUEBAS.md) |

## 18. Matriz de trazabilidad y cumplimiento

La matriz vigente esta en [`TRAZABILIDAD.md`](TRAZABILIDAD.md): una fila por RF
(32), RNF (30) y RN (15), la lista de casos de uso, y una tabla de ampliacion
del segundo parcial que apunta a archivo y prueba. En este trabajo se
corrigieron contra el codigo RNF-13 (de pendiente a parcial), RNF-15 y RN-14
(de pendiente a parcial por los enlaces firmados HMAC), RNF-28, la cuenta de
XSD, el lugar de los triggers de RN-07 y los casos de uso UC-18 a UC-21 y UC-27.

Con la evidencia de la VM del 21 y 22 de octubre se ajustaron ademas: RNF-11
(de "sin prueba dedicada de XXE" a probado por E2E FMT-07), RNF-22 (de
implementado a parcial: cuatro servicios sin `healthcheck` en Compose) y
RNF-28 (con los resultados reales). RF-28, RF-29, UC-24 y UC-25 pasaron a
implementados al integrar la sesion 01.

Cumplimiento por rubro:

| Rubro | Estado |
|---|---|
| Microservicios (8) | Implementados y ejecutados en la VM: 238 casos de Newman, 767 verificaciones, 0 fallos ([apartado 13](#13-evidencias-requestresponse)) |
| Contratos JSON/XML/XSD | 22 XSD y 8 OpenAPI; XML real por servicio (apartado 10); faltan ejemplos en 5 `openapi.yaml` y capturas de Swagger |
| Web + PostgreSQL + MongoDB + Redis + JWT + Docker | Integrado y verificado en la VM (E2E 100/100, doce contenedores, nueve `/health` en 200); faltan capturas del web y del panel 8/8 |
| Pruebas | 119 unitarias, 34 de integracion y 100 E2E, todas en verde; faltan caidas de dependencias, concurrencia real, archivo mayor a 10 MB, carga y unitarias dentro de los contenedores |
| Documentacion | Este documento con evidencia real, 8 diagramas, trazabilidad, [`PRUEBAS.md`](PRUEBAS.md) y [`EVIDENCIAS.md`](EVIDENCIAS.md); faltan portada completa, aportacion de Josue y las capturas listadas en 19.3 |
| Aplicaciones movil y de escritorio | Fuera del alcance acordado (ver apartado 3) |

## 19. Conclusiones tecnicas y trabajo pendiente

### 19.1 Conclusiones

1. La separacion en ocho servicios con una libreria `shared/` comun permitio
   que seguridad, formato de errores, paginacion y negociacion JSON/XML se
   comportaran igual en todos, con pocas lineas por servicio.
2. Llevar las reglas criticas a triggers de PostgreSQL y a un lock de Redis
   hizo que RN-03, RN-04, RN-06 y RN-07 se cumplan aunque un servicio falle; el
   candado respondio 409 `reembolso_en_proceso` en la VM.
3. Se usan las tres bases con una razon cada una (transaccion, estructura
   variable y datos efimeros) y los enlaces entre ellas son por identificador,
   no por llave foranea (el `mongo_doc_id` de la inspeccion 21 apunta al
   documento de Mongo).
4. La decision de compartir la base de datos simplifico la integracion pero
   limita la independencia de los servicios.
5. La suite E2E encontro un bug de producto real (H-11, `Decimal` contra
   `float`) y un riesgo operativo (H-07, rate limit por IP) que el codigo por si
   solo no mostraba; ambos quedaron documentados y el primero corregido. Con la
   evidencia de la VM, lo que falta ya no es la ejecucion de los flujos sino las
   pruebas de caida, concurrencia y carga, y las capturas de pantalla.

### 19.2 Requerimientos no implementados o parciales

La justificacion se limita a lo que el repositorio o el documento del curso
permite afirmar.

| ID | Estado | Justificacion | Que falta |
|---|---|---|---|
| RF-02 | Pendiente | Sin implementar y sin una decision registrada en `BITACORA.md`; no bloquea el proceso principal porque el Administrador gestiona las cuentas (RF-03). Requiere definir un canal de entrega (correo) que el proyecto no tiene | Flujo de recuperacion con token de un solo uso |
| RF-14 | Pendiente | Requiere la aplicacion movil (escaneo de QR o codigo de barras), fuera del alcance acordado | App movil |
| RF-19 | Parcial | El codigo de etiqueta y el inventario existen (etiqueta `REC-2026-0081` en la VM); la **impresion** requiere la aplicacion de escritorio e impresora | Impresion de etiquetas |
| RN-14 / RNF-15 | Parcial | Hay enlaces firmados de 15 min sobre volumen local (probados en E2E-05 e INT-EVI-4); el almacenamiento en Google Cloud Storage esta planeado para el tercer parcial (`Entregables.md`) | Bucket de GCS y URLs firmadas del proveedor |
| RNF-13 | Parcial | Solo `auth` y `devoluciones` limitan peticiones (el 429 de `auth` pasa en E2E SEG-23) | Aplicarlo al resto y al web |
| RNF-14 | Parcial | Secretos fuera del codigo; falta cifrado de comunicaciones | HTTPS con proxy TLS |
| RNF-17 | Pendiente | El sistema opera para una sola organizacion; no hay separacion de tenants | Solo si el alcance lo requiere |
| RNF-20 | Pendiente | Hay una instancia por servicio; no se probo ni se configuro escalado horizontal | Balanceador y pruebas |
| RNF-21 | Parcial | El bloqueo sobrevive a Redis y `/health` degrada, pero no se probo la caida real de las dependencias | EV-22 |
| RNF-22 | Parcial | `/health` responde 200 en los nueve endpoints, pero `app`, `logistica`, `inspecciones` y `reembolsos-costos` no tienen `healthcheck` de Compose ([`docker.txt`](evidencias/bases/docker.txt)) | Bloque `healthcheck` en esos cuatro |
| RNF-24 | Pendiente | Respaldo y recuperacion pertenecen al tercer parcial (`Entregables.md`, "Recuperacion ante fallos") | Respaldos de volumenes y prueba de restauracion |
| RNF-28 | Parcial | E2E 100/100 e integracion 8/8 en la VM; 119 unitarias en verde. Faltan caidas de dependencias, concurrencia real, 413 y carga | EV-22, EV-23 y Locust |
| RNF-29 | Pendiente | Las pruebas de carga con Locust son del tercer parcial | Perfiles de Locust |

Otros pendientes del entregable del curso: aplicaciones Android y de
escritorio (fuera de alcance acordado), ejemplos en Swagger de cinco servicios,
healthchecks de Compose en cuatro, eventos de MongoDB en los demas servicios,
y la verificacion en la VM de la campanita desde un navegador (el paso 6b del
E2E ya la prueba por HTTP).

### 19.3 Evidencia pendiente

Lo que sigue sin existir en el repositorio. Quien la puede obtener es cualquier
integrante con acceso a la VM (la salida de la VM muestra la cuenta `pablogcp26`)
o a la consola de GCP; los comandos son sugeridos y se corren **en la VM**.
Despues se versionan por Pull Request (`docs/evidencias/capturas/` esta vacia).

| ID | Que falta | Quien | Comando o pantalla |
|---|---|---|---|
| EV-05 | Mismo `correlation_id` en dos servicios desde una accion del web | Quien tenga VM y navegador | Con el web en modo microservicios, autorizar una devolucion desde `http://<ip-vm>:8000`; tomar el `correlation_id` de la ultima fila de `bitacora` y buscarlo con `docker compose logs --since 10m devoluciones logistica \| grep <id>` |
| EV-22 | Caida de PostgreSQL, MongoDB y Redis | Quien tenga la VM | `docker compose stop postgres`, luego `curl -s localhost:8002/health` y una peticion de negocio; `docker compose start postgres`; repetir con `mongo` y `redis`; con `docker compose stop logistica`, abrir `/integracion/servicios` |
| EV-23 | Concurrencia y archivo mayor a 10 MB | Quien tenga la VM | Dos `curl -X POST .../reembolsos` lanzados con `&` y `wait` sobre la misma devolucion; `head -c 11000000 /dev/zero > grande.png` y subirlo por multipart a `:8007/api/v1/evidencias` (esperado: 413) |
| EV-26 | Panel `/integracion/servicios` con 8 de 8 | Quien tenga navegador | Entrar como Administrador a `http://<ip-vm>:8000/integracion/servicios` y capturar |
| EV-27 | Capturas del web: login con la insignia "API distribuida", panel de causas con Highcharts, bitacora | Quien tenga navegador | Pantallas del web en `http://<ip-vm>:8000` |
| EV-10 a EV-17 | Capturas de Swagger (`:8001/docs` a `:8008/docs`) | Quien tenga navegador | Abrir cada `/docs` y capturar; el checklist esta en [`evidencias/CHECKLIST_CAPTURAS.md`](evidencias/CHECKLIST_CAPTURAS.md) |
| 13.7 | Enlace firmado vencido | Quien tenga la VM | Pedir un enlace, esperar 15 min y descargarlo (esperado 401) |
| 13.8 | Pareto antes de sincronizar (409 `analisis_sin_datos`) | Quien tenga la VM | Solo con la coleccion de analisis vacia; si no se obtiene, queda cubierto por la prueba de division por cero |
| 13.3, 13.4 | Capturas de los casos que solo cubren la suite (devolucion no autorizada, cadena de frio, mas de 30 min, NaN) | Quien tenga la VM | Agregarlos a la coleccion de Postman de cada servicio |
| Portada | Matriculas y apellidos completos | Los cuatro integrantes | Los pide la portada oficial |
| Apartado 20 | Aportacion de Josue Berdeal y su evidencia en git | Josue Berdeal | Subir su trabajo a una rama `josue/...` y abrir Pull Request; este documento no le atribuye lo que git no muestra |

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
