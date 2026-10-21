# Resultado local de las pruebas unitarias — 2026-10-21

Ejecutado en la laptop **sin bases de datos** (CLAUDE.md, restriccion 1), con la rama ya fusionada con `origin/main` (sesion 01 incluida).
Las pruebas de integracion y E2E se saltan aqui (`INTEGRACION` no definida) y quedan pendientes en la VM.

- Python: Python 3.13.1, pytest: pytest 8.3.3
- Rama: roberto/suite-e2e, base eaf0433 (origin/main)
- Comando por carpeta: `cd services/<servicio> && PYTHONPATH=<raiz>:. python -m pytest -v tests` (y `apps/web` con `app/tests`)

## services/analisis_auditoria/

```
tests/test_integracion.py::IntegracionAnalisis::test_auditoria_y_eventos_solo_para_analista_o_admin SKIPPED
tests/test_integracion.py::IntegracionAnalisis::test_clasificar_motivo_solo_sugiere SKIPPED
tests/test_integracion.py::IntegracionAnalisis::test_pareto_primero_calcula_y_luego_sale_del_cache_con_ttl SKIPPED
tests/test_integracion.py::IntegracionAnalisis::test_sincronizar_proyecta_postgres_en_mongo_sin_modificar_postgres SKIPPED
tests/test_pareto.py::test_pareto_motivo_frecuencia PASSED
tests/test_pareto.py::test_pareto_vacio_sin_division_por_cero PASSED
tests/test_pareto.py::test_clasificacion_explica_coincidencias PASSED
tests/test_pareto.py::test_clasificacion_desconocida_no_inventa PASSED
========================= 4 passed, 4 skipped in 0.24s =========================
```

## services/auth/

```
tests/test_auth.py::PruebaAuth::test_access_token_no_sirve_como_refresh PASSED
tests/test_auth.py::PruebaAuth::test_administrador_cierra_sesiones_de_otro PASSED
tests/test_auth.py::PruebaAuth::test_bloqueo_tras_intentos_fallidos PASSED
tests/test_auth.py::PruebaAuth::test_contratos_publicados PASSED
tests/test_auth.py::PruebaAuth::test_error_en_xml PASSED
tests/test_auth.py::PruebaAuth::test_errores_en_xml_cumplen_xsd PASSED
tests/test_auth.py::PruebaAuth::test_formato_no_soportado PASSED
tests/test_auth.py::PruebaAuth::test_login_correcto_emite_tokens_y_sesion PASSED
tests/test_auth.py::PruebaAuth::test_login_en_xml PASSED
tests/test_auth.py::PruebaAuth::test_logout_revoca_token PASSED
tests/test_auth.py::PruebaAuth::test_password_incorrecta_responde_401_generico PASSED
tests/test_auth.py::PruebaAuth::test_rate_limit_de_login PASSED
tests/test_auth.py::PruebaAuth::test_redis_caido_niega_acceso PASSED
tests/test_auth.py::PruebaAuth::test_refresh_en_xml_cumple_xsd PASSED
tests/test_auth.py::PruebaAuth::test_refresh_funciona_y_muere_con_logout PASSED
tests/test_auth.py::PruebaAuth::test_respuesta_de_login_cumple_xsd PASSED
tests/test_auth.py::PruebaAuth::test_respuesta_de_sesion_cumple_xsd PASSED
tests/test_auth.py::PruebaAuth::test_rol_sin_permiso_responde_403 PASSED
tests/test_auth.py::PruebaAuth::test_ruta_inexistente_formato_estandar PASSED
tests/test_auth.py::PruebaAuth::test_sesion_con_token_valido PASSED
tests/test_auth.py::PruebaAuth::test_sin_token_responde_401 PASSED
tests/test_auth.py::PruebaAuth::test_token_con_firma_falsa PASSED
tests/test_auth.py::PruebaAuth::test_token_expirado PASSED
tests/test_auth.py::PruebaAuth::test_usuario_inexistente_responde_404 PASSED
tests/test_auth.py::PruebaAuth::test_validacion_de_campos PASSED
tests/test_auth.py::PruebaAuth::test_xml_mal_formado PASSED
tests/test_auth.py::PruebaAuth::test_xml_que_no_cumple_xsd PASSED
tests/test_integracion.py::IntegracionAuth::test_admin_cierra_todas_las_sesiones_de_un_usuario SKIPPED
tests/test_integracion.py::IntegracionAuth::test_credenciales_malas_quedan_en_el_historial_sin_revelar_nada SKIPPED
tests/test_integracion.py::IntegracionAuth::test_login_crea_sesion_en_redis_historial_y_bitacora SKIPPED
tests/test_integracion.py::IntegracionAuth::test_logout_revoca_el_token_y_borra_la_sesion SKIPPED
tests/test_integracion.py::IntegracionAuth::test_refresh_emite_un_access_nuevo_de_la_misma_sesion SKIPPED
======================== 27 passed, 5 skipped in 5.34s =========================
```

