# Resultado de pruebas en la VM — 2026-10-21

Primera corrida real de `bash scripts/correr_e2e.sh` en la VM, sobre `main` con las
sesiones 01, 02 y 03 integradas (suite E2E y pruebas de integracion por servicio).

**Fuente y alcance.** Este registro sale del reporte de esa corrida (91 de 100 E2E,
las nueve pruebas que fallaron, que servicios corrieron y cuales no, y las causas ya
diagnosticadas). No se conserva en el repositorio la salida completa
(`docs/pruebas/salida_2026-10-21.txt`), asi que no hay lineas `[E2E]` ni resumen
`pytest` por caso que pegar. Los casos que no se nombran como fallo se registran como
`paso` por el conteo (91 pasan + 9 fallan = 100, sin saltadas). Lo que no corrio figura
como `bloqueado por 429`, no como `paso` ni `fallo`. Las correcciones de abajo **no se han
reconfirmado en la VM**.

- Fecha: 2026-10-21
- Rama y commit: `main` con las sesiones 01, 02 y 03 (PR #5, #6 y #7)
- Correcciones: rama `roberto/correcciones-vm` (sin push ni PR todavia)

## Suite E2E (`tests/e2e`): 91 pasan, 9 fallan

| Prueba | Caso en `PRUEBAS.md` | Estado | Causa |
|---|---|---|---|
| `test_paso_06_analista_autoriza` | E2E-06 | fallo | Esperaba `["autorizacion"]`; al autorizar el servicio inserta ademas `autorizacion_logistica` (aviso al Coordinador, a proposito, sesion 01). Prueba desactualizada |
| `test_paso_09_reembolso_unico_con_lock` | E2E-09 | fallo | **Bug de producto (H-11).** Reembolso por el monto maximo exacto rechazado con 409 `monto_excedido`: `Decimal` contra `float` |
| `test_cantidad_excedida_responde_409` | SEG-15 | fallo (cascada) | 409 `sin_disponible` en lugar de `cantidad_excedida`: la suite agoto la linea de venta |
| `test_reembolso_sin_autorizar_responde_409` | SEG-16 | fallo (cascada) | Igual: el registro previo respondio `sin_disponible` |
| `test_rechazo_exige_justificacion` | SEG-17 | fallo (cascada) | Igual |
| `test_logistica_solo_programa_devoluciones_autorizadas_409` | SEG-18 | fallo (cascada) | Igual |
| `test_cadena_de_frio_rota_impide_inventario_409` | SEG-19 | fallo (cascada) | Igual |
| `test_refrigerado_sin_temperatura_responde_400` | SEG-20 | fallo (cascada) | Igual |
| `test_devolucion_creada_con_cuerpo_xml` | FMT-04 | fallo (cascada) | Igual |
| Las otras 91 (pasos 1 a 5, 6b, 7, 8, 10 y 11; SEG-01 a SEG-14 y SEG-21 a SEG-23; FMT-01 a FMT-03 y FMT-05 a FMT-08, con sus casos parametrizados) | resto de E2E y SEG/FMT | paso | Sin salida por caso en el repo |

Nota de conteo: el reporte decia "6 en cascada" pero enumera siete (SEG-15 a SEG-20 y
FMT-04), que con las dos pruebas de arriba suman los 9 fallos. La lista de siete es la
que cuadra con 91 + 9 = 100. Se confirma al repetir la corrida.

La cascada empezo porque `ctx.linea` es una sola linea de venta (`venta_detalle` 63) con
unas 3 unidades disponibles y cada registro de la suite consume 1: tras tres devoluciones
(paso 4, la del otro cliente y la de logistica con fecha pasada) todo lo siguiente
respondio 409 `sin_disponible`.

## Integracion por servicio (`tests/test_integracion.py`)

| Servicio | Resultado | Estado | Causa |
|---|---|---|---|
| auth | 5/5 | paso | |
| ventas-catalogos | 4/4 | paso | |
| evidencias | 4/4 | paso | |
| devoluciones | 3/4 | fallo (1) | `test_1_flujo_registro_revision_y_autorizacion`: esperaba `[..., "autorizacion"]`; ahora tambien `autorizacion_logistica`. Prueba desactualizada |
| logistica | no corrio | bloqueado por 429 | Login 429 |
| inspecciones | no corrio | bloqueado por 429 | Login 429 |
| reembolsos-costos | no corrio | bloqueado por 429 | Login 429 |
| analisis-auditoria | no corrio | bloqueado por 429 | Login 429 |

El 429 es el hallazgo **H-07 confirmado en la VM**: `test_99` llega al limite a proposito
y despues 8 suites hacen varios logins desde la misma IP (limite de 10 por minuto por IP,
`LOGIN_MAX_POR_MINUTO`).

## Correcciones aplicadas (por reconfirmar en la VM)

| Causa | Correccion | Archivos |
|---|---|---|
| H-11 Decimal/float | Se compara `Decimal` con `Decimal` (valor devuelto cuantizado a 0.01); `detalles.maximo` se sigue serializando como float. Dos pruebas unitarias: monto igual al maximo -> 201; maximo + 0.01 -> 409. Verificado en local que la primera falla con el codigo anterior. No hay otras comparaciones Decimal/float del mismo tipo en `services/*/app.py` | `services/reembolsos_costos/app.py`, `.../tests/test_api.py` |
| Pruebas desactualizadas | Se acepta `autorizacion_logistica` tras `autorizacion` (el reparto a coordinadores ya lo verifica el paso 6b) | `tests/e2e/test_01_proceso_completo.py`, `services/devoluciones/tests/test_integracion.py` |
| Linea agotada | Un fixture `autouse` marca como `rechazada` las devoluciones de cada prueba de error al terminar (el calculo de `disponible` las excluye; el borrado final las elimina); el proceso completo conserva las suyas. `cantidad_excedida` lee lo disponible en ese momento y pide `disponible + 1`. El fixture del contexto ahora exige al menos 3 unidades disponibles | `tests/e2e/conftest.py`, `tests/e2e/flujo.py`, `tests/e2e/test_02_seguridad_y_errores.py` |
| Rate limit | El script borra las claves `devoluciones:limite:*:login` de Redis antes de cada bloque. No se toco `auth` | `scripts/correr_e2e.sh` |

Local (sin bases, 2026-10-21): `services/reembolsos_costos` 8 passed, 5 skipped;
`services/devoluciones` 24 passed, 4 skipped; `tests/e2e` descubre 100 pruebas y todas se
saltan sin `INTEGRACION=1`; `bash -n scripts/correr_e2e.sh` sin errores.

## Pendiente

Repetir `bash scripts/correr_e2e.sh` en la VM con la rama corregida. Esperado: 100/100 E2E
y 8/8 servicios. Con esa salida se reemplazan los `fallo` y `bloqueado por 429` de
`docs/PRUEBAS.md` y se confirma o corrige este documento.

## Corridas posteriores (2026-10-21)

Tras integrar PR #8 (correccion del monto maximo de reembolso y ajustes de la
suite) y PR #9 (la prueba de devoluciones solo usa cuentas demo), en la VM:

- `bash scripts/correr_e2e.sh`, E2E: **100 passed in 5.84 s** (12 del proceso
  completo, 23 de seguridad y errores, 8 de JSON/XML y el resto con parametros).
  El paso 9 aprobo el reembolso de 227.17 con 201, el segundo intento dio 409
  `reembolso_duplicado` y con el lock tomado 409 `reembolso_en_proceso`.
- Integracion por servicio: auth 5, ventas 4, evidencias 4, logistica 3,
  inspecciones 5, reembolsos 5 y analisis 4, todas passed.
- `devoluciones` (reconstruida la imagen tras PR #9): **4 passed in 1.33 s**.
  Antes fallaba con 401 al iniciar porque la prueba elegia a `prueba@gmail.com`,
  una cuenta real con otra contrasena, como "otro cliente".

La causa de que devoluciones fallara una vez mas tras PR #8 fue operativa: la
suite de cada servicio corre con el archivo que esta dentro de su imagen, y solo
se habia reconstruido `reembolsos-costos`. Hay que reconstruir cada servicio cuyas
pruebas cambian.

