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

## Suite E2E y casos de prueba (21 de octubre de 2026)

- **Decision.** La suite E2E vive en `tests/e2e/` (raiz) y corre dentro de la imagen de
  `devoluciones` con el repositorio montado en `/repo`; asi usa `shared/` y los XSD sin
  agregar una imagen ni librerias. Las pruebas de integracion por servicio viven en cada
  `services/<x>/tests/` y se corren en su propia imagen, por eso repiten un poco de codigo.
- **Por que.** Las bases solo existen en la VM; la suite se escribe y se valida aqui
  (compilacion, `--collect-only`, unitarias) y se ejecuta alla.
- **Detalles que otro deberia saber.** El rate limit de login es de 10 por minuto por IP:
  la suite borra las claves `devoluciones:limite:*:login` antes de cada bloque de logins
  y la prueba de 429 va al final. La evidencia del cliente va antes de autorizar porque
  `evidencias` no deja adjuntar despues. RNF-28 queda `parcial` hasta pegar la salida de
  la VM en `docs/pruebas/` (ver `docs/PRUEBAS.md`).

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

## Colecciones Postman y evidencias desde una sola especificacion (21 de octubre de 2026)

**Decision.** Las 8 colecciones, el environment, `docs/EVIDENCIAS.md` y el checklist
de capturas se generan con `docs/postman/generar_colecciones.py` a partir de
`docs/postman/especificaciones.py`. Reemplaza a `generar_devoluciones.py`.

**Por que asi.**
- *Una sola fuente:* el id de captura (`NNN_servicio_metodo_endpoint_codigo`) aparece
  en Postman, en `EVIDENCIAS.md` y en el checklist; escribirlos a mano los haria
  divergir.
- *Sin PyYAML:* la VM y las laptops no instalan nada para regenerar. Por eso el
  generador no parsea `openapi.yaml`: los casos estan en codigo y el generador solo
  **compara** con regex las rutas y metodos de cada `openapi.yaml` y avisa si falta
  un endpoint o sobra un caso (termina con codigo 1).
- *Cada coleccion inicia sesion con sus roles:* asi corre sola. Los ids que pasan
  de una coleccion a otra (`devolucion_id`, `ruta_id`, ...) viajan por el
  environment, no por variables de coleccion. A cambio, el login (10 por minuto
  por IP, RNF-13) obliga a esperar entre colecciones.
- *Evidencias crea y cancela su propia devolucion:* el cliente solo adjunta
  mientras la devolucion esta en solicitud o revision, y el flujo principal ya la
  autorizo.
- *Casos de bloqueo y limite repiten la peticion* (`setNextRequest`) hasta ver 423
  o 429; usan `email_bloqueo` (Sofia) para no bloquear a los usuarios del resto.

**Que no es.** Ninguna respuesta de `EVIDENCIAS.md` fue ejecutada. Los codigos y
`error.tipo` salieron de leer `services/*/app.py`; los cuerpos XML se validaron
con `xmllint` contra los XSD, pero la corrida real es en la VM. Si una peticion
falla ahi, lo correcto es revisar si cambio el servicio y corregir
`especificaciones.py`.

---

## 2026-11-09 — Roles de la aplicacion Android (tercer parcial)

**Decision.** La migracion 014 agrega `Recolector`, `Operador de Almacen` y
`Supervisor`, los perfiles que la retroalimentacion del segundo parcial pide para
la app Android (recoleccion, recepcion en almacen y supervision de incidencias).
Se declaran en `shared/seguridad.py` y en `apps/web/app/security.py`, y
`seed_demo.py` crea una cuenta de demostracion para cada uno.

**Por que no entran en `TODOS_LOS_ROLES` de la web.** Ese grupo abre ventas,
devoluciones, reportes y el panel completo. Agregarlos ahi le daria a un
recolector acceso a todos los expedientes, contra el minimo privilegio (RN-13).
Su canal es la app Android; si una vista web los necesita, debe nombrarlos
explicitamente. Hoy, si entran a la web, ven la pagina de "No tienes permiso".

**Por que no cambian permisos existentes.** En los microservicios cada endpoint
lista sus roles en `@requiere_jwt(...)`. Ninguno los acepta por omision: cada
servicio debe autorizarlos de forma explicita donde corresponda.

**Nombres sin "o transportista".** El documento habla de "recolector o
transportista"; se uso `Recolector` para cubrir ambos, porque el nombre del rol
viaja en cada JWT y se compara textualmente.

