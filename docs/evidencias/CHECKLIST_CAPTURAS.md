# Checklist de capturas

<!-- Generado por docs/postman/generar_colecciones.py. Marca [x] al guardar el archivo. -->

Guarda cada captura en `docs/evidencias/capturas/<id>.png` (la peticion y la respuesta visibles; **oculta o tacha el token Bearer**). Los ids son los mismos que los marcadores `CAPTURA PENDIENTE` de `docs/EVIDENCIAS.md`.

## auth

| Listo | Archivo | Carpeta de la coleccion | Caso |
|---|---|---|---|
| [ ] | `001_auth_get_health_200.png` | 00 Salud y contratos | health 200 |
| [ ] | `002_auth_get_health_200_xml.png` | 00 Salud y contratos | health 200 XML |
| [ ] | `003_auth_post_login_200.png` | 01 Login | login 200 exitoso |
| [ ] | `004_auth_post_login_200_xml.png` | 01 Login | login 200 XML (admin) |
| [ ] | `005_auth_post_login_400.png` | 01 Login | login 400 datos invalidos |
| [ ] | `006_auth_post_login_401.png` | 01 Login | login 401 credenciales invalidas |
| [ ] | `007_auth_post_login_415.png` | 01 Login | login 415 formato no soportado |
| [ ] | `008_auth_post_login_400_xml.png` | 01 Login | login 400 XML mal formado |
| [ ] | `009_auth_post_login_400_xml.png` | 01 Login | login 400 XML no cumple XSD |
| [ ] | `010_auth_get_sesion_200.png` | 02 Sesion | sesion 200 exitoso |
| [ ] | `011_auth_get_sesion_200_xml.png` | 02 Sesion | sesion 200 XML |
| [ ] | `012_auth_get_sesion_401.png` | 02 Sesion | sesion 401 sin token |
| [ ] | `013_auth_get_sesion_401.png` | 02 Sesion | sesion 401 token invalido |
| [ ] | `014_auth_post_refresh_200.png` | 03 Refresh | refresh 200 exitoso |
| [ ] | `015_auth_post_refresh_401.png` | 03 Refresh | refresh 401 con access token |
| [ ] | `016_auth_post_refresh_400.png` | 03 Refresh | refresh 400 sin refresh_token |
| [ ] | `017_auth_delete_usuarios_id_sesiones_403.png` | 04 Administracion de sesiones | cerrar sesiones 403 rol sin permiso |
| [ ] | `018_auth_delete_usuarios_id_sesiones_404.png` | 04 Administracion de sesiones | cerrar sesiones 404 usuario inexistente |
| [ ] | `019_auth_post_logout_200.png` | 05 Revocacion | logout 200 exitoso |
| [ ] | `020_auth_get_sesion_401.png` | 05 Revocacion | sesion 401 token revocado |
| [ ] | `021_auth_post_refresh_401.png` | 05 Revocacion | refresh 401 sesion inactiva |
| [ ] | `022_auth_delete_usuarios_id_sesiones_200.png` | 05 Revocacion | cerrar sesiones 200 admin |
| [ ] | `023_auth_get_sesion_401.png` | 05 Revocacion | sesion 401 sesion inactiva |
| [ ] | `024_auth_post_login_423.png` | 06 Casos limite (correr aparte, bloquea una cuenta 15 min) | login 423 cuenta bloqueada |
| [ ] | `025_auth_post_login_429.png` | 06 Casos limite (correr aparte, bloquea una cuenta 15 min) | login 429 rate limit |

## devoluciones

