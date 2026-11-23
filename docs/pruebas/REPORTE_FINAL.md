# Reporte final de pruebas

Este es el documento de referencia del resultado de las pruebas. Arriba esta el
**resultado definitivo** de una sola corrida, identificada por commit, fecha y
entorno; abajo, el **historial**: cada corrida anterior en su propia fila, con su
version, para que nunca se mezclen resultados de distintas versiones.

> La corrida se repite con `bash scripts/correr_e2e.sh`. El script escribe solo
> el encabezado de identificacion (commit, rama, fecha, versiones); no se completa
> a mano.

## 1. Resultado definitivo

| Dato | Valor |
|---|---|
| Fecha (UTC) | 2026-11-23 01:57:16 |
| Rama | `david/pruebas-seguridad`: `main` hasta el PR #69 (retiro del analisis del 8008, trazabilidad, rediseno) mas la suite de seguridad del tercer parcial |
| Commit | `9e64b5a62ee30e6efad5ced1d116df70ba655f46` |
| Arbol de trabajo | limpio (sin cambios sin commit) |
| Entorno | VM `maquina01` de Google Compute Engine (e2-standard-2), CentOS Stream 10, kernel 6.12.0 |
| Contenedores | Docker 29.9.1, Docker Compose 5.6.0; 18 contenedores (web, 14 microservicios y 3 bases), todas las imagenes reconstruidas antes de la corrida |
| Bases | PostgreSQL 16.15, Redis 7.4.11, MongoDB 7.0.45 |
| Esquema | Migraciones hasta `045_bitacora_solo_agregar.sql` |
| Datos | `db/seeds/001_catalogos.sql` + `scripts/seed_demo.py` del mismo dia |
| Salida completa | [`salida_2026-11-23.txt`](salida_2026-11-23.txt) (1087 lineas, sin contrasenas ni tokens) |
| Resultado | **0 bloques con fallos** |

### E2E, paridad e integracion

| Bloque | Pruebas | Resultado |
|---|---|---|
| Suite E2E (`tests/e2e`): proceso completo, seguridad y errores, JSON/XML, **seguridad del tercer parcial** (`test_04`), rate limit | 143 | **143 passed** |
| Paridad monolito / distribuido / API (`apps/web/app/tests/test_paridad.py`) | 8 casos x 3 caminos | **8 OK** |
| Integracion `auth` | 7 | 7 passed |
| Integracion `ventas-catalogos` | 4 | 4 passed |
| Integracion `devoluciones` | 6 | 6 passed |
| Integracion `evidencias` | 4 | 4 passed |
| Integracion `logistica` | 3 | 3 passed |
| Integracion `inspecciones` | 5 | 5 passed |
| Integracion `reembolsos-costos` | 5 | 5 passed |
| Integracion `analisis-auditoria` | 10 | 10 passed |
| Integracion `clasificacion-motivos` | 6 | 6 passed |
| Integracion `causa-raiz` | 4 | 4 passed |
| Integracion `proveedores` | 5 | 5 passed |
| Integracion `reportes-analitica` | 16 | 16 passed |
| Integracion `sincronizacion` | 9 | 9 passed |
| Integracion `integraciones-monitoreo` | 8 | 8 passed |
| Integracion `ventas-catalogos`: trazabilidad de lotes y series | 8 | 8 passed |
| **Total** | **251** | **251 aprobadas, 0 fallos** |

### Unitarias (misma corrida, en la VM)

Las pruebas de integracion de cada carpeta se saltan solas sin `INTEGRACION=1`;
por eso cada bloque muestra pruebas "skipped".

| Componente | Resultado |
|---|---|
| auth | 42 passed |
| ventas-catalogos | 30 passed |
| devoluciones | 31 passed |
| evidencias | 3 passed |
| logistica | 5 passed |
| inspecciones | 5 passed |
| reembolsos-costos | 8 passed |
| analisis-auditoria | 31 passed |
| clasificacion-motivos | 67 passed |
| causa-raiz | 132 passed |
| proveedores | 74 passed |
| reportes-analitica | 133 passed |
| sincronizacion | 24 passed |
| integraciones-monitoreo | 19 passed |
| web (`apps/web/app/tests`) | 37 OK |
| **Total** | **641 aprobadas** |

**Total de la corrida: 892 pruebas aprobadas, 0 fallos.**

### Prueba de recuperacion (aparte)

`scripts/prueba_recuperacion.py` detiene servicios a proposito (devoluciones,
sincronizacion, PostgreSQL y Redis), por lo que no forma parte de la corrida
automatica. Ultima ejecucion: 2026-11-20, commit `0e628ab`, **18 de 18
comprobaciones correctas**. Salida: [`recuperacion_2026-11-20.txt`](recuperacion_2026-11-20.txt).

## 2. Historial de corridas

Cada fila es una corrida distinta. Los resultados **no se suman ni se comparan**
entre filas: cambian el codigo, las pruebas o ambos.

