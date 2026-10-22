# Checklist de capturas

<!-- Generado por docs/postman/generar_colecciones.py. Marca [x] al guardar el archivo. -->

Guarda cada captura en `docs/evidencias/capturas/<id>.png` (la peticion y la respuesta visibles; **oculta o tacha el token Bearer**). Los ids son los mismos que los marcadores `CAPTURA PENDIENTE` de `docs/EVIDENCIAS.md`.

## auth

| Listo | Archivo | Carpeta de la coleccion | Caso |
|---|---|---|---|
| [x] | `001_auth_get_health_200.png` | 00 Salud y contratos | health 200 |
| [x] | `002_auth_get_health_200_xml.png` | 00 Salud y contratos | health 200 XML |
| [x] | `003_auth_post_login_200.png` | 01 Login | login 200 exitoso |
| [x] | `004_auth_post_login_200_xml.png` | 01 Login | login 200 XML (admin) |
| [x] | `005_auth_post_login_400.png` | 01 Login | login 400 datos invalidos |
| [x] | `006_auth_post_login_401.png` | 01 Login | login 401 credenciales invalidas |
| [x] | `007_auth_post_login_415.png` | 01 Login | login 415 formato no soportado |
| [x] | `008_auth_post_login_400_xml.png` | 01 Login | login 400 XML mal formado |
| [x] | `009_auth_post_login_400_xml.png` | 01 Login | login 400 XML no cumple XSD |
| [x] | `010_auth_get_sesion_200.png` | 02 Sesion | sesion 200 exitoso |
| [x] | `011_auth_get_sesion_200_xml.png` | 02 Sesion | sesion 200 XML |
| [x] | `012_auth_get_sesion_401.png` | 02 Sesion | sesion 401 sin token |
| [x] | `013_auth_get_sesion_401.png` | 02 Sesion | sesion 401 token invalido |
| [x] | `014_auth_post_refresh_200.png` | 03 Refresh | refresh 200 exitoso |
| [x] | `015_auth_post_refresh_401.png` | 03 Refresh | refresh 401 con access token |
| [x] | `016_auth_post_refresh_400.png` | 03 Refresh | refresh 400 sin refresh_token |
| [x] | `017_auth_delete_usuarios_id_sesiones_403.png` | 04 Administracion de sesiones | cerrar sesiones 403 rol sin permiso |
| [x] | `018_auth_delete_usuarios_id_sesiones_404.png` | 04 Administracion de sesiones | cerrar sesiones 404 usuario inexistente |
| [x] | `019_auth_post_logout_200.png` | 05 Revocacion | logout 200 exitoso |
| [x] | `020_auth_get_sesion_401.png` | 05 Revocacion | sesion 401 token revocado |
| [x] | `021_auth_post_refresh_401.png` | 05 Revocacion | refresh 401 sesion inactiva |
| [x] | `022_auth_delete_usuarios_id_sesiones_200.png` | 05 Revocacion | cerrar sesiones 200 admin |
| [x] | `023_auth_get_sesion_401.png` | 05 Revocacion | sesion 401 sesion inactiva |
| [ ] | `024_auth_post_login_423.png` | 06 Casos limite (correr aparte, bloquea una cuenta 15 min) | login 423 cuenta bloqueada |
| [ ] | `025_auth_post_login_429.png` | 06 Casos limite (correr aparte, bloquea una cuenta 15 min) | login 429 rate limit |

## devoluciones

