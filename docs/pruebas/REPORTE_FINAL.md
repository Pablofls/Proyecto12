# Reporte final de pruebas

Este es el documento de referencia del resultado de las pruebas. Arriba esta el
**resultado definitivo** de una sola corrida, identificada por commit, fecha y
entorno; abajo, el **historial**: cada corrida anterior en su propia fila, con su
version, para que nunca se mezclen resultados de distintas versiones.

> Para la entrega se repite la corrida sobre el commit final de `main` con
> `bash scripts/correr_e2e.sh` y se actualiza la seccion 1. El script escribe
> solo el encabezado de identificacion; no se completa a mano.

## 1. Resultado definitivo

| Dato | Valor |
|---|---|
| Fecha (UTC) | 2026-11-10 22:10:43 |
| Rama | `david/validaciones-devoluciones` (incluye `main` hasta PR #26, control por sucursal y validaciones de devoluciones) |
| Commit | `eeed8a45cda5d38e7cbbd4870fc2cf0c70e1c65b` |
| Arbol de trabajo | limpio (sin cambios sin commit) |
| Entorno | VM `maquina01` de Google Compute Engine (e2-standard-2), CentOS Stream 10, kernel 6.12.0 |
| Contenedores | Docker 29.9.1, Docker Compose 5.6.0 |
| Bases | PostgreSQL 16.15, Redis 7.4.11, MongoDB 7.0.45 |
| Esquema | Migraciones hasta `016_politicas_devolucion.sql` |
| Datos | `db/seeds/001_catalogos.sql` + `scripts/seed_demo.py` del mismo dia |
| Salida completa | [`salida_2026-11-10.txt`](salida_2026-11-10.txt) (537 lineas, sin contrasenas ni tokens) |

### Pruebas de integracion y E2E (`bash scripts/correr_e2e.sh`)

| Bloque | Pruebas | Resultado |
|---|---|---|
| Suite E2E (`tests/e2e`): proceso completo, seguridad y errores, JSON/XML, rate limit | 100 | **100 passed** |
| Integracion `auth` | 7 | 7 passed |
| Integracion `ventas-catalogos` | 4 | 4 passed |
| Integracion `devoluciones` | 6 | 6 passed |
| Integracion `evidencias` | 4 | 4 passed |
| Integracion `logistica` | 3 | 3 passed |
| Integracion `inspecciones` | 5 | 5 passed |
| Integracion `reembolsos-costos` | 5 | 5 passed |
| Integracion `analisis-auditoria` | 4 | 4 passed |
| **Total** | **138** | **138 passed, 0 fallos, 0 saltadas** |

### Pruebas unitarias (mismo commit, en la VM)

| Componente | Resultado |
|---|---|
| auth | 42 passed |
| devoluciones | 31 passed |
| logistica | 5 passed |
| inspecciones | 5 passed |
| reembolsos-costos | 8 passed |
| ventas-catalogos | 8 passed |
| evidencias | 3 passed |
| analisis-auditoria | 4 passed |
| web (`apps/web/app/tests`) | 37 passed |
| **Total** | **143 passed** |

## 2. Historial de corridas

Cada fila es una corrida distinta. Los resultados **no se suman ni se comparan**
entre filas: cambian el codigo, las pruebas o ambos.

| # | Fecha | Version | E2E | Integracion por servicio | Notas |
|---|---|---|---|---|---|
| 1 | 2026-10-21 | `main` con PR #5, #6 y #7 | 91 / 100 (9 fallos) | 3 de 8 completos; devoluciones 3/4; 4 servicios no corrieron (429) | Primera corrida real. Sin salida completa guardada. Detalle en [`resultado_2026-10-21.md`](resultado_2026-10-21.md) |
| 2 | 2026-10-21 | `main` con PR #8 y #9 | 100 / 100 | 8 de 8 | Tras corregir los fallos de la corrida 1 (tabla 3). Salidas parciales en [`salida_2026-10-21.txt`](salida_2026-10-21.txt) y [`salida_2026-10-21_servicios.txt`](salida_2026-10-21_servicios.txt), **sin commit registrado**; la de servicios incluye la corrida intermedia en la que devoluciones fallo (tabla 3, fila 1 → 2) |
| 3 | 2026-11-10 | `eeed8a4` (seccion 1) | 100 / 100 | 8 de 8 | Resultado definitivo. Primera corrida con encabezado automatico y salida completa |

## 3. Fallos encontrados y como se corrigieron

| Corrida | Fallo | Tipo | Causa | Correccion | Verificada en |
|---|---|---|---|---|---|
| 1 | `test_paso_09_reembolso_unico_con_lock` | **Bug de producto (H-11)** | Un reembolso por el monto maximo exacto se rechazaba con 409 `monto_excedido`: se comparaba `Decimal` contra `float` | Se compara `Decimal` con `Decimal`, cuantizado a 0.01; dos pruebas unitarias nuevas (monto igual al maximo y maximo + 0.01) | Corrida 2 |
| 1 | `test_paso_06_analista_autoriza` y la integracion de devoluciones | Prueba desactualizada | Al autorizar se agrego el aviso `autorizacion_logistica` al Coordinador y la prueba esperaba solo `autorizacion` | La prueba acepta el aviso adicional (el reparto lo verifica el paso 6b) | Corrida 2 |
| 1 | 7 pruebas de SEG-15 a SEG-20 y FMT-04 | Fallo en cascada de la suite | Todas usan la misma linea de venta y la agotaron: respondian 409 `sin_disponible` | Las devoluciones de cada prueba de error se marcan como rechazadas al terminar; la linea elegida debe tener 3 unidades | Corrida 2 |
| 1 | logistica, inspecciones, reembolsos y analisis no corrieron | Entorno (H-07) | Limite de 10 logins por minuto por IP: todas las suites salen de la misma IP | `correr_e2e.sh` borra los contadores de login antes de cada bloque | Corrida 2 |
| 1 → 2 | devoluciones fallo una vez mas | Operativo | Solo se habia reconstruido la imagen de reembolsos; las pruebas corren con el archivo de su imagen | Reconstruir cada servicio cuyas pruebas cambian | Corrida 2 |
| 2 → 3 | (cambio de reglas, no fallo) | Ajuste por RN-16 | El plazo de devolucion deja fuera de plazo las ventas de agosto y prohibe dos solicitudes abiertas con la misma linea y motivo | La suite elige una linea dentro del plazo y un motivo libre (`flujo.motivo_libre`); `seed_demo.py` agrega ventas recientes | Corrida 3 |

## 4. Como reproducir

En la VM, con el entorno levantado y el `.env` completo:

```bash
git switch <rama-o-commit>
docker compose up -d --build                      # reconstruye todas las imagenes
docker compose exec app python scripts/migrate.py
docker compose exec app python scripts/seed_demo.py   # el mismo dia: ventas dentro del plazo (RN-16)
bash scripts/correr_e2e.sh                        # guarda docs/pruebas/salida_<fecha>.txt
```

La salida empieza con el commit, la rama, la fecha y las versiones del entorno, y
termina con un resumen por bloque y el numero de bloques con fallos.