| Listo | Archivo | Carpeta de la coleccion | Caso |
|---|---|---|---|
| [ ] | `026_devoluciones_get_health_200.png` | 00 Preparacion (tokens) | health 200 |
| [ ] | `027_devoluciones_post_raiz_409.png` | 01 Registro (POST) | registrar 409 cantidad excedida |
| [ ] | `028_devoluciones_post_raiz_201.png` | 01 Registro (POST) | registrar 201 exitoso |
| [ ] | `029_devoluciones_post_raiz_201_xml.png` | 01 Registro (POST) | registrar 201 XML |
| [ ] | `030_devoluciones_post_raiz_400.png` | 01 Registro (POST) | registrar 400 datos invalidos |
| [ ] | `031_devoluciones_post_raiz_400_xml.png` | 01 Registro (POST) | registrar 400 XML no cumple XSD |
| [ ] | `032_devoluciones_post_raiz_401.png` | 01 Registro (POST) | registrar 401 sin token |
| [ ] | `033_devoluciones_post_raiz_403.png` | 01 Registro (POST) | registrar 403 compra de otro cliente |
| [ ] | `034_devoluciones_post_raiz_404.png` | 01 Registro (POST) | registrar 404 linea inexistente |
| [ ] | `035_devoluciones_get_raiz_200.png` | 02 Consulta (GET) | listar 200 cliente paginado |
| [ ] | `036_devoluciones_get_raiz_200_xml.png` | 02 Consulta (GET) | listar 200 analista filtro XML |
| [ ] | `037_devoluciones_get_raiz_400.png` | 02 Consulta (GET) | listar 400 estado invalido |
| [ ] | `038_devoluciones_get_raiz_401.png` | 02 Consulta (GET) | listar 401 sin token |
| [ ] | `039_devoluciones_get_raiz_401.png` | 02 Consulta (GET) | listar 401 token invalido |
| [ ] | `040_devoluciones_get_id_200.png` | 02 Consulta (GET) | detalle 200 exitoso |
| [ ] | `041_devoluciones_get_id_403.png` | 02 Consulta (GET) | detalle 403 otro cliente |
| [ ] | `042_devoluciones_get_id_404.png` | 02 Consulta (GET) | detalle 404 inexistente |
| [ ] | `043_devoluciones_patch_id_resolucion_403.png` | 03 Revision (PATCH y PUT) | resolver 403 cliente sin permiso |
| [ ] | `044_devoluciones_patch_id_resolucion_400.png` | 03 Revision (PATCH y PUT) | resolver 400 rechazo sin justificacion |
| [ ] | `045_devoluciones_patch_id_resolucion_200.png` | 03 Revision (PATCH y PUT) | resolver 200 pedir informacion |
| [ ] | `046_devoluciones_put_id_200.png` | 03 Revision (PATCH y PUT) | corregir 200 PUT |
| [ ] | `047_devoluciones_delete_id_409.png` | 03 Revision (PATCH y PUT) | cancelar 409 ya revisada |
| [ ] | `048_devoluciones_patch_id_resolucion_200_xml.png` | 03 Revision (PATCH y PUT) | resolver 200 autorizar XML |
| [ ] | `049_devoluciones_patch_id_resolucion_409.png` | 03 Revision (PATCH y PUT) | resolver 409 ya resuelta |
| [ ] | `050_devoluciones_get_id_200.png` | 03 Revision (PATCH y PUT) | detalle 200 historial completo |
| [ ] | `051_devoluciones_delete_id_200.png` | 04 Cancelacion (DELETE) | cancelar 200 exitoso |
| [ ] | `052_devoluciones_get_id_404.png` | 04 Cancelacion (DELETE) | detalle 404 cancelada |

## logistica

