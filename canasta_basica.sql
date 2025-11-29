-- ============================================
--   CREAR BASE DE DATOS
-- ============================================
CREATE DATABASE IF NOT EXISTS canasta_basica;
USE canasta_basica;

-- ============================================
--   TABLA: categorias
-- ============================================
CREATE TABLE IF NOT EXISTS categorias (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(150) NOT NULL
);

-- ============================================
--   TABLA: unidades
-- ============================================
CREATE TABLE IF NOT EXISTS unidades (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL,
    abreviatura VARCHAR(10) NOT NULL,
    UNIQUE KEY (abreviatura)   -- 🔐 importante para ON DUPLICATE
);

-- ============================================
--   TABLA: supermercados
-- ============================================
CREATE TABLE IF NOT EXISTS supermercados (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(150) NOT NULL,
    sitio VARCHAR(255),
    ubicacion VARCHAR(255) NULL,
    UNIQUE KEY (nombre)       -- 🔐 evitar duplicados
);

-- ============================================
--   TABLA: productos
-- ============================================
CREATE TABLE IF NOT EXISTS productos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(255) NOT NULL,
    precio DECIMAL(10,2) NOT NULL,
    presentacion VARCHAR(50),

    id_categoria INT,
    supermercado_id INT,
    unidad_id INT,

    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_categoria) REFERENCES categorias(id)
        ON UPDATE CASCADE ON DELETE SET NULL,

    FOREIGN KEY (supermercado_id) REFERENCES supermercados(id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    FOREIGN KEY (unidad_id) REFERENCES unidades(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

-- ============================================
--   TABLA: historial de precios
-- ============================================
CREATE TABLE IF NOT EXISTS historial_precios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    producto_id INT NOT NULL,
    precio DECIMAL(10,2) NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    supermercado_id INT NOT NULL,

    FOREIGN KEY (producto_id) REFERENCES productos(id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    FOREIGN KEY (supermercado_id) REFERENCES supermercados(id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- ============================================
--   TABLA: logs del ETL / scraping
-- ============================================
CREATE TABLE IF NOT EXISTS logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    origen VARCHAR(100),
    mensaje TEXT,
    tipo VARCHAR(20)
);

-- ============================================
--   INSERTAR UNIDADES ESTÁNDAR
-- ============================================
INSERT IGNORE INTO unidades (nombre, abreviatura) VALUES
('Gramos', 'g'),
('Kilogramos', 'kg'),
('Mililitros', 'ml'),
('Litros', 'l'),
('Pieza', 'pza'),
('Sobre', 'sob');
