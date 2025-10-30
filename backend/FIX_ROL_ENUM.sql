-- ========================================
-- FIX: Actualizar columna ROL en la tabla usuarios
-- ========================================

-- IMPORTANTE: Ejecutar esto en phpMyAdmin para que coincida con el código

-- Opción 1: Si la tabla está vacía (recomendado)
-- Eliminar y recrear la columna con los nuevos valores
ALTER TABLE usuarios 
MODIFY COLUMN rol ENUM('Mantenedor', 'Supervisor', 'Gerente') 
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci 
NOT NULL;

-- Opción 2: Si tienes datos y quieres migrarlos
-- Primero cambiar a VARCHAR temporal
-- ALTER TABLE usuarios MODIFY COLUMN rol VARCHAR(50);

-- Mapear valores antiguos a nuevos
-- UPDATE usuarios SET rol = 'Gerente' WHERE rol = 'Admin';
-- UPDATE usuarios SET rol = 'Supervisor' WHERE rol = 'Analista';
-- UPDATE usuarios SET rol = 'Mantenedor' WHERE rol = 'Consultor';
-- UPDATE usuarios SET rol = 'Mantenedor' WHERE rol = 'Visualizador';

-- Luego cambiar a ENUM con nuevos valores
-- ALTER TABLE usuarios 
-- MODIFY COLUMN rol ENUM('Mantenedor', 'Supervisor', 'Gerente') 
-- CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci 
-- NOT NULL;

-- Verificar que cambió correctamente
SHOW COLUMNS FROM usuarios LIKE 'rol';

-- Debería mostrar:
-- Type: enum('Mantenedor','Supervisor','Gerente')