| Listo | Archivo | Carpeta de la coleccion | Caso |
|---|---|---|---|
| [ ] | `053_logistica_get_health_200.png` | 00 Preparacion (requiere devolucion_id autorizada: coleccion devoluciones) | health 200 |
| [ ] | `054_logistica_post_recolecciones_401.png` | 01 Programar recoleccion (POST) | programar 401 sin token |
| [ ] | `055_logistica_post_recolecciones_401.png` | 01 Programar recoleccion (POST) | programar 401 token invalido |
| [ ] | `056_logistica_post_recolecciones_403.png` | 01 Programar recoleccion (POST) | programar 403 centro sin permiso |
| [ ] | `057_logistica_post_recolecciones_400.png` | 01 Programar recoleccion (POST) | programar 400 devolucion_id invalido |
| [ ] | `058_logistica_post_recolecciones_404.png` | 01 Programar recoleccion (POST) | programar 404 devolucion inexistente |
| [ ] | `059_logistica_post_recolecciones_400.png` | 01 Programar recoleccion (POST) | programar 400 fecha en el pasado |
| [ ] | `060_logistica_post_recolecciones_400_xml.png` | 01 Programar recoleccion (POST) | programar 400 XML no cumple XSD |
| [ ] | `061_logistica_post_recolecciones_201.png` | 01 Programar recoleccion (POST) | programar 201 exitoso |
| [ ] | `062_logistica_post_recolecciones_409.png` | 01 Programar recoleccion (POST) | programar 409 ya programada |
| [ ] | `063_logistica_get_recolecciones_200.png` | 02 Consulta (GET) | listar 200 coordinador |
| [ ] | `064_logistica_get_recolecciones_200_xml.png` | 02 Consulta (GET) | listar 200 centro XML con filtro |
| [ ] | `065_logistica_get_recolecciones_400.png` | 02 Consulta (GET) | listar 400 estado invalido |
| [ ] | `066_logistica_get_recolecciones_403.png` | 02 Consulta (GET) | listar 403 cliente |
| [ ] | `067_logistica_get_recolecciones_401.png` | 02 Consulta (GET) | listar 401 sin token |
| [ ] | `068_logistica_patch_recolecciones_id_asignacion_403.png` | 03 Asignar ruta y transportista (PATCH) | asignar 403 centro sin permiso |
| [ ] | `069_logistica_patch_recolecciones_id_asignacion_400.png` | 03 Asignar ruta y transportista (PATCH) | asignar 400 ruta invalida |
| [ ] | `070_logistica_patch_recolecciones_id_asignacion_400.png` | 03 Asignar ruta y transportista (PATCH) | asignar 400 ruta inexistente |
| [ ] | `071_logistica_patch_recolecciones_id_asignacion_404.png` | 03 Asignar ruta y transportista (PATCH) | asignar 404 recoleccion inexistente |
| [ ] | `072_logistica_patch_recolecciones_id_asignacion_200_xml.png` | 03 Asignar ruta y transportista (PATCH) | asignar 200 XML |
| [ ] | `073_logistica_patch_recolecciones_id_estado_409.png` | 04 Estado de la recoleccion (PATCH) | estado 409 transicion invalida |
| [ ] | `074_logistica_patch_recolecciones_id_estado_404.png` | 04 Estado de la recoleccion (PATCH) | estado 404 inexistente |
| [ ] | `075_logistica_patch_recolecciones_id_estado_200.png` | 04 Estado de la recoleccion (PATCH) | estado 200 en_transito |
| [ ] | `076_logistica_patch_recolecciones_id_asignacion_409.png` | 04 Estado de la recoleccion (PATCH) | asignar 409 ya inicio |
| [ ] | `077_logistica_patch_recolecciones_id_estado_200_xml.png` | 04 Estado de la recoleccion (PATCH) | estado 200 completada XML |
| [ ] | `078_logistica_post_recepciones_403.png` | 05 Recepcion en el centro (POST) | recepcion 403 coordinador |
| [ ] | `079_logistica_post_recepciones_400.png` | 05 Recepcion en el centro (POST) | recepcion 400 devolucion invalida |
| [ ] | `080_logistica_post_recepciones_404.png` | 05 Recepcion en el centro (POST) | recepcion 404 inexistente |
| [ ] | `081_logistica_post_recepciones_400.png` | 05 Recepcion en el centro (POST) | recepcion 400 booleano invalido |
| [ ] | `082_logistica_post_recepciones_201.png` | 05 Recepcion en el centro (POST) | recepcion 201 exitoso |
| [ ] | `083_logistica_post_recepciones_409.png` | 05 Recepcion en el centro (POST) | recepcion 409 duplicada |

## inspecciones

