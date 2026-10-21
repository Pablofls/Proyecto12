# Secuencia: proceso completo de una devolucion

Recorre una devolucion de un producto refrigerado desde el login hasta el
Pareto, con las transiciones de estado que realmente aplica el codigo. Verificado
contra los `app.py` de los ocho servicios y las migraciones 001 a 013.

Estados de `devoluciones.estado` (CHECK de la migracion 001):
`solicitada` -> `en_revision` / `autorizada` / `rechazada` -> `en_recoleccion`
-> `recibida` -> `en_inspeccion` -> `resuelta` -> `cerrada`.

Todas las llamadas llevan `Authorization: Bearer` y cada servicio verifica el
JWT y consulta Redis antes de ejecutar (ver `secuencia_login_jwt.md`); aqui no
se repite para no saturar el diagrama.

Trazabilidad: RF-01, RF-06 a RF-13, RF-15 a RF-23, RF-26, RF-27, RN-01 a RN-07,
RNF-19, RNF-23.

```mermaid
sequenceDiagram
    autonumber
    actor CLI as Cliente
    actor ANL as Analista
    actor COO as Coordinador de Logistica
    actor ENC as Encargado del Centro
    actor INSP as Inspector
    actor REEM as Encargado de Reembolsos
    participant AU as auth
    participant VE as ventas-catalogos
    participant DE as devoluciones
    participant EV as evidencias
    participant LO as logistica
    participant IN as inspecciones
    participant RE as reembolsos-costos
    participant AN as analisis-auditoria
    participant PG as PostgreSQL
    participant MG as MongoDB
    participant RD as Redis

    rect rgb(235, 242, 250)
    Note over CLI,AU: 1. Autenticacion
    CLI->>AU: POST /api/v1/auth/login
    AU->>RD: sesion_api:SID + limite + intentos
    AU-->>CLI: access y refresh token
    end

    rect rgb(235, 250, 240)
    Note over CLI,DE: 2. Venta y solicitud (RF-06, RF-07, RN-01)
    CLI->>VE: GET /api/v1/ventas/ID (solo sus ventas)
    VE->>PG: venta y lineas con cantidad disponible
    VE-->>CLI: lineas de venta
    opt sugerencia de motivo (RF-22)
        CLI->>AN: POST /api/v1/analisis/clasificar-motivo
        AN-->>CLI: sugerencias con requiere_confirmacion = true
    end
    CLI->>DE: POST /api/v1/devoluciones (venta_detalle_id, motivo, cantidad)
    DE->>RD: limite crear_devolucion (20 por minuto)
    DE->>PG: SELECT linea FOR UPDATE y cantidad ya devuelta
    alt cantidad mayor a la disponible
        DE-->>CLI: 409 cantidad_excedida
    end
    DE->>PG: INSERT devoluciones (estado solicitada, folio por secuencia)
    DE->>PG: INSERT bitacora (alta_devolucion)
    DE->>MG: INSERT eventos (devolucion_registrada, correlation_id)
    DE-->>CLI: 201 folio DEV-AAAA-NNNN
    end

    rect rgb(250, 245, 230)
    Note over CLI,EV: 3. Evidencia (RF-09)
    CLI->>EV: POST /api/v1/evidencias (multipart JPG, PNG o PDF)
    EV->>EV: valida magic bytes, maximo 10 MB, nombre aleatorio
    EV->>EV: guarda el archivo en el volumen evidencias_data
    EV->>PG: INSERT evidencias (bucket, objeto, mime, tamano)
    EV->>MG: INSERT evidencias_metadatos
    EV-->>CLI: 201 id y metadatos_id
    end

    rect rgb(250, 238, 238)
    Note over ANL,DE: 4. Autorizacion (RF-10)
    ANL->>DE: PATCH /api/v1/devoluciones/ID/resolucion decision = autorizar
    DE->>PG: SELECT FOR UPDATE, UPDATE estado = autorizada
    DE->>PG: INSERT notificaciones (cliente) y bitacora
    DE->>MG: INSERT eventos (devolucion_autorizacion)
    DE-->>ANL: 200 estado autorizada
    end

    rect rgb(240, 236, 250)
    Note over COO,LO: 5. Logistica (RF-12, RF-13, RF-15)
    COO->>LO: POST /recolecciones (fecha, lugar)
    LO->>PG: INSERT recolecciones, estado devolucion = en_recoleccion
    COO->>LO: PATCH /recolecciones/ID/asignacion (ruta, transportista)
    COO->>LO: PATCH /recolecciones/ID/estado en_transito, luego completada
    ENC->>LO: POST /recepciones
    LO->>PG: INSERT recepciones, estado devolucion = recibida
    end

    rect rgb(232, 246, 246)
    Note over INSP,IN: 6. Inspeccion y disposicion (RF-16 a RF-19, RN-05 a RN-07)
    INSP->>IN: POST /api/v1/inspecciones (cadena de frio, minutos, danos)
    IN->>IN: evaluar_aptitud (mas de 30 min fuera de refrigeracion = no apto)
    IN->>MG: INSERT inspecciones (documento de detalle)
    IN->>PG: INSERT inspecciones_ref (mongo_doc_id, apto_para_inventario)
    IN->>PG: UPDATE estado devolucion = en_inspeccion
    ANL->>IN: POST /api/v1/inspecciones/ID/disposicion destino
    IN->>PG: INSERT disposiciones (trigger fn_validar_destino_inventario)
    alt destino inventario y la inspeccion dice no apto
        IN-->>ANL: 409 no_apto_inventario
    end
    IN->>PG: UPDATE estado devolucion = resuelta
    opt destino inventario
        ENC->>IN: POST /inventario/DISPOSICION/etiqueta
        IN->>PG: INSERT inventario_recuperado (etiqueta REC-...)
    end
    end

    rect rgb(250, 242, 232)
    Note over REEM,RE: 7. Reembolso unico (RF-20, RF-21, RN-03, RN-04)
    REEM->>RE: POST /api/v1/reembolsos-costos/reembolsos
    RE->>RD: SET lock:reembolso:ID NX EX 30
    alt el lock ya existe
        RE-->>REEM: 409 reembolso_en_proceso
    end
    RE->>PG: SELECT devolucion FOR UPDATE y valida estado y monto
    RE->>PG: INSERT reembolsos (UNIQUE devolucion_id, trigger fn_validar_reembolso)
    RE->>PG: INSERT costos (etapa reembolso)
    RE->>PG: UPDATE devolucion = cerrada con fecha_cierre
    RE->>PG: INSERT notificaciones y bitacora
    RE->>RD: libera el lock (compare-and-delete con Lua)
    RE-->>REEM: 201 reembolso aprobado
    REEM->>RE: segundo POST para la misma devolucion
    RE->>PG: ya existe un reembolso vigente
    RE-->>REEM: 409 reembolso_duplicado
    end

    rect rgb(238, 238, 238)
    Note over ANL,AN: 8. Analisis de causa raiz (RF-23, RF-26)
    ANL->>AN: POST /api/v1/analisis/sincronizar
    AN->>PG: SELECT de snapshots (solo lectura)
    AN->>MG: bulk upsert resultados_analisis (snapshot_devolucion)
    AN->>RD: INCR analisis:version
    ANL->>AN: GET /api/v1/analisis/pareto?dimension=motivo
    AN->>RD: GET cache:causas:HASH
    AN->>MG: aggregate (match, group, sort) y guarda el calculo
    AN->>RD: SETEX cache:causas:HASH 600 s
    AN-->>ANL: 200 cache = miss
    ANL->>AN: GET /api/v1/analisis/pareto (mismos parametros)
    AN->>RD: GET cache:causas:HASH
    AN-->>ANL: 200 cache = hit
    end
```

