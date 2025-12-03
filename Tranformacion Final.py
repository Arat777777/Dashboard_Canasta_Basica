import pandas as pd
import re

#  Extract
# --------------------------
df = pd.read_csv("dataset/canasta_soriana.csv")
df2 = pd.read_csv("dataset/canasta_calimax.csv")

#  Añadir columna Ciudad
# --------------------------
df["Ciudad"] = "Tijuana"
df2["Ciudad"] = "Tijuana"



#  Función: Extraer presentación desde nombre o columna
# ---------------------------------------------------
def extraer_presentacion(nombre, presentacion):

    if presentacion not in [None, "", "No disponible", "Desconocida"]:
        return presentacion

    nombre = str(nombre).lower()

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

    if "por kg" in nombre or "kg" in nombre:
        return "1 kg"

    if "por g" in nombre or "g" in nombre:
        return "100 g"

    if "unidad" in nombre or "pieza" in nombre or "pza" in nombre or "pz" in nombre:
        return "1 pza"

    return "Desconocida"

#  Función: Extraer unidad
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


#  Función: extraer cantidad
# ---------------------------------------------------
def extraer_cantidad(presentacion):
    match = re.search(r"(\d+\.?\d*)", str(presentacion))
    return float(match.group(1)) if match else 1.0



#  Transformar - Soriana
# ---------------------------------------------------
df['Precio'] = (
    df['Precio']
    .astype(str)
    .str.replace(r'[\$,]', '', regex=True)
    .replace("No disponible", "0")
).astype(float)

df['Presentación'] = df.apply(
    lambda row: extraer_presentacion(row['Nombre'], row['Presentación']),
    axis=1
)

df["Unidad"] = df["Presentación"].apply(detectar_unidad)
df["Cantidad"] = df["Presentación"].apply(extraer_cantidad)

df = df.drop_duplicates(subset=['Nombre', 'Supermercado'])

#  Transformar - Calimax
# ---------------------------------------------------
df2["Precio"] = (
    df2["Precio"]
    .astype(str)
    .str.replace(r"[\$,]", "", regex=True)
    .replace("No disponible", "0")
).astype(float)

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

df2["Presentación"] = df2.apply(
    lambda row: extraer_presentacion(row["Nombre"], row.get("Presentación", "No disponible")),
    axis=1
)

df2["Unidad"] = df2["Presentación"].apply(detectar_unidad)
df2["Cantidad"] = df2["Presentación"].apply(extraer_cantidad)

df2 = df2.drop_duplicates(subset=["Nombre", "Supermercado"])

columnas_comunes = list(set(df.columns).union(set(df2.columns)))
df = df.reindex(columns=columnas_comunes)
df2 = df2.reindex(columns=columnas_comunes)


#  Cálculo de promedios por categoría y supermercado
# ---------------------------------------------------
def calcular_promedios(df):

    df["Precio_limpio"] = (
        df["Precio"]
        .astype(str)
        .str.replace(r"[\$,]", "", regex=True)
    )

    df["Precio_limpio"] = pd.to_numeric(df["Precio_limpio"], errors="coerce")
    df = df.dropna(subset=["Precio_limpio"])

    def precio_por_unidad(row):
        try:
            if row["Cantidad"] and row["Cantidad"] > 0:
                return row["Precio_limpio"] / float(row["Cantidad"])
        except:
            pass
        return row["Precio_limpio"]

    df["Precio_por_unidad"] = df.apply(precio_por_unidad, axis=1)

    if "Producto buscado" in df.columns:
        df["Categoria"] = df["Producto buscado"].fillna("Desconocida")
    else:
        df["Categoria"] = "General"

    promedios = (
        df.groupby(["Categoria", "Supermercado"])["Precio_por_unidad"]
        .mean()
        .reset_index()
        .rename(columns={"Precio_por_unidad": "Promedio_categoria_supermercado"})
    )

    df = df.merge(promedios, on=["Categoria", "Supermercado"], how="left")

    #  Redondear valores numéricos importantes
    # -------------------------------------------
    df["Precio_por_unidad"] = df["Precio_por_unidad"].round(4)
    df["Promedio_categoria_supermercado"] = df["Promedio_categoria_supermercado"].round(2)

    if "Precio promedio categoría" in df.columns:
        df["Precio promedio categoría"] = df["Precio promedio categoría"].round(2)

    return df


#  Aplicar promedios
# ---------------------------------------------------
df = calcular_promedios(df)
df2 = calcular_promedios(df2)

df.to_csv("dataset/canasta_soriana_transformado.csv", index=False)
df2.to_csv("dataset/canasta_calimax_transformado.csv", index=False)

#  UNIFICAR DATASETS Soriana + Calimax
# ---------------------------------------------------

# Concatenar ambos dataframes
df_total = pd.concat([df, df2], ignore_index=True)

# Eliminar duplicados por seguridad
df_total = df_total.drop_duplicates(
    subset=["Nombre", "Supermercado", "Presentación"],
    keep="first"
)

columnas_orden = [
    "Producto buscado",
    "Categoria",
    "Nombre",
    "Presentación",
    "Unidad",
    "Cantidad",
    "Precio",
    "Precio_limpio",
    "Precio_por_unidad",
    "Promedio_categoria_supermercado",
    "Supermercado",
    "Ciudad"
]

df_total = df_total[columnas_orden]


columnas_a_eliminar = [
    "Categoria",
    "Precio_limpio",
    "Ciudad",
    "Presentación"
]

for col in columnas_a_eliminar:
    if col in df_total.columns:
        df_total = df_total.drop(columns=[col])

df_total.to_csv("dataset/canasta_total_limpio.csv", index=False)

print("Dataset final limpio guardado como: dataset/canasta_total_limpio.csv")