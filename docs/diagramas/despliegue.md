# Diagrama de despliegue

Nodo fisico: la maquina virtual de Google Compute Engine del equipo (CentOS
Stream 10 con SELinux en `Enforcing`, segun `docs/BITACORA.md`). Todo corre en
contenedores de un unico `docker-compose.yml`. Los puertos y la direccion de
enlace salen literalmente del compose.

Trazabilidad: RNF-02, RNF-03, RNF-22, RNF-27.

```mermaid
flowchart TB
    INET(("Internet / red del equipo"))

    subgraph VM["VM de GCP - Compute Engine (Docker Engine + Docker Compose)"]
        direction TB

        NATIVO["PostgreSQL nativo de la VM<br/>:5432 (NO es del proyecto)"]

        subgraph PUB["Publicados en 0.0.0.0 (accesibles segun el firewall de GCP)"]
            APP["app (web) 0.0.0.0:8000 -> 8000"]
            AUTH["auth 0.0.0.0:8001 -> 8000"]
            DEV["devoluciones 0.0.0.0:8002 -> 8000"]
            LOG["logistica 0.0.0.0:8003 -> 8000"]
            INS["inspecciones 0.0.0.0:8004 -> 8000"]
            REE["reembolsos-costos 0.0.0.0:8005 -> 8000"]
            VEN["ventas-catalogos 0.0.0.0:8006 -> 8000"]
            EVI["evidencias 0.0.0.0:8007 -> 8000"]
            ANA["analisis-auditoria 0.0.0.0:8008 -> 8000"]
        end

        subgraph LOCAL["Publicados solo en 127.0.0.1 (solo desde la propia VM)"]
            PG[("postgres:16-alpine<br/>127.0.0.1:55432 -> 5432")]
            RD[("redis:7-alpine<br/>127.0.0.1:56379 -> 6379")]
            MG[("mongo:7<br/>127.0.0.1:57017 -> 27017")]
        end

        subgraph VOLS["Volumenes con nombre"]
            V1[/"postgres_data"/]
            V2[/"redis_data"/]
            V3[/"mongo_data"/]
            V4[/"evidencias_data"/]
        end

        RED{{"Red por defecto de Docker Compose<br/>DNS por nombre de servicio: postgres, redis, mongo, auth..."}}
    end

    INET -->|"HTTP :8000"| APP
    INET -->|"HTTP :8001-8008<br/>(Swagger /docs, /health)"| AUTH
    APP --- RED
    AUTH --- RED
    DEV --- RED
    LOG --- RED
    INS --- RED
    REE --- RED
    VEN --- RED
    EVI --- RED
    ANA --- RED
    RED --- PG
    RED --- RD
    RED --- MG

    PG --- V1
    RD --- V2
    MG --- V3
    EVI --- V4
```

## Puertos

| Contenedor | Puerto host | Enlace | Puerto interno | Comentario |
|---|---:|---|---:|---|
| app (web) | `${APP_PORT:-8000}` | `0.0.0.0` | 8000 | monta `./:/srv/app:z` (SELinux) |
| auth | 8001 | `0.0.0.0` | 8000 | con `healthcheck` |
| devoluciones | 8002 | `0.0.0.0` | 8000 | con `healthcheck` |
| logistica | 8003 | `0.0.0.0` | 8000 | sin `healthcheck` en el compose |
| inspecciones | 8004 | `0.0.0.0` | 8000 | sin `healthcheck` en el compose |
| reembolsos-costos | 8005 | `0.0.0.0` | 8000 | sin `healthcheck` en el compose |
| ventas-catalogos | 8006 | `0.0.0.0` | 8000 | con `healthcheck` |
| evidencias | 8007 | `0.0.0.0` | 8000 | con `healthcheck`; volumen `evidencias_data` en `/srv/evidencias_privadas` |
| analisis-auditoria | 8008 | `0.0.0.0` | 8000 | con `healthcheck` |
| postgres | 55432 | `127.0.0.1` | 5432 | el 5432 de la VM lo ocupa un PostgreSQL nativo ajeno |
| redis | 56379 | `127.0.0.1` | 6379 | `--appendonly yes` |
| mongo | 57017 | `127.0.0.1` | 27017 | `init.js` solo corre con el volumen vacio |

Los contenedores se hablan por la red interna de Compose usando el nombre del
servicio y el puerto **interno** (por ejemplo `http://auth:8000`,
`postgres:5432`); los puertos `55432/56379/57017` solo sirven para clientes
ejecutados dentro de la VM.

Los servicios sin `healthcheck` en el compose (logistica, inspecciones,
reembolsos-costos) igualmente exponen `GET /health`; el panel web
`/integracion/servicios` consulta los ocho.

## Volumenes

| Volumen | Montado en | Contenido |
|---|---|---|
| `postgres_data` | `/var/lib/postgresql/data` (postgres) | datos de PostgreSQL |
| `redis_data` | `/data` (redis) | AOF de Redis |
| `mongo_data` | `/data/db` (mongo) | datos de MongoDB |
| `evidencias_data` | `/srv/evidencias_privadas` (evidencias) | archivos JPG/PNG/PDF con nombre aleatorio |

> **EVIDENCIA PENDIENTE [EV-01]:** captura de `docker compose ps` en la VM con
> los 12 contenedores y sus puertos. <!-- EVIDENCIA PENDIENTE: EV-01 docker compose ps -->

> **EVIDENCIA PENDIENTE [EV-02]:** captura de las reglas de firewall de GCP y
> de la VM en la consola de Compute Engine.
> <!-- EVIDENCIA PENDIENTE: EV-02 firewall y VM en consola GCP -->
