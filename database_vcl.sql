-- ROLES 

CREATE TABLE Roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(25) NOT NULL UNIQUE
);





DROP TABLE IF EXISTS Usuarios CASCADE;

CREATE TABLE Usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(40) NOT NULL,
    email VARCHAR(40) NOT NULL UNIQUE,
    -- La contraseña se hashea sola combinando el texto con el email usando MD5 nativo
    password VARCHAR(255) NOT NULL, 
    rol_id INT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE,
    puede_ver_reclamaciones BOOLEAN DEFAULT TRUE,
    puede_ver_tickets BOOLEAN DEFAULT TRUE,
    puede_ver_reportes BOOLEAN DEFAULT FALSE,
    puede_gestionar_usuarios BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (rol_id) REFERENCES Roles(id)
);




-- RECLAMACIONES TABLES
CREATE TABLE Categorias (
    id_categorias SERIAL PRIMARY KEY,
    categoria VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE Defectos (
    id_defecto SERIAL PRIMARY KEY,
    defecto VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE Ocurrencias (
    id_ocurrencia SERIAL PRIMARY KEY,
    ocurrencia VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE Tipo_de_Reclamacion (
    id_tipo_de_reclamacion SERIAL PRIMARY KEY,
    tipo_reclamacion VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE Estatus_Reclamaciones (
    id_estatus SERIAL PRIMARY KEY,
    descripcion_status VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE Clientes (
    id_cliente SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL
);

CREATE TABLE Contenedores (
    id_numero_contenedor SERIAL PRIMARY KEY,
    numero_contenedor VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Reclamaciones (
    id SERIAL PRIMARY KEY,
    id_reporte_cliente VARCHAR(50) NOT NULL UNIQUE,
    issue VARCHAR(255) NOT NULL,
    id_defecto INT NOT NULL,
    id_categoria INT NOT NULL,
    id_ocurrencia INT NOT NULL,
    id_numero_contenedor INT,
    id_tipo_de_reclamacion INT NOT NULL,
    numero_parte VARCHAR(50),
    id_cliente INT,
    lote VARCHAR(50),
    cantidad_piezas INT,
    cantidad_kg DECIMAL(10,2),
    fecha_reporte DATE NOT NULL,
    fecha_confirmacion DATE,
    fecha_contencion DATE,
    fecha_CR_AC DATE,
    fecha_cierre DATE,
    dias_retrazo_al_reclamo INT DEFAULT 0,

    periodo VARCHAR(50),
    id_estatus INT NOT NULL,

    FOREIGN KEY (id_defecto) REFERENCES Defectos(id_defecto),
    FOREIGN KEY (id_categoria) REFERENCES Categorias(id_categorias),
    FOREIGN KEY (id_ocurrencia) REFERENCES Ocurrencias(id_ocurrencia),
    FOREIGN KEY (id_numero_contenedor) REFERENCES Contenedores(id_numero_contenedor),
    FOREIGN KEY (id_cliente) REFERENCES Clientes(id_cliente),
    FOREIGN KEY (id_estatus) REFERENCES Estatus_Reclamaciones(id_estatus),
    FOREIGN KEY (id_tipo_de_reclamacion) REFERENCES Tipo_de_Reclamacion(id_tipo_de_reclamacion)
);

-- TICKETS TABLES

CREATE TABLE Color_Ticket (
    id_color SERIAL PRIMARY KEY,
    color_ticket VARCHAR(20) NOT NULL UNIQUE,
    descripcion_color_ticket VARCHAR(255)
);

CREATE TABLE Area (
    id_area SERIAL PRIMARY KEY,
    area VARCHAR(100) NOT NULL UNIQUE
);


CREATE TABLE Estatus_Ticket (
    id_estatus_ticket SERIAL PRIMARY KEY,
    status_descripcion VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE Ticket (
    id_folio_ticket SERIAL PRIMARY KEY,
    id_color_ticket INT,
    emisor VARCHAR(100),
    id_area_responsable INT,
    fecha_emicion DATE NOT NULL,
    fecha_compromiso DATE,
    fecha_cierre DATE,
    id_estatus_ticket INT NOT NULL,
    dias_retrazo INT DEFAULT 0,
    FOREIGN KEY (id_color_ticket) REFERENCES Color_Ticket(id_color),
    FOREIGN KEY (id_area_responsable) REFERENCES Area(id_area),
    FOREIGN KEY (id_estatus_ticket) REFERENCES Estatus_Ticket(id_estatus_ticket)
);

-- INSERT ROLES Y ÁREAS

INSERT INTO Roles (nombre) VALUES 
    ('ADMIN'),
    ('ENCARGADO'),
    ('CTL''s'),
    ('Calidad'),
    ('Estampado'),
    ('Cadena de suministro'),
    ('Mantenimiento'),
    ('Ventas'),
    ('Taller / Ingeniería'),
    ('Nuevos desarrollos'),
    ('Horno'),
    ('TI'),
    ('Planeación'),
    ('SH');


INSERT INTO Area (area) VALUES 
    ('CTL''s'),
    ('Calidad'),
    ('Estampado'),
    ('Cadena de suministro'),
    ('Mantenimiento'),
    ('Ventas'),
    ('Taller / Ingeniería'),
    ('Nuevos desarrollos'),
    ('Horno'),
    ('TI'),
    ('Planeación'),
    ('SH');



    -- =========================================================================
-- 1. CATÁLOGOS MODIFICADOS Y NUEVOS
-- =========================================================================

CREATE TABLE Turnos (
    id_turno SERIAL PRIMARY KEY,
    nombre_turno VARCHAR(25) NOT NULL UNIQUE, -- 'Turno Primero', 'Turno Segundo'
    hora_inicio TIME NOT NULL,                -- Ejemplo: '06:00:00'
    hora_fin TIME NOT NULL                    -- Ejemplo: '14:00:00'
);

CREATE TABLE Maquinas (
    id_maquina SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Operadores (
    id_operador SERIAL PRIMARY KEY,
    nombre VARCHAR(60) NOT NULL UNIQUE
);

CREATE TABLE Defectos_Scrap (
    id_defecto_scrap SERIAL PRIMARY KEY,
    defecto VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE Clasificaciones_Scrap (
    id_clasificacion SERIAL PRIMARY KEY,
    clasificacion VARCHAR(50) NOT NULL UNIQUE -- 'Scrap Directo', 'Retrabajable', 'Producto NG'
);

CREATE TABLE Supervisores (
    id_supervisor SERIAL PRIMARY KEY,
    nombre VARCHAR(60) NOT NULL UNIQUE
);

CREATE TABLE Tipos_Acero (
    id_tipo_acero SERIAL PRIMARY KEY,
    especificacion VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Estatus_Scrap (
    id_estatus_scrap SERIAL PRIMARY KEY,
    descripcion_status VARCHAR(50) NOT NULL UNIQUE
);

-- =========================================================================
-- 2. TABLA OPERATIVA (RELACIÓN DINÁMICA)
-- =========================================================================

CREATE TABLE Scrap (
    id SERIAL PRIMARY KEY,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Año, mes, día, hora, minutos
    
    id_maquina INT NOT NULL,
    id_operador INT NOT NULL,
    id_turno INT NOT NULL,         -- Se calculará comparando la hora actual con el rango de la tabla Turnos
    id_defecto_scrap INT NOT NULL,
    id_clasificacion INT NOT NULL,
    id_supervisor INT NOT NULL,
    id_cliente INT NOT NULL,      -- Relación directa a tu tabla de Clientes existente
    id_tipo_acero INT NOT NULL,
    id_estatus_scrap INT NOT NULL,
    
    numero_parte VARCHAR(50) NOT NULL,
    lote VARCHAR(50) NOT NULL,
    peso DECIMAL(10,2) NOT NULL,
    cantidad_retrabajado INT DEFAULT 0,
    cantidad_ng INT DEFAULT 0,
    
    usuario_registro_id INT NOT NULL, -- Historial: Quién lo registró (session['user_id'])

    FOREIGN KEY (id_maquina) REFERENCES Maquinas(id_maquina),
    FOREIGN KEY (id_operador) REFERENCES Operadores(id_operador),
    FOREIGN KEY (id_turno) REFERENCES Turnos(id_turno),
    FOREIGN KEY (id_defecto_scrap) REFERENCES Defectos_Scrap(id_defecto_scrap),
    FOREIGN KEY (id_clasificacion) REFERENCES Clasificaciones_Scrap(id_clasificacion),
    FOREIGN KEY (id_supervisor) REFERENCES Supervisores(id_supervisor),
    FOREIGN KEY (id_cliente) REFERENCES Clientes(id_cliente),
    FOREIGN KEY (id_tipo_acero) REFERENCES Tipos_Acero(id_tipo_acero),
    FOREIGN KEY (id_estatus_scrap) REFERENCES Estatus_Scrap(id_estatus_scrap),
    FOREIGN KEY (usuario_registro_id) REFERENCES Usuarios(id)
);

-- =========================================================================
-- 3. INSERTS DE CONFIGURACIÓN CON SUS HORARIOS (TIME)
-- =========================================================================

-- Ajusta  ('HH:MM:SS') según los turnos reales de VC Laminations
INSERT INTO Turnos (nombre_turno, hora_inicio, hora_fin) VALUES 
    ('Turno Primero', '06:00:00', '14:00:00'),
    ('Turno Segundo', '14:00:00', '22:00:00');

INSERT INTO Estatus_Scrap (descripcion_status) VALUES 
    ('Pendiente de Validación'),
    ('Aprobado / Procesado'),
    ('Rechazado');