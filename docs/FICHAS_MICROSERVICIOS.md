# Fichas tecnicas de microservicios

Version verificada el 21 de octubre de 2026. Todos usan Flask 3, rutas
`/api/v1`, JWT HS256 emitido por `auth`, sesion/revocacion Redis, errores
uniformes con `X-Correlation-ID`, JSON/XML, Swagger en `/docs`, XSD publicados
en `/contratos/<archivo>.xsd`, Dockerfile propio y `/health`.

## 1. auth — puerto 8001

| Elemento | Implementacion |
|---|---|
| Proposito | Login, access/refresh JWT, consulta y revocacion de sesiones. |
| Justificacion | RF-01, RF-04, RF-30; punto comun de seguridad para toda la arquitectura. |
| Componentes | Blueprint Flask, `shared.seguridad`, PostgreSQL para usuarios/intentos y Redis para sesiones, rate limit y blacklist. |
| Endpoints | `/login`, `/refresh`, `/sesion`, `/logout`, `/usuarios/{id}/sesiones`, `/health`. |
| Entrada/salida | JSON o XML validado por cuatro XSD; respuesta negociada por `Accept`; 200/201/400/401/403/429/503. |
| Roles | Login publico; sesion/logout autenticados; revocacion global solo Administrador. |
| Despliegue/pruebas | `services/auth/Dockerfile`, Compose `auth`; 27 pruebas unitarias/API. |

## 2. devoluciones — puerto 8002

| Elemento | Implementacion |
|---|---|
| Proposito | Registrar, consultar, corregir, resolver y cancelar solicitudes ligadas a una linea de venta. |
| Justificacion | RF-06 a RF-11, RF-29, RN-01, RN-02, RN-12. |
| Persistencia | Expediente PostgreSQL, eventos MongoDB y seguridad/rate limit Redis. |
| Endpoints | `POST/GET /devoluciones`, `GET/PUT/DELETE /devoluciones/{id}`, `GET /{id}/historial`, `PATCH /{id}/resolucion`. |
| Reglas | Propiedad del cliente, cantidad disponible, estado valido, folio unico, eliminacion logica y autorizacion por rol. |
| Despliegue/pruebas | `services/devoluciones/Dockerfile`, Compose `devoluciones`; 24 pruebas aprobadas y 4 integraciones condicionadas a la VM. |

## 3. logistica — puerto 8003

| Elemento | Implementacion |
|---|---|
| Proposito | Programar y asignar recoleccion, controlar transiciones y confirmar recepcion. |
| Justificacion | RF-12, RF-13, RF-15 y trazabilidad RN-12. |
| Persistencia | `recolecciones`, `recepciones`, `devoluciones`, `rutas`, `transportistas`; sesion Redis. |
| Endpoints | `POST/GET /recolecciones`, `PATCH /recolecciones/{id}/asignacion`, `PATCH /{id}/estado`, `POST /recepciones`. |
| Reglas | Solo caso autorizado, fecha ISO no pasada, ruta/transportista activos, maquina de estados y booleano estricto. |
| Roles | Coordinador programa/asigna/actualiza; Encargado del Centro recibe. |
| Despliegue/pruebas | Dockerfile y Compose propios; 5 pruebas locales, incluidos 401/403/XML. |

## 4. inspecciones — puerto 8004

| Elemento | Implementacion |
|---|---|
| Proposito | Inspeccion tecnica, cadena de frio, disposicion e inventario recuperado. |
| Justificacion | RF-16 a RF-19 y RN-05 a RN-07. |
| Persistencia | Detalle semiestructurado MongoDB; referencia/veredicto, disposicion e inventario PostgreSQL; sesion Redis. |
| Endpoints | `POST /inspecciones`, `GET/PATCH /{devolucion_id}`, `POST /{id}/disposicion`, `POST /inventario/{id}/etiqueta`. |
| Reglas | Producto recibido, una inspeccion, minutos no negativos, booleanos estrictos, inventario solo si es apto. |
| Roles | Inspector inspecciona; Analista dispone; Encargado del Centro etiqueta. |
| Despliegue/pruebas | Dockerfile y Compose propios; 5 pruebas de reglas y seguridad. |

