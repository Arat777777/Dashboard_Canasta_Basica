# app.py
import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import plotly.express as px

st.set_page_config(layout="wide", page_title="Comparador Calimax vs Soriana")

# -------------------------
# UTIL: parseo de precios
# -------------------------
def parse_price(p):
    if pd.isna(p):
        return None
    s = str(p).replace(',', '').replace('$', '').strip()
    if s.lower() in ["no disponible", "", "nan", "0"]:
        return None
    try:
        return float(re.findall(r"\d+\.?\d*", s)[0])
    except:
        return None

# -------------------------
# CARGA DATOS AUTOMÁTICA
# -------------------------
dataset_path = "dataset"
sor_csv = os.path.join(dataset_path, r"C:\Users\usuario\Downloads\dataset\canasta_soriana.csv")
cal_csv = os.path.join(dataset_path, r"C:\Users\usuario\Downloads\dataset\canasta_calimax.csv")

files = [f for f in [sor_csv, cal_csv] if os.path.exists(f)]
if not files:
    st.error(f"No se encontraron CSV en '{dataset_path}'.")
    st.stop()

dfs = []
for f in files:
    tmp = pd.read_csv(f)
    tmp["Precio_num"] = tmp["Precio"].apply(parse_price)
    if "Supermercado" not in tmp.columns and "supermercado" in tmp.columns:
        tmp["Supermercado"] = tmp["supermercado"]
    dfs.append(tmp)

df_products = pd.concat(dfs, ignore_index=True)
df_products["Fecha"] = pd.to_datetime(datetime.now().date())
df_products["precio"] = df_products["Precio_num"]
df_products.columns = [c.strip() for c in df_products.columns]

# -------------------------
# PESTAÑAS PRINCIPALES
# -------------------------
st.title("📊 Comparación de Precios: Calimax vs Soriana")

tabs = st.tabs(["Resumen de Precios", "Comparador por Producto", "Buscar por Presupuesto"])

# -------------------------
# PESTAÑA 1: Resumen de Precios
# -------------------------
with tabs[0]:
    st.header("Resumen de Precios")
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Productos registrados", len(df_products))
    col2.metric("Productos distintos", df_products["Nombre"].nunique())
    col3.metric("Precio promedio", f"${df_products['precio'].mean():.2f}")

    grp = df_products.groupby("Supermercado")["precio"].mean().sort_values()
    col4.metric("Supermercado más barato", grp.index[0], f"${grp.iloc[0]:.2f}")

    st.markdown("---")
    st.subheader("Top 10 productos más económicos")
    top = df_products.sort_values("precio").head(10)
    st.dataframe(top[["Nombre", "precio", "Supermercado"]])

# -------------------------
# PESTAÑA 2: Comparador por Producto
# -------------------------
with tabs[1]:
    st.header("Comparador por Producto")
    prod = st.text_input("Buscar producto:", key="comparador_producto")
    if prod:
        matches = df_products[df_products["Nombre"].str.contains(prod, case=False, na=False)]
        if matches.empty:
            st.warning("No se encontraron coincidencias.")
        else:
            st.dataframe(matches[["Nombre", "precio", "Supermercado"]])
            fig = px.box(matches, x="Supermercado", y="precio",
                         points="all", title=f"Comparación de precios — '{prod}'")
            st.plotly_chart(fig, width="stretch")

# -------------------------
# PESTAÑA 3: Buscar por Presupuesto (diseño profesional)
# -------------------------
with tabs[2]:
    st.header("Buscar por Presupuesto")
    st.markdown("Selecciona tus filtros y obtén productos dentro de tu presupuesto.")

    # FILTROS HORIZONTALES
    col1, col2, col3 = st.columns([3, 2, 2])

    with col1:
        supermercados = df_products["Supermercado"].dropna().unique().tolist()
        selected_super = st.multiselect("Supermercado", supermercados, help="Selecciona al menos un supermercado")

    with col2:
        min_precio = st.number_input("Precio mínimo", min_value=0.0, value=0.0, step=1.0)

    with col3:
        max_precio = st.number_input("Precio máximo (0 = sin límite)", min_value=0.0, value=0.0, step=1.0)

    # VALIDACIÓN DE SELECCIÓN
    if not selected_super:
        st.warning("⚠️ Por favor selecciona al menos un supermercado.")
        st.stop()

    # FILTRADO DE DATOS
    dff = df_products[df_products["Supermercado"].isin(selected_super)]
    dff = dff[dff["precio"].notna()]
    dff = dff[dff["precio"] >= min_precio]
    if max_precio > 0:
        dff = dff[dff["precio"] <= max_precio]

    # RESULTADOS
    st.markdown("---")
    st.subheader("Productos encontrados")
    if dff.empty:
        st.info("No se encontraron productos con los filtros aplicados.")
    else:
        st.dataframe(dff[["Nombre", "precio", "Supermercado"]].sort_values("precio"))

        st.subheader("Visualización de precios")
        fig = px.bar(
            dff.sort_values("precio"),
            x="Nombre",
            y="precio",
            color="Supermercado",
            labels={"precio": "Precio"},
            title="Productos dentro del presupuesto"
        )
        st.plotly_chart(fig, width="stretch")

# -------------------------
# EXPORTAR
# -------------------------
st.sidebar.header("Exportar")
if st.sidebar.button("Exportar CSV filtrado"):
    df_products.to_csv("export_filtrado.csv", index=False)
    st.sidebar.success("Archivo exportado: export_filtrado.csv")