---

## 2026-11-10 — Control por sucursal y operaciones criticas

**Correccion de la entrada anterior.** El 2026-11-09 se escribio que ningun
endpoint aceptaba los roles de campo por omision. No era cierto: los 11
endpoints con `@requiere_jwt()` sin roles aceptaban a cualquier usuario
autenticado, asi que un recolector podia listar todas las devoluciones, ventas y
evidencias. Ahora `requiere_jwt()` sin roles acepta solo `ROLES_BASE` (los 7
originales); los roles nuevos deben nombrarse. Auth abre `/sesion`, `/logout` y
`/autorizar-operacion` a `TODOS_LOS_ROLES`, porque cualquiera debe poder cerrar
su sesion. En devoluciones, el listado y el detalle admiten ademas al Supervisor
y al Operador de Almacen; el Recolector no (ve sus tareas en logistica).

**Sucursal (migracion 015).** `usuarios.tienda_id` es nullable: NULL = opera en
todas. Auth la copia al claim `tienda_id` (tambien en el refresh) y
`shared/seguridad.py` ofrece `condicion_tienda` para listados y `exigir_tienda`
para un registro. La sucursal de una devolucion es la de su venta. Se aplica en
devoluciones como ejemplo para el resto de servicios.

**Operaciones criticas.** `POST /api/v1/auth/autorizar-operacion` pide de nuevo
la contrasena y emite un JWT de tipo `operacion` ligado a la operacion, al
registro y a la sesion, valido 5 minutos. Su `jti` se guarda en Redis
(`devoluciones:operacion_autorizada:<jti>`) y `exigir_autorizacion_operacion` lo
borra al usarlo. Se eligio reconfirmar la contrasena (como el NIP de una
transferencia) porque protege ante una sesion abierta y desatendida, y el
consumo atomico con `DELETE` evita ademas dobles aprobaciones simultaneas.

**Por que el permiso se consume antes de escribir.** Si la operacion falla
despues (por ejemplo, un 409 de negocio), el usuario debe reconfirmar. Se
prefirio eso a dejar un permiso reutilizable: el costo es una contrasena mas,
el beneficio es que nunca hay dos usos del mismo permiso.

**Contrasena incorrecta.** Cuenta como intento fallido para el bloqueo de la
cuenta (RNF-12), igual que en el login.

---

## 2026-11-10 — Plazo de devolucion y solicitudes duplicadas (RN-16)

**Decision.** Se agrega la regla de negocio RN-16, que el documento no tenia:
una devolucion se puede solicitar hasta 30 dias naturales despues de la venta si
el producto no es refrigerado, y hasta 7 si es refrigerado; el ultimo dia todavia
se acepta. Ademas, no puede haber dos solicitudes abiertas (no rechazadas ni
cerradas) con la misma linea de venta y el mismo motivo: la segunda responde
`409 solicitud_duplicada` y para cambiar la primera se usa PUT.

**Por que en una tabla y no en el `.env`.** La retroalimentacion pide que las
decisiones respondan a politicas formalmente definidas y que el modo monolitico y
el distribuido no apliquen reglas distintas. `politicas_devolucion` (migracion
016) es la unica fuente del plazo: la leen el servicio de devoluciones y la web.

**Por que no un trigger.** El seed y las pruebas siembran devoluciones historicas
sobre ventas de agosto; un trigger con `CURRENT_DATE` las rechazaria. La regla se
aplica donde nace una solicitud nueva: la API y el formulario de la web.

**Datos de demostracion.** Las ventas de agosto quedan fuera de plazo y sirven
para demostrar el 409. `seed_demo.py` agrega cada dia que se corre seis ventas
recientes (de hoy a hace 6 dias). Hay que correrlo el dia de la demostracion.

**Pruebas del equipo afectadas.** La suite E2E y las pruebas de integracion de
devoluciones eligen ahora una linea dentro del plazo, y cada registro usa un
motivo sin otra solicitud abierta en esa linea (`flujo.motivo_libre`).

**Elegibilidad.** `GET /api/v1/devoluciones/elegibilidad` responde, sin escribir,
si una linea se puede devolver, hasta cuando, cuantas unidades y que solicitudes
siguen abiertas; la app Android lo usa para mostrar las condiciones antes de la
solicitud.

## 2026-11-10 — Servicio de sincronizacion offline (dominio 20, puerto 8020)

