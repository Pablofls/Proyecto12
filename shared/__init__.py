"""Codigo comun a todos los microservicios (segundo parcial).

Cada servicio copia esta carpeta dentro de su imagen (ver su Dockerfile), de
modo que todos responden, fallan, se autentican y se registran igual:
- respuestas.py: formato JSON/XML, errores estandar y lectura del cuerpo.
- seguridad.py:  validacion comun de JWT contra Redis y control por rol.
- infra.py:      conexiones a PostgreSQL y Redis, bitacora y rate limiting.
- mongo.py:      conexion a MongoDB y eventos entre servicios (requiere pymongo).
- paginacion.py: parametros ?pagina=&por_pagina= y bloque "paginacion".
- docs.py:       Swagger UI sobre el contrato OpenAPI de cada servicio.
"""
