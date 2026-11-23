# Guia de arranque

## Microservicios del segundo parcial

Despues de aplicar migraciones y cargar los datos de demostracion:

```bash
docker compose up -d --build
docker compose ps
```

En la rama de integracion, confirma en `.env`:

```dotenv
USE_MICROSERVICES=true
MICROSERVICE_TIMEOUT=5
```

Con `true`, la barra superior muestra **API distribuida** y las operaciones
criticas pasan por los servicios. `false` habilita el modo de contingencia del
monolito. La matriz de llamadas esta en
`docs/INTEGRACION_WEB_MICROSERVICIOS.md`.

| Servicio | API | Swagger | Salud |
|---|---|---|---|
| auth | `http://HOST:8001/api/v1/auth` | `http://HOST:8001/docs` | `:8001/health` |
| devoluciones | `http://HOST:8002/api/v1/devoluciones` | `http://HOST:8002/docs` | `:8002/health` |
| logistica | `http://HOST:8003/api/v1/logistica` | `http://HOST:8003/docs` | `:8003/health` |
| inspecciones | `http://HOST:8004/api/v1/inspecciones` | `http://HOST:8004/docs` | `:8004/health` |
| reembolsos-costos | `http://HOST:8005/api/v1/reembolsos-costos` | `http://HOST:8005/docs` | `:8005/health` |
| ventas-catalogos | `http://HOST:8006/api/v1/ventas`, `/catalogos` y `/trazabilidad` | `http://HOST:8006/docs` | `:8006/health` |
| evidencias | `http://HOST:8007/api/v1/evidencias` | `http://HOST:8007/docs` | `:8007/health` |
| analisis-auditoria | `http://HOST:8008/api/v1/auditoria` (y `/analisis`, obsoleto) | `http://HOST:8008/docs` | `:8008/health` |
| clasificacion-motivos | `http://HOST:8010/api/v1/motivos` | `http://HOST:8010/docs` | `:8010/health` |
| causa-raiz | `http://HOST:8011/api/v1/causa-raiz` | `http://HOST:8011/docs` | `:8011/health` |
| proveedores | `http://HOST:8013/api/v1/proveedores` | `http://HOST:8013/docs` | `:8013/health` |
| reportes-analitica | `http://HOST:8018/api/v1/reportes`, `/graficas` y `/analitica` | `http://HOST:8018/docs` | `:8018/health` |

`HOST` es la IP o dominio de la VM. Todos los servicios comparten
`JWT_SECRET`; no debe publicarse ni quedar escrito en el repositorio. Los servicios
`sincronizacion` (8020) e `integraciones-monitoreo` (8021) se levantan igual y estan
descritos en `docs/GUIA_SINCRONIZACION.md` y `docs/GUIA_INTEGRACIONES_MONITOREO.md`.

### Servicios del tercer parcial: calidad y causa raiz

Agregan las migraciones 040 a 045 y los servicios 8010, 8011, 8013 y 8018, ademas de
cambios en 8006 y 8008. En la VM:

```bash
cd ~/Proyecto12
git pull origin main
docker compose up -d --build app
docker compose exec -T app python scripts/migrate.py --estado   # lista las pendientes
docker compose exec -T app python scripts/migrate.py
docker compose up -d --build ventas-catalogos analisis-auditoria clasificacion-motivos \
    proveedores causa-raiz reportes-analitica
docker compose exec -T app python scripts/seed_demo.py
```

- **Reconstruye `app` antes de migrar.** La imagen trae `scripts/` y `db/migrations/`;
  sin reconstruirla, `migrate.py --estado` responde que no hay pendientes aunque el
  repositorio ya tenga migraciones nuevas.
- **Respaldo antes de migrar** (fuera del repositorio; nunca se commitean volcados):
  `docker compose exec -T postgres pg_dump -U devoluciones_app -d devoluciones | gzip > ~/respaldos/antes_de_migrar.sql.gz`.
  Las migraciones 040 a 045 solo crean tablas, funciones y triggers; no alteran datos
  existentes.