| Listo | Archivo | Carpeta de la coleccion | Caso |
|---|---|---|---|
| [ ] | `084_inspecciones_get_health_200.png` | 00 Preparacion (requiere devolucion_id recibida: coleccion logistica) | health 200 |
| [ ] | `085_inspecciones_post_raiz_401.png` | 01 Registrar inspeccion (POST) | registrar 401 sin token |
| [ ] | `086_inspecciones_post_raiz_403.png` | 01 Registrar inspeccion (POST) | registrar 403 analista |
| [ ] | `087_inspecciones_post_raiz_400.png` | 01 Registrar inspeccion (POST) | registrar 400 devolucion_id invalido |
| [ ] | `088_inspecciones_post_raiz_404.png` | 01 Registrar inspeccion (POST) | registrar 404 devolucion inexistente |
| [ ] | `089_inspecciones_post_raiz_400_xml.png` | 01 Registrar inspeccion (POST) | registrar 400 XML no cumple XSD |
| [ ] | `090_inspecciones_post_raiz_400.png` | 01 Registrar inspeccion (POST) | registrar 400 empaque sin describir |
| [ ] | `091_inspecciones_post_raiz_400.png` | 01 Registrar inspeccion (POST) | registrar 400 booleano invalido |
| [ ] | `092_inspecciones_post_raiz_201.png` | 01 Registrar inspeccion (POST) | registrar 201 exitoso |
| [ ] | `093_inspecciones_post_raiz_409.png` | 01 Registrar inspeccion (POST) | registrar 409 duplicada |
| [ ] | `094_inspecciones_get_id_200.png` | 02 Consulta (GET) | detalle 200 inspector |
| [ ] | `095_inspecciones_get_id_200_xml.png` | 02 Consulta (GET) | detalle 200 analista XML |
| [ ] | `096_inspecciones_get_id_403.png` | 02 Consulta (GET) | detalle 403 cliente |
| [ ] | `097_inspecciones_get_id_404.png` | 02 Consulta (GET) | detalle 404 inexistente |
| [ ] | `098_inspecciones_get_id_401.png` | 02 Consulta (GET) | detalle 401 token invalido |
| [ ] | `099_inspecciones_patch_id_400.png` | 03 Actualizar detalle (PATCH) | actualizar 400 sin cambios |
| [ ] | `100_inspecciones_patch_id_403.png` | 03 Actualizar detalle (PATCH) | actualizar 403 analista |
| [ ] | `101_inspecciones_patch_id_404.png` | 03 Actualizar detalle (PATCH) | actualizar 404 inexistente |
| [ ] | `102_inspecciones_patch_id_200_xml.png` | 03 Actualizar detalle (PATCH) | actualizar 200 XML |
| [ ] | `103_inspecciones_post_id_disposicion_403.png` | 04 Disposicion (POST) | disposicion 403 inspector |
| [ ] | `104_inspecciones_post_id_disposicion_400.png` | 04 Disposicion (POST) | disposicion 400 destino invalido |
| [ ] | `105_inspecciones_post_id_disposicion_404.png` | 04 Disposicion (POST) | disposicion 404 inexistente |
| [ ] | `106_inspecciones_post_id_disposicion_201_xml.png` | 04 Disposicion (POST) | disposicion 201 XML |
| [ ] | `107_inspecciones_post_id_disposicion_409.png` | 04 Disposicion (POST) | disposicion 409 duplicada |
| [ ] | `108_inspecciones_post_inventario_id_etiqueta_403.png` | 05 Etiqueta de inventario (POST) | etiqueta 403 inspector |
| [ ] | `109_inspecciones_post_inventario_id_etiqueta_404.png` | 05 Etiqueta de inventario (POST) | etiqueta 404 inexistente |
| [ ] | `110_inspecciones_post_inventario_id_etiqueta_201.png` | 05 Etiqueta de inventario (POST) | etiqueta 201 exitoso |

## reembolsos_costos

