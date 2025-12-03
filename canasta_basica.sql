CREATE DATABASE IF NOT EXISTS canasta_basica;
USE canasta_basica;

-- logs
CREATE TABLE IF NOT EXISTS logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    origen VARCHAR(100),
    mensaje TEXT,
    tipo VARCHAR(20),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- TABLA: unidades de los productos
CREATE TABLE IF NOT EXISTS unidades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    abreviatura VARCHAR(10) UNIQUE NOT NULL
);

INSERT IGNORE INTO unidades (abreviatura) VALUES
('ml'), ('g'), ('kg'), ('l'), ('pza'), ('sob');


-- supermercados
CREATE TABLE IF NOT EXISTS supermercados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    sitio VARCHAR(255)
);


-- categorias

CREATE TABLE IF NOT EXISTS categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) UNIQUE NOT NULL
);


--  productos
CREATE TABLE IF NOT EXISTS productos (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- NUEVO DATASET
    nombre VARCHAR(300) NOT NULL,
    id_categoria INT,
    supermercado_id INT,
    unidad_id INT,

    cantidad FLOAT,
    precio FLOAT,
    precio_por_unidad FLOAT,
    promedio_categoria_supermercado FLOAT,

    presentacion VARCHAR(100) NULL,

    FOREIGN KEY (id_categoria) REFERENCES categorias(id),
    FOREIGN KEY (supermercado_id) REFERENCES supermercados(id),
    FOREIGN KEY (unidad_id) REFERENCES unidades(id)
);


-- historial de precios

CREATE TABLE IF NOT EXISTS historial_precios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    producto_id INT NOT NULL,
    precio FLOAT NOT NULL,
    precio_por_unidad FLOAT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    supermercado_id INT,
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (supermercado_id) REFERENCES supermercados(id)
);
