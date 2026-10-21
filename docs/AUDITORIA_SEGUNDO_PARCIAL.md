# Auditoria de cumplimiento — segundo parcial

Fecha de corte: 21 de octubre de 2026. Esta auditoria distingue implementacion,
verificacion local y evidencia que solo puede obtenerse en la VM.

## Resultado ejecutivo

| Rubro | Peso | Estado actual | Riesgo |
|---|---:|---|---|
| Documentacion tecnica | 20% | Arquitectura, setup, trazabilidad y 8 fichas actualizadas; falta incorporar capturas y resultados reales al documento final | medio |
| Microservicios | 25% | 8 responsabilidades reales, Dockerfile, v1, JWT/RBAC, health y Swagger | bajo hasta probar imagenes en VM |
| Request/response y contratos | 15% | 8 OpenAPI y 22 XSD validos; colecciones parciales; faltan capturas y matriz por cada endpoint | alto |
| Web + PostgreSQL + MongoDB + Redis + JWT + Docker | 20% | Integracion declarada en Compose y panel web de salud; falta demostrar proceso de negocio web→API y despliegue conjunto | alto |
| Pruebas y cumplimiento | 10% | 84 pruebas locales aprobadas, 4 integraciones condicionadas; falta suite E2E de los 8 servicios | medio-alto |
| Presentacion y YouTube | 10% | Guion base actualizado; video/capturas dependen del equipo | alto |

No debe afirmarse cumplimiento del 100% hasta completar los controles de VM
marcados abajo. El codigo esta considerablemente avanzado, pero la rubrica
otorga puntos por demostracion real, no solo por archivos presentes.

## Verificado localmente

- Ocho servicios importan y compilan.
- 84 pruebas pasan; cuatro pruebas de integracion de devoluciones se omiten si
  `INTEGRACION` no vale `1`.
- Ocho documentos OpenAPI cargan como YAML.
- Veintidos XSD compilan con `lxml`.
- `docker compose config` resuelve 12 servicios y cuatro volumenes usando
  `.env.example` como archivo de validacion.
- No se versionan `.env`, bytecode, cache de pytest ni dependencias locales.
- JWT, rol, sesion activa y revocacion Redis se verifican mediante
  `shared/seguridad.py` en todos los endpoints protegidos.
- JSON/XML y errores uniformes se centralizan en `shared/respuestas.py`.
- Se corrigieron validaciones de fecha, booleanos, minutos y montos no finitos.
- El web consulta los ocho `/health` sin perder su operacion independiente.

## Bloqueadores antes de declarar “todo bien”

1. **Resuelto el 21 de octubre de 2026:** Compose fue construido en la VM, los
   nueve endpoints web/servicios respondieron 200 y las dependencias quedaron
   saludables.
2. Ejecutar `INTEGRACION=1` para las pruebas distribuidas y crear una suite E2E
   que recorra auth→venta→devolucion→logistica→inspeccion→evidencia→reembolso→Pareto.
3. **Resuelto en la rama `roberto/integracion-web-microservicios`:** se ejecuto
   web→auth→ventas/devoluciones→logistica→inspecciones→reembolso y se cerro el
   caso `DEV-2026-0033`. Ver `docs/INTEGRACION_WEB_MICROSERVICIOS.md`.
4. Completar Postman por **cada endpoint** con 2xx, validacion 400, 401, 403,
   404 y conflicto 409 cuando corresponda.
5. Capturar evidencia persistida: filas PostgreSQL, documentos MongoDB, claves
   Redis con TTL/blacklist/cache/lock y archivos del volumen privado.
6. Probar en vivo request y response XML contra cada endpoint con body; Swagger
   debe mostrar ejemplos y aceptar `Bearer` real.
7. Incorporar capturas, resultados obtenidos y responsables al documento final.
8. Grabar el video de YouTube y ensayar la participacion de los cuatro miembros.

## Proceso E2E obligatorio sugerido

1. `auth`: login y token; mostrar sesion Redis.
2. `ventas-catalogos`: localizar una linea vendida.
3. `analisis-auditoria`: sugerir motivo a partir de la descripcion.
4. `devoluciones`: registrar y autorizar la solicitud.
5. `evidencias`: adjuntar una fotografia y mostrar PostgreSQL, Mongo y volumen.
6. `logistica`: programar, asignar, pasar a transito/completada y recibir.
7. `inspecciones`: registrar cadena de frio, disponer y etiquetar si aplica.
8. `reembolsos-costos`: aprobar una vez; repetir para demostrar el 409/lock.
9. `analisis-auditoria`: sincronizar, ejecutar Pareto y alertas de fraude;
   repetir Pareto para demostrar `cache=hit` y TTL Redis.
10. Web: abrir **Servicios** y verificar 8/8 disponibles; mostrar historial y
    correlacion del caso.

## Criterio de salida

El proyecto se considera listo cuando: Compose esta healthy; la suite local y
E2E pasa; cada endpoint tiene evidencia exitosa y de error; JSON y XML fueron
ejecutados; las tres bases y el volumen muestran efectos reales; el web llama
una API de negocio; y la documentacion final contiene capturas coherentes con
el commit presentado.
