# Manual de usuario

Recorrido de la plataforma por perfil. Cada seccion describe que ve el usuario
al entrar, que puede hacer y que tiene prohibido.

Todos entran por la misma pantalla de inicio de sesion. Lo que cambia despues es
el menu: cada perfil ve unicamente las secciones que le corresponden, y aunque
escriba a mano la direccion de una seccion ajena, el sistema responde 403 y deja
el intento registrado en la bitacora (RNF-09, RN-13).

El recorrido sigue el orden natural del proceso: cliente, analista, coordinador,
encargado del centro, inspector, encargado de reembolsos y administrador.

---

## Cliente

**Menu:** Panel, Ventas, Devoluciones.

Al entrar ve **Mis devoluciones**: un contador por cada estado en el que tiene
casos y la lista de sus solicitudes recientes. Es el resumen de su situacion, no
del sistema.

**Registrar una devolucion.** Entra a **Ventas**, donde aparecen unicamente sus
compras. Abre una venta y ve sus articulos con producto, lote, caducidad,
proveedor, cantidad comprada y cuantas unidades ya devolvio. Pulsa **Devolver**
en el articulo que corresponda.

La devolucion se registra sobre la linea especifica, no sobre la venta completa:
si compro cinco productos y quiere devolver uno, eso es lo que hace (RF-06). El
sistema no permite devolver mas unidades de las que compro, y si ya devolvio
todas, el boton desaparece.

Captura el motivo, la cantidad y la descripcion del problema. Al guardar, la
plataforma genera un folio unico e irrepetible (RN-02) y abre el expediente.

**Agregar evidencia.** Dentro del expediente puede sumar comentarios y la
referencia de fotografias o documentos en cualquier momento del proceso (RF-09).

**Consultar el estado.** El expediente muestra el avance completo: la
autorizacion, la recoleccion, la inspeccion, la disposicion y el reembolso
conforme ocurren, mas el historial del caso reconstruido desde la bitacora
(RF-11).

**No puede:** ver devoluciones ni compras de otros clientes, aunque conozca el
folio o el identificador; autorizar; inspeccionar; decidir el destino del
producto; entrar a catalogos, usuarios o bitacora.

---

## Analista de devoluciones

**Menu:** Panel, Ventas, Devoluciones, Causas, Costos, Catalogos, Usuarios,
Bitacora.

Es el perfil con mayor capacidad de decision. Al entrar ve el **Panel general**
con el total de devoluciones, el desglose por estado y las mas recientes de todo
el sistema.

**Autorizar solicitudes.** Abre un expediente en estado *solicitada* o *en
revision* y aparece el bloque **Revisar solicitud** con tres opciones:
autorizar, rechazar o solicitar informacion adicional (RF-10). El rechazo exige
justificacion. La decision queda registrada con su nombre y la fecha (RN-12).

**Decidir el destino del producto.** Cuando existe una inspeccion, el expediente
ofrece decidir la disposicion: inventario, reparacion, reacondicionamiento,
reciclaje, devolucion al proveedor o desecho (RF-18).

Si la inspeccion marco el producto como no apto, la opcion *inventario* aparece
deshabilitada, y si alguien manipula la peticion para forzarla, PostgreSQL la
rechaza con un mensaje explicito. La regla se cumple en la base de datos, no en
el formulario (RN-06, RN-07).

**Panel de causas.** Agrupa las devoluciones por motivo, producto, lote,
proveedor y clasificacion de temperatura, con graficas. Sirve para detectar que
un lote o un proveedor concentra casos (RF-26, RN-10). Conforme a RN-09, el
panel presenta coincidencias: no determina causas ni asigna responsabilidades.

**Costos.** Muestra el gasto acumulado por etapa del proceso y el detalle por
caso (RF-27).

**Bitacora.** Consulta el historial de acciones del sistema, con filtros por
accion y entidad (RF-30).

**No puede:** dar de alta usuarios ni modificar catalogos; solo consultarlos.
Tampoco inspecciona productos ni aprueba reembolsos.

---

## Coordinador de logistica

**Menu:** Panel, Ventas, Devoluciones, Recolecciones.

Su pantalla de trabajo es **Recolecciones**, dividida en dos partes: las
devoluciones autorizadas que todavia no tienen recoleccion programada, y las
recolecciones ya registradas con su estado.

**Programar una recoleccion.** Solo aparece para devoluciones autorizadas.
Captura fecha y lugar, y asigna ruta y transportista (RF-12, RF-13). Si el
producto es refrigerado, la pantalla lo advierte para que considere transporte
con control de temperatura y no se rompa la cadena de frio antes de la
inspeccion.

Al guardar, la devolucion pasa al estado *en recoleccion*.

**Actualizar el estado.** Desde el expediente puede mover la recoleccion entre
programada, asignada, en transito, completada y fallida. No podra marcarla como
completada si le faltan fecha, lugar, ruta o transportista (RN-08).

**No puede:** entrar a inspecciones ni decidir el destino del producto.