| Listo | Archivo | Carpeta de la coleccion | Caso |
|---|---|---|---|
| [x] | `026_devoluciones_get_health_200.png` | 00 Preparacion (tokens) | health 200 |
| [x] | `027_devoluciones_post_raiz_409.png` | 01 Registro (POST) | registrar 409 cantidad excedida |
| [x] | `028_devoluciones_post_raiz_201.png` | 01 Registro (POST) | registrar 201 exitoso |
| [x] | `029_devoluciones_post_raiz_201_xml.png` | 01 Registro (POST) | registrar 201 XML |
| [x] | `030_devoluciones_post_raiz_400.png` | 01 Registro (POST) | registrar 400 datos invalidos |
| [x] | `031_devoluciones_post_raiz_400_xml.png` | 01 Registro (POST) | registrar 400 XML no cumple XSD |
| [x] | `032_devoluciones_post_raiz_401.png` | 01 Registro (POST) | registrar 401 sin token |
| [x] | `033_devoluciones_post_raiz_403.png` | 01 Registro (POST) | registrar 403 compra de otro cliente |
| [x] | `034_devoluciones_post_raiz_404.png` | 01 Registro (POST) | registrar 404 linea inexistente |
| [x] | `035_devoluciones_get_raiz_200.png` | 02 Consulta (GET) | listar 200 cliente paginado |
| [x] | `036_devoluciones_get_raiz_200_xml.png` | 02 Consulta (GET) | listar 200 analista filtro XML |
| [x] | `037_devoluciones_get_raiz_400.png` | 02 Consulta (GET) | listar 400 estado invalido |
| [x] | `038_devoluciones_get_raiz_401.png` | 02 Consulta (GET) | listar 401 sin token |
| [x] | `039_devoluciones_get_raiz_401.png` | 02 Consulta (GET) | listar 401 token invalido |
| [x] | `040_devoluciones_get_id_200.png` | 02 Consulta (GET) | detalle 200 exitoso |
| [x] | `041_devoluciones_get_id_403.png` | 02 Consulta (GET) | detalle 403 otro cliente |
| [x] | `042_devoluciones_get_id_404.png` | 02 Consulta (GET) | detalle 404 inexistente |
| [x] | `043_devoluciones_patch_id_resolucion_403.png` | 03 Revision (PATCH y PUT) | resolver 403 cliente sin permiso |
| [x] | `044_devoluciones_patch_id_resolucion_400.png` | 03 Revision (PATCH y PUT) | resolver 400 rechazo sin justificacion |
| [x] | `045_devoluciones_patch_id_resolucion_200.png` | 03 Revision (PATCH y PUT) | resolver 200 pedir informacion |
| [x] | `046_devoluciones_put_id_200.png` | 03 Revision (PATCH y PUT) | corregir 200 PUT |
| [x] | `047_devoluciones_delete_id_409.png` | 03 Revision (PATCH y PUT) | cancelar 409 ya revisada |
| [x] | `048_devoluciones_patch_id_resolucion_200_xml.png` | 03 Revision (PATCH y PUT) | resolver 200 autorizar XML |
| [x] | `049_devoluciones_patch_id_resolucion_409.png` | 03 Revision (PATCH y PUT) | resolver 409 ya resuelta |
| [x] | `050_devoluciones_get_id_200.png` | 03 Revision (PATCH y PUT) | detalle 200 historial completo |
| [x] | `051_devoluciones_delete_id_200.png` | 04 Cancelacion (DELETE) | cancelar 200 exitoso |
| [x] | `052_devoluciones_get_id_404.png` | 04 Cancelacion (DELETE) | detalle 404 cancelada |

## logistica

