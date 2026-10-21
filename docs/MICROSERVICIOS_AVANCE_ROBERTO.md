# Fichas tecnicas - avance de tres microservicios

Este documento registra el aporte de la rama `roberto/tres-microservicios` para
la segunda entrega. Completa tres de los seis servicios que faltaban despues de
`auth` y `devoluciones`: logistica, inspecciones y reembolsos-costos.

Todos usan rutas `/api/v1`, JWT comun, roles, revocacion/sesion en Redis,
respuestas JSON o XML segun `Accept`, cuerpos JSON o XML, errores uniformes,
correlation id, bitacora, `/health`, Swagger en `/docs` y contratos XSD en
`/contratos/<archivo>`.

## 1. Logistica inversa

| Elemento | Implementacion |
|---|---|
| Identificacion | `logistica`, puerto 8003. Programa, asigna, sigue y recibe recolecciones. |
| Justificacion | RF-12 a RF-15; conecta una devolucion autorizada con el centro de devoluciones. |
| Diseno | Flask Blueprint; validacion XSD; capa compartida de seguridad, respuestas e infraestructura. |
| Tecnologia | Python 3.11, Flask, psycopg2, Redis, PyJWT, lxml, Gunicorn. |
| Endpoints | `POST/GET /api/v1/logistica/recolecciones`; `PATCH .../{id}/asignacion`; `PATCH .../{id}/estado`; `POST /api/v1/logistica/recepciones`. |
| Entrada/salida | JSON o XML. `recoleccion.xsd`, `asignacion.xsd`, `estado_recoleccion.xsd`, `recepcion.xsd`. Codigos 200/201/400/401/403/404/409/415/500. |
| Seguridad | Coordinador programa/asigna/avanza; Encargado del Centro confirma recepcion. JWT y sesion Redis. |
| Persistencia | PostgreSQL: `recolecciones`, `recepciones`, `devoluciones`, `bitacora`. Redis: sesion y revocacion JWT. |
| Integracion | Consume el expediente iniciado por devoluciones. Cambia `autorizada -> en_recoleccion -> recibida`. |
| Despliegue | `services/logistica/Dockerfile`; servicio Compose `logistica`; puerto 8003. |
| Pruebas | Seguridad sin token, rol incorrecto y XML que no cumple XSD. |

Transiciones controladas: `programada -> asignada -> en_transito -> completada`
o `fallida`. La recepcion solo se admite si la recoleccion esta completada.

## 2. Inspecciones y disposicion

| Elemento | Implementacion |
|---|---|
| Identificacion | `inspecciones`, puerto 8004. Registra detalle tecnico, determina aptitud, disposicion y etiqueta. |
| Justificacion | RF-16 a RF-19 y RN-05 a RN-07; aplica reglas distintas a productos refrigerados. |
| Diseno | Escritura dual compensada: documento en MongoDB y referencia/resultado en PostgreSQL; si PostgreSQL falla, elimina el documento recien insertado. |
| Tecnologia | Python 3.11, Flask, PostgreSQL, MongoDB, Redis, PyJWT, lxml, Gunicorn. |
| Endpoints | `POST /api/v1/inspecciones`; `GET/PATCH /api/v1/inspecciones/{devolucion_id}`; `POST .../{id}/disposicion`; `POST .../inventario/{id}/etiqueta`. |
| Entrada/salida | JSON/XML; `inspeccion.xsd`, `inspeccion_actualizacion.xsd`, `disposicion.xsd`. |
| Seguridad | Inspector registra/actualiza; Analista decide disposicion; Encargado etiqueta inventario. |
| Persistencia | MongoDB `inspecciones` (indice unico `devolucion_id`); PostgreSQL `inspecciones_ref`, `disposiciones`, `inventario_recuperado`, `bitacora`. |
| Integracion | Recibe casos en estado `recibida`; deja `en_inspeccion` y despues `resuelta`. |
| Despliegue | `services/inspecciones/Dockerfile`; Compose `inspecciones`; puerto 8004. |
| Pruebas | Cuatro casos de aptitud: sano, dano, ruptura de cadena y exceso de tiempo. |

El producto no es apto si tiene danos, caducidad vencida o, siendo
refrigerado, ruptura de cadena de frio o mas de 30 minutos fuera de
refrigeracion. Un producto no apto no puede tener destino `inventario`.

## 3. Reembolsos y costos

| Elemento | Implementacion |
|---|---|
| Identificacion | `reembolsos-costos`, puerto 8005. Resuelve reembolsos y acumula costos por etapa. |
| Justificacion | RF-20, RF-21, RF-27, RN-03 y RN-04. Evita pagos duplicados. |
| Diseno | Lock distribuido Redis de 30 s por devolucion, fila PostgreSQL bloqueada y restriccion UNIQUE como tres defensas complementarias. |
| Tecnologia | Python 3.11, Flask, PostgreSQL, Redis, PyJWT, lxml, Gunicorn. |
| Endpoints | `POST/GET /api/v1/reembolsos-costos/reembolsos`; `POST /costos`; `GET /costos/{devolucion_id}`. |
| Entrada/salida | JSON/XML; `reembolso.xsd`, `costo.xsd`; codigos 200/201/400/401/403/404/409. |
| Seguridad | Encargado de Reembolsos resuelve; Encargado y Analista consultan; costos por roles autorizados. |
| Persistencia | PostgreSQL `reembolsos`, `costos`, `notificaciones`, `devoluciones`, `bitacora`; Redis `devoluciones:lock:reembolso:<id>` con TTL 30 s. |
| Integracion | Valida valor devuelto, notifica al cliente y cierra el caso si la disposicion ya lo dejo resuelto. |
| Despliegue | `services/reembolsos_costos/Dockerfile`; Compose `reembolsos-costos`; puerto 8005. |
| Pruebas | Sin token, rol prohibido, monto negativo y XML que viola XSD. |

La liberacion del lock usa compare-and-delete: un proceso nunca borra el lock
adquirido despues por otro proceso.

## Ejecucion y evidencias en la VM

```bash
docker compose up -d --build logistica inspecciones reembolsos-costos
docker compose ps
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
```

Swagger queda disponible en `http://HOST:8003/docs`, `:8004/docs` y
`:8005/docs`. Para la evidencia, ejecutar en cada endpoint un caso exitoso,
uno sin JWT, uno con rol incorrecto, uno con datos invalidos y uno que viole
una regla de negocio. Mostrar despues las filas de PostgreSQL, el documento de
MongoDB o la clave/TTL de Redis que correspondan.

## Resultado de pruebas locales

El 19 de octubre de 2026 se ejecutaron todas las pruebas sin bases reales:

- auth: 27 aprobadas;
- devoluciones: 24 aprobadas y 4 de integracion omitidas por requerir la VM;
- logistica: 3 aprobadas;
- inspecciones: 4 aprobadas;
- reembolsos-costos: 4 aprobadas.

Total: 62 aprobadas, 4 omitidas. La ejecucion integrada con PostgreSQL,
MongoDB y Redis debe hacerse en la VM conforme a las reglas del equipo.