| Listo | Archivo | Carpeta de la coleccion | Caso |
|---|---|---|---|
| [ ] | `111_reembolsos_costos_get_health_200.png` | 00 Preparacion (requiere devolucion_id autorizada o resuelta) | health 200 |
| [ ] | `112_reembolsos_costos_post_costos_401.png` | 01 Costos (POST) | costo 401 sin token |
| [ ] | `113_reembolsos_costos_post_costos_403.png` | 01 Costos (POST) | costo 403 cliente |
| [ ] | `114_reembolsos_costos_post_costos_403.png` | 01 Costos (POST) | costo 403 etapa de otro rol |
| [ ] | `115_reembolsos_costos_post_costos_400.png` | 01 Costos (POST) | costo 400 monto negativo |
| [ ] | `116_reembolsos_costos_post_costos_400.png` | 01 Costos (POST) | costo 400 etapa invalida |
| [ ] | `117_reembolsos_costos_post_costos_400.png` | 01 Costos (POST) | costo 400 devolucion_id invalido |
| [ ] | `118_reembolsos_costos_post_costos_400_xml.png` | 01 Costos (POST) | costo 400 XML no cumple XSD |
| [ ] | `119_reembolsos_costos_post_costos_404.png` | 01 Costos (POST) | costo 404 devolucion inexistente |
| [ ] | `120_reembolsos_costos_post_costos_201.png` | 01 Costos (POST) | costo 201 transporte JSON |
| [ ] | `121_reembolsos_costos_post_costos_201_xml.png` | 01 Costos (POST) | costo 201 almacenamiento XML |
| [ ] | `122_reembolsos_costos_post_reembolsos_403.png` | 02 Reembolsos (POST) | reembolso 403 analista |
| [ ] | `123_reembolsos_costos_post_reembolsos_400.png` | 02 Reembolsos (POST) | reembolso 400 estado invalido |
| [ ] | `124_reembolsos_costos_post_reembolsos_400.png` | 02 Reembolsos (POST) | reembolso 400 metodo invalido |
| [ ] | `125_reembolsos_costos_post_reembolsos_400.png` | 02 Reembolsos (POST) | reembolso 400 devolucion_id invalido |
| [ ] | `126_reembolsos_costos_post_reembolsos_404.png` | 02 Reembolsos (POST) | reembolso 404 devolucion inexistente |
| [ ] | `127_reembolsos_costos_post_reembolsos_409.png` | 02 Reembolsos (POST) | reembolso 409 monto excedido |
| [ ] | `128_reembolsos_costos_post_reembolsos_201.png` | 02 Reembolsos (POST) | reembolso 201 aprobado |
| [ ] | `129_reembolsos_costos_post_reembolsos_409_xml.png` | 02 Reembolsos (POST) | reembolso 409 duplicado XML |
| [ ] | `130_reembolsos_costos_get_reembolsos_200.png` | 03 Consulta (GET) | reembolsos 200 lista |
| [ ] | `131_reembolsos_costos_get_reembolsos_200_xml.png` | 03 Consulta (GET) | reembolsos 200 analista XML |
| [ ] | `132_reembolsos_costos_get_reembolsos_403.png` | 03 Consulta (GET) | reembolsos 403 cliente |
| [ ] | `133_reembolsos_costos_get_reembolsos_401.png` | 03 Consulta (GET) | reembolsos 401 token invalido |
| [ ] | `134_reembolsos_costos_get_costos_id_200.png` | 03 Consulta (GET) | costos 200 desglose |
| [ ] | `135_reembolsos_costos_get_costos_id_200_xml.png` | 03 Consulta (GET) | costos 200 analista XML |
| [ ] | `136_reembolsos_costos_get_costos_id_403.png` | 03 Consulta (GET) | costos 403 centro |
| [ ] | `137_reembolsos_costos_get_costos_id_404.png` | 03 Consulta (GET) | costos 404 devolucion inexistente |

## ventas_catalogos

