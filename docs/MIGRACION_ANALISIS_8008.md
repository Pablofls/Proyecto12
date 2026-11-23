# Separar el analisis de la auditoria (puerto 8008)

Correccion del profe: **separar la auditoria del analisis, para que cambiar el
analisis nunca toque la auditoria.** Este documento dice que se hizo, que falta
y como terminarlo sin romper a nadie.

## Estado: separacion en etapas

El servicio `analisis-auditoria` lo usan la web (modo distribuido), la suite E2E y
las colecciones de Postman, y los servicios que lo sustituyen (`clasificacion-motivos`
8010 y `reportes-analitica` 8018) aun estaban en PRs sin mergear. Quitar las rutas de
golpe habria roto a todos, asi que se hace en etapas:

| Etapa | Que pasa | Estado |
|---|---|---|
| 1. Aislar | El codigo se divide en `auditoria.py` y `analisis.py`; el analisis se marca obsoleto; la auditoria gana filtros y se protege en la base | **Hecha** |
| 2. Migrar clientes | La web, la suite E2E y Postman dejan de usar las rutas `/api/v1/analisis/*` | Web y E2E **hechas**; Postman pendiente (ver abajo) |
| 3. Cortar | `ANALISIS_HABILITADO=false`: las rutas responden 410 y el servicio queda solo con auditoria | **Hecha** el 2026-11-22 (el interruptor ya no existe: lo sustituye la etapa 4) |
| 4. Retirar | Se borra `analisis.py` y deja de usarse la coleccion Mongo `resultados_analisis` | **Hecha** el 2026-11-22 (ver "Etapa 4") |

## Que hace la etapa 1

- **`auditoria.py`** (bitacora y traza de eventos) **no importa nada del analisis**, y
  solo tiene rutas `GET`. Dos pruebas (`tests/test_separacion.py`) hacen cumplir ambas
  cosas; una la verifique rompiendo la regla a proposito y la prueba fallo.
- **`analisis.py`** conserva el comportamiento de siempre. Cada respuesta lleva
  `Deprecation: true` y, si hay sucesor, `Link: <...>; rel="successor-version"`. La
  dependencia va en un solo sentido: el analisis puede usar a la auditoria (para el alias
  de `/eventos`), nunca al reves.
- **Interruptor `ANALISIS_HABILITADO`** (por omision `true`, se lee en cada peticion, no
  exige reconstruir la imagen): con `false`, las seis rutas de analisis responden **410**
  `servicio_movido` con los sucesores, aun sin token. La auditoria sigue igual.
- **La auditoria gana**: los filtros `entidad_id`, `usuario_id`, `desde` y `hasta` en
  `GET /api/v1/auditoria`; `GET /api/v1/auditoria/eventos` (la traza por correlation id
  vivia, mal ubicada, bajo `/analisis`); y `GET /api/v1/auditoria/estado`.
- **La base protege la bitacora** (migracion 045): `UPDATE`, `DELETE` y `TRUNCATE` fallan.
  Hasta ahora "ver el historial sin poder modificarlo" solo era cierto porque este servicio
  no tiene rutas de escritura, pero **todos** los servicios escriben con la misma cuenta de
  base de datos; un descuido o una inyeccion SQL en cualquiera podia reescribir el rastro.
  - Excepcion unica: si `usuarios` borra a una persona, la llave `ON DELETE SET NULL`
    anonimiza `usuario_id`. Se permite solo cuando ese es el unico cambio de la fila.
  - Se reviso que ningun codigo del repositorio actualiza ni borra la bitacora, por lo que
    ningun flujo existente se rompe.
  - **Alcance honesto**: es proteccion del esquema. Frena a la aplicacion y a una inyeccion;
    no a quien administre PostgreSQL y desactive el trigger a proposito (exige ser dueno de la
    tabla). `GET /auditoria/estado` informa si el trigger esta puesto y activo, para no
    prometer mas de lo que hay. Depurar registros antiguos exige desactivarlo de forma
    explicita.

## A donde se fue cada ruta

| Ruta obsoleta (8008) | Sucesor | Diferencias a considerar |
|---|---|---|
| `POST /api/v1/analisis/clasificar-motivo` | `clasificacion-motivos` (8010) `POST /api/v1/motivos/sugerencias` | La respuesta trae `codigo`, `categoria` y `version` del submotivo; ya no `motivo` ni `puntaje` con ese nombre |
| `GET /api/v1/analisis/alertas-fraude` | `reportes-analitica` (8018) `GET /api/v1/analitica/alertas-fraude` | **Igual**: mismo SQL, mismos umbrales y mismo formato |
| `GET /api/v1/analisis/pareto` | `reportes-analitica` (8018) `GET /api/v1/reportes/pareto` | Reporte paginado con `columnas` y `datos`; para graficar, `GET /api/v1/graficas/pareto`. Sin cache `hit/miss` ni dependencia de sincronizar |
| `POST /api/v1/analisis/sincronizar` | ninguno | 8018 calcula directo en PostgreSQL y siempre esta al dia |
| `GET /api/v1/analisis/resumen` | ninguno | Solo contaba snapshots de Mongo |
| `GET /api/v1/analisis/eventos` | este servicio, `GET /api/v1/auditoria/eventos` | **Igual**; el alias obsoleto sigue respondiendo |