| Listo | Archivo | Carpeta de la coleccion | Caso |
|---|---|---|---|
| [x] | `053_logistica_get_health_200.png` | 00 Preparacion (requiere devolucion_id autorizada: coleccion devoluciones) | health 200 |
| [x] | `054_logistica_post_recolecciones_401.png` | 01 Programar recoleccion (POST) | programar 401 sin token |
| [x] | `055_logistica_post_recolecciones_401.png` | 01 Programar recoleccion (POST) | programar 401 token invalido |
| [x] | `056_logistica_post_recolecciones_403.png` | 01 Programar recoleccion (POST) | programar 403 centro sin permiso |
| [x] | `057_logistica_post_recolecciones_400.png` | 01 Programar recoleccion (POST) | programar 400 devolucion_id invalido |
| [x] | `058_logistica_post_recolecciones_404.png` | 01 Programar recoleccion (POST) | programar 404 devolucion inexistente |
| [x] | `059_logistica_post_recolecciones_400.png` | 01 Programar recoleccion (POST) | programar 400 fecha en el pasado |
| [x] | `060_logistica_post_recolecciones_400_xml.png` | 01 Programar recoleccion (POST) | programar 400 XML no cumple XSD |
| [x] | `061_logistica_post_recolecciones_201.png` | 01 Programar recoleccion (POST) | programar 201 exitoso |
| [x] | `062_logistica_post_recolecciones_409.png` | 01 Programar recoleccion (POST) | programar 409 ya programada |
| [x] | `063_logistica_get_recolecciones_200.png` | 02 Consulta (GET) | listar 200 coordinador |
| [x] | `064_logistica_get_recolecciones_200_xml.png` | 02 Consulta (GET) | listar 200 centro XML con filtro |
| [x] | `065_logistica_get_recolecciones_400.png` | 02 Consulta (GET) | listar 400 estado invalido |
| [x] | `066_logistica_get_recolecciones_403.png` | 02 Consulta (GET) | listar 403 cliente |
| [x] | `067_logistica_get_recolecciones_401.png` | 02 Consulta (GET) | listar 401 sin token |
| [x] | `068_logistica_patch_recolecciones_id_asignacion_403.png` | 03 Asignar ruta y transportista (PATCH) | asignar 403 centro sin permiso |
| [x] | `069_logistica_patch_recolecciones_id_asignacion_400.png` | 03 Asignar ruta y transportista (PATCH) | asignar 400 ruta invalida |
| [x] | `070_logistica_patch_recolecciones_id_asignacion_400.png` | 03 Asignar ruta y transportista (PATCH) | asignar 400 ruta inexistente |
| [x] | `071_logistica_patch_recolecciones_id_asignacion_404.png` | 03 Asignar ruta y transportista (PATCH) | asignar 404 recoleccion inexistente |
| [x] | `072_logistica_patch_recolecciones_id_asignacion_200_xml.png` | 03 Asignar ruta y transportista (PATCH) | asignar 200 XML |
| [x] | `073_logistica_patch_recolecciones_id_estado_409.png` | 04 Estado de la recoleccion (PATCH) | estado 409 transicion invalida |
| [x] | `074_logistica_patch_recolecciones_id_estado_404.png` | 04 Estado de la recoleccion (PATCH) | estado 404 inexistente |
| [x] | `075_logistica_patch_recolecciones_id_estado_200.png` | 04 Estado de la recoleccion (PATCH) | estado 200 en_transito |
| [x] | `076_logistica_patch_recolecciones_id_asignacion_409.png` | 04 Estado de la recoleccion (PATCH) | asignar 409 ya inicio |
| [x] | `077_logistica_patch_recolecciones_id_estado_200_xml.png` | 04 Estado de la recoleccion (PATCH) | estado 200 completada XML |
| [x] | `078_logistica_post_recepciones_403.png` | 05 Recepcion en el centro (POST) | recepcion 403 coordinador |
| [x] | `079_logistica_post_recepciones_400.png` | 05 Recepcion en el centro (POST) | recepcion 400 devolucion invalida |
| [x] | `080_logistica_post_recepciones_404.png` | 05 Recepcion en el centro (POST) | recepcion 404 inexistente |
| [x] | `081_logistica_post_recepciones_400.png` | 05 Recepcion en el centro (POST) | recepcion 400 booleano invalido |
| [x] | `082_logistica_post_recepciones_201.png` | 05 Recepcion en el centro (POST) | recepcion 201 exitoso |
| [x] | `083_logistica_post_recepciones_409.png` | 05 Recepcion en el centro (POST) | recepcion 409 duplicada |

## inspecciones