| # | Fecha | Version | E2E | Integracion por servicio | Notas |
|---|---|---|---|---|---|
| 1 | 2026-10-21 | `main` con PR #5, #6 y #7 | 91 / 100 (9 fallos) | 3 de 8 completos; devoluciones 3/4; 4 servicios no corrieron (429) | Primera corrida real. Sin salida completa guardada. Detalle en [`resultado_2026-10-21.md`](resultado_2026-10-21.md) |
| 2 | 2026-10-21 | `main` con PR #8 y #9 | 100 / 100 | 8 de 8 | Tras corregir los fallos de la corrida 1. Salidas parciales en [`salida_2026-10-21.txt`](salida_2026-10-21.txt) y [`salida_2026-10-21_servicios.txt`](salida_2026-10-21_servicios.txt), **sin commit registrado** |
| 3 | 2026-11-10 | `eeed8a4` | 100 / 100 | 8 de 8 (38 pruebas) | Primera corrida con encabezado automatico y salida completa ([`salida_2026-11-10.txt`](salida_2026-11-10.txt)) |
| 4 | 2026-11-22 | `aaaee06` | 130 / 130 | 13 de 14; devoluciones 3/6; paridad 4/8 | Los fallos fueron 429 del limite de 20 registros por minuto: el script no liberaba bien los contadores (ver tabla 3). Salida no incluida en el repositorio |
| 5 | 2026-11-22 | `01c7c24` | 130 / 130 | 13 de 14; devoluciones 3/6; paridad 4/8 | Mismo 429: el primer arreglo del script todavia borraba solo la primera clave. Salida no incluida |
| 6 | 2026-11-22 | `4a0fe99` | 130 / 130 | 14 de 14; paridad 8/8 | 866 pruebas, 0 fallos. Antes de integrar los PR #40 a #69. Salida en [`salida_2026-11-22.txt`](salida_2026-11-22.txt) |
| 7 | 2026-11-23 | `d900e93` | 143 / 143 | 14 de 14; paridad 8/8; trazabilidad 6/8 | Tras mergear `main`. 2 fallos de trazabilidad por datos: el seed sumo una venta reciente al lote problematico (ver tabla 3). Salida no incluida |
| 8 | 2026-11-23 | `9e64b5a` (seccion 1) | 143 / 143 | 14 de 14 + trazabilidad; paridad 8/8 | **Resultado definitivo.** 892 pruebas, 0 fallos |

## 3. Fallos encontrados y como se corrigieron

| Corrida | Fallo | Tipo | Causa | Correccion | Verificada en |
|---|---|---|---|---|---|
| 1 | `test_paso_09_reembolso_unico_con_lock` | **Bug de producto (H-11)** | Un reembolso por el monto maximo exacto se rechazaba con 409 `monto_excedido`: se comparaba `Decimal` contra `float` | Se compara `Decimal` con `Decimal`, cuantizado a 0.01; dos pruebas unitarias nuevas | Corrida 2 |
| 1 | `test_paso_06_analista_autoriza` y la integracion de devoluciones | Prueba desactualizada | Al autorizar se agrego el aviso `autorizacion_logistica` al Coordinador y la prueba esperaba solo `autorizacion` | La prueba acepta el aviso adicional | Corrida 2 |
| 1 | 7 pruebas de SEG-15 a SEG-20 y FMT-04 | Fallo en cascada de la suite | Todas usaban la misma linea de venta y la agotaron (409 `sin_disponible`) | Las devoluciones de cada prueba de error se rechazan al terminar; la linea elegida debe tener 3 unidades | Corrida 2 |
| 1 | logistica, inspecciones, reembolsos y analisis no corrieron | Entorno (H-07) | Limite de 10 logins por minuto por IP | `correr_e2e.sh` borra los contadores de login antes de cada bloque | Corrida 2 |
| 2 → 3 | (cambio de reglas, no fallo) | Ajuste por RN-16 | El plazo de devolucion deja fuera de plazo las ventas de agosto | La suite elige una linea dentro del plazo y un motivo libre; `seed_demo.py` agrega ventas recientes | Corrida 3 |
| Paridad, 2026-11-20 | La web monolitica aceptaba descripciones de mas de 2000 caracteres | **Bug de producto** | La web no validaba el maximo que si valida la API | `MAX_DESCRIPCION` en la web | Paridad 8/8 |
| Paridad, 2026-11-20 | La web monolitica respondia 500 con un motivo inexistente | **Bug de producto** | La web no comprobaba que el motivo existiera | La web valida que el motivo exista y este activo | Paridad 8/8 |
| 4 y 5 | Paridad (4 casos) e integracion de devoluciones (3) con 429 | Entorno: **bug del script de pruebas** | `liberar_limite_login` corria `docker compose exec` dentro de un `while read`; el `exec` consumia la entrada y solo se borraba la primera clave, asi que el contador de registros de devoluciones seguia lleno | Se borran todos los contadores dentro del contenedor de Redis de una sola vez (`redis-cli --scan` + `xargs redis-cli DEL`); se comprobo que borra 3 de 3 claves de prueba | Corrida 6 |

| 7 | `test_integracion_trazabilidad` (2 pruebas): 27 unidades en vez de 24, 59.26 % en vez de 66.67 % | Datos de prueba: **bug del seed** | Al cambiar el dia, `crear_ventas_recientes` eligio el lote `L-2026-PROB-01` para la venta `VTA-20261123-R6` | El seed excluye el lote problematico de las ventas recientes; en la VM se borro esa linea (sin devoluciones) | Corrida 8 |

El 429 de las corridas 4 y 5 confirma que el limite de 20 registros por minuto
por usuario (RNF-13) funciona; lo que fallaba era la preparacion entre bloques.

## 4. Como reproducir

En la VM, con el entorno levantado y el `.env` completo:

```bash
git switch <rama-o-commit>
docker compose up -d --build                      # reconstruye todas las imagenes
docker compose exec app python scripts/migrate.py
docker compose exec app python scripts/seed_demo.py   # el mismo dia: ventas dentro del plazo (RN-16)
bash scripts/correr_e2e.sh                        # todo; o: e2e | paridad | servicios | unitarias
python3 scripts/prueba_recuperacion.py            # aparte: detiene servicios a proposito
```

La salida empieza con el commit, la rama, la fecha y las versiones del entorno, y
termina con un resumen por bloque y el numero de bloques con fallos.