## Lo que el diagrama no inventa

- El **segundo intento de reembolso** devuelve `409 reembolso_duplicado`. Si
  dos solicitudes llegan a la vez, la segunda recibe `409 reembolso_en_proceso`
  por el lock de Redis; si el lock ya se libero, la protege el `UNIQUE
  (devolucion_id)` y la verificacion previa.
- El estado `cerrada` solo se aplica si la devolucion estaba `resuelta`
  (`services/reembolsos_costos/app.py`). Un rechazo del reembolso tambien
  queda registrado como fila en `reembolsos` con monto 0.
- Solo `devoluciones` publica eventos en la coleccion `eventos`; los otros
  servicios dejan huella en `bitacora` (PostgreSQL) con el mismo
  `correlation_id`.
- El hash de `cache:causas:HASH` incluye la version de datos, dimension, medida
  y rango de fechas; una nueva sincronizacion invalida el cache sin borrarlo.

> **EVIDENCIA PENDIENTE [EV-04]:** ejecucion real de este flujo en la VM
> (Postman o web) con capturas de cada paso, filas de PostgreSQL, documentos
> de MongoDB y claves de Redis. Existe un antecedente narrado en
> `docs/INTEGRACION_WEB_MICROSERVICIOS.md` (caso `DEV-2026-0033`), pero sin
> capturas en el repositorio.
> <!-- EVIDENCIA PENDIENTE: EV-04 flujo E2E con capturas -->