| Listo | Archivo | Carpeta de la coleccion | Caso |
|---|---|---|---|
| [x] | `084_inspecciones_get_health_200.png` | 00 Preparacion (requiere devolucion_id recibida: coleccion logistica) | health 200 |
| [x] | `085_inspecciones_post_raiz_401.png` | 01 Registrar inspeccion (POST) | registrar 401 sin token |
| [x] | `086_inspecciones_post_raiz_403.png` | 01 Registrar inspeccion (POST) | registrar 403 analista |
| [x] | `087_inspecciones_post_raiz_400.png` | 01 Registrar inspeccion (POST) | registrar 400 devolucion_id invalido |
| [x] | `088_inspecciones_post_raiz_404.png` | 01 Registrar inspeccion (POST) | registrar 404 devolucion inexistente |
| [x] | `089_inspecciones_post_raiz_400_xml.png` | 01 Registrar inspeccion (POST) | registrar 400 XML no cumple XSD |
| [x] | `090_inspecciones_post_raiz_400.png` | 01 Registrar inspeccion (POST) | registrar 400 empaque sin describir |
| [x] | `091_inspecciones_post_raiz_400.png` | 01 Registrar inspeccion (POST) | registrar 400 booleano invalido |
| [x] | `092_inspecciones_post_raiz_201.png` | 01 Registrar inspeccion (POST) | registrar 201 exitoso |
| [x] | `093_inspecciones_post_raiz_409.png` | 01 Registrar inspeccion (POST) | registrar 409 duplicada |
| [x] | `094_inspecciones_get_id_200.png` | 02 Consulta (GET) | detalle 200 inspector |
| [x] | `095_inspecciones_get_id_200_xml.png` | 02 Consulta (GET) | detalle 200 analista XML |
| [x] | `096_inspecciones_get_id_403.png` | 02 Consulta (GET) | detalle 403 cliente |
| [x] | `097_inspecciones_get_id_404.png` | 02 Consulta (GET) | detalle 404 inexistente |
| [x] | `098_inspecciones_get_id_401.png` | 02 Consulta (GET) | detalle 401 token invalido |
| [x] | `099_inspecciones_patch_id_400.png` | 03 Actualizar detalle (PATCH) | actualizar 400 sin cambios |
| [x] | `100_inspecciones_patch_id_403.png` | 03 Actualizar detalle (PATCH) | actualizar 403 analista |
| [x] | `101_inspecciones_patch_id_404.png` | 03 Actualizar detalle (PATCH) | actualizar 404 inexistente |
| [x] | `102_inspecciones_patch_id_200_xml.png` | 03 Actualizar detalle (PATCH) | actualizar 200 XML |
| [x] | `103_inspecciones_post_id_disposicion_403.png` | 04 Disposicion (POST) | disposicion 403 inspector |
| [x] | `104_inspecciones_post_id_disposicion_400.png` | 04 Disposicion (POST) | disposicion 400 destino invalido |
| [x] | `105_inspecciones_post_id_disposicion_404.png` | 04 Disposicion (POST) | disposicion 404 inexistente |
| [x] | `106_inspecciones_post_id_disposicion_201_xml.png` | 04 Disposicion (POST) | disposicion 201 XML |
| [x] | `107_inspecciones_post_id_disposicion_409.png` | 04 Disposicion (POST) | disposicion 409 duplicada |
| [x] | `108_inspecciones_post_inventario_id_etiqueta_403.png` | 05 Etiqueta de inventario (POST) | etiqueta 403 inspector |
| [x] | `109_inspecciones_post_inventario_id_etiqueta_404.png` | 05 Etiqueta de inventario (POST) | etiqueta 404 inexistente |
| [x] | `110_inspecciones_post_inventario_id_etiqueta_201.png` | 05 Etiqueta de inventario (POST) | etiqueta 201 exitoso |

## reembolsos_costos

