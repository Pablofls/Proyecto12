# Guion de la presentacion del primer parcial

Cubre los ocho puntos que exige la demostracion, en un orden que no repite
pantallas. Duracion estimada: 12 a 15 minutos.

## Antes de empezar

Cinco minutos antes, en la VM:

```bash
cd ~/Proyecto12
docker compose ps          # los tres contenedores arriba
curl -s localhost:8000/health
curl -s ifconfig.me; echo  # confirma la IP externa actual
```

En la laptop:

- **Ventana normal** con sesion de cliente y **ventana de incognito** con sesion
  de personal interno. Las sesiones se guardan por cookie, asi que dos ventanas
  te permiten cambiar de rol sin cerrar sesion cada vez. Esto ahorra la mitad
  del tiempo de la demostracion.
- Una terminal con la sesion SSH ya abierta en la VM.
- La contrasena de demostracion a la mano.

## 1. Infraestructura y contenedores (1 min)

En la terminal:

```bash
docker compose ps
curl -s localhost:8000/health
```

**Que decir.** Que la plataforma corre en una maquina virtual de Google Cloud
mediante tres contenedores independientes: la aplicacion web, PostgreSQL y
Redis. Que el punto `/health` informa el estado de cada dependencia por
separado y responde con error si alguna falla, lo cual es la base del monitoreo
que exige RF-32 y anticipa la arquitectura distribuida del siguiente parcial.

**Cubre:** ejecucion mediante contenedores.

## 2. Inicio de sesion y acceso diferenciado (2 min)

Entra como **cliente**. Senala que ve tres opciones en el menu: Panel, Ventas y
Devoluciones, y que el panel muestra unicamente sus propios casos.

En la ventana de incognito entra como **administrador**. El menu ahora tiene
once opciones y el panel muestra el total del sistema.

Vuelve a la ventana del cliente y escribe a mano la direccion `/usuarios/`.
Responde **403**.

**Que decir.** Que el control de acceso opera en dos niveles: por rol, que
determina a que secciones entra cada perfil, y por recurso, que impide que un
cliente vea el caso de otro cliente aunque conozca el identificador. Que el
intento denegado queda registrado en la bitacora, cosa que se mostrara al final.

**Cubre:** inicio de sesion, acceso diferenciado por perfil.

## 3. El proceso completo (5 min)

Es el centro de la demostracion. Registra una devolucion nueva y llevala hasta
el cierre. Conviene usar un producto **refrigerado**, porque activa las reglas
mas interesantes.

| Paso | Perfil | Que hacer |
|---|---|---|
| 1 | Cliente | Ventas, abrir una venta, **Devolver** en un articulo refrigerado |
| 2 | Cliente | Motivo "cadena de frio rota", cantidad 1, descripcion del problema |
| 3 | Cliente | En el expediente, agregar un comentario como evidencia |
| 4 | Analista | Abrir el expediente, **Autorizar** |
| 5 | Coordinador | Recolecciones, **Programar**: fecha, lugar, ruta y transportista |
| 6 | Encargado del centro | En el expediente, **Confirmar recepcion** |
| 7 | Inspector | Inspecciones, **Inspeccionar** |
| 8 | Analista | **Decidir destino del producto** |
| 9 | Encargado de reembolsos | Reembolsos, **Gestionar**, aprobar |

**Puntos que conviene senalar mientras avanzas:**

- En el paso 1, que la devolucion se registra sobre la **linea especifica** de
  la venta y no sobre la venta completa, para poder devolver un solo articulo de
  una compra con varios (RF-06, RN-01). Y que el sistema no permite devolver mas
  unidades de las que se compraron.
- En el paso 2, que el folio se genera solo, unico e irrepetible (RN-02).
- En el paso 7, que el formulario **cambia segun el producto**: al ser
  refrigerado exige temperatura, minutos fuera de refrigeracion y estado de la
  cadena de frio, campos que no aparecen en un producto no refrigerado (RN-05).
  Captura ruptura de cadena de frio en "si" y un tiempo alto, por ejemplo 420
  minutos.
- Al guardar la inspeccion, lee en voz alta el resultado que calcula el sistema:
  *"no apto: ruptura documentada de la cadena de frio; permanecio 420 minutos
  fuera de refrigeracion (limite 240)"*. Ese veredicto es el que condiciona el
  paso siguiente.
- En el paso 8, muestra que la opcion **inventario aparece deshabilitada**.
- Al final, baja al **historial del caso** y muestra que reconstruye todos los
  movimientos con su responsable y su fecha, tomandolos de la bitacora.

**Cubre:** ejecucion de un proceso principal, consulta de informacion.

## 4. Las reglas que bloquea la base de datos (3 min)

Es el momento mas fuerte de la presentacion, porque demuestra que las reglas no
dependen del formulario.

**Primero el intento por la interfaz.** En el paso anterior la opcion
"inventario" estaba deshabilitada. Explica que eso solo es la interfaz siendo
amable, y que la regla real esta mas abajo.

**Luego el intento saltandose la interfaz.** Abre las herramientas de
desarrollador del navegador (F12), pestana de consola, y pega:

```javascript
await fetch('/inspecciones/33/disposicion', {
  method: 'POST',
  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
  body: 'destino=inventario&justificacion=forzado'
}).then(r => r.status)
```

