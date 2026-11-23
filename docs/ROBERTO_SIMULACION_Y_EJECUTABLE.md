# Simulación integral y aplicación de escritorio — Roberto Sandoval

## Alcance comprobado

La simulación `SIM-6480AEC3` recorrió un proceso real desde la generación de una compra hasta el dictamen técnico del inspector. No sustituye los componentes de otros integrantes: los consume mediante sus contratos HTTP y utiliza la parte de Roberto para recepción, inspección, disposición, costos y cliente de escritorio.

El resultado reproducible se encuentra en `docs/evidencias/simulacion_roberto.json`. El caso principal quedó identificado como venta `33`, detalle `80`, devolución `56`, recolección `20`, recepción `16` e inspección `18`.

## Recorrido ejecutado

1. **Compra externa.** Un POS/ERP generó la venta y su detalle en PostgreSQL. `ventas-catalogos` es deliberadamente de consulta; no inventa compras dentro del sistema de devoluciones.
2. **Consulta y elegibilidad.** El cliente consultó su compra y `devoluciones` comprobó propiedad, producto, cantidad disponible y plazo.
3. **Solicitud.** Se creó `DEV-2026-0056`, vinculada al detalle concreto de la venta, no sólo a su encabezado.
4. **Evidencia inicial.** El comentario quedó referenciado en PostgreSQL y sus metadatos flexibles en MongoDB.
5. **Autorización.** Un analista autorizado cambió la solicitud a `autorizada`.
6. **Logística.** Se programó la recolección, se asignaron ruta y transportista, se transitó por `en_transito` y terminó en `completada`.
7. **Recepción.** El centro confirmó que el producto coincidía con el expediente; la devolución pasó a `recibida`.
8. **Inspección desde el contrato de escritorio.** Se envió XML, se validó contra XSD y se registró un dictamen concluido: producto apto y recomendación `reintegrar`.
9. **Evidencia del inspector.** Después de la asignación, el inspector pudo agregar evidencia. Antes de estar asignado, el servicio responde correctamente `403`.
10. **Lectura consolidada.** La referencia transaccional se recuperó de PostgreSQL y el detalle técnico de MongoDB. El estado final fue `en_inspeccion`, recibido e inspeccionado.

## Lectura del código por responsabilidad

- `scripts/simular_flujo_hasta_inspeccion.py`: orquesta el escenario sin saltarse APIs de negocio. Sólo la compra se inserta como evento de un POS externo.
- `apps/escritorio/main.py`: interfaz PySide6 por roles. El inspector consulta trabajo, registra hallazgos, propone disposición y visualiza evidencia; el centro gestiona recepción e inventario; reembolsos y supervisión sólo aparecen a roles autorizados.
- `apps/escritorio/cliente_xml.py`: único punto de comunicación del cliente. Fuerza XML, valida XSD antes de enviar, valida respuestas y transforma errores estándar sin exponer secretos.
- `services/inspecciones`: aplica reglas distintas para refrigerados y no refrigerados, mantiene la referencia relacional en PostgreSQL y el detalle variable en MongoDB.
- `services/disposicion_inventario`: exige autorización crítica para decidir destino, administra cuarentena y evita reincorporar inventario sin autorización.
- `services/reembolsos_costos`: calcula costos y recuperación y protege contra reembolsos duplicados mediante bloqueo distribuido.
- `services/evidencias`: controla pertenencia/asignación y mantiene metadatos en MongoDB. La prueba confirmó que un inspector no puede adjuntar evidencia antes de tener una inspección asignada.
- `services/auth`: emite JWT, aplica roles y consulta Redis para sesión/revocación. La aplicación no guarda contraseña ni token en disco.

## Ejecutable de escritorio

La aplicación se distribuye como `dist/CentroDevoluciones.exe`. El archivo `dist/config.json`, situado junto al ejecutable, permite cambiar las URL sin recompilar. Los contratos XSD se incluyen dentro del paquete y las rutas funcionan tanto desde código fuente como desde PyInstaller.

Para reconstruirlo:

```powershell
python -m pip install -r apps/escritorio/requirements.txt -r apps/escritorio/requirements-build.txt
powershell -ExecutionPolicy Bypass -File apps/escritorio/construir.ps1
```

El acceso directo del escritorio apunta al ejecutable en `dist`, con ese directorio como carpeta de inicio. Los microservicios y bases de datos deben estar levantados; el ejecutable es un cliente profesional y no reemplaza el backend distribuido.

## Evidencia y límites

- La simulación demuestra integración real con PostgreSQL, MongoDB, Redis, JWT, JSON entre servicios web y XML/XSD para escritorio.
- La compra, autorización y logística pertenecen a dependencias del flujo completo; no se presentan como desarrollo exclusivo de Roberto.
- La responsabilidad propia demostrada comprende el cliente de escritorio y su integración con inspecciones, disposición/inventario y reembolsos/costos.
- Se conserva como evidencia un primer intento controlado que produjo `403` por intentar registrar evidencia antes de asignar la inspección. No causó corrupción y confirmó la regla de autorización.
