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

---

## 2026-10-17 — MongoDB entra al entorno (segundo parcial)

**Contexto.** La entrada del 2026-09-06 dejo MongoDB declarado pero sin uso.
El segundo parcial exige operaciones reales sobre Mongo (insercion, consulta,
actualizacion, agregaciones e indices) y que todo se levante con Docker Compose.

**Decision.** Se agrega el contenedor `mongo` (imagen `mongo:7`) al compose,
con volumen `mongo_data`, healthcheck y puerto `127.0.0.1:57017`. El script
`db/mongo/init.js` crea la base, un usuario de aplicacion con permiso
`readWrite` solo sobre ella, las cuatro colecciones de la seccion 5.4 y sus
indices.

**Por que.**
- El puerto sigue el mismo criterio que Postgres (55432) y Redis (56379):
  solo accesible desde la VM y con prefijo 5 para no chocar con servicios
  nativos.
- Los servicios no usan el usuario administrador del motor: si una credencial
  se filtra, solo compromete la base del proyecto (RNF-14).
- Las colecciones e indices se crean por script para que el entorno sea
  reproducible sin pasos manuales (RNF-27).
- La app del monolito no declara `depends_on: mongo` porque todavia no lo usa;
  asi una falla de Mongo no impide arrancar el sistema web.

**Cuidado.** `init.js` solo corre cuando el volumen esta vacio. Si se modifica
despues, hay que aplicar el cambio a mano o recrear el volumen con
`docker compose down` y `docker volume rm proyecto12_mongo_data` (se pierden los
datos de Mongo).

---

## 2026-10-17 — El seed de demostracion usaba una etapa de costo eliminada

**Contexto.** La migracion 009 renombro la etapa de costo `recoleccion` a
`transporte` y cambio el CHECK de `costos.etapa`. `scripts/seed_demo.py`
siguio insertando `'recoleccion'`. En la VM del equipo no se noto porque el
seed se habia corrido antes de la 009 y el `UPDATE` de esa migracion
reclasifico los datos. En una base nueva, el seed fallaba con
`costos_etapa_check`.

**Decision.** El seed inserta `'transporte'`.

**Por que.** El entorno debe poder levantarse desde cero siguiendo
`docs/SETUP.md` (RNF-27); con el error, nadie podia reconstruir los datos de
demostracion en una base limpia.

---

## 2026-10-17 — Servicio auth y carpeta shared/ comun a los microservicios

**Decision.** Se crea `services/auth` (Flask, puerto 8001) y la carpeta
`shared/`, que cada microservicio copia en su imagen. `shared/` concentra lo
que todos deben hacer igual: formato JSON/XML segun `Accept`, formato de error,
correlation id, registro de actividad, validacion de JWT y rate limiting.

**Por que Flask y no otro framework.** Mantiene el stack fijo del proyecto y
permite reutilizar el codigo del monolito (consultas SQL, bloqueo por intentos).
Swagger UI se sirve desde CDN sobre un `openapi.yaml` escrito a mano, asi que
la unica dependencia nueva es PyJWT (mas PyYAML para leer el contrato).

**Sesion ademas del JWT.** Cada login crea `devoluciones:sesion_api:<sid>` en
Redis y el `sid` viaja dentro del token. Los servicios aceptan un token solo si
su sesion existe y su `jti` no esta en `devoluciones:jwt_revocado:`. Asi:
- logout revoca el token actual y borra la sesion (mata tambien el refresh);
- el administrador puede cerrar todas las sesiones de un usuario (RNF-08);
- si Redis no responde, se niega el acceso (falla cerrada).

**423 para cuenta bloqueada.** Se distingue del 401 de credenciales y del 429
de rate limiting para que el cliente sepa que esperar no es lo mismo que
reintentar.

---

## 2026-10-18 — Correcciones de shared/ y modulos comunes de MongoDB y paginacion

