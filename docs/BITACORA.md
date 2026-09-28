# Bitacora de decisiones tecnicas

Registro de las decisiones que no son evidentes leyendo el codigo. Si tomas una
decision que otro integrante podria cuestionar dentro de un mes, escribela aqui.

---

## 2026-09-06 — Se agrego `venta_detalle`

**Contexto.** La seccion 5.1 del documento dice que la devolucion se vincula al
detalle especifico de una venta, pero el esquema original tenia `lote_id`,
`cantidad` y `precio` directamente en `ventas`, de modo que una venta solo podia
tener un producto.

**Decision.** Se creo `venta_detalle` y `devoluciones.venta_id` se sustituyo por
`venta_detalle_id` (migracion 002).

**Por que.** Una compra real lleva varios articulos y el cliente devuelve uno.
Con el modelo anterior no habia forma de representarlo, y el documento ya
prometia esa capacidad. Ademas permite calcular el valor exacto de lo devuelto,
que es la base de la validacion antifraude del reembolso.

---

## 2026-09-06 — Las reglas criticas viven en triggers, no solo en el codigo

**Decision.** RN-04, RN-06, RN-07 y el limite del monto del reembolso se
implementan como triggers de PostgreSQL, ademas de validarse en los formularios.

**Por que.** En el segundo parcial varios microservicios escribiran sobre las
mismas tablas. Una regla que vive solo en el codigo de la aplicacion web se
rompe en cuanto otro servicio escribe sin ella. En la base de datos se cumple
siempre. Tambien sirve para la demostracion: se puede ensenar que la regla
aguanta aunque se manipule la peticion.

**Costo aceptado.** Los mensajes de error de los triggers llegan a la interfaz
como excepciones de psycopg2 y hay que traducirlos. Se resolvio capturando
`psycopg2.errors.RaiseException` y mostrando el texto del trigger, que por eso
esta redactado para que un usuario lo entienda.

---

## 2026-09-06 — El bloqueo de cuenta se guarda en Redis y en PostgreSQL

**Decision.** El conteo de intentos vive en Redis con expiracion; el momento
hasta el que la cuenta esta bloqueada se guarda ademas en
`usuarios.bloqueado_hasta`, y el historial completo en `intentos_acceso`.

**Por que.** Redis solo habria sido mas simple, pero reiniciar el contenedor
levantaria todos los bloqueos. Postgres solo habria significado escribir en la
tabla en cada intento fallido, incluido un ataque de fuerza bruta. La
combinacion cubre RNF-12 y RNF-21 sin castigar el rendimiento.

---

## 2026-09-06 — Sin ORM

**Decision.** Se usa `psycopg2` con SQL escrito a mano y parametros ligados.

**Por que.** El esquema ya estaba disenado y documentado en SQL, con triggers y
restricciones que un ORM tiende a esconder. Escribir el SQL directamente hace
visible en el codigo lo mismo que se entrega en el documento. La proteccion
contra inyeccion (RNF-11) se garantiza usando siempre parametros ligados, nunca
concatenacion.

**Riesgo.** En `catalogos.py` los nombres de tabla si se interpolan en la
consulta. Se controla con una lista blanca: los nombres salen del diccionario
`CATALOGOS` del propio modulo, nunca de la peticion.

---

## 2026-09-06 — El folio se genera con una secuencia

**Decision.** `fn_nuevo_folio_devolucion()` usa `nextval` sobre una secuencia
(migracion 007) en lugar de contar las filas existentes.

**Por que.** Contar filas produce folios duplicados en cuanto dos usuarios
registran una devolucion al mismo tiempo, lo que violaria RN-02 y ademas
contradice RNF-19.

---

## 2026-09-06 — MongoDB queda declarado pero sin uso

**Decision.** El diseno contempla MongoDB para el detalle de la inspeccion, la
columna `inspecciones_ref.mongo_doc_id` existe, pero en esta entrega queda en
NULL y el detalle se guarda como evidencia de tipo comentario.

**Por que.** La demostracion del primer parcial exige almacenamiento en
PostgreSQL, no en Mongo. Agregar un tercer motor ahora sumaba superficie de
falla sin sumar puntos. La columna ya existe, asi que habilitarlo en el segundo
parcial no requiere migrar datos.

---

## 2026-09-06 — Los puertos de Postgres y Redis se publican en 55432 y 56379

**Contexto.** La VM de GCP ya tenia un PostgreSQL instalado de forma nativa,
escuchando en `127.0.0.1:5432`, y el contenedor no podia arrancar porque el
puerto estaba ocupado.

**Decision.** Se movio el mapeo del host a `55432` para PostgreSQL y `56379`
para Redis, en lugar de apagar el servicio nativo.

**Por que.** No se sabe si ese PostgreSQL nativo lo usa alguien mas o alguna
practica anterior de la materia, y apagarlo era un riesgo innecesario. La
aplicacion no se ve afectada: se conecta por la red interna de Docker al nombre
`postgres`, no por el puerto del host. Ese mapeo solo sirve para conectarse con
un cliente desde la propia VM.

**Cuidado.** Al conectarte con `psql` desde la VM hay dos bases distintas. La
del proyecto es la del contenedor. Para entrar a la correcta, usa siempre:

```bash
docker compose exec postgres psql -U devoluciones_app -d devoluciones
```

Si usas `psql` directo sin `docker compose exec`, estaras hablando con el
PostgreSQL nativo, que no tiene nada de este proyecto.

---

## 2026-09-06 — El montaje del codigo lleva la etiqueta `:z` por SELinux

