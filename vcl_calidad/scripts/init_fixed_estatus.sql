-- ============================================================
-- SCRIPT PARA INICIALIZAR ESTATUS FIJOS
-- Ejecutar este script si los estatus no están en la BD
-- ============================================================

-- ESTATUS DE TICKETS
INSERT INTO Estatus_Ticket (status_descripcion) VALUES 
    ('Sin atender'),
    ('En proceso'),
    ('Pendiente de validación'),
    ('Cerrado')
ON CONFLICT DO NOTHING;

-- ESTATUS DE SCRAP
INSERT INTO Estatus_Scrap (descripcion_status) VALUES 
    ('Pendiente de Validación'),
    ('Aprobado / Procesado'),
    ('Rechazado')
ON CONFLICT DO NOTHING;

-- Verificar que los estatus fueron insertados
SELECT 'Estatus Tickets:' as tipo;
SELECT * FROM Estatus_Ticket;

SELECT 'Estatus Scrap:' as tipo;
SELECT * FROM Estatus_Scrap;