**Correcciones.**
- `ip_origen()` ya no lee `X-Forwarded-For`. No hay proxy delante de los
  servicios, asi que ese header lo escribe el cliente: mandando un valor
  distinto en cada peticion se evitaba el rate limit (RNF-13). Verificado en la
  VM: con 12 IPs falsas, la peticion 11 recibe 429.
- Un error 500 ya no confirma la transaccion. El manejador de errores atrapa la
  excepcion, por lo que el teardown la recibia como `exc=None` y hacia commit
  de cambios a medias. Ahora `respuestas.py` marca `g.error_interno` y
  `cerrar_conexion` hace rollback.
- `/health` ya no devuelve el texto de la excepcion (host, usuario de la base);
  el detalle va al log del contenedor (RNF-16).

**Modulos nuevos.**
- `shared/mongo.py`: conexion con el usuario de minimo privilegio, conversion
  de documentos a JSON/XML, `registrar_evento()` sobre la coleccion `eventos`
  con correlation_id (RNF-23) y `salud_mongo()`. Va en archivo aparte para que
  los servicios sin MongoDB no instalen `pymongo`.
- `shared/paginacion.py`: contrato unico `?pagina=&por_pagina=` y bloque
  `paginacion` en la respuesta, igual en JSON y XML.

**Dependencia nueva.** `pymongo==4.8.0`, solo en los servicios que usan
MongoDB. Es el driver oficial; sin el no hay forma de cumplir la seccion 7 del
segundo parcial (uso real de MongoDB).

---

## 2026-10-18 — Contratos XSD y validacion de los cuerpos XML

**Decision.** Cada servicio guarda sus esquemas en `services/<servicio>/contratos/`
y el del error estandar vive en `shared/contratos/error.xsd`. Los cuerpos XML
se validan con `leer_cuerpo(xsd=...)` antes de procesarse; si no cumplen, la
respuesta es `400 xml_no_cumple_xsd` con la linea y el problema. Cada servicio
publica sus esquemas en `GET /contratos/<nombre>.xsd` y Swagger los enlaza.

**Por que.** La seccion 6 del parcial pide esquemas XSD y demostrar la
recepcion de XML; un XSD que nadie usa no demuestra nada. Las pruebas de auth
validan tambien las respuestas generadas contra su esquema.

**Detalles.**
- Se usa `xs:all`: los campos pueden llegar en cualquier orden.
- Sin espacio de nombres: los documentos son autocontenidos y el elemento raiz
  identifica el mensaje.
- Dependencia nueva `lxml==5.3.0`, solo en los servicios con contratos XSD: la
  biblioteca estandar no valida esquemas. El parser no resuelve entidades ni
  accede a la red (proteccion contra XXE).

---

## 2026-10-18 — Microservicio de devoluciones

**Decision.** `services/devoluciones` (puerto 8002) expone el registro y la
resolucion de devoluciones con las mismas reglas del monolito: POST para
registrar, GET para listar (filtros y paginacion) y consultar, PUT para que el
cliente corrija cuando le piden informacion, PATCH para la resolucion del
analista y DELETE para cancelar.

**Por que estas reglas.**
- La linea de venta y la devolucion se bloquean con `SELECT ... FOR UPDATE`:
  sin eso, dos solicitudes simultaneas podian devolver mas de lo comprado, o
  dos analistas resolver la misma devolucion.
- Un cliente que pide una devolucion ajena recibe 403 y queda en la bitacora
  (`acceso_denegado`), igual que en la web.
- DELETE es eliminacion logica (`eliminado_en`, RNF-30) y solo procede si
  ningun analista la ha revisado.
- Al resolver se inserta en `notificaciones` (RF-29), tabla que existia sin uso.
- Cada operacion publica un evento en MongoDB (`eventos`). El servicio crea el
  indice `idx_devolucion_fecha` (create_index es idempotente) porque init.js
  solo indexa correlation_id y fecha.