| Listo | Archivo | Carpeta de la coleccion | Caso |
|---|---|---|---|
| [x] | `111_reembolsos_costos_get_health_200.png` | 00 Preparacion (requiere devolucion_id autorizada o resuelta) | health 200 |
| [x] | `112_reembolsos_costos_post_costos_401.png` | 01 Costos (POST) | costo 401 sin token |
| [x] | `113_reembolsos_costos_post_costos_403.png` | 01 Costos (POST) | costo 403 cliente |
| [x] | `114_reembolsos_costos_post_costos_403.png` | 01 Costos (POST) | costo 403 etapa de otro rol |
| [x] | `115_reembolsos_costos_post_costos_400.png` | 01 Costos (POST) | costo 400 monto negativo |
| [x] | `116_reembolsos_costos_post_costos_400.png` | 01 Costos (POST) | costo 400 etapa invalida |
| [x] | `117_reembolsos_costos_post_costos_400.png` | 01 Costos (POST) | costo 400 devolucion_id invalido |
| [x] | `118_reembolsos_costos_post_costos_400_xml.png` | 01 Costos (POST) | costo 400 XML no cumple XSD |
| [x] | `119_reembolsos_costos_post_costos_404.png` | 01 Costos (POST) | costo 404 devolucion inexistente |
| [x] | `120_reembolsos_costos_post_costos_201.png` | 01 Costos (POST) | costo 201 transporte JSON |
| [x] | `121_reembolsos_costos_post_costos_201_xml.png` | 01 Costos (POST) | costo 201 almacenamiento XML |
| [x] | `122_reembolsos_costos_post_reembolsos_403.png` | 02 Reembolsos (POST) | reembolso 403 analista |
| [x] | `123_reembolsos_costos_post_reembolsos_400.png` | 02 Reembolsos (POST) | reembolso 400 estado invalido |
| [x] | `124_reembolsos_costos_post_reembolsos_400.png` | 02 Reembolsos (POST) | reembolso 400 metodo invalido |
| [x] | `125_reembolsos_costos_post_reembolsos_400.png` | 02 Reembolsos (POST) | reembolso 400 devolucion_id invalido |
| [x] | `126_reembolsos_costos_post_reembolsos_404.png` | 02 Reembolsos (POST) | reembolso 404 devolucion inexistente |
| [x] | `127_reembolsos_costos_post_reembolsos_409.png` | 02 Reembolsos (POST) | reembolso 409 monto excedido |
| [x] | `128_reembolsos_costos_post_reembolsos_201.png` | 02 Reembolsos (POST) | reembolso 201 aprobado |
| [x] | `129_reembolsos_costos_post_reembolsos_409_xml.png` | 02 Reembolsos (POST) | reembolso 409 duplicado XML |
| [x] | `130_reembolsos_costos_get_reembolsos_200.png` | 03 Consulta (GET) | reembolsos 200 lista |
| [x] | `131_reembolsos_costos_get_reembolsos_200_xml.png` | 03 Consulta (GET) | reembolsos 200 analista XML |
| [x] | `132_reembolsos_costos_get_reembolsos_403.png` | 03 Consulta (GET) | reembolsos 403 cliente |
| [x] | `133_reembolsos_costos_get_reembolsos_401.png` | 03 Consulta (GET) | reembolsos 401 token invalido |
| [x] | `134_reembolsos_costos_get_costos_id_200.png` | 03 Consulta (GET) | costos 200 desglose |
| [x] | `135_reembolsos_costos_get_costos_id_200_xml.png` | 03 Consulta (GET) | costos 200 analista XML |
| [x] | `136_reembolsos_costos_get_costos_id_403.png` | 03 Consulta (GET) | costos 403 centro |
| [x] | `137_reembolsos_costos_get_costos_id_404.png` | 03 Consulta (GET) | costos 404 devolucion inexistente |

## ventas_catalogos