---

## Encargado del centro de devoluciones

**Menu:** Panel, Ventas, Devoluciones, Recolecciones, Inventario.

**Confirmar la recepcion.** Cuando un producto llega al centro, abre el
expediente correspondiente y registra la recepcion, indicando si el articulo
coincide con lo declarado (RF-15). La devolucion pasa a *recibida* y queda lista
para inspeccion. Si no coincide, queda asentado en el historial del caso.

**Inventario recuperado.** La pantalla tiene dos partes. Arriba, los productos
cuya disposicion fue *inventario* y aun no tienen etiqueta; pulsa **Generar
etiqueta** y el sistema crea un codigo unico derivado del folio. Abajo, el
inventario recuperado completo con su codigo, producto, devolucion de origen y
estado (RF-19).

**No puede:** aprobar reembolsos ni modificar catalogos.

---

## Inspector

**Menu:** Panel, Ventas, Devoluciones, Inspecciones.

**Inspecciones** es su cola de trabajo: arriba los productos recibidos
pendientes de revisar, abajo las inspecciones ya realizadas.

**Registrar una inspeccion.** El formulario cambia segun el producto (RN-05):

- Siempre pide estado del empaque, danos fisicos visibles y si la caducidad esta
  vencida.
- Si el producto es **refrigerado**, ademas exige temperatura de recepcion,
  minutos fuera de refrigeracion y si hubo ruptura de la cadena de frio
  (RF-17). Sin esos datos no deja guardar.

Al guardar, el sistema calcula solo si el producto es apto para inventario y
explica por que. Por ejemplo: *"no apto: ruptura documentada de la cadena de
frio; permanecio 420 minutos fuera de refrigeracion (limite 240)"*. Ese veredicto
es el que despues condiciona la decision del analista (RN-06, RN-07).

El detalle capturado queda ademas como evidencia dentro del expediente.

**No puede:** autorizar solicitudes ni decidir el destino final del producto. Su
trabajo es documentar el estado del articulo, no resolver el caso.

---

## Encargado de reembolsos

**Menu:** Panel, Ventas, Devoluciones, Reembolsos, Costos.

**Reembolsos** lista los casos pendientes de resolver y los ya registrados. En
la lista de pendientes aparecen unicamente devoluciones que ya pasaron por
autorizacion: una solicitud sin autorizar no es visible ni gestionable (RN-04).

**Gestionar un reembolso.** La pantalla muestra la cantidad devuelta, el precio
unitario y el valor maximo a reembolsar. Puede aprobar, capturando monto y
metodo, o rechazar (RF-20).

Si captura un monto mayor al valor de lo devuelto, PostgreSQL lo rechaza
senalando posible fraude. Igual que con el destino del producto, la regla vive
en la base de datos (RF-25).

Al aprobar, el monto se registra como costo de la etapa de reembolso y, si la
devolucion ya tenia disposicion, el caso se cierra.

**No puede:** decidir el destino del producto ni autorizar la devolucion. Solo
actua sobre casos ya autorizados.

---

## Administrador

**Menu:** Panel, Ventas, Devoluciones, Causas, Costos, Catalogos, Usuarios,
Bitacora.

**Usuarios.** Da de alta cuentas asignando rol, edita, restablece contrasenas,
desbloquea cuentas bloqueadas por intentos fallidos y da de baja (RF-03, RF-04).

La baja es logica: la cuenta deja de poder entrar pero se conserva, porque su
nombre aparece en devoluciones, inspecciones y bitacoras que deben seguir siendo
legibles (RNF-30).

**Catalogos.** Mantiene los siete catalogos del sistema: proveedores, productos,
lotes, tiendas, rutas, transportistas y motivos de devolucion (RF-05).

Los registros no se borran, se desactivan. Un producto desactivado ya no aparece
al registrar una devolucion nueva, pero las devoluciones existentes que lo
referencian siguen intactas.

**Bitacora.** Revisa todas las acciones del sistema con su usuario, fecha,
entidad afectada, identificador de correlacion y direccion de origen (RF-30).

**No participa** en la operacion diaria: no autoriza devoluciones, no
inspecciona y no aprueba reembolsos.

---

## El proceso completo, de principio a fin

| Paso | Perfil | Accion | Estado resultante |
|---|---|---|---|
| 1 | Cliente | Registra la devolucion desde una linea de venta | solicitada |
| 2 | Cliente | Agrega evidencia | solicitada |
| 3 | Analista | Autoriza | autorizada |
| 4 | Coordinador | Programa la recoleccion | en recoleccion |
| 5 | Encargado del centro | Confirma la recepcion | recibida |
| 6 | Inspector | Registra la inspeccion | en inspeccion |
| 7 | Analista | Decide el destino | resuelta |
| 8 | Encargado de reembolsos | Aprueba el reembolso | cerrada |

En cualquier punto, el analista puede rechazar la solicitud o pedir informacion
adicional, y cada movimiento queda en el historial del caso.