**Que hace.** Las apps Android y de escritorio guardan operaciones mientras no
hay red y las mandan a `POST /api/v1/sincronizacion/operaciones` cuando vuelve.
Se aceptan sin conexion: avance de una recoleccion (Recolector, Coordinador),
recepcion en el centro (Operador de Almacen, Encargado del Centro) y evidencias
de esas dos etapas (comentario o foto). La respuesta trae un resultado por
operacion: `aceptada`, `conflicto`, `rechazada` o `reintentar`.

**Sin duplicados.** Cada operacion trae un `id_operacion` (UUID) que genera el
dispositivo al capturarla y que reutiliza en cada reintento. Es la llave primaria
de `operaciones_offline` (migracion 017): si la misma operacion llega otra vez,
se responde el resultado guardado con `repetida: true` y no se aplica. La fila y
el efecto se guardan en la misma transaccion, y la transaccion se confirma antes
de responder. Dos envios simultaneos del mismo id: PostgreSQL hace esperar al
segundo en la llave primaria y solo uno se aplica (probado con dos hilos). Si un
id llega con otros datos se rechaza con `id_reutilizado`.

**Conflictos.** El dispositivo manda el estado que vio (`estado_esperado`). Si el
servidor cambio mientras estaba sin red (por ejemplo, el coordinador marco la
recoleccion como fallida), la operacion queda en `conflicto` con el estado del
servidor y no se aplica. Un 409 de negocio es conflicto; cualquier otro error es
rechazo. Ambos se guardan: el reintento recibe la misma respuesta.

**Lo que nunca es offline.** Autorizar, programar recoleccion, reembolsos,
disposiciones, reincorporar inventario y cerrar investigaciones se rechazan con
`requiere_conexion`: deben comprobar permisos y estado en el momento.

**Evidencias seguras.** La foto viaja en base64 con su SHA-256; si no coincide se
rechaza con `archivo_corrupto`. Se guarda en el mismo volumen privado y con el
mismo formato que el servicio de evidencias, y los metadatos en MongoDB llevan
el `id_operacion` como llave para no duplicarse.

**Otros controles.** Captura de hace mas de 7 dias o con fecha en el futuro: se
rechaza. La sucursal del usuario se respeta (`fuera_de_sucursal`). La recepcion
guarda como fecha la de la captura, no la de la sincronizacion. GPS opcional en
el avance de la recoleccion; queda en la bitacora.

**Cambio en `shared/infra.py`.** Nueva funcion `confirmar()`: hace el commit antes
de responder, para que la app nunca marque como confirmada una operacion que no
quedo guardada. No cambia nada para los demas servicios.

**Pruebas en la VM:** 24 unitarias y 9 de integracion, todas pasan.

## 2026-11-20 — Servicio de integraciones y monitoreo (dominios 21 y 22, puerto 8021)

**Por que un solo contenedor.** La propuesta de puertos (`docs/PUERTOS.md`)
agrupa integraciones (21) y monitoreo (22) en 8021: los dos miran a toda la
plataforma desde afuera y ninguno es dueno de datos del negocio.

**Integraciones.** La tabla `integraciones_ids` (migracion 018) guarda la
equivalencia entre ids externos (POS, ERP, WMS, transportista, financiero) e
internos. Su llave (sistema, tipo, id_externo) hace idempotente la importacion:
el mismo ticket del POS dos veces es la misma venta; dos envios simultaneos se
ordenan con un candado de PostgreSQL (`pg_advisory_xact_lock`) y solo uno crea.
Un id sin equivalencia responde `422 sin_conciliar` en lugar de adivinar. La
exportacion para ERP y finanzas incluye reembolso, costo total y los ids
externos. El transportista reporta el avance con su guia; reenviar el evento no
cambia nada.

**Monitoreo.** Un hilo revisa cada 60 s el `/health` de los diez servicios, las
tres bases y la cola de sincronizacion; un candado en Redis evita que los dos
workers de gunicorn revisen a la vez. Los chequeos van a MongoDB (se borran a
los 7 dias) y de ahi salen disponibilidad, tiempo promedio y p95. Las alertas
(servicio caido o degradado, respuesta lenta, base caida, demasiados conflictos
offline) se abren una sola vez por problema y se resuelven solas. La traza junta
bitacora y eventos de todos los servicios con el mismo `X-Correlation-ID`.