| Listo | Archivo | Carpeta de la coleccion | Caso |
|---|---|---|---|
| [ ] | `138_ventas_catalogos_get_health_200.png` | 00 Preparacion (tokens) | health 200 |
| [ ] | `139_ventas_catalogos_get_raiz_200.png` | 01 Ventas | ventas 200 cliente paginado |
| [ ] | `140_ventas_catalogos_get_raiz_200_xml.png` | 01 Ventas | ventas 200 analista XML |
| [ ] | `141_ventas_catalogos_get_raiz_400.png` | 01 Ventas | ventas 400 paginacion invalida |
| [ ] | `142_ventas_catalogos_get_raiz_401.png` | 01 Ventas | ventas 401 sin token |
| [ ] | `143_ventas_catalogos_get_raiz_401.png` | 01 Ventas | ventas 401 token invalido |
| [ ] | `144_ventas_catalogos_get_id_200.png` | 01 Ventas | venta 200 detalle |
| [ ] | `145_ventas_catalogos_get_id_200_xml.png` | 01 Ventas | venta 200 detalle XML |
| [ ] | `146_ventas_catalogos_get_id_403.png` | 01 Ventas | venta 403 de otro cliente |
| [ ] | `147_ventas_catalogos_get_id_404.png` | 01 Ventas | venta 404 inexistente |
| [ ] | `148_ventas_catalogos_get_catalogos_200.png` | 02 Catalogos (lectura) | catalogos 200 lista |
| [ ] | `149_ventas_catalogos_get_catalogos_403.png` | 02 Catalogos (lectura) | catalogos 403 cliente |
| [ ] | `150_ventas_catalogos_get_catalogos_nombre_200.png` | 02 Catalogos (lectura) | catalogo motivos 200 cliente |
| [ ] | `151_ventas_catalogos_get_catalogos_nombre_200_xml.png` | 02 Catalogos (lectura) | catalogo motivos 200 XML con inactivos |
| [ ] | `152_ventas_catalogos_get_catalogos_nombre_403.png` | 02 Catalogos (lectura) | catalogo productos 403 cliente |
| [ ] | `153_ventas_catalogos_get_catalogos_nombre_404.png` | 02 Catalogos (lectura) | catalogo inexistente 404 |
| [ ] | `154_ventas_catalogos_get_catalogos_nombre_200.png` | 02 Catalogos (lectura) | catalogo rutas 200 |
| [ ] | `155_ventas_catalogos_get_catalogos_nombre_200.png` | 02 Catalogos (lectura) | catalogo transportistas 200 |
| [ ] | `156_ventas_catalogos_get_catalogos_nombre_registro_id_200.png` | 02 Catalogos (lectura) | registro 200 detalle |
| [ ] | `157_ventas_catalogos_get_catalogos_nombre_registro_id_404.png` | 02 Catalogos (lectura) | registro 404 inexistente |
| [ ] | `158_ventas_catalogos_post_catalogos_nombre_201.png` | 03 Catalogos (escritura, Administrador) | alta 201 JSON |
| [ ] | `159_ventas_catalogos_post_catalogos_nombre_201_xml.png` | 03 Catalogos (escritura, Administrador) | alta 201 XML |
| [ ] | `160_ventas_catalogos_post_catalogos_nombre_400.png` | 03 Catalogos (escritura, Administrador) | alta 400 sin nombre |
| [ ] | `161_ventas_catalogos_post_catalogos_nombre_401.png` | 03 Catalogos (escritura, Administrador) | alta 401 sin token |
| [ ] | `162_ventas_catalogos_post_catalogos_nombre_403.png` | 03 Catalogos (escritura, Administrador) | alta 403 analista |
| [ ] | `163_ventas_catalogos_post_catalogos_nombre_404.png` | 03 Catalogos (escritura, Administrador) | alta 404 catalogo inexistente |
| [ ] | `164_ventas_catalogos_post_catalogos_nombre_409.png` | 03 Catalogos (escritura, Administrador) | alta 409 referencia inactiva |
| [ ] | `165_ventas_catalogos_put_catalogos_nombre_registro_id_200.png` | 03 Catalogos (escritura, Administrador) | edicion 200 PUT |
| [ ] | `166_ventas_catalogos_put_catalogos_nombre_registro_id_400.png` | 03 Catalogos (escritura, Administrador) | edicion 400 tipo invalido |
| [ ] | `167_ventas_catalogos_put_catalogos_nombre_registro_id_404.png` | 03 Catalogos (escritura, Administrador) | edicion 404 inexistente |
| [ ] | `168_ventas_catalogos_patch_catalogos_nombre_id_estado_200.png` | 03 Catalogos (escritura, Administrador) | estado 200 desactivar |
| [ ] | `169_ventas_catalogos_patch_catalogos_nombre_id_estado_400.png` | 03 Catalogos (escritura, Administrador) | estado 400 booleano invalido |
| [ ] | `170_ventas_catalogos_patch_catalogos_nombre_id_estado_404.png` | 03 Catalogos (escritura, Administrador) | estado 404 inexistente |
| [ ] | `171_ventas_catalogos_delete_catalogos_nombre_registro_id_200.png` | 03 Catalogos (escritura, Administrador) | baja 200 desactivar |
| [ ] | `172_ventas_catalogos_delete_catalogos_nombre_registro_id_404.png` | 03 Catalogos (escritura, Administrador) | baja 404 inexistente |

## evidencias