**Fechas en las respuestas.** `shared/respuestas.py` convierte fechas a ISO 8601
y NUMERIC a numero antes de responder; jsonify usaba el formato RFC 822.

**Pruebas.** Unitarias (reglas y API con Redis en memoria) y de integracion
(`tests/test_integracion.py`): obtienen el token del contenedor auth por HTTP,
operan contra PostgreSQL, MongoDB y Redis reales, y comprueban que un logout en
auth revoca el token en devoluciones. Borran lo que crean al terminar.

## Integracion de ramas a main (21 de octubre de 2026)

**Orden.** Las ramas `david/base-microservicios`, `david/servicio-devoluciones`
y `roberto/integracion-web-microservicios` estaban apiladas (cada una contiene
a la anterior), asi que entran a `main` con un solo Pull Request y merge commit,
sin squash: el historial conserva la autoria de cada integrante (evidencia del
parcial).

**Estructura.** Se mantiene `app/` en la raiz durante la integracion para no
mezclar un movimiento de carpetas con el primer despliegue conjunto en la VM.
La reorganizacion del monorepo (`apps/web`, `docs/enunciado`, `docs/postman`)
va en un PR posterior, una vez validado el despliegue.

**Contingencia.** `USE_MICROSERVICES=false` devuelve el web al modo monolito sin
tocar codigo.

## Reorganizacion del monorepo (21 de octubre de 2026)

Con la integracion validada en la VM (9 `/health` en 200, 8/8 servicios en el
panel), se ordeno el repositorio con `git mv` para conservar el historial:

- `app/`, `wsgi.py`, `requirements.txt` y `docker/Dockerfile` pasan a `apps/web/`.
  El paquete sigue llamandose `app`, asi que ningun `import` cambia. Deja
  `apps/` listo para las aplicaciones Android y de escritorio del tercer parcial.
- Los PDF y los `.md` del enunciado pasan a `docs/enunciado/`; `postman/` pasa a
  `docs/postman/`.
- El contenedor `app` conserva el contexto de build en la raiz y el bind mount
  `./:/srv/app`, porque `scripts/migrate.py` y `db/` se ejecutan desde ahi; gunicorn
  arranca con `--chdir apps/web`.
- Las migraciones no se tocaron (checksums intactos).

## Diagramas en Mermaid dentro del repositorio (21 de octubre de 2026)

**Decision.** Los ocho diagramas del segundo parcial (componentes, despliegue,
dos secuencias, comunicacion web-servicios, PostgreSQL, MongoDB y Redis) se
escriben como bloques Mermaid en `docs/diagramas/*.md` y el documento tecnico
(`docs/DOCUMENTO_TECNICO.md`) los enlaza.

**Por que.**
- GitHub renderiza Mermaid, asi que el diagrama se ve en el repositorio sin
  herramientas externas, y el historial de versiones muestra quien lo cambio y
  cuando.
- Es texto: se revisa en un Pull Request y se corrige junto con el codigo que
  describe, en lugar de quedar como una imagen que nadie reabre.
- Cada diagrama se redacto leyendo `docker-compose.yml`, las migraciones y los
  `app.py`, no de memoria. Esa verificacion detecto que las fichas de
  microservicios mencionaban un `GET /devoluciones/{id}/historial` que no existe,
  que RNF-13 estaba marcado pendiente pese a que `shared/infra.py:limitar` se
  usa en `auth` y `devoluciones`, y que solo `devoluciones` publica eventos en la
  coleccion `eventos` de MongoDB.

**Costo aceptado.** Mermaid tiene limites de maquetacion (un ER grande se
reparte en varios bloques) y la sintaxis de cada bloque se valido con el
analizador de Mermaid 10.9.1, no renderizado en GitHub. Si un bloque no se ve
en GitHub, la causa mas probable es la version del renderizador.


## Notificaciones por rol: campanita, sondeo y matriz de destinatarios (21 de octubre de 2026)

