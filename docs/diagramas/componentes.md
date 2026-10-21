# Diagrama de componentes

Muestra las piezas del sistema y el protocolo de cada conexion. Se verifico
contra `docker-compose.yml`, `apps/web/app/config.py` (`SERVICE_URLS`),
`shared/infra.py`, `shared/mongo.py` y los `import` de cada `services/*/app.py`.

Trazabilidad: RNF-02, RNF-03, RNF-06, RNF-27, RF-31, RF-32.

```mermaid
flowchart LR
    NAV["Navegador<br/>(cliente web)"]
    MOV["Clientes movil y escritorio<br/>(fuera de alcance, contrato listo)"]

    subgraph WEB["Monolito web - Flask + Jinja2 (puerto 8000)"]
        W["apps/web/app<br/>blueprints + api_client.py"]
    end

    subgraph SRV["Microservicios - Flask + gunicorn, /api/v1"]
        AUTH["auth :8001"]
        DEV["devoluciones :8002"]
        LOG["logistica :8003"]
        INS["inspecciones :8004"]
        REE["reembolsos-costos :8005"]
        VEN["ventas-catalogos :8006"]
        EVI["evidencias :8007"]
        ANA["analisis-auditoria :8008"]
        SH[["shared/ (JWT, JSON/XML, XSD, paginacion)<br/>copiado en cada imagen"]]
    end

    subgraph DATOS["Persistencia (contenedores en la VM)"]
        PG[("PostgreSQL 16<br/>expediente transaccional")]
        RD[("Redis 7<br/>sesiones, revocacion, cache, lock")]
        MG[("MongoDB 7<br/>detalle semiestructurado")]
        VOL[/"Volumen evidencias_data<br/>archivos privados"/]
    end

    NAV -->|"HTTP, cookie de sesion"| W
    MOV -.->|"HTTP + JWT, JSON / XML"| SRV

    W -->|"HTTP + JWT + X-Correlation-ID (JSON)"| AUTH
    W -->|"HTTP + JWT"| DEV
    W -->|"HTTP + JWT"| LOG
    W -->|"HTTP + JWT"| INS
    W -->|"HTTP + JWT"| REE
    W -->|"HTTP + JWT"| VEN
    W -->|"HTTP + JWT"| EVI
    W -->|"HTTP + JWT"| ANA
    W -->|"GET /health de los 8 servicios"| SRV

    W -->|"SQL psycopg2 (lecturas compuestas)"| PG
    W -->|"Flask-Session, intentos y bloqueo"| RD

    AUTH -->|SQL| PG
    AUTH -->|"comandos Redis"| RD
    DEV -->|SQL| PG
    DEV -->|"comandos Redis"| RD
    DEV -->|"pymongo (eventos)"| MG
    LOG -->|SQL| PG
    LOG -->|"comandos Redis"| RD
    INS -->|SQL| PG
    INS -->|"comandos Redis"| RD
    INS -->|"pymongo (inspecciones)"| MG
    REE -->|SQL| PG
    REE -->|"comandos Redis (lock)"| RD
    VEN -->|SQL| PG
    VEN -->|"comandos Redis"| RD
    EVI -->|SQL| PG
    EVI -->|"comandos Redis"| RD
    EVI -->|"pymongo (metadatos)"| MG
    EVI -->|"archivos en disco"| VOL
    ANA -->|"SQL (solo lectura de negocio)"| PG
    ANA -->|"comandos Redis (cache Pareto)"| RD
    ANA -->|"pymongo (snapshots, Pareto)"| MG
```

## Lectura del diagrama

- Los **ocho** servicios consultan Redis en cada peticion protegida para
  verificar la sesion y la revocacion (`shared/seguridad.py:comprobar_en_redis`).
  Por eso todos tienen una flecha a Redis aunque solo `auth` escribe sesiones.
- Solo `devoluciones`, `inspecciones`, `evidencias` y `analisis-auditoria`
  hablan con MongoDB. `logistica`, `reembolsos-costos`, `ventas-catalogos` y
  `auth` no lo usan, y por eso sus contenedores no declaran `depends_on: mongo`.
- El web **no** se conecta a MongoDB.
- Las lecturas compuestas del expediente y de los paneles siguen yendo del web
  a PostgreSQL; las mutaciones del proceso pasan por el servicio responsable
  (`docs/INTEGRACION_WEB_MICROSERVICIOS.md`). Con `USE_MICROSERVICES=false` el
  web recupera su modo monolito.
- Los clientes movil y escritorio no forman parte de esta entrega (ver
  `CLAUDE.md`, "Alcance"); la linea punteada indica que el contrato JSON/XML ya
  esta implementado.
