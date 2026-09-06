# Arquitectura del monolito

## Por que un monolito ahora

El primer parcial pide un sistema web ejecutable, no una arquitectura
distribuida. Construir microservicios desde el inicio habria significado
resolver descubrimiento de servicios, comunicacion y despliegue antes de tener
siquiera el flujo del negocio funcionando.

La decision fue construir un **monolito modular**: una sola aplicacion que se
despliega junta, pero cuyo codigo esta separado por area de negocio de modo que
cada modulo pueda convertirse despues en un microservicio sin reescribir la
logica. Esto es lo que declara la seccion 5.2 del documento.

## Capas

```
Navegador
    |
    v
Plantillas Jinja2  (app/templates)          <- presentacion
    |
    v
Blueprints         (app/blueprints)         <- controladores y reglas del caso de uso
    |
    v
db.py / cache.py   (app)                    <- acceso a datos
    |
    v
PostgreSQL   Redis                          <- contenedores en la VM
```

Las plantillas nunca consultan la base de datos. Los blueprints nunca abren
conexiones a mano: usan `consultar` y `ejecutar` de `app/db.py`. Esa separacion
es lo que permite mover un modulo a un microservicio mas adelante cambiando solo
la capa de acceso.

## Modulos

| Blueprint | Prefijo | Responsabilidad |
|---|---|---|
| `auth` | `/login`, `/logout` | Autenticacion, intentos fallidos, bloqueo |
| `panel` | `/panel`, `/bitacora` | Tableros, causas, costos, auditoria |
| `usuarios` | `/usuarios` | Cuentas, roles y bajas logicas |
| `catalogos` | `/catalogos` | Productos, lotes, proveedores, tiendas, rutas, transportistas, motivos |
| `ventas` | `/ventas` | Consulta de ventas y su detalle |
| `devoluciones` | `/devoluciones` | Expediente, evidencias, autorizacion |
| `logistica` | `/logistica` | Recoleccion y recepcion |
| `inspecciones` | `/inspecciones` | Inspeccion, disposicion e inventario recuperado |
| `reembolsos` | `/reembolsos` | Gestion del reembolso |

Cada blueprint corresponde a un microservicio del catalogo declarado en el
documento. La correspondencia es intencional: al partir el monolito, cada uno se
convierte en un servicio.

## Reglas de negocio en la base de datos, no solo en el codigo

Esta es la decision de diseno mas importante del proyecto. Las reglas criticas
estan implementadas como **triggers de PostgreSQL**, no solo como validaciones
del formulario:

| Trigger | Que impide |
|---|---|
| `trg_validar_destino_inventario` | Mandar a inventario un producto que la inspeccion marco como no apto (RN-06, RN-07) |
| `trg_validar_inspeccion_vs_disposicion` | Marcar una inspeccion como no apta cuando ya existe una disposicion a inventario |
| `trg_validar_reembolso` | Reembolsar mas que el valor devuelto, o aprobar sobre una devolucion sin autorizar (RN-04, RF-25) |

El motivo: cuando el sistema se parta en microservicios, varios servicios
escribiran sobre las mismas tablas. Si la regla vive solo en el codigo de la
aplicacion web, el primer servicio con un error la rompe. En la base de datos,
la regla se cumple sin importar quien escriba.

## Distribucion de los datos

| Motor | Que guarda | Por que ahi |
|---|---|---|
| PostgreSQL | Expediente completo: ventas, devoluciones, inspecciones, reembolsos, costos, bitacora | Datos relacionales con reglas de integridad y consultas de agregacion |
| Redis | Sesiones, conteo de intentos fallidos, bloqueo temporal | Datos efimeros con expiracion automatica, escritos en cada peticion |
| MongoDB | Detalle extenso de la inspeccion | Estructura variable segun el tipo de producto. **No se usa todavia**: `inspecciones_ref.mongo_doc_id` existe y queda en NULL |
| Google Cloud Storage | Fotografias y documentos de evidencia | Archivos binarios que no deben vivir en la base. **No se usa todavia** |

El bloqueo de cuenta se escribe en **los dos** motores a proposito: Redis lleva
el conteo vivo con expiracion automatica, y PostgreSQL conserva el bloqueo si
Redis se reinicia. Si se guardara solo en Redis, reiniciar el contenedor
levantaria todos los bloqueos (RNF-21).

## Autorizacion en dos niveles

1. **Por rol** — el decorador `roles_required(...)` en cada vista. Responde 403
   y deja el intento en la bitacora (RNF-09, RN-13).
2. **Por recurso** — `exigir_devolucion_visible(...)`. Un cliente que conoce el
   identificador de la devolucion de otro cliente recibe 403 igualmente. Esto es
   lo que la seccion 5.3 del documento describe como autorizacion por recurso.

## Preparacion para los siguientes parciales

El monolito ya incluye piezas que solo tienen sentido en la arquitectura
distribuida, para no tener que reconstruir despues:

- **`/health`** devuelve el estado de cada dependencia por separado y responde
  503 si alguna falla (RNF-22, RF-32).
- **Identificador de correlacion** en cada registro de bitacora, que permitira
  seguir una peticion entre servicios (RNF-23).
- **`inspecciones_ref`** ya esta separada del detalle de la inspeccion,
  anticipando que ese detalle vivira en MongoDB.
- **`evidencias`** guarda bucket y objeto, nunca una URL publica, para que el
  enlace firmado se genere al consultar (RNF-15).
- **Configuracion por variables de entorno**, sin ningun valor en el codigo.