| Listo | Archivo | Carpeta de la coleccion | Caso |
|---|---|---|---|
| [x] | `138_ventas_catalogos_get_health_200.png` | 00 Preparacion (tokens) | health 200 |
| [x] | `139_ventas_catalogos_get_raiz_200.png` | 01 Ventas | ventas 200 cliente paginado |
| [x] | `140_ventas_catalogos_get_raiz_200_xml.png` | 01 Ventas | ventas 200 analista XML |
| [x] | `141_ventas_catalogos_get_raiz_400.png` | 01 Ventas | ventas 400 paginacion invalida |
| [x] | `142_ventas_catalogos_get_raiz_401.png` | 01 Ventas | ventas 401 sin token |
| [x] | `143_ventas_catalogos_get_raiz_401.png` | 01 Ventas | ventas 401 token invalido |
| [x] | `144_ventas_catalogos_get_id_200.png` | 01 Ventas | venta 200 detalle |
| [x] | `145_ventas_catalogos_get_id_200_xml.png` | 01 Ventas | venta 200 detalle XML |
| [x] | `146_ventas_catalogos_get_id_403.png` | 01 Ventas | venta 403 de otro cliente |
| [x] | `147_ventas_catalogos_get_id_404.png` | 01 Ventas | venta 404 inexistente |
| [x] | `148_ventas_catalogos_get_catalogos_200.png` | 02 Catalogos (lectura) | catalogos 200 lista |
| [x] | `149_ventas_catalogos_get_catalogos_403.png` | 02 Catalogos (lectura) | catalogos 403 cliente |
| [x] | `150_ventas_catalogos_get_catalogos_nombre_200.png` | 02 Catalogos (lectura) | catalogo motivos 200 cliente |
| [x] | `151_ventas_catalogos_get_catalogos_nombre_200_xml.png` | 02 Catalogos (lectura) | catalogo motivos 200 XML con inactivos |
| [x] | `152_ventas_catalogos_get_catalogos_nombre_403.png` | 02 Catalogos (lectura) | catalogo productos 403 cliente |
| [x] | `153_ventas_catalogos_get_catalogos_nombre_404.png` | 02 Catalogos (lectura) | catalogo inexistente 404 |
| [x] | `154_ventas_catalogos_get_catalogos_nombre_200.png` | 02 Catalogos (lectura) | catalogo rutas 200 |
| [x] | `155_ventas_catalogos_get_catalogos_nombre_200.png` | 02 Catalogos (lectura) | catalogo transportistas 200 |
| [x] | `156_ventas_catalogos_get_catalogos_nombre_registro_id_200.png` | 02 Catalogos (lectura) | registro 200 detalle |
| [x] | `157_ventas_catalogos_get_catalogos_nombre_registro_id_404.png` | 02 Catalogos (lectura) | registro 404 inexistente |
| [x] | `158_ventas_catalogos_post_catalogos_nombre_201.png` | 03 Catalogos (escritura, Administrador) | alta 201 JSON |
| [x] | `159_ventas_catalogos_post_catalogos_nombre_201_xml.png` | 03 Catalogos (escritura, Administrador) | alta 201 XML |
| [x] | `160_ventas_catalogos_post_catalogos_nombre_400.png` | 03 Catalogos (escritura, Administrador) | alta 400 sin nombre |
| [x] | `161_ventas_catalogos_post_catalogos_nombre_401.png` | 03 Catalogos (escritura, Administrador) | alta 401 sin token |
| [x] | `162_ventas_catalogos_post_catalogos_nombre_403.png` | 03 Catalogos (escritura, Administrador) | alta 403 analista |
| [x] | `163_ventas_catalogos_post_catalogos_nombre_404.png` | 03 Catalogos (escritura, Administrador) | alta 404 catalogo inexistente |
| [x] | `164_ventas_catalogos_post_catalogos_nombre_409.png` | 03 Catalogos (escritura, Administrador) | alta 409 referencia inactiva |
| [x] | `165_ventas_catalogos_put_catalogos_nombre_registro_id_200.png` | 03 Catalogos (escritura, Administrador) | edicion 200 PUT |
| [x] | `166_ventas_catalogos_put_catalogos_nombre_registro_id_400.png` | 03 Catalogos (escritura, Administrador) | edicion 400 tipo invalido |
| [x] | `167_ventas_catalogos_put_catalogos_nombre_registro_id_404.png` | 03 Catalogos (escritura, Administrador) | edicion 404 inexistente |
| [x] | `168_ventas_catalogos_patch_catalogos_nombre_id_estado_200.png` | 03 Catalogos (escritura, Administrador) | estado 200 desactivar |
| [x] | `169_ventas_catalogos_patch_catalogos_nombre_id_estado_400.png` | 03 Catalogos (escritura, Administrador) | estado 400 booleano invalido |
| [x] | `170_ventas_catalogos_patch_catalogos_nombre_id_estado_404.png` | 03 Catalogos (escritura, Administrador) | estado 404 inexistente |
| [x] | `171_ventas_catalogos_delete_catalogos_nombre_registro_id_200.png` | 03 Catalogos (escritura, Administrador) | baja 200 desactivar |
| [x] | `172_ventas_catalogos_delete_catalogos_nombre_registro_id_404.png` | 03 Catalogos (escritura, Administrador) | baja 404 inexistente |

## evidencias

