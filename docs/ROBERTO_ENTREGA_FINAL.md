# Entrega de Roberto: inspección, disposición, costos y escritorio

## Alcance y propiedad de datos

| Componente | Es dueño de | No decide |
|---|---|---|
| `inspecciones` (8004) | Hallazgos técnicos en MongoDB y referencia del dictamen en PostgreSQL | Destino comercial, alta de inventario o reembolso |
| `disposicion-inventario` (8014) | Decisión autorizada, cuarentena, ubicación y reincorporación | Dictamen técnico o pago |
| `reembolsos-costos` (8005) | Reembolso único, costos, valor recuperado e impacto neto | Aptitud o destino |
| `apps/escritorio` | Presentación y captura XML | Reglas del negocio o acceso directo a bases |

Esta separación evita dos fuentes de verdad. La recomendación de inspección no
reintegra un artículo: una persona autorizada decide el destino y otra operación
autorizada lo libera de cuarentena.

## Casos obligatorios

1. **Producto dañado:** inspección no apta; reintegro rechazado.
2. **Empaque alterado:** hallazgo técnico explícito; reintegro rechazado.
3. **Cadena de frío:** temperatura mayor a 8 °C, ruptura o más de 30 minutos
   fuera de refrigeración generan dictamen no apto. Esos campos no se aplican
   a productos no refrigerados.
4. **Evidencia insuficiente:** estado `evidencia_insuficiente`; ninguna
   disposición puede aprobarse.
5. **Producto recuperable:** inspección recomienda reintegrar, disposición
   autorizada lo manda a cuarentena y una autorización independiente lo vuelve
   disponible.

## Seguridad y concurrencia

- JWT común, sesión y revocación verificadas en Redis.
- Roles mínimos por endpoint.
- `aprobar_disposicion`, `reincorporar_inventario` y `aprobar_reembolso`
  requieren reconfirmar contraseña en `auth`.
- El permiso viaja en `X-Autorizacion-Operacion`, dura cinco minutos, está
  ligado a usuario, sesión, operación y recurso, y se consume atómicamente.
- Toda mutación relevante registra `correlation_id` y bitácora.
- El bloqueo Redis y la llave única de PostgreSQL impiden el doble reembolso.

## Aplicación de escritorio

La aplicación PySide6 envía `Accept: application/xml` y, cuando hay cuerpo,
`Content-Type: application/xml`. Valida cada petición contra el XSD antes de
usar la red. Los microservicios vuelven a validarla. No hay fallback JSON ni
conexiones directas a PostgreSQL, MongoDB o Redis.

## Migración y compatibilidad

La migración `030_roberto_inspeccion_disposicion_costos.sql` es aditiva y usa
el rango 030–039 reservado para Roberto. Conserva `inventario` como valor
histórico de base, aunque el contrato nuevo usa `reintegrar`.

El sistema web distribuido llama al nuevo servicio. El servicio de inspección
ya no publica endpoints que escriban disposición o inventario, evitando que un
cliente nuevo eluda las autorizaciones.

## Ejecución

```powershell
Copy-Item .env.example .env
# Completar secretos y PASSWORD_DEMO; después:
docker compose build inspecciones disposicion-inventario reembolsos-costos web
docker compose up -d postgres redis mongo auth inspecciones disposicion-inventario reembolsos-costos web
docker compose run --rm migraciones
```

```powershell
Copy-Item apps/escritorio/config.example.json apps/escritorio/config.json
python -m pip install -r apps/escritorio/requirements.txt
python apps/escritorio/main.py
```

## Evidencias a capturar en la VM

No se inventan resultados. Al ejecutar en el ambiente del equipo, guardar:

- `docker compose ps` con 8004, 8005 y 8014 saludables.
- Swagger de los tres servicios.
- XML válido aceptado y XML inválido con `xml_no_cumple_xsd`.
- Los cinco casos de inspección y su documento MongoDB.
- Disposición sin autorización (403) y autorizada (201).
- Inventario en cuarentena y reincorporación autorizada.
- Dos solicitudes simultáneas: exactamente un 201, un 409 y una fila.
- Desglose de costos, valor recuperado y costo neto.
- Bitácora con los mismos `correlation_id`.

## Pruebas

```powershell
docker compose run --rm inspecciones python -m pytest -q tests
docker compose run --rm disposicion-inventario python -m pytest -q tests
docker compose run --rm reembolsos-costos python -m pytest -q tests
docker compose run --rm -e INTEGRACION=1 reembolsos-costos python -m pytest -v tests/test_integracion.py
```

La prueba real crea dos autorizaciones válidas, envía dos solicitudes en
paralelo y comprueba códigos `[201, 409]` y una sola fila en PostgreSQL.