## 5. reembolsos-costos — puerto 8005

| Elemento | Implementacion |
|---|---|
| Proposito | Resolver un reembolso una sola vez y acumular costo por etapa. |
| Justificacion | RF-20, RF-21, RF-27, RN-03, RN-04. |
| Persistencia | PostgreSQL con `UNIQUE` y trigger de monto; lock Redis compare-and-delete evita doble proceso. |
| Endpoints | `POST/GET /reembolsos`, `POST /costos`, `GET /costos/{devolucion_id}`. |
| Reglas | Monto decimal finito, metodo permitido, caso autorizado, monto no mayor al vendido y cierre del expediente. |
| Roles | Encargado de Reembolsos resuelve; Encargado y Analista consultan/registran costos. |
| Despliegue/pruebas | Dockerfile y Compose propios; 5 pruebas, incluida regresion NaN/Infinity. |

## 6. ventas-catalogos — puerto 8006

| Elemento | Implementacion |
|---|---|
| Proposito | Consultar ventas/lineas y administrar siete catalogos reales. |
| Justificacion | RF-05 y RF-06; fuente para validar producto, lote, proveedor y motivo. |
| Persistencia | PostgreSQL; tablas y columnas dinamicas limitadas por listas blancas; sesion Redis. |
| Endpoints | `GET /ventas`, `GET /ventas/{id}`, CRUD y estado bajo `/catalogos/{nombre}`. |
| Reglas | Clientes solo ven sus ventas y motivos activos; referencias activas; paginacion y busqueda limitada. |
| Roles | Lectura autenticada con restricciones; escritura solo Administrador. |
| Despliegue/pruebas | Dockerfile y Compose propios; 8 pruebas puras de validacion. |

## 7. evidencias — puerto 8007

| Elemento | Implementacion |
|---|---|
| Proposito | Comentarios y archivos privados JPG/PNG/PDF asociados a la devolucion. |
| Justificacion | RF-09 y RNF-15; evita publicar archivos como contenido estatico. |
| Persistencia | Referencia oficial PostgreSQL, metadatos MongoDB y bytes en volumen `evidencias_data`. |
| Endpoints | `POST/GET /evidencias`, `GET/DELETE /{id}`, `GET /{id}/enlace`, `GET /{id}/archivo`. |
| Reglas | Magic bytes, maximo 10 MB, nombre interno aleatorio, propiedad/asignacion, enlace HMAC de 15 minutos y retiro logico. |
| Roles | Cliente adjunta en solicitud; Inspector en inspeccion; roles internos autorizados consultan. |
| Despliegue/pruebas | Dockerfile, volumen y Compose propios; 3 pruebas de archivo/ruta/extension. |

## 8. analisis-auditoria — puerto 8008

| Elemento | Implementacion |
|---|---|
| Proposito | Snapshot analitico, Pareto, patrones, clasificacion, fraude y auditoria. |
| Justificacion | RF-22 a RF-26 y RF-30; mantiene decisiones humanas y no altera el expediente. |
| Persistencia | Lee PostgreSQL, materializa resultados/eventos en MongoDB y cachea Pareto 600 s en Redis. |
| Endpoints | `/sincronizar`, `/pareto`, `/resumen`, `/eventos`, `/clasificar-motivo`, `/alertas-fraude`, `/api/v1/auditoria`. |
| Reglas | Dimensiones/medidas en lista blanca, fechas ISO, version de cache, sugerencias explicables y alertas sin acusacion automatica. |
| Roles | Administrador/Analista; Cliente tambien puede solicitar sugerencia de motivo. |
| Despliegue/pruebas | Dockerfile y Compose propios; 4 pruebas del pipeline y clasificador. |

## Evidencia requerida por endpoint

Para cada operacion se debe anexar: URL/metodo, objetivo, parametros, headers,
body JSON o XML, respuesta completa, codigo HTTP, captura Swagger/Postman,
efecto en PostgreSQL/MongoDB/Redis y al menos un error controlado. El codigo y
esta ficha no sustituyen esas ejecuciones.
