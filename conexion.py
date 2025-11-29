import pandas as pd
import mysql.connector
from datetime import datetime

# ============================
# CONFIGURACIÓN
# ============================
CSV_SORIANA = "dataset/canasta_soriana_transformado.csv"
CSV_CALIMAX = "dataset/canasta_calimax_transformado.csv"

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'fortnite',
    'database': 'canasta_basica'
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(buffered=True)

# ============================
# FUNCIONES DE APOYO
# ============================

def log(origen, mensaje, tipo="INFO"):
    cursor.execute("""
        INSERT INTO logs (origen, mensaje, tipo)
        VALUES (%s, %s, %s)
    """, (origen, mensaje, tipo))

def limpiar_precio(valor):
    if pd.isna(valor):
        return 0.00
    val = str(valor).replace("$", "").replace(",", "").strip()
    try:
        return float(val)
    except:
        return 0.00

def safe(v):
    """Convierte NaN, None, 'nan', '', etc → None"""
    if v is None:
        return None
    if pd.isna(v):
        return None
    v = str(v).strip()
    if v.lower() in ["nan", "none", "null", ""]:
        return None
    return v

def obtener_unidad_id(unidad):
    unidad = safe(unidad)
    if unidad is None:
        unidad = "pza"

    unidad = str(unidad).lower().strip()

    mapa = {
        "ml": "ml",
        "g": "g",
        "kg": "kg",
        "l": "l",
        "pza": "pza",
        "sob": "sob"
    }

    if unidad not in mapa:
        unidad = "pza"

    cursor.execute("SELECT id FROM unidades WHERE abreviatura=%s", (unidad,))
    res = cursor.fetchone()
    return res[0] if res else None


# ============================
# ETL PRINCIPAL
# ============================

def insertar_supermercado_y_productos(csv_file, nombre_super, sitio):

    log("ETL", f"Iniciando carga de {nombre_super}", "INFO")

    # Insertar supermercado
    cursor.execute("""
        INSERT INTO supermercados (nombre, sitio)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE sitio = VALUES(sitio)
    """, (nombre_super, sitio))

    cursor.execute("SELECT id FROM supermercados WHERE nombre=%s", (nombre_super,))
    supermercado_id = cursor.fetchone()[0]

    # Cargar CSV con None
    df = pd.read_csv(csv_file).where(pd.notnull(pd.read_csv(csv_file)), None)

    for index, row in df.iterrows():

        categoria = safe(row.get("Producto buscado"))
        nombre = safe(row.get("Nombre"))
        precio = limpiar_precio(row.get("Precio"))
        presentacion = safe(row.get("Presentación"))
        unidad = safe(row.get("Unidad"))
        cantidad = safe(row.get("Cantidad"))

        # 🚫 Si el nombre del producto viene vacío → saltar fila
        if nombre is None:
            log("ETL", f"Fila {index} saltada en {nombre_super}: 'nombre' es NULL", "WARNING")
            continue

        # Insertar categoría
        cursor.execute("""
            INSERT IGNORE INTO categorias (nombre) VALUES (%s)
        """, (categoria,))

        cursor.execute("SELECT id FROM categorias WHERE nombre=%s", (categoria,))
        id_categoria = cursor.fetchone()[0]

        # Unidad
        unidad_id = obtener_unidad_id(unidad)

        # Insertar producto
        cursor.execute("""
            INSERT INTO productos (nombre, precio, presentacion, id_categoria, supermercado_id, unidad_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            nombre,
            precio,
            presentacion,
            id_categoria,
            supermercado_id,
            unidad_id
        ))

        producto_id = cursor.lastrowid

        # Historial de precios
        cursor.execute("""
            INSERT INTO historial_precios (producto_id, precio, supermercado_id)
            VALUES (%s, %s, %s)
        """, (producto_id, precio, supermercado_id))

    conn.commit()
    log("ETL", f"Finalizó la carga de {nombre_super}", "SUCCESS")


# ============================
# EJECUCIÓN
# ============================

insertar_supermercado_y_productos(CSV_SORIANA, "Soriana", "https://www.soriana.com")
insertar_supermercado_y_productos(CSV_CALIMAX, "Calimax", "https://tienda.calimax.com.mx")

cursor.close()
conn.close()

print("\n✅ TODOS LOS DATOS DE SORIANA Y CALIMAX INSERTADOS EXITOSAMENTE.")