Sustituye el 33 por el numero de la devolucion que acabas de crear. Responde
**409**, y al recargar el expediente se ve el mensaje del disparador de
PostgreSQL.

**Repite con el reembolso.** Intenta aprobar un monto muy superior al valor
devuelto. El sistema responde que excede el valor y senala posible fraude.

**Que decir.** Que estas reglas viven como disparadores dentro de PostgreSQL y
no en el codigo de la aplicacion. La razon es la evolucion del sistema: a partir
del segundo parcial varios microservicios escribiran sobre las mismas tablas, y
una regla que solo vive en la aplicacion web se rompe en cuanto otro servicio
omite verificarla. En la base de datos se cumple siempre, sin importar quien
escriba.

**Cubre:** RN-04, RN-06, RN-07, RF-25.

## 5. Almacenamiento en PostgreSQL (2 min)

Deja el panel general visible en el navegador y en la terminal ejecuta:

```bash
docker compose exec postgres psql -U devoluciones_app -d devoluciones \
  -c "SELECT estado, COUNT(*) FROM devoluciones WHERE eliminado_en IS NULL GROUP BY estado ORDER BY 2 DESC;"
```

Los numeros coinciden exactamente con las tarjetas de la pantalla.

Muestra tambien las claves de Redis:

```bash
docker compose exec redis redis-cli KEYS 'devoluciones:*'
```

Apareceran las sesiones activas.

**Que decir.** Que la informacion esta repartida con criterio: PostgreSQL guarda
el expediente, que debe ser integro y auditable, y Redis guarda lo temporal
—sesiones, intentos fallidos y bloqueos— que se escribe en cada peticion y puede
expirar solo.

**Cubre:** almacenamiento en PostgreSQL, distribucion justificada de datos.

## 6. Catalogos y auditoria (2 min)

Como administrador, entra a **Catalogos**, agrega un motivo de devolucion nuevo
y desactiva otro.

Senala que los registros **no se borran, se desactivan**: un producto
desactivado deja de aparecer al registrar una devolucion nueva, pero las
devoluciones existentes que lo referencian permanecen intactas.

Entra despues a **Bitacora**. Arriba aparece la accion que acabas de ejecutar,
con tu usuario, la fecha, la entidad afectada, el identificador de correlacion
y la direccion de origen.

Filtra por la accion `acceso_denegado` y muestra el intento del cliente que
bloqueaste en el punto 2.

**Que decir.** Que toda operacion importante deja rastro, incluidos los intentos
fallidos de acceso, y que el identificador de correlacion existe desde ahora
porque sera lo que permita seguir una peticion entre microservicios cuando el
sistema se divida.

**Cubre:** operacion de catalogos, registro de auditoria.

## 7. Cierre (1 min)

Di con claridad que es lo que **no** esta construido y por que: microservicios,
aplicacion movil, aplicacion de escritorio, JWT, XML, MongoDB en operacion y
Cloud Storage corresponden al segundo y tercer parcial. Explica que el monolito
se diseno para poder partirse: cada modulo del codigo corresponde a un
microservicio del catalogo, las capas estan separadas, y ya existen el health
check y el identificador de correlacion, que solo tienen sentido en la
arquitectura distribuida.

Reconocer el alcance real da mas credibilidad que aparentar que todo esta hecho.

## Preguntas probables

**"Como se que esto no esta programado a mano en la pantalla."**
Muestra la consulta de `psql` junto al panel, o crea una devolucion en vivo y
observa como cambia el contador.

**"Que pasa si se cae Redis."**
El expediente no se pierde, porque vive integramente en PostgreSQL. El usuario
tendria que iniciar sesion nuevamente. El bloqueo de cuentas no se levanta,
porque se persiste tambien en la columna `usuarios.bloqueado_hasta`.

**"Por que no usaron un ORM."**
Porque el esquema ya estaba disenado en SQL, con disparadores y restricciones
que un ORM tiende a ocultar. La proteccion contra inyeccion se garantiza usando
siempre parametros ligados, nunca concatenacion.

**"Donde esta MongoDB."**
Disenado en la seccion 4.4 pero no implementado. La columna
`inspecciones_ref.mongo_doc_id` ya existe con valor nulo, de modo que
habilitarlo no requerira migrar informacion ni modificar el esquema relacional.

**"Como colaboro el equipo."**
Ramas por integrante y solicitudes de incorporacion hacia la rama principal. El
historial de git es la evidencia.

**"Que pasa si dos usuarios registran una devolucion al mismo tiempo."**
El folio se genera con una secuencia de PostgreSQL, no contando registros, asi
que no puede duplicarse.

## Si algo falla durante la presentacion

- **La pagina no carga.** Verifica la IP externa: cambia cada vez que se apaga y
  enciende la instancia. Comprueba tambien que la regla del firewall incluya la
  red desde la que estas presentando.
- **Un contenedor esta caido.** `docker compose up -d` y espera veinte segundos.
- **Una cuenta quedo bloqueada por intentos fallidos.** Entra como administrador
  y usa **Desbloquear** en la pantalla de usuarios.
- **Los datos quedaron desordenados de una prueba anterior.** El procedimiento
  para reiniciar la base desde cero esta en `docs/SETUP.md`. Requiere unos dos
  minutos, asi que hazlo antes de presentar, nunca durante.
