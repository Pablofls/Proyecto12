# Resultado de pruebas en la VM — AAAA-MM-DD

Copia este archivo como `resultado_AAAA-MM-DD.md` y llena cada seccion con la
salida **real**. No inventes ni resumas de memoria: pega lo que imprimio `pytest`.
No pegues tokens ni contrasenas (la suite ya no los imprime; revisa antes de commitear).

- Quien ejecuto (integrante):
- Fecha y hora:
- Rama y commit (`git rev-parse --short HEAD`):
- `docker compose ps` (todos `healthy`):
- Migraciones aplicadas (`python scripts/migrate.py`) y `seed_demo.py` corrido: si / no
- Sesion 01 (notificaciones) ya integrada en esta rama: si / no (si no, el paso de notificaciones queda pendiente)

## Suite E2E

Comando:

```bash
docker compose run --rm -v "$PWD":/repo -w /repo -e PYTHONPATH=/repo -e INTEGRACION=1 devoluciones python -m pytest -v -s tests/e2e
```

Resumen final de `pytest` (la linea `N passed, M failed ...`):

```
<pegar aqui>
```

Lineas `[E2E]` de los pasos que se citaran en el documento tecnico (pasos 4, 6, 9, 10 y 11 como minimo):

```
<pegar aqui>
```

## Integracion por servicio

Una seccion por servicio: `auth`, `ventas-catalogos`, `devoluciones`, `evidencias`,
`logistica`, `inspecciones`, `reembolsos-costos`, `analisis-auditoria`.

Comando (ejemplo):

```bash
docker compose run --rm -e INTEGRACION=1 logistica python -m pytest -v tests/test_integracion.py
```

```
<pegar aqui el pytest -v de cada servicio>
```

## Fallos y hallazgos nuevos

| Prueba | Que fallo | Es bug del servicio, de la prueba o del entorno | Accion |
|---|---|---|---|
|  |  |  |  |

## Despues de pegar

- [ ] Reemplace cada `<!-- EJECUTAR EN VM -->` de `docs/PRUEBAS.md` por el resultado real.
- [ ] Anote en "Hallazgos" de `docs/PRUEBAS.md` cualquier bug nuevo (sin corregirlo en la misma rama).
- [ ] Commit con el mensaje `docs(pruebas): resultados de la VM (RNF-28)`.