**Contexto.** Solo `services/devoluciones` y `services/reembolsos_costos`
insertaban en `notificaciones` y ninguna pantalla las mostraba (RF-29 parcial).

**Decision.** Una funcion unica, `notificar_evento` en `apps/web/app/notificaciones.py`,
con un catalogo `EVENTOS` (evento -> avisos con destinatario, tipo, texto y
pantalla destino). Los blueprints la llaman en la misma peticion que cambia el
estado, asi la notificacion y el cambio se confirman o revierten juntos. La
migracion 013 agrega `notificaciones.url` y el indice de bandeja.

**Sondeo y no push.** La campanita consulta `GET /notificaciones/resumen` cada
30 s (y al volver a la pestana). Se descarto WebSocket/SSE: con tres workers de
gunicorn las conexiones abiertas ocupan workers, exigirian una libreria nueva
(CLAUDE.md pide acordarlas) y para un contador de avisos 30 s es suficiente.

**Matriz de destinatarios.** Sigue el flujo real de estados sin inventar nuevos:
el aviso va a quien debe actuar despues (analista tras la solicitud; coordinador
tras autorizar; inspector tras la recepcion; analista tras la inspeccion;
encargado de reembolsos tras la disposicion) y el cliente recibe los cambios de
su caso. Quien ejecuta la accion no se notifica. Si un rol no tiene usuarios
activos, el aviso se omite y queda `notificacion_omitida` en bitacora. El
Administrador no recibe avisos de flujo.

**Web y microservicios sin duplicados.** Con `USE_MICROSERVICES=true`, resolver
y reembolsar ya notifican al cliente desde el servicio, asi que el web no repite
esos avisos (`omitir_cliente`); el servicio de devoluciones ahora tambien avisa
al Coordinador al autorizar y guarda el enlace. `reembolsos_costos` no se toco:
su aviso al cliente queda sin `url` y la campanita cae al expediente. Tipos y
textos son los mismos en ambos lados.

**Pruebas.** `apps/web/app/tests/test_notificaciones.py` con dobles de BD
(`tests/dobles.py`): ownership, destinatarios por rol y bandeja. Lo que necesita
PostgreSQL se verifica en la VM.

## Exportacion CSV de reportes (21 de octubre de 2026)

**Decision.** Un blueprint `reportes` (`/reportes/*.csv`) junto a la libreria
`app/exportacion.py`, solo con el modulo `csv` de la libreria estandar (sin
dependencias nuevas). Cada ruta repite el `@roles_required` y los filtros de la
pantalla de origen; el Pareto reutiliza `panel.sql_pareto` (antes inline en
`panel.causas`) para que archivo y pantalla no puedan diferir.

**Por que asi.**
- *Streaming:* cursor nombrado de psycopg2 (`itersize` 500) y respuesta por
  bloques; el archivo no se arma en memoria. Tope de 50,000 filas
  (`EXPORT_MAX_FILAS`) para no saturar la base compartida.
- *Bitacora antes del stream:* `registrar_bitacora` y un `commit()` explicito
  ocurren antes de empezar a enviar, porque la transaccion de la peticion
  termina despues de que acaba el generador y una descarga cortada no debe
  perder la auditoria.
- *Inyeccion de formulas:* las celdas de texto que empiezan con `= + - @`, tab o
  retorno se prefijan con `'`. Los numeros se dejan intactos (un monto negativo
  no es una formula).
- *Devoluciones:* el listado de pantalla usa la API cuando `USE_MICROSERVICES`
  esta activo, pero la exportacion lee directo de PostgreSQL (como ya hacen
  costos, bitacora y reembolsos) para poder recorrer mas de 100 filas; el
  cliente sigue restringido a sus casos.
- La version HTML imprimible para PDF queda fuera de esta entrega.

**Pruebas.** `test_exportacion.py`: BOM, escape de formulas, bloques, filtros
como parametros ligados, 403 por rol y bitacora sin datos sensibles. El
streaming real con cursor nombrado solo se puede comprobar en la VM.