- **La migracion 045 vuelve la bitacora de solo agregar**: desde entonces `UPDATE`,
  `DELETE` y `TRUNCATE` sobre `bitacora` fallan. `GET /api/v1/auditoria/estado` informa si
  la proteccion esta puesta.
- **El seed crea el lote `L-2026-PROB-01`** (4 ventas de 6 unidades con 16 devueltas),
  pensado para la demo de causa raiz: con los datos de demostracion llega a ~2.3 veces
  el promedio global y es el unico lote que dispararia una alerta. Para reemplazar una
  version anterior del lote: `docker compose exec -T app python scripts/seed_demo.py --rehacer-lote`.
  Borra solo lo que creo el seed, se detiene con error si alguien colgo algo del lote
  (una investigacion, una reclamacion) y no toca la bitacora.
- **Analisis retirado de `analisis-auditoria`** (`docs/MIGRACION_ANALISIS_8008.md`): ya no hay
  variable ni interruptor. Las rutas de `/api/v1/analisis/*` responden siempre 410
  `servicio_movido` con sus sucesores (clasificacion-motivos 8010 y reportes-analitica 8018) y
  el servicio queda solo con auditoria. La coleccion `resultados_analisis` de MongoDB ya no se
  crea en un volumen nuevo; en uno existente queda sin uso.

Para validar Compose sin crear un archivo con secretos puede usarse
`APP_ENV_FILE=.env.example docker compose --env-file .env.example config`.
Para desplegar, copie `.env.example` a `.env`, reemplace todos los valores de
ejemplo y no agregue `.env` a Git.

## Donde se ejecuta cada cosa

| Tarea | Donde |
|---|---|
| Escribir codigo, plantillas y documentacion | Tu laptop |
| Levantar PostgreSQL, Redis y MongoDB | **Solo en la VM de GCP** |
| Correr migraciones y seeds | **Solo en la VM de GCP** |
| Probar la aplicacion con datos | **Solo en la VM de GCP** |

No instales bases de datos en tu maquina. El equipo trabaja contra una sola
base, la de la VM, para que todos vean el mismo estado.

---

## 1. Primera vez en la VM de GCP

```bash
cd ~/Proyecto12
git pull origin main
cp .env.example .env
nano .env          # completar POSTGRES_PASSWORD, FLASK_SECRET_KEY y las MONGO_*_PASSWORD
```

Para generar una clave secreta larga:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Levantar el entorno:

```bash
docker compose up -d --build
docker compose ps
```

Aplicar las migraciones y cargar los datos:

```bash
docker compose exec app python scripts/migrate.py
docker compose exec -T postgres psql -U devoluciones_app -d devoluciones < db/seeds/001_catalogos.sql
docker compose exec app python scripts/seed_demo.py
```

Comprobar que responde a través del único punto de entrada:

```bash
curl -s localhost/proxy-health
curl -s localhost/health
```

Debe devolver `"estado": "ok"` con PostgreSQL y Redis en `true`.

### Abrir el puerto en GCP

Nginx es el único componente público. Para HTTP/HTTPS se permiten únicamente
los puertos 80 y 443:

```bash
gcloud compute firewall-rules create permitir-orvia-web \
  --allow=tcp:80,tcp:443 --description="Punto de entrada Orvia"
```

Después se entra en `http://IP_EXTERNA_DE_LA_VM` o al dominio HTTPS.

Los microservicios ya no publican `8001–8021`; Nginx los alcanza por la red
interna. Swagger y health checks se consultan mediante
`/servicios/<servicio>/docs` y `/servicios/<servicio>/health`. Consulte
`docs/REVERSE_PROXY.md` para HTTPS, certificados y diagnóstico.

PostgreSQL y Redis estan publicados solo en `127.0.0.1` dentro de la VM, asi que
no quedan expuestos a internet aunque el puerto 8000 si lo este. Se publican en
los puertos **55432** y **56379** del host, no en los estandar, porque la VM ya
tiene un PostgreSQL nativo ocupando el 5432 (ver `docs/BITACORA.md`).

---

## 2. Trabajo diario

### Desde tu laptop