| Listo | Archivo | Carpeta de la coleccion | Caso |
|---|---|---|---|
| [ ] | `173_evidencias_get_health_200.png` | 00 Preparacion (crea una devolucion propia para adjuntar) | health 200 |
| [ ] | `174_evidencias_post_raiz_201.png` | 01 Alta (POST) | alta 201 comentario JSON |
| [ ] | `175_evidencias_post_raiz_201_xml.png` | 01 Alta (POST) | alta 201 comentario XML |
| [ ] | `176_evidencias_post_raiz_201.png` | 01 Alta (POST) | alta 201 archivo PNG |
| [ ] | `177_evidencias_post_raiz_400.png` | 01 Alta (POST) | alta 400 comentario vacio |
| [ ] | `178_evidencias_post_raiz_400.png` | 01 Alta (POST) | alta 400 tipo no permitido en JSON |
| [ ] | `179_evidencias_post_raiz_400.png` | 01 Alta (POST) | alta 400 etapa invalida |
| [ ] | `180_evidencias_post_raiz_400.png` | 01 Alta (POST) | alta 400 multipart sin archivo |
| [ ] | `181_evidencias_post_raiz_401.png` | 01 Alta (POST) | alta 401 sin token |
| [ ] | `182_evidencias_post_raiz_401.png` | 01 Alta (POST) | alta 401 token invalido |
| [ ] | `183_evidencias_post_raiz_403.png` | 01 Alta (POST) | alta 403 analista |
| [ ] | `184_evidencias_post_raiz_403.png` | 01 Alta (POST) | alta 403 otro cliente |
| [ ] | `185_evidencias_post_raiz_403.png` | 01 Alta (POST) | alta 403 inspector sin inspeccion |
| [ ] | `186_evidencias_post_raiz_404.png` | 01 Alta (POST) | alta 404 devolucion inexistente |
| [ ] | `187_evidencias_post_raiz_409.png` | 01 Alta (POST) | alta 409 etapa no permitida al cliente |
| [ ] | `188_evidencias_post_raiz_415.png` | 01 Alta (POST) | alta 415 archivo no soportado |
| [ ] | `189_evidencias_get_raiz_200.png` | 02 Consulta (GET) | listar 200 cliente |
| [ ] | `190_evidencias_get_raiz_200_xml.png` | 02 Consulta (GET) | listar 200 analista XML |
| [ ] | `191_evidencias_get_raiz_400.png` | 02 Consulta (GET) | listar 400 sin devolucion_id |
| [ ] | `192_evidencias_get_raiz_403.png` | 02 Consulta (GET) | listar 403 otro cliente |
| [ ] | `193_evidencias_get_raiz_404.png` | 02 Consulta (GET) | listar 404 devolucion inexistente |
| [ ] | `194_evidencias_get_id_200.png` | 02 Consulta (GET) | detalle 200 con metadatos |
| [ ] | `195_evidencias_get_id_404.png` | 02 Consulta (GET) | detalle 404 inexistente |
| [ ] | `196_evidencias_get_id_403.png` | 02 Consulta (GET) | detalle 403 otro cliente |
| [ ] | `197_evidencias_get_id_enlace_200.png` | 02 Consulta (GET) | enlace 200 firmado |
| [ ] | `198_evidencias_get_id_enlace_409.png` | 02 Consulta (GET) | enlace 409 comentario sin archivo |
| [ ] | `199_evidencias_get_evidencia_id_archivo_200.png` | 02 Consulta (GET) | archivo 200 con enlace firmado |
| [ ] | `200_evidencias_get_id_archivo_200.png` | 02 Consulta (GET) | archivo 200 con Bearer |
| [ ] | `201_evidencias_get_id_archivo_401.png` | 02 Consulta (GET) | archivo 401 sin firma ni token |
| [ ] | `202_evidencias_get_id_archivo_404.png` | 02 Consulta (GET) | archivo 404 inexistente |
| [ ] | `203_evidencias_delete_id_403.png` | 03 Retiro (DELETE) | retiro 403 analista |
| [ ] | `204_evidencias_delete_id_403.png` | 03 Retiro (DELETE) | retiro 403 otro cliente |
| [ ] | `205_evidencias_delete_id_200.png` | 03 Retiro (DELETE) | retiro 200 exitoso |
| [ ] | `206_evidencias_delete_id_404.png` | 03 Retiro (DELETE) | retiro 404 ya retirada |
| [ ] | `207_evidencias_delete_id_404.png` | 03 Retiro (DELETE) | retiro 404 inexistente |
| [ ] | `208_evidencias_post_raiz_201.png` | 04 Inspector (requiere haber corrido la coleccion inspecciones) | alta 201 inspector en etapa inspeccion |

## analisis_auditoria

