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