Como las formas de respuesta cambian, no se hizo un reenvio automatico desde 8008: habria
ocultado diferencias reales y hecho que la auditoria dependiera del analisis.

## Etapa 2: lo que hay que migrar

| Cliente | Donde | Que hacer |
|---|---|---|
| **Web** (modo distribuido) | `apps/web/app/blueprints/panel.py` (vista `causas` y ruta `sincronizar_causas`) y `panel/causas.html` | **Hecho.** Se quito el bloque de snapshots de MongoDB, el boton "Sincronizar PostgreSQL → MongoDB" y la ruta `POST /panel/causas/sincronizar`. El panel ya calculaba su Pareto y sus tasas desde PostgreSQL, asi que no pierde informacion. `config.py` y `microservicios.py` conservan la URL de 8008 porque la auditoria sigue ahi y se monitorea |
| **Suite E2E** | `tests/e2e/cliente.py`, `test_01_proceso_completo.py` (pasos 03 y 10) y `test_02_seguridad_y_errores.py` | **Hecho.** El paso 03 usa `POST /api/v1/motivos/sugerencias` (8010) y comprueba que sugiere `empaque_roto` con codigo, categoria y version. El paso 10 se reescribio, no se tradujo: el Pareto de 8018 cuenta la devolucion del paso 4 sin sincronizar y suma lo mismo que la base; ya no se comprueba cache de Redis ni snapshots de MongoDB, que no existen en el sucesor. La traza por correlation id y la bitacora se leen de `/api/v1/auditoria`. `test_02` cubre ahora los endpoints de auditoria, motivos y reportes |
| **Postman** | `docs/postman/especificaciones.py` (`analisis_auditoria`), `generar_colecciones.py`, `volcar_ejecuciones.py` y las evidencias ejecutadas | **Pendiente, a proposito.** Tras el corte la coleccion de 8008 prueba rutas que ya responden 410 (por eso sus evidencias de Newman quedan desactualizadas). Regenerarla reescribe `docs/EVIDENCIAS.md` y su checklist y obliga a volver a correr Newman en la VM; las evidencias de los servicios del tercer parcial se hicieron con `curl` (`docs/evidencias/ejecuciones/auditoria.md`, `causa_raiz.md`, etc.) |
| **Monitoreo** | `integraciones-monitoreo` y la lista de servicios de la web | Nada: 8008 sigue existiendo |

## Etapa 3: el corte

1. Mergear `clasificacion-motivos` y `reportes-analitica`, y completar la etapa 2.
2. En `docker-compose.yml`, servicio `analisis-auditoria`: `ANALISIS_HABILITADO: "false"`.
3. `docker compose up -d analisis-auditoria` y comprobar:
   - `GET /health` muestra `"analisis": "retirado"`.
   - `GET /api/v1/analisis/pareto` responde **410** `servicio_movido`.
   - `GET /api/v1/auditoria`, `/auditoria/eventos` y `/auditoria/estado` siguen en 200.
4. Si algo fallaba, se volvia a `"true"` y se reiniciaba: nada se habia borrado. Tras la etapa 4 esto
   ya no es posible sin recuperar el codigo del historial de git.

## Etapa 4: retirar

Hecha el 2026-11-22, despues de verificar la web (PR #58), la suite E2E (113 pruebas) y el corte en la VM.

- **Se borro** `services/analisis_auditoria/analisis.py` (sincronizar, Pareto con cache, clasificar motivo,
  alertas de fraude, resumen y el alias de eventos), su contrato `clasificacion.xsd` y `tests/test_pareto.py`.
  Todo sigue en el historial de git.
- **Se agrego** `retirado.py`, un stub sin logica: cualquier metodo y ruta bajo `/api/v1/analisis` responde
  **410 `servicio_movido`**, aun sin token, con los sucesores y `Deprecation: true`. Se prefirio a dejar un 404
  mudo para que un cliente rezagado sepa a donde ir. `/health` sigue diciendo `"analisis": "retirado"`.
- **Ya no existe** la variable `ANALISIS_HABILITADO` (compose, `.env.example`, pruebas). Volver atras
  exige `git revert` del cambio.
- **MongoDB**: `db/mongo/init.js` ya no crea `resultados_analisis`. **No se borraron los datos** de esa coleccion
  en la VM: un volumen existente la conserva sin que nadie la lea. Si se quiere liberar el espacio, es un
  `db.resultados_analisis.drop()` manual y no se puede deshacer.
- **Pruebas**: `test_separacion.py` comprueba que el codigo del analisis ya no existe, que el stub es la
  unica ruta de `/analisis` y que responde 410 con cualquier metodo; `test_integracion.py` conserva
  `IntegracionCorte` (410 con sucesor y auditoria en pie).
- **No se tocaron** documentos historicos del segundo parcial (DOCUMENTO_TECNICO, diagramas, evidencias de
  Newman, `EVIDENCIAS.md`, `scripts/evidencias_vm.sh`) que describen cuando el analisis existia, ni Postman.

## Para la demo

`GET /api/v1/auditoria/estado` muestra la bitacora y `"completa": true` en la proteccion.
Despues, en la VM, intentar `UPDATE bitacora SET detalle = 'x' WHERE id = 1;` falla con
*"La bitacora es de solo agregar"*: es la evidencia de que el historial no se puede
modificar.