**Pruebas en la VM:** 19 unitarias y 8 de integracion, todas pasan. El primer
chequeo automatico quedo guardado un minuto despues de arrancar, con los diez
servicios en `ok` y sin alertas activas.

## 2026-11-20 — Monolitico vs distribuido y prueba de recuperacion

**Paridad.** `apps/web/app/tests/test_paridad.py` manda la misma solicitud por la
web en modo monolitico, la web en modo distribuido y la API directa, y exige la
misma decision en ocho casos. En la primera corrida encontro dos diferencias: el
monolito aceptaba descripciones de mas de 2000 caracteres y respondia 500 con
un motivo inexistente. Se corrigio la web (`MAX_DESCRIPCION` y validacion del
motivo activo); la segunda corrida da 8 de 8 iguales. Ambas salidas estan en
`docs/pruebas/paridad_2026-11-20.txt`.

**Recuperacion.** `scripts/prueba_recuperacion.py` mata devoluciones y
sincronizacion, detiene PostgreSQL y reinicia Redis. Lo confirmado sigue ahi,
los reintentos no duplican (409 `solicitud_duplicada`, `repetida: true`), los
servicios responden 503 en lugar de dejar datos a medias y el monitoreo abre y
resuelve la alerta de la base. 18 de 18 comprobaciones OK.

**Corrida consolidada.** `scripts/correr_e2e.sh` incluye un bloque `paridad`.
El contenedor de la web no trae pytest, asi que la prueba usa unittest.

**Documento.** `docs/MONOLITICO_VS_DISTRIBUIDO.md`: donde vive cada regla en los
dos modos y por que la caida de una API no duplica operaciones.


## 2026-11-21 — Clasificacion de motivos (Persona 4, dominio 10)

**Decision.** Servicio propio en el puerto 8010 con cinco categorias de origen
y doce submotivos iniciales que viven en la migracion 041 (son parte del
contrato, como los roles de la 008). Cada submotivo apunta a un motivo del
catalogo existente sin reemplazarlo, asi las devoluciones registradas siguen
validas y el analisis puede agrupar por origen.

**Versiones.** Cada cambio (incluido activar o desactivar) sube `version` y
guarda una copia en `submotivos_versiones`, que nunca se edita. Se exige el
motivo del cambio. Cada clasificacion revisada guarda la version con la que se
decidio. `PUT` con los mismos datos no crea version: responde `sin_cambios`.

**Revision humana (RN-11).** La sugerencia por palabras clave se guarda como
`pendiente`; solo una persona la confirma, corrige o descarta, y el servicio no
toca la devolucion. Una restriccion de la base impide una clasificacion
definitiva sin responsable. Una palabra coincide solo al inicio de una palabra
del texto (`caduc` si coincide con `caducado`; `sol` no con `solo`), porque el
primer intento por fragmentos daba sugerencias absurdas.

**Cliente.** Puede pedir una sugerencia de texto para su formulario, pero la
respuesta omite las palabras clave y esta limitada a 30 por minuto.

**Pendiente.** `analisis-auditoria` conserva su `clasificar-motivo`; se retira
al separar la auditoria (bloque final del plan de Persona 4).

## 2026-11-21 — Lotes, series y tasas (Persona 4, dominio 9)

**Decision.** La trazabilidad vive en `ventas-catalogos` (8006) y no en un
servicio nuevo: lote, serie y venta ya estan en las mismas tablas, y la
trazabilidad es una consulta sobre ellas (ver `docs/PUERTOS.md`). Se agrega la
tabla `series_producto` (migracion 040, rango de Persona 4) con `numero_serie`
UNIQUE global y `venta_detalle_id` nulo mientras la unidad sigue en almacen.

**Tasas.** Para proveedor, tienda, producto y lote la tasa es unidades
devueltas entre unidades vendidas, con el mismo conteo que `panel.causas`, de
modo que el panel y el servicio no pueden discrepar. Una ruta no tiene
"unidades vendidas", asi que ahi se mide el dano: inspecciones no aptas entre
inspecciones realizadas. Un lote sin ventas devuelve `null`, no 0.

**Seguridad.** Los clientes no consultan trazabilidad (expone proveedores y
costos internos); la respuesta no incluye datos del cliente (RN-15). Todo es
informacion para revision humana, no una causa (RN-09).