## services/devoluciones/

```
tests/test_api.py::PruebaApi::test_analista_no_puede_cancelar PASSED
tests/test_api.py::PruebaApi::test_cliente_no_puede_resolver PASSED
tests/test_api.py::PruebaApi::test_contratos_publicados PASSED
tests/test_api.py::PruebaApi::test_filtro_de_estado_invalido PASSED
tests/test_api.py::PruebaApi::test_inspector_no_puede_registrar PASSED
tests/test_api.py::PruebaApi::test_paginacion_invalida PASSED
tests/test_api.py::PruebaApi::test_rate_limit_de_registro PASSED
tests/test_api.py::PruebaApi::test_registro_con_datos_invalidos PASSED
tests/test_api.py::PruebaApi::test_resolucion_rechazo_sin_justificacion PASSED
tests/test_api.py::PruebaApi::test_sin_token_responde_401 PASSED
tests/test_api.py::PruebaApi::test_token_revocado_responde_401 PASSED
tests/test_api.py::PruebaApi::test_xml_de_registro_incompleto PASSED
tests/test_api.py::PruebaApi::test_xml_que_no_cumple_xsd PASSED
tests/test_integracion.py::PruebaIntegracion::test_1_flujo_registro_revision_y_autorizacion SKIPPED
tests/test_integracion.py::PruebaIntegracion::test_2_cancelacion_logica SKIPPED
tests/test_integracion.py::PruebaIntegracion::test_3_listado_del_cliente_solo_trae_lo_suyo SKIPPED
tests/test_integracion.py::PruebaIntegracion::test_4_logout_en_auth_revoca_el_token_en_devoluciones SKIPPED
tests/test_reglas.py::PruebaReglas::test_booleano_no_cuenta_como_entero PASSED
tests/test_reglas.py::PruebaReglas::test_decision_desconocida PASSED
tests/test_reglas.py::PruebaReglas::test_descripcion_corta_y_larga PASSED
tests/test_reglas.py::PruebaReglas::test_edicion_exige_cantidad PASSED
tests/test_reglas.py::PruebaReglas::test_enteros_invalidos PASSED
tests/test_reglas.py::PruebaReglas::test_filtro_de_estado PASSED
tests/test_reglas.py::PruebaReglas::test_justificacion_demasiado_larga PASSED
tests/test_reglas.py::PruebaReglas::test_nueva_sin_campos PASSED
tests/test_reglas.py::PruebaReglas::test_nueva_valida_y_cantidad_por_defecto PASSED
tests/test_reglas.py::PruebaReglas::test_rechazo_sin_justificacion PASSED
tests/test_reglas.py::PruebaReglas::test_resolucion_valida PASSED
======================== 24 passed, 4 skipped in 0.38s =========================
```

## services/evidencias/

```
tests/test_integracion.py::IntegracionEvidencias::test_archivo_sin_firma_ni_token_no_se_descarga SKIPPED
tests/test_integracion.py::IntegracionEvidencias::test_comentario_json_y_archivo_png SKIPPED
tests/test_integracion.py::IntegracionEvidencias::test_otro_rol_no_adjunta SKIPPED
tests/test_integracion.py::IntegracionEvidencias::test_un_archivo_que_no_es_imagen_ni_pdf_se_rechaza SKIPPED
tests/test_seguridad_archivos.py::test_detecta_mime_por_contenido PASSED
tests/test_seguridad_archivos.py::test_enlace_temporal_firmado PASSED
tests/test_seguridad_archivos.py::test_archivo_crea_id_privado_y_rechaza_exe PASSED
========================= 3 passed, 4 skipped in 0.14s =========================
```

## services/inspecciones/

