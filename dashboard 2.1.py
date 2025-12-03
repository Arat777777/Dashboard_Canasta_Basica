# streamlit run "C:\Users\usuario\PycharmProjects\PythonProject8\dashboard 2.1.py"
import streamlit as st
import pandas as pd
import re
import unicodedata
from datetime import datetime
import plotly.express as px

#Titulo de la pestaña
st.set_page_config(page_title="Comparador Calimax vs Soriana", layout="wide")

# =====================================================================
st.markdown("""
    <style>
    body, .block-container {
        background-color: #111 !important;
        color: white !important;
    }
    .stButton button {
        background-color: #333 !important;
        color: white !important;
        border: 1px solid #555 !important;
        font-weight: bold;
    }
    .stTextInput > div > div > input,
    .stNumberInput > div > input {
        background-color: #222 !important;
        color: white !important;
        border: 1px solid #555 !important;
    }
    .stMultiSelect > div > div,
    .stSelectbox > div > div {
        background-color: #222 !important;
        color: white !important;
        border: 1px solid #555 !important;
    }
    table {
        background-color: #222 !important;
        color: white !important;
    }
    h1, h2, h3 {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# Colores de los gráficos
COLOR_SUPERS = {"Calimax": "#6C8EBF", "Soriana": "#E39C7C"}

#Limpieza para mejor visualizacion y busqueda
# =====================================================================
def quitar_acentos(texto):
    if pd.isna(texto): return ""
    texto = str(texto)
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn')

def limpiar_nombre(nombre):
    if pd.isna(nombre): return ""
    nombre = str(nombre)
    nombre = re.sub(r"-\s*\d+%?", "", nombre)
    nombre = re.sub(r"\s{2,}", " ", nombre)
    return nombre.strip()

def renombrar(df):
    return df.rename(columns={
        "Nombre_limpio": "Producto",
        "Precio_display": "Precio",
        "Supermercado": "Supermercado",
        "Categoria": "Categoría"
    })

#Cargar csv por el usuario para mejor visualizacion estetica
# =====================================================================
st.sidebar.header("Cargar archivo CSV")
archivo = st.sidebar.file_uploader("Sube el archivo canasta_total_limpio.csv", type=["csv"])

if archivo:
    df = pd.read_csv(archivo)

    # Limpieza
    df["Nombre_limpio"] = df["Nombre"].apply(limpiar_nombre)
    df["Nombre_sin_acentos"] = df["Nombre_limpio"].apply(quitar_acentos)
    df["Precio_display"] = df["Precio"].apply(lambda x: f"${float(x):.2f}")
    df["Categoria"] = df["Producto buscado"].fillna("Sin categoría")
    df["Fecha"] = pd.to_datetime(datetime.now().date())

    # ================================================================
    # TÍTULO + TABS
    # ================================================================
    st.title("Análisis Comparativo Calimax - Soriana")

    tabs = st.tabs([
        "Resumen General",
        "Comparador Por Categoria",
        "Buscar Por Presupuesto",
        "Lista Inteligente",
        "Visualización Por Categoría",
    ])


    # TAB 1 — Resumen general
    # ================================================================
    with tabs[0]:
        st.header("Resumen General")

        precios_sup = df.groupby("Supermercado")["Precio"].mean().reset_index()
        precios_sup["Precio"] = precios_sup["Precio"].apply(lambda x: f"${x:.2f}")

        super_mas_barato = precios_sup.sort_values("Precio").iloc[0]["Supermercado"]

        col1, col2, col3 = st.columns(3)
        col1.metric("Productos registrados", len(df))
        col2.metric("Categorías", df["Categoria"].nunique())
        col3.metric("Supermercado más barato", super_mas_barato)

        st.markdown("---")
        st.subheader("Precio promedio por supermercado")
        st.dataframe(precios_sup)

        st.markdown("---")

        # ========== TOP 10 ==========
        top_baratos = df.sort_values("Precio").head(10)
        top_caros = df.sort_values("Precio", ascending=False).head(10)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔻 Top 10 más baratos")
            st.dataframe(renombrar(
                top_baratos[["Nombre_limpio", "Precio_display", "Supermercado", "Categoria"]]
            ))

            fig1 = px.bar(
                top_baratos.sort_values("Precio"),
                x="Precio",
                y="Nombre_limpio",
                orientation="h",
                color="Supermercado",
                color_discrete_map=COLOR_SUPERS,
                text=top_baratos["Precio"].apply(lambda x: f"${x:.2f}"),
                title="Top 10 más baratos",
                template="plotly_dark"
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("🔺 Top 10 más caros")
            st.dataframe(renombrar(
                top_caros[["Nombre_limpio", "Precio_display", "Supermercado", "Categoria"]]
            ))

            fig2 = px.bar(
                top_caros.sort_values("Precio", ascending=True),
                x="Precio",
                y="Nombre_limpio",
                orientation="h",
                color="Supermercado",
                color_discrete_map=COLOR_SUPERS,
                text=top_caros["Precio"].apply(lambda x: f"${x:.2f}"),
                title="Top 10 más caros",
                template="plotly_dark"
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Gráfica comparativa por categoría")

        fig = px.bar(
            df,
            x="Categoria",
            y="Precio",
            color="Supermercado",
            barmode="group",
            color_discrete_map=COLOR_SUPERS,
            text="Precio_display",
            title="Comparación de precios por categoría y supermercado",
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

    # TAB 2 — Comparar por categoria
    # ================================================================
    with tabs[1]:
        st.header("Comparación Por Categoría")

        categoria_sel = st.selectbox("Selecciona categoría:", sorted(df["Categoria"].unique()))
        sub = df[df["Categoria"] == categoria_sel]

        if sub.empty:
            st.warning("No hay productos en esta categoría.")
        else:
            st.dataframe(renombrar(
                sub[["Nombre_limpio", "Precio_display", "Supermercado", "Categoria"]]
            ))

            fig = px.bar(
                sub,
                x="Nombre_limpio",
                y="Precio",
                color="Supermercado",
                color_discrete_map=COLOR_SUPERS,
                text=sub["Precio"].apply(lambda x: f"${x:.2f}"),
                title=f"Comparación de precios — {categoria_sel}",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)


    # TAB 3 — Buscar por presupuesto
    # ================================================================
    with tabs[2]:
        st.header("Buscar por Presupuesto")

        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            selected = st.multiselect("Supermercado", df["Supermercado"].unique().tolist())
        with col2:
            min_p = st.number_input("Mínimo", min_value=0.0, value=0.0)
        with col3:
            max_p = st.number_input("Máximo (0 = sin límite)", min_value=0.0, value=0.0)

        if selected:
            dff = df[df["Supermercado"].isin(selected) & (df["Precio"] >= min_p)]
            if max_p > 0:
                dff = dff[dff["Precio"] <= max_p]

            st.dataframe(renombrar(
                dff[["Nombre_limpio", "Precio_display", "Supermercado", "Categoria"]]
            ))

            fig = px.bar(
                dff.sort_values("Precio"),
                x="Nombre_limpio",
                y="Precio",
                color="Supermercado",
                color_discrete_map=COLOR_SUPERS,
                text=dff["Precio"].apply(lambda x: f"${x:.2f}"),
                title="Productos dentro del presupuesto",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

    # TAB 4 — Lista inteligente/interactiva
    # ================================================================
    with tabs[3]:

        st.header("Lista Inteligente — Arma tu Canasta Básica")

        #
        if "carrito" not in st.session_state:
            st.session_state.carrito = []

        if "rerun_tab4" not in st.session_state:
            st.session_state.rerun_tab4 = 0

        st.subheader("Agregar productos a la lista")

        categorias = sorted(df["Categoria"].unique())
        categoria = st.selectbox(
            "Selecciona una categoría:",
            ["-- Selecciona --"] + categorias,
            key="categoria_select_tab4"
        )

        if categoria != "-- Selecciona --":
            productos_disp = sorted(df[df["Categoria"] == categoria]["Nombre_limpio"].unique())

            producto = st.selectbox(
                "Producto:",
                ["-- Selecciona --"] + productos_disp,
                key="producto_select_tab4"
            )

            if producto != "-- Selecciona --":
                cantidad = st.number_input(
                    "Cantidad:",
                    min_value=1,
                    step=1,
                    value=1,
                    key="cantidad_input_tab4"
                )

                if st.button("Agregar a la lista", key="btn_agregar_tab4"):

                    existe = next((item for item in st.session_state.carrito
                                   if item["producto"] == producto), None)

                    if existe:
                        existe["cantidad"] += cantidad
                        st.info(f"Cantidad actualizada: {producto} → {existe['cantidad']}")
                    else:
                        st.session_state.carrito.append({
                            "producto": producto,
                            "categoria": categoria,
                            "cantidad": cantidad
                        })
                        st.success(f"{producto} agregado a la lista")

        st.subheader("Tu Lista de Productos")

        if len(st.session_state.carrito) == 0:
            st.info("Aún no has agregado productos.")
        else:
            df_carrito = pd.DataFrame(st.session_state.carrito)

            for i, item in enumerate(st.session_state.carrito):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                col1.write(item["producto"])
                col2.write(item["categoria"])
                col3.write(f"Cantidad: {item['cantidad']}")
                if col4.button("❌", key=f"del_tab4_{i}"):
                    st.session_state.carrito.pop(i)
                    st.session_state.rerun_tab4 += 1

            st.markdown("---")

            lista_productos = df_carrito["producto"].tolist()
            sub = df[df["Nombre_limpio"].isin(lista_productos)]
            sub = sub.merge(df_carrito, left_on="Nombre_limpio", right_on="producto")
            sub["Subtotal"] = sub["Precio"] * sub["cantidad"]

            st.subheader("Desglose lista")
            detalle = sub[["producto", "cantidad", "Supermercado", "Precio", "Subtotal"]]

            tabla_detalle = detalle.pivot_table(
                index=["producto", "cantidad"],
                columns="Supermercado",
                values=["Precio", "Subtotal"],
                aggfunc="first"
            ).reset_index()

            tabla_detalle.columns = ['_'.join(col).strip('_') for col in tabla_detalle.columns.values]

            tabla_detalle = tabla_detalle.rename(columns={
                "producto": "Producto",
                "cantidad": "Cantidad",
                "Precio_Calimax": "Precio Calimax",
                "Precio_Soriana": "Precio Soriana",
                "Subtotal_Calimax": "Subtotal Calimax",
                "Subtotal_Soriana": "Subtotal Soriana"
            })

            for col in ["Precio Calimax", "Precio Soriana", "Subtotal Calimax", "Subtotal Soriana"]:
                if col in tabla_detalle.columns:
                    tabla_detalle[col] = tabla_detalle[col].apply(
                        lambda x: f"${x:.2f}" if pd.notnull(x) else "—"
                    )

            st.dataframe(tabla_detalle, use_container_width=True)

            st.subheader("Comparación de precios por producto")
            fig2 = px.bar(
                detalle,
                x="producto",
                y="Precio",
                color="Supermercado",
                barmode="group",
                title="Precio por producto en cada supermercado",
                template="plotly_dark",
                color_discrete_map=COLOR_SUPERS
            )
            st.plotly_chart(fig2, use_container_width=True)

            st.markdown("---")

            resumen = sub.groupby("Supermercado")["Subtotal"].sum().reset_index()
            resumen["Total"] = resumen["Subtotal"].apply(lambda x: f"${x:.2f}")

            st.subheader("Totales por Supermercado")
            st.dataframe(resumen[["Supermercado", "Total"]])

            if len(resumen) == 2:
                cali = resumen.loc[resumen["Supermercado"] == "Calimax", "Subtotal"].values[0]
                sori = resumen.loc[resumen["Supermercado"] == "Soriana", "Subtotal"].values[0]
                ahorro = abs(cali - sori)
                ganador = "Calimax" if cali < sori else "Soriana"
                st.success(f"Más barato: {ganador} (Ahorro: ${ahorro:.2f})")

            fig = px.bar(
                resumen,
                x="Supermercado",
                y="Subtotal",
                text=resumen["Subtotal"].apply(lambda x: f"${x:.2f}"),
                color="Supermercado",
                color_discrete_map=COLOR_SUPERS,
                title="Total comparado entre supermercados",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Vaciar lista
            if st.button("Vaciar lista", key="btn_vaciar_tab4"):
                st.session_state.carrito = []
                st.warning("Lista vaciada.")
                st.session_state.rerun_tab4 += 1  # Incrementa trigger para rerun

    # TAB 5 — Visualizacion por categoria
    # ================================================================
    with tabs[4]:
        st.header("Visualización por Categoría")

        categorias = sorted(df["Categoria"].unique())

        for cat in categorias:
            st.subheader(f"Categoría: {cat}")

            sub = df[df["Categoria"] == cat]
            resumen = sub.groupby("Supermercado")["Precio"].mean().reset_index()
            resumen["Precio_display"] = resumen["Precio"].apply(lambda x: f"${x:.2f}")

            fig = px.bar(
                resumen.sort_values("Supermercado"),
                x="Supermercado",
                y="Precio",
                color="Supermercado",
                text="Precio_display",
                color_discrete_map=COLOR_SUPERS,
                title=f"Promedio de precios en {cat}",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("Tabla general — De lo más barato a lo más caro")

        ranking = df.groupby(["Categoria", "Supermercado"], as_index=False)["Precio"].mean()
        ranking = ranking.sort_values("Precio")
        ranking["Precio"] = ranking["Precio"].apply(lambda x: f"${x:.2f}")

        st.dataframe(ranking)


else:
    st.title("Comparador Calimax - Soriana")
    st.info("Sube tu archivo CSV en la barra lateral para comenzar.")