| Listo | Archivo | Carpeta de la coleccion | Caso |
|---|---|---|---|
| [x] | `173_evidencias_get_health_200.png` | 00 Preparacion (crea una devolucion propia para adjuntar) | health 200 |
| [x] | `174_evidencias_post_raiz_201.png` | 01 Alta (POST) | alta 201 comentario JSON |
| [x] | `175_evidencias_post_raiz_201_xml.png` | 01 Alta (POST) | alta 201 comentario XML |
| [x] | `176_evidencias_post_raiz_201.png` | 01 Alta (POST) | alta 201 archivo PNG |
| [x] | `177_evidencias_post_raiz_400.png` | 01 Alta (POST) | alta 400 comentario vacio |
| [x] | `178_evidencias_post_raiz_400.png` | 01 Alta (POST) | alta 400 tipo no permitido en JSON |
| [x] | `179_evidencias_post_raiz_400.png` | 01 Alta (POST) | alta 400 etapa invalida |
| [x] | `180_evidencias_post_raiz_400.png` | 01 Alta (POST) | alta 400 multipart sin archivo |
| [x] | `181_evidencias_post_raiz_401.png` | 01 Alta (POST) | alta 401 sin token |
| [x] | `182_evidencias_post_raiz_401.png` | 01 Alta (POST) | alta 401 token invalido |
| [x] | `183_evidencias_post_raiz_403.png` | 01 Alta (POST) | alta 403 analista |
| [x] | `184_evidencias_post_raiz_403.png` | 01 Alta (POST) | alta 403 otro cliente |
| [x] | `185_evidencias_post_raiz_403.png` | 01 Alta (POST) | alta 403 inspector sin inspeccion |
| [x] | `186_evidencias_post_raiz_404.png` | 01 Alta (POST) | alta 404 devolucion inexistente |
| [x] | `187_evidencias_post_raiz_409.png` | 01 Alta (POST) | alta 409 etapa no permitida al cliente |
| [x] | `188_evidencias_post_raiz_415.png` | 01 Alta (POST) | alta 415 archivo no soportado |
| [x] | `189_evidencias_get_raiz_200.png` | 02 Consulta (GET) | listar 200 cliente |
| [x] | `190_evidencias_get_raiz_200_xml.png` | 02 Consulta (GET) | listar 200 analista XML |
| [x] | `191_evidencias_get_raiz_400.png` | 02 Consulta (GET) | listar 400 sin devolucion_id |
| [x] | `192_evidencias_get_raiz_403.png` | 02 Consulta (GET) | listar 403 otro cliente |
| [x] | `193_evidencias_get_raiz_404.png` | 02 Consulta (GET) | listar 404 devolucion inexistente |
| [x] | `194_evidencias_get_id_200.png` | 02 Consulta (GET) | detalle 200 con metadatos |
| [x] | `195_evidencias_get_id_404.png` | 02 Consulta (GET) | detalle 404 inexistente |
| [x] | `196_evidencias_get_id_403.png` | 02 Consulta (GET) | detalle 403 otro cliente |
| [x] | `197_evidencias_get_id_enlace_200.png` | 02 Consulta (GET) | enlace 200 firmado |
| [x] | `198_evidencias_get_id_enlace_409.png` | 02 Consulta (GET) | enlace 409 comentario sin archivo |
| [x] | `199_evidencias_get_evidencia_id_archivo_200.png` | 02 Consulta (GET) | archivo 200 con enlace firmado |
| [x] | `200_evidencias_get_id_archivo_200.png` | 02 Consulta (GET) | archivo 200 con Bearer |
| [x] | `201_evidencias_get_id_archivo_401.png` | 02 Consulta (GET) | archivo 401 sin firma ni token |
| [x] | `202_evidencias_get_id_archivo_404.png` | 02 Consulta (GET) | archivo 404 inexistente |
| [x] | `203_evidencias_delete_id_403.png` | 03 Retiro (DELETE) | retiro 403 analista |
| [x] | `204_evidencias_delete_id_403.png` | 03 Retiro (DELETE) | retiro 403 otro cliente |
| [x] | `205_evidencias_delete_id_200.png` | 03 Retiro (DELETE) | retiro 200 exitoso |
| [x] | `206_evidencias_delete_id_404.png` | 03 Retiro (DELETE) | retiro 404 ya retirada |
| [x] | `207_evidencias_delete_id_404.png` | 03 Retiro (DELETE) | retiro 404 inexistente |
| [x] | `208_evidencias_post_raiz_201.png` | 04 Inspector (requiere haber corrido la coleccion inspecciones) | alta 201 inspector en etapa inspeccion |

## analisis_auditoria