```bash
git checkout main
git pull origin main
git checkout -b tu-nombre/lo-que-vas-a-hacer

# ... editar archivos ...

git add .
git commit -m "feat(modulo): descripcion (RF-XX, RN-YY)"
git push -u origin tu-nombre/lo-que-vas-a-hacer
```

Despues abres el Pull Request en GitHub hacia `main`.

Puedes verificar sin base de datos que las plantillas y el codigo no tengan
errores de sintaxis:

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r apps/web/requirements.txt
python -m py_compile apps/web/app/*.py apps/web/app/blueprints/*.py scripts/*.py
(cd apps/web && python -c "from app import create_app; create_app(); print('la app arranca')")
```

Eso no requiere PostgreSQL ni Redis: solo comprueba que el codigo carga.

### En la VM, para probar de verdad

```bash
cd ~/Proyecto12
git pull origin main            # o la rama que quieras probar
docker compose up -d --build
docker compose exec app python scripts/migrate.py
docker compose logs -f app
```

---

## 3. Comandos utiles

```bash
# Estado de las migraciones
docker compose exec app python scripts/migrate.py --estado

# Consola de PostgreSQL
# Usa SIEMPRE esta forma. La VM tiene ademas un PostgreSQL nativo en el puerto
# 5432 que no pertenece al proyecto; si ejecutas psql directo hablaras con ese.
docker compose exec postgres psql -U devoluciones_app -d devoluciones

# Consola de Redis
docker compose exec redis redis-cli

# Consola de MongoDB (con el usuario de la aplicacion). Toma las credenciales
# de las variables del contenedor, asi no hay que teclear la contrasena.
docker compose exec mongo sh -c 'mongosh -u "$MONGO_APP_USER" -p "$MONGO_APP_PASSWORD" --authenticationDatabase "$MONGO_DB" "$MONGO_DB"'

# Comprobar que MongoDB creo las colecciones e indices de la seccion 5.4
docker compose exec mongo sh -c 'mongosh --quiet -u "$MONGO_APP_USER" -p "$MONGO_APP_PASSWORD" --authenticationDatabase "$MONGO_DB" "$MONGO_DB" --eval "db.getCollectionNames().forEach(c => printjson({coleccion: c, indices: db[c].getIndexes().map(i => i.name)}))"'

# Reiniciar solo la aplicacion tras un cambio de codigo Python
# (las plantillas se recargan solas cuando FLASK_ENV=development)
docker compose restart app

# Recrear la aplicacion tras un cambio en el .env
# (restart no relee el archivo de entorno; up -d si)
docker compose up -d app

# Ver los ultimos errores
docker compose logs --tail=100 app
```

### Microservicio auth (segundo parcial)

```bash
# Construir y levantar (tras cualquier cambio en services/auth o shared/)
docker compose up -d --build auth

# Salud del servicio
curl -s "http://localhost:$(grep ^PROXY_HTTP_PORT .env | cut -d= -f2)/servicios/auth/health"

# Pruebas unitarias dentro del contenedor
docker compose run --rm --no-deps auth python -m pytest -v

# Swagger UI: http://<IP-de-la-VM>:8001/docs  (abrir el puerto 8001 en GCP)

# Claves que crea en Redis
docker compose exec redis redis-cli --scan --pattern 'devoluciones:sesion_api:*'
docker compose exec redis redis-cli --scan --pattern 'devoluciones:jwt_revocado:*'
```

### Empezar la base desde cero

Borra todos los datos. Solo cuando el equipo este de acuerdo:

```bash
docker compose down -v
docker compose up -d --build
docker compose exec app python scripts/migrate.py
docker compose exec -T postgres psql -U devoluciones_app -d devoluciones < db/seeds/001_catalogos.sql
docker compose exec app python scripts/seed_demo.py
```

---

## 4. Cuentas de demostracion

La contrasena **no esta en el repositorio**. Se define en `PASSWORD_DEMO` dentro
del `.env` de la VM, que esta fuera de git. El script `scripts/seed_demo.py` la
imprime al terminar; si la variable esta vacia, genera una al azar y la muestra
una sola vez.

Para cambiarla en las cuentas que ya existen:

```bash
docker compose up -d app
docker compose exec app python scripts/seed_demo.py --rotar
```

**Usa `up -d`, no `restart`.** `docker compose restart` reinicia el proceso pero
conserva la configuracion con la que se creo el contenedor, de modo que no
relee el `.env`. Si cambias una variable y solo reinicias, el contenedor sigue
viendo el valor anterior. `up -d` recrea el contenedor cuando detecta que el
entorno cambio.

Eso tambien desbloquea cualquier cuenta que se haya bloqueado por intentos
fallidos.

| Rol | Correo |
|---|---|
| Cliente | `ana.cliente@demo.mx` |
| Cliente | `miguel.cliente@demo.mx` |
| Cliente | `sofia.cliente@demo.mx` |
| Inspector | `valentina.inspector@demo.mx` |
| Encargado del Centro de Devoluciones | `roberto.centro@demo.mx` |
| Coordinador de Logistica | `david.logistica@demo.mx` |
| Analista de Devoluciones | `josue.analista@demo.mx` |
| Encargado de Reembolsos | `carla.reembolsos@demo.mx` |
| Administrador | `pablo.admin@demo.mx` |
| Recolector (app Android, Tienda Centro) | `luis.recolector@demo.mx` |
| Operador de Almacen (app Android, Tienda Centro) | `marta.almacen@demo.mx` |
| Supervisor (app Android) | `jorge.supervisor@demo.mx` |

Los tres perfiles de la app Android (migracion 014) inician sesion en el servicio
auth, pero la web les responde "No tienes permiso": no forman parte de
`TODOS_LOS_ROLES` a proposito (ver docs/BITACORA.md, 2026-11-09).

**Antes de la demostracion, corre `seed_demo.py` ese mismo dia.** Por el plazo de
devolucion (RN-16: 7 dias refrigerados, 30 los demas), las ventas historicas de
agosto ya no se pueden devolver. El script agrega cada dia seis ventas recientes
(`VTA-AAAAMMDD-R1` a `R6`) dentro del plazo; las pruebas E2E e integracion tambien
las necesitan.

Tras 5 intentos fallidos la cuenta se bloquea 15 minutos (RNF-12). Para
desbloquearla sin esperar, entra como administrador y usa el boton
"Desbloquear" en la pantalla de usuarios, o corre el script con `--rotar`.

## Exponer la aplicacion a mas gente

El firewall de GCP limita quien puede abrir el puerto 8000. Para dejarlo
accesible desde cualquier lado:

```bash
gcloud compute firewall-rules update permitir-8000-devoluciones --source-ranges=0.0.0.0/0
```

Antes de hacerlo, asegurate de que `PASSWORD_DEMO` sea una contrasena que no
este en ningun lado publico. Ten presente ademas que la aplicacion sirve por
HTTP sin cifrar, asi que las credenciales viajan en claro; para el alcance de
este parcial se acepta, y el cifrado de comunicaciones (RNF-14) se resuelve al
poner la plataforma detras de un proxy con TLS en el tercer parcial.

Para volver a restringirlo:

```bash
gcloud compute firewall-rules update permitir-8000-devoluciones --source-ranges=TU_IP/32
```

---

## 5. Guion de la demostracion del parcial

El parcial pide demostrar ocho cosas. Este es el recorrido que las cubre:

1. **Inicio de sesion** — entra con `ana.cliente@demo.mx`.
2. **Acceso diferenciado por perfil** — observa el menu; luego cierra sesion y
   entra con `pablo.admin@demo.mx`: el menu cambia. Intenta abrir
   `/usuarios/` como cliente: responde 403.
3. **Operacion de catalogos** — como administrador, agrega un motivo de
   devolucion y desactiva otro.
4. **Proceso principal completo** — el recorrido esta descrito abajo.
5. **Almacenamiento en PostgreSQL** — `docker compose exec postgres psql ...`
   y consulta la tabla `devoluciones`.
6. **Consulta de informacion** — panel de causas y panel de costos.
7. **Registro de auditoria** — pantalla de bitacora, filtrando por accion.
8. **Ejecucion mediante contenedores** — `docker compose ps` y `/health`.

### Recorrido del proceso principal

| Paso | Entra como | Que hacer |
|---|---|---|
| 1 | `ana.cliente@demo.mx` | Ventas -> abrir una venta -> "Devolver" en una linea -> registrar la solicitud |
| 2 | `ana.cliente@demo.mx` | En el expediente, agregar una evidencia de tipo comentario |
| 3 | `josue.analista@demo.mx` | Abrir el expediente -> Autorizar |
| 4 | `david.logistica@demo.mx` | Recolecciones -> Programar (fecha, lugar, ruta, transportista) |
| 5 | `roberto.centro@demo.mx` | Abrir el expediente -> Confirmar recepcion |
| 6 | `valentina.inspector@demo.mx` | Inspecciones -> Inspeccionar -> capturar condiciones |
| 7 | `josue.analista@demo.mx` | Expediente -> Decidir destino del producto |
| 8 | `carla.reembolsos@demo.mx` | Reembolsos -> Gestionar -> Aprobar |
| 9 | cualquiera | Revisar el historial del caso al final del expediente |

### Reglas de negocio que conviene demostrar en vivo

Estas son las que impresionan porque las bloquea **la base de datos**, no el
formulario:

- **RN-06 / RN-07** — inspecciona un producto refrigerado marcando "cadena de
  frio rota". Al decidir el destino, la opcion "inventario" aparece
  deshabilitada, y si se fuerza la peticion, el trigger de PostgreSQL la
  rechaza con un mensaje explicito.
- **RF-25 (monto excesivo)** — en el reembolso, captura un monto mayor al valor
  devuelto. El trigger lo rechaza senalando posible fraude.
- **RN-04** — intenta gestionar el reembolso de una devolucion que aun no ha
  sido autorizada. No aparece en la lista y la ruta directa lo impide.
- **RN-01** — no existe forma de registrar una devolucion sin partir de una
  linea de venta: el formulario solo se abre desde el detalle de la venta.
- **RNF-12** — falla el inicio de sesion cinco veces y muestra el bloqueo.
- **Autorizacion por recurso** — como `ana.cliente@demo.mx`, abre la URL de una
  devolucion de otro cliente. Responde 403 y el intento queda en la bitacora.

## Pruebas E2E y de integracion (solo en la VM)

Requieren el entorno levantado, migraciones, `seed_demo.py` y `PASSWORD_DEMO` en
el `.env`. Detalle, variables y como registrar el resultado: `docs/PRUEBAS.md`.

```bash
# Todo (E2E + integracion por servicio); guarda docs/pruebas/salida_<fecha>.txt
bash scripts/correr_e2e.sh

# Solo la suite E2E de 11 pasos y casos de seguridad
docker compose run --rm -v "$PWD":/repo -w /repo -e PYTHONPATH=/repo -e INTEGRACION=1 devoluciones python -m pytest -v -s tests/e2e

# Integracion de un servicio (ejemplo)
docker compose run --rm -e INTEGRACION=1 logistica python -m pytest -v tests/test_integracion.py
```

**Servicios de calidad y causa raiz.** `scripts/correr_e2e.sh servicios` ya incluye `clasificacion-motivos`,
`proveedores`, `causa-raiz`, `reportes-analitica` y el segundo archivo de pruebas de `ventas-catalogos`
(`test_integracion_trazabilidad.py`). Para correr uno solo:

```bash
docker compose run --rm --no-deps -T -e INTEGRACION=1 causa-raiz python -m pytest -v tests/test_integracion.py
```

- **Deja pasar un minuto entre una suite y otra.** `auth` limita el login a 10 por minuto por
  IP (H-07 en `docs/PRUEBAS.md`) y cada suite inicia sesion con varios roles; seguidas, la
  siguiente recibe 429. `correr_e2e.sh` lo evita borrando los contadores entre bloques.
- La suite de `reportes-analitica` agota a proposito el limite de descargas del
  Administrador (20 por minuto): no la corras dos veces seguidas.
- Las pruebas de `analisis-auditoria` dejan unos pocos registros `prueba_integracion_auditoria`
  en la bitacora. No se pueden borrar: es justo lo que prueban.