| Listo | Archivo | Carpeta de la coleccion | Caso |
|---|---|---|---|
| [ ] | `209_analisis_auditoria_get_health_200.png` | 00 Preparacion (tokens) | health 200 |
| [ ] | `210_analisis_auditoria_post_clasificar_motivo_200.png` | 01 Clasificar motivo (POST) | clasificar 200 cliente |
| [ ] | `211_analisis_auditoria_post_clasificar_motivo_200_xml.png` | 01 Clasificar motivo (POST) | clasificar 200 analista XML |
| [ ] | `212_analisis_auditoria_post_clasificar_motivo_400.png` | 01 Clasificar motivo (POST) | clasificar 400 descripcion corta |
| [ ] | `213_analisis_auditoria_post_clasificar_motivo_401.png` | 01 Clasificar motivo (POST) | clasificar 401 sin token |
| [ ] | `214_analisis_auditoria_post_clasificar_motivo_403.png` | 01 Clasificar motivo (POST) | clasificar 403 centro |
| [ ] | `215_analisis_auditoria_post_sincronizar_403.png` | 02 Sincronizar y Pareto | sincronizar 403 cliente |
| [ ] | `216_analisis_auditoria_post_sincronizar_401.png` | 02 Sincronizar y Pareto | sincronizar 401 sin token |
| [ ] | `217_analisis_auditoria_post_sincronizar_200.png` | 02 Sincronizar y Pareto | sincronizar 200 exitoso |
| [ ] | `218_analisis_auditoria_get_pareto_200.png` | 02 Sincronizar y Pareto | pareto 200 miss |
| [ ] | `219_analisis_auditoria_get_pareto_200.png` | 02 Sincronizar y Pareto | pareto 200 hit |
| [ ] | `220_analisis_auditoria_get_pareto_200_xml.png` | 02 Sincronizar y Pareto | pareto 200 XML por proveedor y costo |
| [ ] | `221_analisis_auditoria_get_pareto_400.png` | 02 Sincronizar y Pareto | pareto 400 dimension desconocida |
| [ ] | `222_analisis_auditoria_get_pareto_400.png` | 02 Sincronizar y Pareto | pareto 400 fecha invalida |
| [ ] | `223_analisis_auditoria_get_pareto_400.png` | 02 Sincronizar y Pareto | pareto 400 rango invertido |
| [ ] | `224_analisis_auditoria_get_pareto_403.png` | 02 Sincronizar y Pareto | pareto 403 cliente |
| [ ] | `225_analisis_auditoria_get_pareto_401.png` | 02 Sincronizar y Pareto | pareto 401 token invalido |
| [ ] | `226_analisis_auditoria_get_resumen_200.png` | 03 Resumen, alertas y eventos | resumen 200 |
| [ ] | `227_analisis_auditoria_get_resumen_403.png` | 03 Resumen, alertas y eventos | resumen 403 cliente |
| [ ] | `228_analisis_auditoria_get_alertas_fraude_200.png` | 03 Resumen, alertas y eventos | alertas 200 |
| [ ] | `229_analisis_auditoria_get_alertas_fraude_200_xml.png` | 03 Resumen, alertas y eventos | alertas 200 XML |
| [ ] | `230_analisis_auditoria_get_alertas_fraude_403.png` | 03 Resumen, alertas y eventos | alertas 403 cliente |
| [ ] | `231_analisis_auditoria_get_eventos_200.png` | 03 Resumen, alertas y eventos | eventos 200 paginado |
| [ ] | `232_analisis_auditoria_get_eventos_200_xml.png` | 03 Resumen, alertas y eventos | eventos 200 XML |
| [ ] | `233_analisis_auditoria_get_eventos_400.png` | 03 Resumen, alertas y eventos | eventos 400 correlation_id largo |
| [ ] | `234_analisis_auditoria_get_eventos_400.png` | 03 Resumen, alertas y eventos | eventos 400 paginacion invalida |
| [ ] | `235_analisis_auditoria_get_eventos_403.png` | 03 Resumen, alertas y eventos | eventos 403 cliente |
| [ ] | `236_analisis_auditoria_get_auditoria_200.png` | 04 Auditoria (bitacora) | bitacora 200 paginada |
| [ ] | `237_analisis_auditoria_get_auditoria_200_xml.png` | 04 Auditoria (bitacora) | bitacora 200 filtro XML |
| [ ] | `238_analisis_auditoria_get_auditoria_400.png` | 04 Auditoria (bitacora) | bitacora 400 filtro largo |
| [ ] | `239_analisis_auditoria_get_auditoria_403.png` | 04 Auditoria (bitacora) | bitacora 403 cliente |
| [ ] | `240_analisis_auditoria_get_auditoria_401.png` | 04 Auditoria (bitacora) | bitacora 401 sin token |

