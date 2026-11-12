-- FloodAlert · Esquema SQLite (se aplica automáticamente en el primer arranque)

CREATE TABLE IF NOT EXISTS usuarios (
  id_usuario      INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre_completo VARCHAR(120) NOT NULL,
  correo          VARCHAR(150) NOT NULL UNIQUE,
  contrasena_hash VARCHAR(255) NOT NULL,
  rol             TEXT NOT NULL DEFAULT 'ciudadano'
                  CHECK (rol IN ('ciudadano','administrador')),
  activo          INTEGER NOT NULL DEFAULT 1,
  creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS municipios (
  id_municipio INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre       VARCHAR(100) NOT NULL UNIQUE,
  departamento VARCHAR(80) NOT NULL DEFAULT 'Chocó',
  lat          REAL NOT NULL,
  lng          REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS incidentes (
  id_incidente    INTEGER PRIMARY KEY AUTOINCREMENT,
  id_usuario      INTEGER NOT NULL REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
  id_municipio    INTEGER NOT NULL REFERENCES municipios(id_municipio),
  barrio          VARCHAR(120) NOT NULL,
  descripcion     TEXT NOT NULL,
  nivel_agua      TEXT NOT NULL
                  CHECK (nivel_agua IN ('tobillo','rodilla','cintura','pecho','techo')),
  estado          TEXT NOT NULL DEFAULT 'pendiente'
                  CHECK (estado IN ('pendiente','verificado','seguimiento',
                                    'atendido','cerrado','rechazado')),
  lat             REAL NOT NULL,
  lng             REAL NOT NULL,
  fecha_incidente TIMESTAMP,
  creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evidencias (
  id_evidencia  INTEGER PRIMARY KEY AUTOINCREMENT,
  id_incidente  INTEGER NOT NULL REFERENCES incidentes(id_incidente) ON DELETE CASCADE,
  archivo       VARCHAR(255) NOT NULL,
  subida_en     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS seguimiento (
  id_seguimiento INTEGER PRIMARY KEY AUTOINCREMENT,
  id_incidente   INTEGER NOT NULL REFERENCES incidentes(id_incidente) ON DELETE CASCADE,
  id_admin       INTEGER REFERENCES usuarios(id_usuario),
  estado_nuevo   TEXT NOT NULL
                 CHECK (estado_nuevo IN ('pendiente','verificado','seguimiento',
                                         'atendido','cerrado','rechazado')),
  comentario     TEXT,
  creado_en      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS denuncias (
  id_denuncia  INTEGER PRIMARY KEY AUTOINCREMENT,
  id_incidente INTEGER NOT NULL REFERENCES incidentes(id_incidente) ON DELETE CASCADE,
  motivo       VARCHAR(255) NOT NULL,
  creado_en    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inc_estado    ON incidentes(estado);
CREATE INDEX IF NOT EXISTS idx_inc_municipio ON incidentes(id_municipio);
CREATE INDEX IF NOT EXISTS idx_inc_fecha     ON incidentes(fecha_incidente);

-- Municipios del Chocó
INSERT OR IGNORE INTO municipios (nombre, lat, lng) VALUES
  ('Quibdó', 5.694100, -76.661300),
  ('Bagadó', 5.688900, -76.651100),
  ('Istmina', 5.141700, -76.686400),
  ('Condoto', 5.107200, -76.644400),
  ('El Carmen de Atrato', 5.706400, -76.658100),
  ('Lloró', 5.567800, -76.630300),
  ('Nuquí', 5.712000, -77.262200),
  ('Bahía Solano', 6.221400, -77.383300),
  ('Alto Baudó', 5.716700, -76.783300);