**Datos de demo.** `crear_lote_problematico` en `scripts/seed_demo.py` crea el
lote refrigerado `L-2026-PROB-01`: 12 ventas de 8 unidades, 9 devoluciones de 2
unidades (18.75 %), 6 de ellas en Tienda Centro por una misma ruta. Sin `random`
e idempotente. Lo necesitan las inspecciones (Persona 3) y la demo de causa raiz.

## 2026-11-21 — Proveedores y reclamaciones (Persona 4, dominio 13)

**Decision.** Servicio propio en el puerto 8013 que NO duplica el alta de
proveedores: el catalogo sigue en `ventas-catalogos` (8006) y aqui se consulta,
se mide y se reclama. "Productos que surten" se deduce de `productos` y
`lotes`, sin tabla nueva, porque un proveedor puede surtir un producto sin ser
su proveedor principal.

**Reclamaciones.** Tres tablas (migracion 042): la reclamacion con folio
generado por la base (`RCL-AAAA-####`, como el de devoluciones), las devoluciones
que la respaldan y una linea de tiempo inmutable. Una restriccion de la base
obliga a que una reclamacion cerrada diga como termino y a que una abierta no
traiga resolucion. Que una devolucion no este en dos reclamaciones abiertas
cruza dos tablas y no cabe en un indice, asi que el servicio bloquea las filas
de las devoluciones al crear. Solo se acepta o rechaza lo que el proveedor ya
respondio; retirarla se puede en cualquier momento.

**Indicadores y semaforo.** La tasa es unidades devueltas entre vendidas, con
el mismo conteo que el panel de causas. El semaforo compara contra el promedio
de todos los proveedores (atencion desde 1.25 veces, critico desde 2) y devuelve
`sin_datos` con menos de 20 unidades vendidas: una tasa con pocas ventas
asusta sin informar. Es una guia para revisar, no un juicio sobre el proveedor
(RN-09). Los montos se manejan como decimales con dos cifras, nunca como float.

**Acceso.** Por tratar costos y reclamos, solo lo leen Administrador, Analista,
Supervisor y Encargado de Reembolsos; Cliente e Inspector reciben 403.

## 2026-11-21 — Causa raiz y acciones correctivas (Persona 4, dominios 11 y 12)

**Decision.** Un solo servicio (8011) para la investigacion y las acciones CAPA:
una accion nace de una investigacion y su eficacia la cierra o la reabre,
comparten ciclo de vida y responsables. Las investigaciones, hipotesis,
evidencias y acciones viven en PostgreSQL, no en MongoDB: todas se relacionan
con devoluciones y usuarios por llave foranea y el flujo necesita transacciones
(cerrar sin acciones pendientes, no dos investigaciones abiertas del mismo
objeto). Las evidencias son inmutables y las restricciones de la base impiden
una conclusion sin responsable ni una hipotesis con campos de otro tipo.

**El analisis no decide (RN-09).** La deteccion solo crea alertas que PROPONEN
investigar y exige 2 veces el promedio, 20 unidades y 3 casos, para no alarmar
por ruido. Confirmar una causa exige evidencia y una hipotesis verificada. Una
investigacion inconclusa se puede cerrar o reabrir.

**Medir si funciono, sin enganarse.** Se compara la tasa de lo vendido antes de
implementar contra lo vendido despues, por cohorte de venta (una devolucion que
llega tarde se cuenta con su venta). El primer diseno comparaba hasta hoy y
tenia un sesgo claro: lo vendido en los ultimos dias todavia puede devolverse,
asi que cualquier accion parecia efectiva. Ahora "despues" se corta en hoy
menos el plazo maximo de devolucion (RN-16, tomado de `politicas_devolucion`).
El periodo "antes" no se recorta: si algo aun no madura, su tasa sale mas baja y
la meta se vuelve mas dificil; el error es conservador. Con menos de 20 unidades
en cualquier periodo el veredicto es `sin_datos`, nunca `efectiva`.

**Cierre.** Lo hace un Supervisor distinto del analista y con la reconfirmacion
de contrasena que David definio para `cerrar_investigacion` en `shared/seguridad.py`.
Las reglas de negocio se validan ANTES de consumir el permiso (de un solo uso),
asi un rechazo por reglas no obliga a reconfirmar. El veredicto final no esconde
fallos: una accion no efectiva, o sin medir, pesa mas que las efectivas.

