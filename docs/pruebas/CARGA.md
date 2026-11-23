# Pruebas de carga con Locust (RNF-29)

Corrida del **2026-11-23 02:14 UTC**, commit `3f5ff52`, rama `david/pruebas-carga`
(`main` despues del PR #65). VM `maquina01` (e2-standard-2: 2 CPU, 7.5 GB),
18 contenedores, Locust 2.31.8 en un contenedor **dentro de la red del compose**:
se mide la plataforma, no el internet entre la VM y quien prueba.

- Codigo: [`tests/carga/locustfile.py`](../../tests/carga/locustfile.py)
- Corrida: `bash scripts/correr_carga.sh` (o `humo`, `normal`, `pico`)
- Resultados crudos: [`carga_2026-11-23/`](carga_2026-11-23/) (CSV, reporte HTML de Locust y uso de recursos por escenario)

## 1. Perfiles

La prueba simula **cinco perfiles con flujos distintos**, no peticiones repetidas a un
solo endpoint. Cada usuario espera de 1 a 3 s entre acciones (el movil, 3 a 6 s).

| Perfil | Peso | Que hace | Servicios |
|---|---|---|---|
| Cliente | 5 | Sus devoluciones; sus compras, el detalle de una y si una linea todavia se puede devolver; sugerencia de motivo | devoluciones, ventas-catalogos, clasificacion-motivos |
| Analista | 3 | Bandeja y detalle de devoluciones, Pareto, tendencias, alertas de fraude, tasas por lote, alertas de causa raiz | devoluciones, reportes-analitica, ventas-catalogos, causa-raiz |
| Operacion | 2 | Coordinador de Logistica (recolecciones) o Inspector (devoluciones por inspeccionar) | logistica, devoluciones |
| Movil de campo | 2 | El Recolector sincroniza su cola offline (reenvia el mismo lote: idempotencia) y consulta sus operaciones | sincronizacion |
| Supervision | 1 | Alertas operativas, disponibilidad, chequeo en vivo de toda la plataforma, proveedores, investigaciones | integraciones-monitoreo, proveedores, causa-raiz |

Se inicia una sesion real por rol al arrancar (el limite de 10 logins por minuto por IP
impide un login por usuario simulado) y los usuarios de cada perfil comparten el token.

## 2. Escenarios y resultados

| Escenario | Usuarios | Duracion | Peticiones | Fallos | Peticiones/s | Mediana | p95 | Maximo |
|---|---|---|---|---|---|---|---|---|
| Humo | 5 | 30 s | 85 | **0** | 2.9 | 39 ms | 180 ms | 275 ms |
| Normal | 25 | 2 min | 1,662 | **0** | 14.1 | 61 ms | 320 ms | 1.2 s |
| Pico | 60 | 2 min | 2,642 | **0** | 21.7 | 540 ms | 2.5 s | 5.1 s |

**Ningun error en ningun escenario** (sin 500, sin timeouts, sin servicios caidos).

Limite por usuario (RNF-13): sugerencias de motivo y sincronizacion permiten 30 peticiones
por minuto por usuario. Como los usuarios simulados comparten token, el limite se activo
9 veces en el escenario normal y 87 en el pico: el servicio respondio 429 con `Retry-After`
en lugar de saturarse. Se cuentan como correctos porque es el comportamiento esperado.

## 3. Lectura

**Carga normal (25 usuarios): holgada.** La mitad de las peticiones responde en 61 ms y el
95 % en menos de un tercio de segundo.

**Pico (60 usuarios): responde, pero aparece un cuello de botella claro.** Por servicio,
la mediana en el pico fue:

| Servicio | Mediana en el pico |
|---|---|
| monitoreo (alertas, disponibilidad) | 24 a 38 ms |
| sincronizacion | 18 a 200 ms |
| motivos (sugerencias) | 110 ms |
| causa-raiz | 150 a 250 ms |
| logistica | 180 ms |
| reportes-analitica | 270 a 320 ms |
| ventas-catalogos | 320 ms |
| **devoluciones** | **1,200 a 1,400 ms** |

`devoluciones` recibe casi la mitad del trafico (lo usan Cliente, Analista, Inspector y
Coordinador) y corre con 2 workers de Gunicorn en una VM de 2 CPU. Los demas servicios
siguen rapidos con la misma carga: **una parte lenta no tumba a las demas**. El chequeo en
vivo del monitoreo (`/monitoreo/estado`, revisa 14 servicios y 3 bases) sube de 350 ms a
1.6 s en el pico porque espera justo a los servicios cargados.

**Memoria estable:** cada microservicio usa 76 a 116 MB y MongoDB 340 MB, de 7.5 GB.

## 3b. Via reverse proxy (2026-11-23, 03:47 UTC)

Esta corrida fue **directa a cada servicio**, sin Nginx. El mismo dia se repitieron `normal`
y `pico` por el proxy (`CARGA_VIA_PROXY=1`) y de nuevo directos, en la misma VM, para comparar:
el proxy agrega 2 a 3 ms a la mediana y no cambia el rendimiento (0 fallos, 0 429 de Nginx).
Detalle y tabla en [`proxy_2026-11-23.md`](proxy_2026-11-23.md). Las cifras de pico de la
seccion 2 no se reprodujeron ese dia (mediana de 55 ms directa, no 540 ms): dependen del estado
de la VM al correr.

## 4. Que haria falta para mas carga

Por orden de costo, sin reconstruir la arquitectura:

1. Mas workers de Gunicorn en `devoluciones` (una linea en su Dockerfile).
2. Una segunda replica de `devoluciones` detras del reverse proxy (NGINX).
3. Una VM con mas CPU: todo corre en una sola maquina de 2 CPU.

No se aplicaron en esta entrega: el resultado se reporta tal como salio.

## 5. Limites de la prueba

- Una sola VM con todo junto: Locust tambien consume CPU de la misma maquina.
- Solo operaciones de lectura y la sincronizacion idempotente: no se crean devoluciones
  masivas para no llenar la base de demostracion ni agotar las lineas de venta.
- No incluye la web monolitica (sesion por formulario) ni la carga de archivos grandes.
