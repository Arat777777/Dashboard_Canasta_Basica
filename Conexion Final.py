import pandas as pd
import mysql.connector

# ============================
# CONFIGURACIÓN
# ============================
CSV_SORIANA = "dataset/canasta_total_limpio.csv"

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'BRUNO0205',
    'database': 'canasta_basicaa'
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(buffered=True)

# ============================
# FUNCIONES AUXILIARES
# ============================

def log(origen, mensaje, tipo="INFO"):
    cursor.execute("""
        INSERT INTO logs (origen, mensaje, tipo)
        VALUES (%s, %s, %s)
    """, (origen, mensaje, tipo))

def limpiar_precio(valor):
    if pd.isna(valor):
        return 0.00
    return float(str(valor).replace("$", "").replace(",", "").strip())

def safe(v):
    if v is None or pd.isna(v):
        return None
    v = str(v).strip()
    return None if v.lower() in ["nan", "none", "null", ""] else v

def obtener_unidad_id(unidad):
    unidad = safe(unidad) or "pza"
    unidad = unidad.lower().strip()

    validas = ["ml", "g", "kg", "l", "pza", "pz", "sob"]
    if unidad not in validas:
        unidad = "pza"

    if unidad == "pz":
        unidad = "pza"

    cursor.execute("SELECT id FROM unidades WHERE abreviatura=%s", (unidad,))
    res = cursor.fetchone()
    return res[0] if res else None

# ============================
# CARGA PRINCIPAL
# ============================

def insertar_supermercado_y_productos(csv_file):

    log("ETL", f"Iniciando carga CSV unificado")

    df = pd.read_csv(csv_file).where(pd.notnull(pd.read_csv(csv_file)), None)

    for index, row in df.iterrows():

        nombre_super = safe(row.get("Supermercado"))
        if nombre_super is None:
            log("ETL", f"Fila {index} sin supermercado", "WARNING")
            continue

        sitio = f"https://{nombre_super.lower().replace(' ', '')}.com"

        # Registrar supermercado
        cursor.execute("""
            INSERT INTO supermercados (nombre, sitio)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE sitio = VALUES(sitio)
        """, (nombre_super, sitio))

        cursor.execute("SELECT id FROM supermercados WHERE nombre=%s", (nombre_super,))
        supermercado_id = cursor.fetchone()[0]

        categoria = safe(row.get("Producto buscado"))
        nombre = safe(row.get("Nombre"))
        unidad = safe(row.get("Unidad"))
        cantidad = row.get("Cantidad")
        precio = limpiar_precio(row.get("Precio"))
        precio_x_u = row.get("Precio_por_unidad")
        promedio_cat = row.get("Promedio_categoria_supermercado")

        if nombre is None:
            log("ETL", f"Fila {index} saltada: Nombre NULL", "WARNING")
            continue

        # Categoría
        cursor.execute("""
            INSERT IGNORE INTO categorias (nombre) VALUES (%s)
        """, (categoria,))
        cursor.execute("SELECT id FROM categorias WHERE nombre=%s", (categoria,))
        id_categoria = cursor.fetchone()[0]

        unidad_id = obtener_unidad_id(unidad)

        # Insertar producto
        cursor.execute("""
            INSERT INTO productos 
            (nombre, id_categoria, supermercado_id, unidad_id, cantidad, precio, precio_por_unidad, promedio_categoria_supermercado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            nombre, id_categoria, supermercado_id, unidad_id,
            cantidad, precio, precio_x_u, promedio_cat
        ))

        producto_id = cursor.lastrowid

        # Historial
        cursor.execute("""
            INSERT INTO historial_precios (producto_id, precio, precio_por_unidad, supermercado_id)
            VALUES (%s, %s, %s, %s)
        """, (producto_id, precio, precio_x_u, supermercado_id))

    conn.commit()
    log("ETL", f"Carga completada", "SUCCESS")


# ============================
# EJECUCIÓN
# ============================

insertar_supermercado_y_productos(CSV_SORIANA)

cursor.close()
conn.close()

print("\nCARGA COMPLETADA EXITOSAMENTE.")