| Listo | Archivo | Carpeta de la coleccion | Caso |
|---|---|---|---|
| [x] | `209_analisis_auditoria_get_health_200.png` | 00 Preparacion (tokens) | health 200 |
| [x] | `210_analisis_auditoria_post_clasificar_motivo_200.png` | 01 Clasificar motivo (POST) | clasificar 200 cliente |
| [x] | `211_analisis_auditoria_post_clasificar_motivo_200_xml.png` | 01 Clasificar motivo (POST) | clasificar 200 analista XML |
| [x] | `212_analisis_auditoria_post_clasificar_motivo_400.png` | 01 Clasificar motivo (POST) | clasificar 400 descripcion corta |
| [x] | `213_analisis_auditoria_post_clasificar_motivo_401.png` | 01 Clasificar motivo (POST) | clasificar 401 sin token |
| [x] | `214_analisis_auditoria_post_clasificar_motivo_403.png` | 01 Clasificar motivo (POST) | clasificar 403 centro |
| [x] | `215_analisis_auditoria_post_sincronizar_403.png` | 02 Sincronizar y Pareto | sincronizar 403 cliente |
| [x] | `216_analisis_auditoria_post_sincronizar_401.png` | 02 Sincronizar y Pareto | sincronizar 401 sin token |
| [x] | `217_analisis_auditoria_post_sincronizar_200.png` | 02 Sincronizar y Pareto | sincronizar 200 exitoso |
| [x] | `218_analisis_auditoria_get_pareto_200.png` | 02 Sincronizar y Pareto | pareto 200 miss |
| [x] | `219_analisis_auditoria_get_pareto_200.png` | 02 Sincronizar y Pareto | pareto 200 hit |
| [x] | `220_analisis_auditoria_get_pareto_200_xml.png` | 02 Sincronizar y Pareto | pareto 200 XML por proveedor y costo |
| [x] | `221_analisis_auditoria_get_pareto_400.png` | 02 Sincronizar y Pareto | pareto 400 dimension desconocida |
| [x] | `222_analisis_auditoria_get_pareto_400.png` | 02 Sincronizar y Pareto | pareto 400 fecha invalida |
| [x] | `223_analisis_auditoria_get_pareto_400.png` | 02 Sincronizar y Pareto | pareto 400 rango invertido |
| [x] | `224_analisis_auditoria_get_pareto_403.png` | 02 Sincronizar y Pareto | pareto 403 cliente |
| [x] | `225_analisis_auditoria_get_pareto_401.png` | 02 Sincronizar y Pareto | pareto 401 token invalido |
| [x] | `226_analisis_auditoria_get_resumen_200.png` | 03 Resumen, alertas y eventos | resumen 200 |
| [x] | `227_analisis_auditoria_get_resumen_403.png` | 03 Resumen, alertas y eventos | resumen 403 cliente |
| [x] | `228_analisis_auditoria_get_alertas_fraude_200.png` | 03 Resumen, alertas y eventos | alertas 200 |
| [x] | `229_analisis_auditoria_get_alertas_fraude_200_xml.png` | 03 Resumen, alertas y eventos | alertas 200 XML |
| [x] | `230_analisis_auditoria_get_alertas_fraude_403.png` | 03 Resumen, alertas y eventos | alertas 403 cliente |
| [x] | `231_analisis_auditoria_get_eventos_200.png` | 03 Resumen, alertas y eventos | eventos 200 paginado |
| [x] | `232_analisis_auditoria_get_eventos_200_xml.png` | 03 Resumen, alertas y eventos | eventos 200 XML |
| [x] | `233_analisis_auditoria_get_eventos_400.png` | 03 Resumen, alertas y eventos | eventos 400 correlation_id largo |
| [x] | `234_analisis_auditoria_get_eventos_400.png` | 03 Resumen, alertas y eventos | eventos 400 paginacion invalida |
| [x] | `235_analisis_auditoria_get_eventos_403.png` | 03 Resumen, alertas y eventos | eventos 403 cliente |
| [x] | `236_analisis_auditoria_get_auditoria_200.png` | 04 Auditoria (bitacora) | bitacora 200 paginada |
| [x] | `237_analisis_auditoria_get_auditoria_200_xml.png` | 04 Auditoria (bitacora) | bitacora 200 filtro XML |
| [x] | `238_analisis_auditoria_get_auditoria_400.png` | 04 Auditoria (bitacora) | bitacora 400 filtro largo |
| [x] | `239_analisis_auditoria_get_auditoria_403.png` | 04 Auditoria (bitacora) | bitacora 403 cliente |
| [x] | `240_analisis_auditoria_get_auditoria_401.png` | 04 Auditoria (bitacora) | bitacora 401 sin token |

