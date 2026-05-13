INSERT INTO support_groups (name, description, is_director_group)
VALUES
('Bases de datos', 'Equipo responsable de plataformas de bases de datos', FALSE),
('Sistemas operativos', 'Equipo responsable de servidores y sistemas operativos', FALSE),
('Respaldos', 'Equipo responsable de respaldos y recuperación', FALSE),
('Redes', 'Equipo responsable de conectividad y redes', FALSE),
('Directores', 'Grupo de directores para escalamiento final', TRUE)
ON CONFLICT (name) DO NOTHING;

INSERT INTO engineers (full_name, extension, mobile_phone)
VALUES
('Pedro Pérez', '101', NULL),
('Juan Molano', '102', NULL),
('Víctor Cifuentes', '103', NULL),

('Wilson Ruiz', '201', NULL),
('Fredy Sánchez', '202', NULL),
('Juan Arango', '203', NULL),

('Pepe Blandón', '301', NULL),
('Catherine Ramos', '302', NULL),
('Sandra Aguilera', '303', NULL),

('Lady Suárez', '401', NULL),
('Paula Ramírez', '402', NULL),
('Laura Díaz', '403', NULL)
ON CONFLICT DO NOTHING;