**Contexto.** CentOS Stream 10 corre SELinux en modo `Enforcing`. Sin etiqueta,
el contenedor no puede leer el directorio del proyecto montado en `/srv/app`.

**Decision.** Se agrego `:z` al montaje en `docker-compose.yml`.

**Por que.** Es la solucion correcta: reetiqueta el directorio para que el
contenedor pueda accederlo, sin desactivar SELinux en la maquina. Desactivar
SELinux habria sido mas rapido pero deja la VM menos protegida, y el proyecto
tiene requisitos de seguridad explicitos (RNF-14).

---

## 2026-09-06 — La contrasena de demostracion sale del repositorio

**Contexto.** El repositorio es publico y `scripts/seed_demo.py` traia la
contrasena escrita en el codigo, ademas de repetirla en `docs/SETUP.md`.
Cualquiera que encontrara la IP de la VM y leyera el repositorio podia entrar
como administrador.

**Decision.** La contrasena se toma de `PASSWORD_DEMO` en el `.env`, que esta
fuera de git. Si la variable esta vacia, el script genera una al azar y la
imprime una sola vez. Se agrego `--rotar` para cambiarla en las cuentas que ya
existen sin volver a sembrar los datos.

**Por que.** Permite compartir la liga de la aplicacion con quien sea sin
regalar el acceso, y deja el repositorio limpio de credenciales (RNF-14,
RNF-16). La contrasena anterior debe considerarse comprometida: quedo en el
historial de git, que es publico y no se reescribe.

**Pendiente.** La aplicacion sirve por HTTP sin cifrar. Si se abre a todo
internet, las credenciales viajan en claro. El cifrado de comunicaciones se
resuelve al poner la plataforma detras de un proxy con TLS en el tercer parcial.

---

## 2026-09-27 — Costo total por devolucion: vista, no columna calculada

**Contexto.** La retroalimentacion del profesor sobre el primer parcial senalo
que el analisis de causa raiz es debil porque no muestra impacto economico:
solo `reembolsos.py` insertaba en `costos` (etapa `reembolso`); transporte,
inspeccion, almacenamiento, reacondicionamiento y destruccion nunca generaban
un registro, asi que el "costo total de la devolucion" no se podia calcular.

**Decision.** Se amplio el enum de `costos.etapa` (migracion 009) y se agrego
la captura del monto en cada modulo que ya conoce ese costo: `logistica.py`
(transporte al completar la recoleccion, almacenamiento al recibir),
`inspecciones.py` (inspeccion al registrar, reacondicionamiento/destruccion al
decidir la disposicion) y una ruta manual en `devoluciones.py` para "otros"
costos no previstos. El total se expone con `vista_costo_devolucion`
(migracion 010), una vista de solo lectura sobre `costos`, en vez de una
columna en `devoluciones` que hubiera que mantener sincronizada a mano.

**Por que.** Una columna calculada dependeria de datos que viven en otra
tabla (`costos`), no de la llave primaria de `devoluciones`: es exactamente el
tipo de dependencia que rompe la normalizacion y que se desincroniza en cuanto
alguien inserta un costo sin acordarse de actualizarla. La vista siempre lee
el dato vivo sin duplicarlo.

**Relacionado.** Se aprovecho el mismo cambio para agregar el destino
`donacion` a `disposiciones` (migracion 011), que la retroalimentacion pide
explicitamente y que faltaba en el catalogo.

---

## 2026-09-27 — RF-24 (ranking de causas) se adelanta al monolito

**Contexto.** `docs/TRAZABILIDAD.md` marcaba RF-24 como pendiente del
microservicio de causa raiz (segundo/tercer parcial), y `panel/causas.html`
decia textualmente que el Pareto se implementaria ahi. La retroalimentacion
del primer parcial exige que el monolito ya cruce
venta-producto-lote-proveedor-tienda-ruta-transportista-motivo y muestre
Pareto de causas dentro de las proximas dos semanas.

**Decision.** RF-23, RF-24 y RF-26 se completan en el monolito ahora, no se
esperan al microservicio. Ver bloque 2 del plan de correccion (analisis de
causa raiz en `panel.causas`).

**Por que.** Es una instruccion directa de la retroalimentacion sobre esta
entrega, no una preferencia del equipo. El cruce se resuelve por completo con
`JOIN` sobre tablas ya existentes (`recolecciones` ya tiene `ruta_id` y
`transportista_id`, `ventas` ya tiene `tienda_id`), asi que no requiere mover
la logica a un servicio nuevo para cumplirla.

---

## 2026-09-27 — fecha_cierre se llena en dos lugares, no solo en cambiar_estado

**Contexto.** El KPI de tiempo de resolucion (migracion 012) necesita
`devoluciones.fecha_cierre` poblada cada vez que el expediente llega a
`cerrada` o `rechazada`. La mayoria de las transiciones de estado pasan por
`devoluciones.py:cambiar_estado`, pero el rechazo inicial de una solicitud
(`devoluciones.resolver`, decision "rechazar") actualiza `estado` y
`analista_id` en el mismo `UPDATE`, sin pasar por esa funcion.

**Decision.** `cambiar_estado` llena `fecha_cierre` cuando el nuevo estado
esta en `ESTADOS_TERMINALES`, y el `UPDATE` de `resolver` para "rechazar" la
llena directamente en la misma sentencia.

**Por que.** Si solo se hubiera tocado `cambiar_estado`, cualquier devolucion
rechazada en la primera revision (el camino mas comun de rechazo) habria
quedado con `fecha_cierre` en NULL para siempre, y el KPI de tiempo de
resolucion la habria ignorado silenciosamente sin que nadie lo notara.