```
tests/test_integracion.py::IntegracionInspecciones::test_el_cliente_no_inspecciona SKIPPED
tests/test_integracion.py::IntegracionInspecciones::test_inspeccion_apta_va_a_mongo_y_postgres_y_se_etiqueta SKIPPED
tests/test_integracion.py::IntegracionInspecciones::test_refrigerado_con_cadena_rota_no_vuelve_a_inventario SKIPPED
tests/test_integracion.py::IntegracionInspecciones::test_refrigerado_exige_temperatura_y_tiempo SKIPPED
tests/test_integracion.py::IntegracionInspecciones::test_solo_se_inspecciona_lo_recibido SKIPPED
tests/test_reglas.py::PruebaAptitud::test_booleano_ambiguo_se_rechaza PASSED
tests/test_reglas.py::PruebaAptitud::test_cadena_frio_impide_inventario PASSED
tests/test_reglas.py::PruebaAptitud::test_dano_impide_inventario PASSED
tests/test_reglas.py::PruebaAptitud::test_seco_sano_es_apto PASSED
tests/test_reglas.py::PruebaAptitud::test_tiempo_fuera_impide_inventario PASSED
========================= 5 passed, 5 skipped in 0.14s =========================
```

## services/logistica/

```
tests/test_api.py::PruebaLogistica::test_booleano_invalido_no_se_convierte_a_false PASSED
tests/test_api.py::PruebaLogistica::test_fecha_invalida_se_rechaza_antes_de_bd PASSED
tests/test_api.py::PruebaLogistica::test_inspector_no_programa PASSED
tests/test_api.py::PruebaLogistica::test_sin_token PASSED
tests/test_api.py::PruebaLogistica::test_xml_invalido PASSED
tests/test_integracion.py::IntegracionLogistica::test_el_cliente_no_puede_programar SKIPPED
tests/test_integracion.py::IntegracionLogistica::test_no_se_programa_una_devolucion_sin_autorizar SKIPPED
tests/test_integracion.py::IntegracionLogistica::test_programar_asignar_transitar_completar_y_recibir SKIPPED
========================= 5 passed, 3 skipped in 0.15s =========================
```

## services/reembolsos_costos/

```
tests/test_api.py::PruebaReembolsos::test_analista_no_resuelve_reembolso PASSED
tests/test_api.py::PruebaReembolsos::test_etapas_separadas_por_responsabilidad PASSED
tests/test_api.py::PruebaReembolsos::test_monto_negativo PASSED
tests/test_api.py::PruebaReembolsos::test_montos_no_finitos PASSED
tests/test_api.py::PruebaReembolsos::test_sin_token PASSED
tests/test_api.py::PruebaReembolsos::test_xml_invalido PASSED
tests/test_integracion.py::IntegracionReembolsos::test_costos_por_etapa_y_total SKIPPED
tests/test_integracion.py::IntegracionReembolsos::test_el_cliente_no_reembolsa SKIPPED
tests/test_integracion.py::IntegracionReembolsos::test_lock_de_redis_bloquea_la_resolucion_concurrente SKIPPED
tests/test_integracion.py::IntegracionReembolsos::test_no_reembolsa_si_no_esta_autorizada_ni_mas_del_valor SKIPPED
tests/test_integracion.py::IntegracionReembolsos::test_un_solo_reembolso_por_devolucion SKIPPED
========================= 6 passed, 5 skipped in 0.23s =========================
```

## services/ventas_catalogos/

```
tests/test_integracion.py::IntegracionVentasCatalogos::test_alta_edicion_y_baja_logica_de_catalogo SKIPPED
tests/test_integracion.py::IntegracionVentasCatalogos::test_catalogo_inexistente_y_rol_sin_permiso SKIPPED
tests/test_integracion.py::IntegracionVentasCatalogos::test_cliente_no_abre_la_venta_de_otro SKIPPED
tests/test_integracion.py::IntegracionVentasCatalogos::test_cliente_solo_ve_sus_ventas_con_paginacion SKIPPED
tests/test_reglas.py::test_catalogos_coinciden_con_monolito PASSED
tests/test_reglas.py::test_producto_valido PASSED
tests/test_reglas.py::test_producto_invalido[datos0] PASSED
tests/test_reglas.py::test_producto_invalido[datos1] PASSED
tests/test_reglas.py::test_producto_invalido[datos2] PASSED
tests/test_reglas.py::test_producto_invalido[datos3] PASSED
tests/test_reglas.py::test_lote_fecha_valida PASSED
tests/test_reglas.py::test_lote_fecha_invalida PASSED
========================= 8 passed, 4 skipped in 0.12s =========================
```

## apps/web

