# Suite E2E (RNF-28)

Pruebas contra los contenedores reales: HTTP por la red del compose y efectos
verificados en PostgreSQL, MongoDB y Redis. **Solo corren en la VM** y solo con
`INTEGRACION=1`; en cualquier otro caso se saltan.

| Archivo | Que cubre |
|---|---|
| `test_01_proceso_completo.py` | El proceso de negocio de 11 pasos, encadenado, mas el paso 6b de notificaciones y campanita (usa `WEB_URL`, por defecto `http://app:8000`) |
| `test_02_seguridad_y_errores.py` | 401, 403, 400, 404 y 409 sobre los 8 servicios; correlation id; bitacora sin tokens |
| `test_03_json_y_xml.py` | Mismo endpoint en JSON y XML; XSD de peticion y de respuesta (auth) con `shared/xsd.py` |
| `test_99_rate_limit.py` | 429 de login; va al final para no bloquear el resto |
| `cliente.py` | HTTP con `urllib`, SQL, Mongo y Redis; limpieza; logs sin secretos |
| `conftest.py` | Fixture `ctx`: sesiones por rol (usuarios leidos de la base) y limpieza al terminar |
| `flujo.py` | Atajos para llegar a un estado dado (escenarios de error) |

Los modulos se ejecutan en orden alfabetico y `test_02` reutiliza la sesion que
revoca el paso 11 de `test_01`; por eso se corre la carpeta completa.

Como correrlo, variables de entorno y como registrar el resultado:
`docs/PRUEBAS.md`. Atajo: `bash scripts/correr_e2e.sh`.

Reglas: no se agregan librerias; las credenciales vienen de `PASSWORD_DEMO` y de
los usuarios del seed (`scripts/seed_demo.py`), nunca se escriben aqui; lo que la
suite crea se borra al terminar (la bitacora se conserva a proposito, RN-12; si
el rol de la app no puede borrar alguna tabla, avisa con `[E2E][limpieza]`).
