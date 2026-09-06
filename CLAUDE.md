# CLAUDE.md — Reglas del proyecto

Este archivo lo lee Claude Code al inicio de cada sesion. Si trabajas en el
proyecto desde tu casa con tu propia sesion de Claude, esta es la fuente de
verdad: respetala antes de proponer cualquier cambio.

## Que es este proyecto

Plataforma distribuida para la gestion y analisis de devoluciones de productos
refrigerados y no refrigerados mediante logistica inversa y analisis de causa
raiz. Proyecto 12, Equipo 02, materia Integracion de Aplicaciones
Computacionales, UDEM.

Entrega actual: **primer parcial — monolito web funcional**.

## Restricciones que no se negocian

### 1. Las bases de datos viven UNICAMENTE en la VM de GCP

PostgreSQL y Redis corren como contenedores en la maquina virtual del equipo.
**Nadie levanta bases de datos en su laptop.** Desde casa se escribe codigo, se
revisan plantillas y se redacta documentacion; la ejecucion real, las
migraciones y las pruebas contra datos se hacen en la VM.

Consecuencias practicas:
- No propongas instalar Postgres, Redis ni Mongo en la maquina local.
- No generes scripts que asuman `localhost:5432` fuera de la VM.
- Si necesitas verificar algo contra la base, la instruccion correcta es
  "corre esto en la VM", no "lo pruebo localmente".

### 2. Todo se sincroniza por GitHub

Repositorio: `git@github.com:Pablofls/Proyecto12.git`

La VM tiene el repositorio clonado. El flujo es siempre:

```
laptop  --push-->  GitHub  --pull-->  VM (aqui se ejecuta)
```

No se copian archivos por Drive, WhatsApp ni scp. Si un archivo no esta en git,
para efectos del proyecto no existe.

### 3. Ramas por integrante y Pull Request

- `main` debe quedar siempre en un estado que arranque.
- Cada quien trabaja en su rama: `pablo/...`, `roberto/...`, `david/...`,
  `josue/...`.
- Los cambios entran a `main` por Pull Request.
- El parcial exige evidencia de participacion de los cuatro integrantes, y el
  historial de git es esa evidencia. Cada quien commitea su propio trabajo.

### 4. Nunca se commitean secretos ni datos

Prohibido subir: `.env`, contrasenas, llaves de servicio de GCP, dumps de la
base de datos, volumenes de Docker. El archivo versionado es `.env.example`,
con valores de ejemplo. Ver `.gitignore`.

### 5. Trazabilidad contra los identificadores del documento

Todo cambio se justifica contra el documento del proyecto. Los identificadores
son: **RF-01…RF-32** (requerimientos funcionales), **RNF-01…RNF-30** (no
funcionales), **RN-01…RN-15** (reglas de negocio), **HU-01…HU-28** (historias de
usuario), **UC-01…UC-27** (casos de uso).

Reglas concretas:
- Cada migracion SQL abre con un comentario que dice **por que** existe y que
  identificadores cubre.
- Cada blueprint y cada funcion no obvia lleva su referencia en el docstring.
- `docs/TRAZABILIDAD.md` mapea requerimiento -> archivo. Si agregas una funcion
  que cubre un RF, **actualiza esa tabla en el mismo commit**.
- Los mensajes de commit citan el identificador. Ejemplo:
  `feat(inspecciones): registro de cadena de frio (RF-17, RN-05, RN-06)`

## Stack fijo

| Pieza | Tecnologia | Por que |
|---|---|---|
| Web | Python 3.11 + Flask + Jinja2 | Declarado en la seccion 5.2 del documento |
| Transaccional | PostgreSQL 16 | Expediente de la devolucion (RNF-06) |
| Sesiones y bloqueo | Redis 7 | Sesiones, intentos fallidos, bloqueo (RNF-08, RNF-12) |
| Graficas | Highcharts (CDN) | Declarado en 5.2 |
| Contenedores | Docker Compose | Requisito del parcial (RNF-27) |

No introduzcas frameworks, ORMs ni librerias nuevas sin acordarlo con el equipo.
En particular: **no hay ORM**. Las consultas son SQL con `psycopg2` y parametros
ligados, por RNF-11 (proteccion contra inyeccion SQL). Nunca se concatena
entrada del usuario dentro de una sentencia.

## Que NO es parte de esta entrega

Microservicios, aplicacion movil, aplicacion de escritorio, JWT, respuestas XML,
Locust, Google Cloud Storage y despliegue automatizado. Todo eso corresponde al
segundo y tercer parcial. El monolito se diseno para poder partirse despues
(capas separadas, health check, correlation id), pero **no se parte ahora**.

MongoDB esta contemplado en el diseno (`inspecciones_ref.mongo_doc_id` existe y
queda en NULL) pero no se usa en esta entrega.

## Estructura del repositorio

```
app/                  Aplicacion Flask
  __init__.py         Fabrica de la app, health check, manejadores de error
  config.py           Configuracion desde variables de entorno
  db.py               Acceso a PostgreSQL
  cache.py            Acceso a Redis
  security.py         Roles, decoradores de acceso, bitacora
  blueprints/         Un modulo por area del negocio
  templates/          Vistas Jinja2
  static/css/         Estilos
db/
  migrations/         Migraciones SQL numeradas (nunca se editan una vez aplicadas)
  seeds/              Datos de catalogo
scripts/
  migrate.py          Aplica las migraciones pendientes
  seed_demo.py        Carga usuarios, ventas y devoluciones de demostracion
docker/Dockerfile     Imagen de la aplicacion
docker-compose.yml    Entorno completo (solo se ejecuta en la VM)
docs/                 Documentacion tecnica del equipo
```

## Migraciones: la regla mas importante

**Una migracion ya aplicada NUNCA se edita.** Si necesitas cambiar el modelo,
creas una migracion nueva con el siguiente numero. `scripts/migrate.py` guarda
un checksum de cada archivo y avisa si alguien rompio esta regla, porque en ese
momento la base de la VM y el repositorio dejan de coincidir.

Numeracion actual: 001 a 008. La siguiente que crees es `009_...sql`.

## Convenciones de codigo

- Codigo, comentarios, nombres de variables y mensajes al usuario **en espanol**,
  sin acentos en identificadores ni en SQL (evita problemas de codificacion).
- Los comentarios explican **por que**, no **que**. Si el codigo ya dice que
  hace, el comentario sobra.
- Toda operacion importante llama a `registrar_bitacora(...)` (RF-30, RN-12).
- Toda vista lleva `@roles_required(...)` o `@login_required` (RNF-09, RN-13).
- Nunca metas contrasenas, tokens ni datos sensibles en la bitacora (RNF-16).

## Documentacion que debes mantener al dia

| Archivo | Cuando actualizarlo |
|---|---|
| `docs/TRAZABILIDAD.md` | Cada vez que implementas o mueves un RF/RN |
| `docs/BITACORA.md` | Cuando tomas una decision tecnica que otro deberia entender |
| `docs/ARQUITECTURA.md` | Cuando agregas un modulo o cambias la estructura |
| `docs/SETUP.md` | Cuando cambia el procedimiento de arranque |