**Pendiente.** No notifica (le tocara al servicio 8017) y la deteccion no tiene
reloj propio; se dispara con `POST /alertas/detectar`. Las investigaciones por
ruta no se soportan porque una ruta no tiene unidades vendidas.

## 2026-11-21 — Reportes y analitica (Persona 4, dominios 18 y 19)

**Decision: PDF y Excel sin librerias.** El documento pide reportes PDF y Excel,
pero el repo no tiene ninguna libreria para eso y `CLAUDE.md` exige acordar las
nuevas con el equipo. Se escribieron con la biblioteca estandar: el XLSX es un
zip de XML con dos hojas y el PDF una tabla en Courier (ancho fijo, asi las
columnas se alinean sin medir glifos). Se verificaron con `pdftotext`, con
renderizado y con Quick Look de macOS, no con Excel; las pruebas comprueban la
estructura (desplazamientos del xref, longitud de cada flujo, XML bien formado,
ninguna formula). Si el equipo prefiere `reportlab` y `openpyxl`, solo cambia
`formatos.py`. El costo de esta decision es un PDF sin graficas; para graficas
estan las opciones de Highcharts.

**Una serie de tasas puede mentir si no se cuida la madurez.** Una tasa por mes
de venta casi siempre parece bajar en los ultimos meses porque sus devoluciones
aun no llegan (plazo de 30 dias, RN-16). Sin correccion, cualquier tendencia y
cualquier pronostico habrian salido optimistas. Las series de tasa solo usan
meses cuyo fin quedo al menos un plazo atras, y las de devoluciones y costo
excluyen el mes en curso. Un mes con menos de 20 unidades no entra a la
regresion. La misma idea se uso en la medicion de eficacia de `causa-raiz`.

**Estadistica explicable.** Regresion lineal con prueba t (la direccion solo se
afirma si el cambio es distinguible del ruido), intervalo de prediccion del
95 % que se ensancha al alejarse, y puntaje z robusto (mediana y MAD) para las
anomalias: el z clasico se deja enganar por el propio valor extremo. Nada de
esto decide una causa (RN-09).

**Pareto y alertas.** Ahora tambien viven aqui, calculados en PostgreSQL y sin
el paso de sincronizar que usa `analisis-auditoria`. Ese servicio no se toca:
se retira al separar la auditoria.

**Seguridad.** Las alertas de fraude nombran clientes y se limitan a
Administrador y Analista (RN-15). Las descargas se limitan a 20 por minuto, no
se cachean y quedan en bitacora sin los datos (RNF-16). El CSV neutraliza las
formulas.

## 2026-11-21 — Separar la auditoria del analisis (Persona 4, servicio 8008)

**Decision: separar por etapas, no de golpe.** La correccion pide que cambiar el
analisis nunca toque la auditoria. Pero `analisis-auditoria` lo consumen la web
(modo distribuido), la suite E2E y las colecciones de Postman, y sus sucesores
(`clasificacion-motivos` 8010 y `reportes-analitica` 8018) seguian en PRs sin
mergear. Quitar las rutas habria roto a los tres. Por eso esta entrega aisla y
deprecia, y deja el retiro como etapas documentadas con su lista de pendientes
(`docs/MIGRACION_ANALISIS_8008.md`); el retiro final es cambiar una variable.

**La separacion se hace cumplir con pruebas, no con una promesa.** `auditoria.py`
no puede importar el analisis y solo puede tener rutas GET; ambas reglas son
pruebas. Verifique que la primera detecta una violacion rompiendola a proposito.
El analisis puede usar a la auditoria (alias de `/eventos`), nunca al reves.

**No hay reenvio automatico a los sucesores.** Las formas de respuesta cambian
(el Pareto pasa a un reporte paginado, la clasificacion trae submotivos), y un
proxy habria escondido esas diferencias y hecho depender a la auditoria del
analisis, que es justo lo que se quiere evitar. Cada respuesta obsoleta avisa con
`Deprecation: true` y `Link: rel="successor-version"`.

**Proteccion real de la bitacora (migracion 045).** "Ver el historial sin poder
modificarlo" solo era cierto porque el servicio de auditoria no tiene rutas de
escritura; pero todos los servicios escriben con la misma cuenta de base de datos,
asi que un descuido o una inyeccion SQL en cualquiera podia reescribir el rastro.
Ahora UPDATE, DELETE y TRUNCATE fallan. Unica excepcion: `ON DELETE SET NULL` de
`usuarios`, que anonimiza `usuario_id` y solo si es el unico cambio de la fila; sin
esa excepcion, borrar a una persona habria fallado. Se verifico en todo el
repositorio que nadie actualiza ni borra la bitacora. Alcance: es del esquema; no
detiene a quien administre PostgreSQL y desactive el trigger. `/auditoria/estado`
informa si esta puesto y activo para no prometer de mas.