```
app/tests/test_api_client.py::PruebaClienteApi::test_401_renueva_token_y_reintenta_una_vez PASSED
app/tests/test_api_client.py::PruebaClienteApi::test_falla_de_red_se_traduce_a_503 PASSED
app/tests/test_api_client.py::PruebaClienteApi::test_login_guarda_tokens_solo_en_sesion_servidor PASSED
app/tests/test_exportacion.py::PruebaCeldaSegura::test_fechas_en_formato_estable PASSED
app/tests/test_exportacion.py::PruebaCeldaSegura::test_neutraliza_formulas_en_texto PASSED
app/tests/test_exportacion.py::PruebaCeldaSegura::test_numeros_negativos_no_se_prefijan PASSED
app/tests/test_exportacion.py::PruebaCeldaSegura::test_texto_normal_y_vacios_no_cambian PASSED
app/tests/test_exportacion.py::PruebaGenerarCsv::test_bom_encabezados_y_acentos PASSED
app/tests/test_exportacion.py::PruebaGenerarCsv::test_entrega_en_bloques_sin_acumular_todo PASSED
app/tests/test_exportacion.py::PruebaGenerarCsv::test_escapa_formulas_en_el_archivo PASSED
app/tests/test_exportacion.py::PruebaGenerarCsv::test_sin_filas_solo_encabezado PASSED
app/tests/test_exportacion.py::PruebaRutas::test_403_por_rol_en_cada_reporte PASSED
app/tests/test_exportacion.py::PruebaRutas::test_bitacora_de_exportacion_lleva_tipo_y_filtros_sin_contenido PASSED
app/tests/test_exportacion.py::PruebaRutas::test_bitacora_y_costos_y_reembolsos_responden_csv PASSED
app/tests/test_exportacion.py::PruebaRutas::test_causas_usa_los_mismos_filtros_del_panel PASSED
app/tests/test_exportacion.py::PruebaRutas::test_cliente_solo_exporta_sus_devoluciones PASSED
app/tests/test_exportacion.py::PruebaRutas::test_descarga_con_cabeceras_de_archivo PASSED
app/tests/test_exportacion.py::PruebaRutas::test_filtros_llegan_como_parametros_ligados PASSED
app/tests/test_exportacion.py::PruebaRutas::test_sin_sesion_redirige PASSED
app/tests/test_microservicios.py::PruebaClienteMicroservicios::test_json_invalido_degrada PASSED
app/tests/test_microservicios.py::PruebaClienteMicroservicios::test_servicio_sano PASSED
app/tests/test_microservicios.py::PruebaClienteMicroservicios::test_timeout_degrada_sin_romper_web PASSED
app/tests/test_notificaciones.py::PruebaBandeja::test_destino_externo_se_ignora PASSED
app/tests/test_notificaciones.py::PruebaBandeja::test_filtro_no_leidas_usa_parametros_ligados PASSED
app/tests/test_notificaciones.py::PruebaBandeja::test_leer_propia_marca_leida_y_redirige_al_destino PASSED
app/tests/test_notificaciones.py::PruebaBandeja::test_leer_todas_filtra_por_usuario PASSED
app/tests/test_notificaciones.py::PruebaBandeja::test_leer_una_ajena_responde_404_y_no_actualiza PASSED
app/tests/test_notificaciones.py::PruebaBandeja::test_resumen_solo_consulta_las_del_usuario_en_sesion PASSED
app/tests/test_notificaciones.py::PruebaBandeja::test_sin_sesion_redirige_al_login PASSED
app/tests/test_notificaciones.py::PruebaDestinatarios::test_autorizacion_avisa_al_cliente_y_al_coordinador_con_su_enlace PASSED
app/tests/test_notificaciones.py::PruebaDestinatarios::test_disposicion_a_inventario_avisa_al_centro_a_la_bandeja_de_inventario PASSED
app/tests/test_notificaciones.py::PruebaDestinatarios::test_matriz_cubre_el_flujo_y_solo_usa_roles_conocidos PASSED
app/tests/test_notificaciones.py::PruebaDestinatarios::test_mensaje_largo_se_recorta_a_500 PASSED
app/tests/test_notificaciones.py::PruebaDestinatarios::test_omitir_cliente_salta_al_cliente_del_caso PASSED
app/tests/test_notificaciones.py::PruebaDestinatarios::test_quien_ejecuta_no_se_notifica_a_si_mismo PASSED
app/tests/test_notificaciones.py::PruebaDestinatarios::test_recepcion_va_al_inspector_con_enlace_de_inspeccion PASSED
app/tests/test_notificaciones.py::PruebaDestinatarios::test_rol_sin_usuarios_se_omite_y_queda_en_bitacora PASSED
============================== 37 passed in 0.36s ==============================
```

## Suite E2E: descubrimiento y salto sin INTEGRACION

```
ssssssssssssssssssssssssssss                                             [100%]
100 skipped in 0.09s
```
