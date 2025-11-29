import pandas as pd
import re

# --------------------------
#  Extract
# --------------------------
df = pd.read_csv("dataset/canasta_soriana.csv")
df2 = pd.read_csv("dataset/canasta_calimax.csv")

# --------------------------
#  Añadir columna Ciudad
# --------------------------
df["Ciudad"] = "Tijuana"
df2["Ciudad"] = "Tijuana"


# ---------------------------------------------------
#  Función: Extraer presentación desde nombre o columna
# ---------------------------------------------------
def extraer_presentacion(nombre, presentacion):
    """
    Devuelve algo como:
    - 220 g
    - 900 ml
    - 1 kg
    - 1 pza
    """

    # Si ya viene una presentación válida → úsala
    if presentacion not in [None, "", "No disponible", "Desconocida"]:
        return presentacion

    nombre = str(nombre).lower()

    # Extraer "500 g", "1 kg", "900 ml", etc
    patron = r"(\d+\.?\d*)\s*-?\s*(g|gr|kg|ml|l|lt|pzas?|pz|pieza|piezas|sob)"
    match = re.search(patron, nombre, re.IGNORECASE)

    if match:
        cantidad = float(match.group(1))
        unidad = match.group(2).lower()

        unit_map = {
            "gr": "g",
            "g": "g",
            "kg": "kg",
            "ml": "ml",
            "l": "l",
            "lt": "l",
            "pz": "pza",
            "pzas": "pza",
            "pieza": "pza",
            "piezas": "pza",
            "sob": "sob"
        }

        unidad = unit_map.get(unidad, unidad)

        if cantidad == 0:
            return "Desconocida"

        return f"{cantidad:g} {unidad}"

    # Extra: detectar "por kg" (frutas, verduras)
    if "por kg" in nombre or "kg" in nombre:
        return "1 kg"

    if "por g" in nombre or "g" in nombre:
        return "100 g"

    # Si pone "unidad / piezas"
    if "unidad" in nombre or "pieza" in nombre or "pza" in nombre or "pz" in nombre:
        return "1 pza"

    return "Desconocida"


# ---------------------------------------------------
#  Extra: Dividir Presentación → Cantidad + Unidad
# ---------------------------------------------------

def dividir_presentacion(presentacion):
    if presentacion in [None, "", "No disponible", "Desconocida"]:
        return None, None

    patron = r"(\d+\.?\d*)\s*(kg|g|ml|l|pza|sob)"
    m = re.match(patron, presentacion)

    if not m:
        return None, None

    cantidad = float(m.group(1))
    unidad = m.group(2)

    if cantidad == 0:
        return None, None

    return cantidad, unidad


# ---------------------------------------------------
#  Función: Extraer unidad abreviada
# ---------------------------------------------------
def detectar_unidad(presentacion):
    if pd.isna(presentacion):
        return "pz"

    p = presentacion.lower()

    if "kg" in p: return "kg"
    if "ml" in p: return "ml"
    if " g" in p or p.endswith("g"): return "g"
    if "lt" in p or " l" in p: return "lt"
    if "pza" in p or "pieza" in p: return "pza"
    if "sob" in p: return "sob"

    return "pz"


# ---------------------------------------------------
#  Función: Extraer cantidad numérica
# ---------------------------------------------------
def extraer_cantidad(presentacion):
    match = re.search(r"(\d+\.?\d*)", str(presentacion))
    return float(match.group(1)) if match else 1.0


# ---------------------------------------------------
#  Transform - Soriana
# ---------------------------------------------------
df['Precio'] = (
    df['Precio']
    .replace(r'[\$,]', '', regex=True)
    .replace('No disponible', '0')
    .astype(float)
)

df['Presentación'] = df.apply(
    lambda row: extraer_presentacion(row['Nombre'], row['Presentación']),
    axis=1
)

df["Unidad"] = df["Presentación"].apply(detectar_unidad)
df["Cantidad"] = df["Presentación"].apply(extraer_cantidad)

df = df.drop_duplicates(subset=['Nombre', 'Supermercado'])


# ---------------------------------------------------
#  Transform - Calimax
# ---------------------------------------------------
df2['Precio'] = (
    df2['Precio']
    .astype(str)
    .str.replace(r'[\$,]', '', regex=True)
    .replace('No disponible', '0')
    .astype(float)
)

def limpiar_nombre_calimax(nombre):
    if pd.isna(nombre):
        return "Desconocido"

    nombre = str(nombre)

    nombre = re.sub(r"(\.\s*\d{1,3}\s*){1,}\+\s*－", "", nombre)
    nombre = re.sub(r"(\.\s*\d{1,3}\s*)+", "", nombre)
    nombre = re.sub(r"(sin interés|agregar|hasta\s*\d+\s*x)", "", nombre, flags=re.IGNORECASE)

    nombre = nombre.replace("＋", "").replace("－", "")
    nombre = re.sub(r"\s{2,}", " ", nombre)
    return nombre.strip()


df2["Nombre"] = df2["Nombre"].apply(limpiar_nombre_calimax)

df2['Presentación'] = df2.apply(
    lambda row: extraer_presentacion(row['Nombre'], row.get('Presentación', "No disponible")),
    axis=1
)

df2["Unidad"] = df2["Presentación"].apply(detectar_unidad)
df2["Cantidad"] = df2["Presentación"].apply(extraer_cantidad)

df2 = df2.drop_duplicates(subset=["Nombre", "Supermercado"])

df2 = df2[df.columns]


# --------------------------
# Guardar archivos transformados
# --------------------------
df.to_csv("dataset/canasta_soriana_transformado.csv", index=False)
df2.to_csv("dataset/canasta_calimax_transformado.csv", index=False)

print("✅ Transformación completa para Soriana y Calimax con Unidad y Cantidad.")