**La auditoria gano lo que le faltaba**: filtros por entidad_id, usuario_id y
rango de fechas, y la ruta `/auditoria/eventos` (la traza vivia mal ubicada bajo
`/analisis`). Los eventos nunca devuelven su campo `datos` (RNF-16).

**Pendiente**: migrar la web, la suite E2E y Postman (las evidencias de Postman se
generaron en la VM y hay que reejecutarlas, no editarlas a mano), y despues cortar.

## 2026-11-22 — Primeras pruebas de integracion en la VM (Persona 4): tres correcciones

Al levantar los servicios en la VM y correr por primera vez las pruebas de
integracion contra la base real aparecieron tres problemas. **Ninguno estaba en el
codigo de los servicios**: el SQL, el trigger de la bitacora y los 9 pasos de
causa raiz funcionaron; fallaron dos pruebas mal escritas y los datos de demo.

**1. El lote problematico de la demo no destacaba (corregido en el seed).** Con la
base de demostracion (273 unidades vendidas, 60 devueltas, 22 %) mi lote de 96
unidades y 18.75 % daba 0.85 veces el promedio: no superaba el promedio y no
habria disparado la alerta de `causa-raiz`. El lote pesaba el 35 % de todo lo
vendido, asi que ni devolviendo las 96 unidades habria llegado a 2 veces el
promedio global. Era un error de dimensionamiento, no de la regla: la comparacion
contra el promedio es correcta, y la base es la que tiene devoluciones altas. El
lote ahora es de 24 unidades (4 ventas de 6) y devuelve 16 (66.7 %), con lo que
llega a ~2.3 veces el promedio y supera las 20 unidades y los 3 casos minimos. El
numero anterior de la entrada del 2026-11-21 (12 ventas, 9 devoluciones, 18.75 %)
queda reemplazado por este. Para aplicarlo en una base que ya tiene el lote viejo:
`docker compose exec app python scripts/seed_demo.py --rehacer-lote`, que borra solo
lo que creo el seed (se detiene con error si alguien colgo algo del lote) y lo
vuelve a crear.

**2. Prueba de causa raiz mal aislada.** Dos casos abrian una investigacion sobre el
mismo lote y el segundo recibia 409 `investigacion_activa`, que es justo la regla
que el servicio debe aplicar. El caso de permisos de CAPA usa ahora su propio lote.

**3. Frase equivocada en una prueba de la bitacora.** El trigger respondio bien
("La bitacora es de solo agregar: no admite UPDATE"); la prueba buscaba "solo de
agregar".

**Para correr las suites de integracion:** `auth` limita los logins a 10 por minuto
por IP (RNF-13) y cada suite inicia sesion con varios roles. Varias suites seguidas
reciben 429; hay que dejar pasar un minuto entre ellas. No se toco el limite.

## 2026-11-22 — Suite de seguridad del tercer parcial y corrida final

**Suite nueva `tests/e2e/test_04_seguridad_tercer_parcial.py`.** Contra los
servicios reales: los seis servicios nuevos rechazan peticiones sin token y con
token revocado; los roles de campo solo entran a lo que los nombra; un usuario
con sucursal no ve devoluciones de otra tienda (ni en el detalle ni en el
listado); operaciones criticas con contrasena incorrecta, rol no permitido, sin
permiso, permiso para otro registro y permiso de un solo uso (se comprueba que
desaparece de Redis al usarse); XXE, inyeccion SQL en el login y en la
sincronizacion, rutas con caracteres peligrosos y `/health` sin datos sensibles.

**Corrida final.** `correr_e2e.sh` ahora cubre los 14 microservicios y las
pruebas unitarias. Las dos primeras corridas del dia fallaron con 429 por un bug
del propio script: `liberar_limite_login` ejecutaba `docker compose exec` dentro
de un `while read` y solo borraba la primera clave. Corregido, la corrida
definitiva (`4a0fe99`) dio 866 pruebas aprobadas y 0 bloques con fallos. Detalle
en `docs/pruebas/REPORTE_FINAL.md`.

