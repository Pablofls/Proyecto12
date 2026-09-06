# Guia de arranque

## Donde se ejecuta cada cosa

| Tarea | Donde |
|---|---|
| Escribir codigo, plantillas y documentacion | Tu laptop |
| Levantar PostgreSQL y Redis | **Solo en la VM de GCP** |
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
nano .env          # completar POSTGRES_PASSWORD y FLASK_SECRET_KEY
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

Comprobar que responde:

```bash
curl -s localhost:8000/health
```

Debe devolver `"estado": "ok"` con PostgreSQL y Redis en `true`.

### Abrir el puerto en GCP

La aplicacion escucha en el puerto 8000. Para verla desde el navegador hay que
permitir ese puerto en el firewall del proyecto de GCP:

```bash
gcloud compute firewall-rules create permitir-8000 \
  --allow=tcp:8000 --description="Monolito de devoluciones (primer parcial)"
```

Despues se entra en `http://IP_EXTERNA_DE_LA_VM:8000`.

PostgreSQL y Redis estan publicados solo en `127.0.0.1` dentro de la VM, asi que
no quedan expuestos a internet aunque el puerto 8000 si lo este.

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
pip install -r requirements.txt
python -m py_compile app/*.py app/blueprints/*.py scripts/*.py
python -c "from app import create_app; create_app(); print('la app arranca')"
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
docker compose exec postgres psql -U devoluciones_app -d devoluciones

# Consola de Redis
docker compose exec redis redis-cli

# Reiniciar solo la aplicacion tras un cambio de codigo
docker compose restart app

# Ver los ultimos errores
docker compose logs --tail=100 app
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

Todas usan la contrasena `Devoluciones2026`. Son cuentas de demostracion y solo
existen dentro de la VM del proyecto.

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

Tras 5 intentos fallidos la cuenta se bloquea 15 minutos (RNF-12). Para
desbloquearla sin esperar, entra como administrador y usa el boton
"Desbloquear" en la pantalla de usuarios.

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
