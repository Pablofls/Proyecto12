# Validación para Persona 2 — Orvia Campo

## Evidencia mínima para presentar al profesor

- [ ] App compilada con Gradle `assembleDebug`; guardar nombre de APK, commit y captura de versión.
- [ ] Login cliente por `/api/v1/auth` a través del reverse proxy; captura petición/respuesta censurando tokens.
- [ ] Lista de compras real (`ventas-catalogos` 8006), eligibilidad y alta válida en 8002.
- [ ] Alta inválida: venta ajena o fuera de plazo. Comprobar HTTP 403/409 según contrato.
- [ ] Cámara: fotografía JPG real; registro de archivo en 8007 con metadatos PostgreSQL/MongoDB.
- [ ] Recolector: ID de recolección asignada por coordinador, cambio `asignada → en_transito` con GPS.
- [ ] Apagar conexión, guardar evidencia, verificar la etiqueta `pendiente` y cola local cifrada.
- [ ] Recuperar red; demostrar sincronización 8020 y evidencia registrada una sola vez.
- [ ] Reintentar exactamente el mismo `id_operacion`; comprobar `repetida: true` sin duplicar datos.
- [ ] Provocar conflicto cambiando estado en servidor antes de sincronizar; debe quedar `conflicto`.
- [ ] Operador de almacén: recepción después de recolección completada; duplicado rechazado.
- [ ] Escanear QR con el ID numérico y comprobar que se rellena el campo correspondiente.
- [ ] Validar roles: un usuario sin permiso recibe 403, no se oculta ni interpreta como éxito.
- [ ] Logout revoca token; token antiguo debe responder 401.
- [ ] Revisar timeouts, permisos GPS y cámara en un teléfono físico, no solo emulador.

## Dependencias del equipo pendientes

1. `8017` notificaciones push/correo/avisos externos y configuración FCM — no está integrado.
2. `8003` listado de recolecciones **filtrado para Recolector**, QR generado por backend y pertenencia de tareas.
3. Firmas de recepción y video seguro en `8007` con política de retención, antivirus y verificación contra archivos maliciosos.
4. Información de rutas y seguimiento GPS en serie, no solo ubicación puntual por evento.
5. Reporte final de pruebas de Android + APIs en el commit exacto de entrega.

## Riesgos conocidos

- La captura de imagen usa Android Camera Intent y comprime a JPEG. La rotación EXIF requiere comprobarse en dispositivos físicos variados.
- La cola con foto cifrada utiliza almacenamiento privado de la app: en Android con almacenamiento limitado conviene migrar a Room/archivos cifrados por operación y hacer política de tamaño antes de producción.
- Google Code Scanner necesita servicios de Google Play disponibles y puede requerir descargar el módulo de escaneo; la entrada manual por ID sigue disponible.
- `http://` es solo para pruebas controladas. Usar HTTPS en producción.
- La app Android no sustituye la validación de permisos, idempotencia ni autorizaciones críticas del backend.
