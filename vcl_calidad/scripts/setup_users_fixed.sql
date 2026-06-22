-- Archivo: scripts/setup_users_fixed.sql
-- Añade la columna `puede_gestionar_usuarios` y crea/actualiza los usuarios solicitados.
-- Usa los roles ya presentes en database_vcl.sql ('Horno' y 'ADMIN').
-- Ejecutar con psql: psql "<CONNECTION_STRING>" -f scripts/setup_users_fixed.sql

BEGIN;

-- 1) Añadir la columna si no existe
ALTER TABLE usuarios
  ADD COLUMN IF NOT EXISTS puede_gestionar_usuarios BOOLEAN DEFAULT FALSE;

-- 2) Asegurar que los roles existen (no hace nada si ya existen)
INSERT INTO roles (nombre) VALUES ('Horno') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO roles (nombre) VALUES ('ADMIN') ON CONFLICT (nombre) DO NOTHING;

-- 3) Insertar o actualizar al usuario 'luis' usando el rol 'Horno'
INSERT INTO usuarios (
  nombre, email, password, rol_id, activo,
  puede_ver_reclamaciones, puede_ver_tickets, puede_ver_reportes, puede_gestionar_usuarios
)
VALUES (
  'luis',
  'luis.perez@pro.com',
  md5('admin' || 'luis.perez@pro.com'),
  (SELECT id FROM roles WHERE nombre = 'Horno'),
  TRUE,
  FALSE,
  TRUE,
  FALSE,
  FALSE
)
ON CONFLICT (email) DO UPDATE SET
  nombre = EXCLUDED.nombre,
  password = EXCLUDED.password,
  rol_id = COALESCE(EXCLUDED.rol_id, usuarios.rol_id),
  activo = EXCLUDED.activo,
  puede_ver_reclamaciones = EXCLUDED.puede_ver_reclamaciones,
  puede_ver_tickets = EXCLUDED.puede_ver_tickets,
  puede_ver_reportes = EXCLUDED.puede_ver_reportes,
  puede_gestionar_usuarios = EXCLUDED.puede_gestionar_usuarios;

-- 4) Insertar o actualizar al usuario admin@vclaminations.com con permisos de gestión de usuarios usando rol 'ADMIN'
INSERT INTO usuarios (
  nombre, email, password, rol_id, activo,
  puede_ver_reclamaciones, puede_ver_tickets, puede_ver_reportes, puede_gestionar_usuarios
)
VALUES (
  'Admin',
  'admin@vclaminations.com',
  md5('admin123' || 'admin@vclaminations.com'),
  (SELECT id FROM roles WHERE nombre = 'ADMIN'),
  TRUE,
  TRUE,
  TRUE,
  TRUE,
  TRUE
)
ON CONFLICT (email) DO UPDATE SET
  password = EXCLUDED.password,
  activo = EXCLUDED.activo,
  puede_ver_reclamaciones = EXCLUDED.puede_ver_reclamaciones,
  puede_ver_tickets = EXCLUDED.puede_ver_tickets,
  puede_ver_reportes = EXCLUDED.puede_ver_reportes,
  puede_gestionar_usuarios = EXCLUDED.puede_gestionar_usuarios;

COMMIT;
