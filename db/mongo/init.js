// Inicializacion de MongoDB -- segundo parcial.
//
// Por que existe: la seccion 5.4 del documento define cuatro colecciones y sus
// indices. Crearlas aqui garantiza que cualquiera que levante el entorno desde
// cero obtenga la misma estructura, sin pasos manuales (RNF-27).
//
// Cubre: RNF-06 (informacion semiestructurada en MongoDB), RNF-23 (seguimiento
// por correlation_id), RN-09 (resultados de analisis como apoyo, no decision).
//
// Se ejecuta UNA sola vez, cuando el volumen mongo_data esta vacio. Si cambias
// este archivo y la base ya existe, el cambio no se aplica: hay que hacerlo a
// mano o borrar el volumen (ver docs/SETUP.md).

const nombreBase = process.env.MONGO_DB || "devoluciones";
const base = db.getSiblingDB(nombreBase);

// Usuario de la aplicacion: solo puede leer y escribir en su propia base,
// nunca administrar el motor (principio de minimo privilegio, RNF-14).
base.createUser({
  user: process.env.MONGO_APP_USER,
  pwd: process.env.MONGO_APP_PASSWORD,
  roles: [{ role: "readWrite", db: nombreBase }],
});

// Detalle completo de la inspeccion. En PostgreSQL queda inspecciones_ref con
// el resumen y mongo_doc_id apunta a este documento (RF-16, RF-17).
base.createCollection("inspecciones");
base.inspecciones.createIndex({ devolucion_id: 1 }, { name: "idx_devolucion" });

// Metadatos variables de cada archivo de evidencia (RF-09).
base.createCollection("evidencias_metadatos");
base.evidencias_metadatos.createIndex({ devolucion_id: 1 }, { name: "idx_devolucion" });

// Eventos publicados por los microservicios. correlation_id permite seguir una
// operacion a traves de varios servicios (RNF-23).
base.createCollection("eventos");
base.eventos.createIndex({ correlation_id: 1 }, { name: "idx_correlation" });
base.eventos.createIndex({ fecha: -1 }, { name: "idx_fecha" });

// Salida del analisis de causa raiz: Pareto, agrupaciones y ranking (RF-23 a
// RF-26). Se consultan por tipo y por el calculo mas reciente.
base.createCollection("resultados_analisis");
base.resultados_analisis.createIndex(
  { tipo_analisis: 1, fecha_calculo: -1 },
  { name: "idx_tipo_fecha" }
);

print(`MongoDB inicializado: base '${nombreBase}' con 4 colecciones e indices.`);
