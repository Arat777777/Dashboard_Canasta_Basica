import time
import random
import os
import re
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

canasta_basica = [
    "Aceite",
    "Arroz",
    "Atún",

]
def get_text(element, selector):
    try:
        e = element.find_element(By.CSS_SELECTOR, selector)
        return e.text.strip()
    except:
        return "No disponible"

def soriana():

    service = Service(ChromeDriverManager().install())
    opc = Options()
    opc.add_argument("--window-size=1200x1000")
    navegador = webdriver.Chrome(service=service, options=opc)

    navegador.get("https://www.soriana.com/")
    time.sleep(4)

    resultados = []

    for producto in canasta_basica:

        print(f"\n🔎 Buscando → {producto}")

        # Timer antes de la búsqueda
        time.sleep(random.uniform(2, 4))

        # Localizar buscador
        try:
            buscador = WebDriverWait(navegador, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input.search-field")
                )
            )
        except:
            print("❌ No se encontró el buscador.")
            continue

        buscador.clear()
        buscador.send_keys(producto)
        time.sleep(1)
        buscador.send_keys(Keys.ENTER)

        # Esperar carga de resultados
        time.sleep(random.uniform(4, 6))

        # Productos
        items = navegador.find_elements(By.CSS_SELECTOR, "a.plp-link")

        if not items:
            print(f"⚠ No se encontraron resultados para: {producto}")
            continue

        # Extraer los primeros 3
        for item in items[:3]:

            # =========================
            # NOMBRE COMPLETO
            # =========================
            nombre_completo = item.text.strip()

            # ===== Separar presentación del final =====
            presentacion = "No disponible"
            nombre = nombre_completo

            match = re.search(r"(\d+\.?\d*\s?(g|kg|ml|l|L|pzas|pz|pieza|piezas))$", nombre_completo, re.IGNORECASE)
            if match:
                presentacion = match.group(1)
                nombre = nombre_completo.replace(presentacion, "").strip()

            # =========================
            # PRECIO
            # =========================
            try:
                price_element = item.find_element(By.XPATH, "../../..//span[contains(@class,'price')]")
                precio = price_element.text.strip()
            except:
                precio = "No disponible"

            # Guardar datos
            resultados.append([producto, nombre, precio, presentacion])

        # Timer después de extraer
        time.sleep(random.uniform(1, 2))

    # ================================
    # CREAR CSV
    # ================================
    df = pd.DataFrame(
        resultados,
        columns=["Producto buscado", "Nombre", "Precio", "Presentación"]
    )

    # Agregar columna del supermercado
    df["Supermercado"] = "Soriana"

    os.makedirs("dataset", exist_ok=True)
    df.to_csv("dataset/canasta_soriana.csv", index=False)

    print("\n📁 Archivo generado: dataset/canasta_soriana.csv\n")

    return df

def calimax():

    service = Service(ChromeDriverManager().install())
    opc = Options()
    opc.add_argument("--window-size=1200x1000")
    navegador = webdriver.Chrome(service=service, options=opc)

    base_url = "https://tienda.calimax.com.mx/"
    navegador.get(base_url)
    time.sleep(4)

    resultados = []

    for producto in canasta_basica:

        print(f"\n🔎 Buscando → {producto}")

        time.sleep(random.uniform(2, 4))

        # Usar el buscador: buscar 'q' en la URL
        # Formar la URL de búsqueda:
        search_url = f"{base_url}{producto.replace(' ', '%20')}?_q={producto.replace(' ', '%20')}&map=ft"
        navegador.get(search_url)
        time.sleep(random.uniform(4, 6))

        html = navegador.page_source
        soup = BeautifulSoup(html, "html.parser")

        # Los productos aparecen como listas de enlaces <a> con texto y precio
        # Buscar todos los items listados
        items = soup.find_all("a", href=True)

        if not items:
            print(f"⚠ No se encontraron resultados para: {producto}")
            continue

        # Extraer los primeros 5 que parezcan de producto
        count = 0
        for a in items:
            text = a.get_text(separator=" ").strip()
            # Filtrar por que contengan nombre + precio — heurística
            if re.search(r"\$\s*\d+", text):
                # Extraer precio
                precio_match = re.search(r"\$\s*[\d\.,]+", text)
                precio = precio_match.group(0) if precio_match else "No disponible"

                # Extraer presentación si existe (gramos, piezas, etc.)
                presentacion = "No disponible"
                m = re.search(r"(\d+\.?\d*\s?(g|kg|ml|l|L|pza|pzas|pieza|piezas))", text, re.IGNORECASE)
                if m:
                    presentacion = m.group(1)

                # Extraer nombre limpiando precio y presentación
                nombre = re.sub(r"\$\s*[\d\.,]+", "", text)
                if presentacion != "No disponible":
                    nombre = nombre.replace(presentacion, "").strip()

                resultados.append([producto, nombre, precio, presentacion])

                count += 1
                if count >= 3:
                    break

        time.sleep(random.uniform(1, 2))

    df = pd.DataFrame(
        resultados,
        columns=["Producto buscado", "Nombre", "Precio", "Presentación"]
    )
    df["Supermercado"] = "Calimax"

    os.makedirs("dataset", exist_ok=True)
    df.to_csv("dataset/canasta_calimax.csv", index=False)

    print("\n📁 Archivo generado: dataset/canasta_calimax.csv\n")

    navegador.quit()
    return df

def justo():

    service = Service(ChromeDriverManager().install())
    opc = Options()
    opc.add_argument("--window-size=1200x1000")
    navegador = webdriver.Chrome(service=service, options=opc)

    base_url = "https://justo.mx/search?query="
    resultados = []

    for producto in canasta_basica:

        print(f"\n🔎 Buscando → {producto}")

        # Armar URL y buscar
        query = producto.replace(" ", "%20")
        navegador.get(base_url + query)
        time.sleep(random.uniform(4, 6))

        html = navegador.page_source
        soup = BeautifulSoup(html, "html.parser")

        # Capturar tarjetas de producto
        items = soup.find_all("div", class_=re.compile("sc-7615cbab"))

        if not items:
            print(f"⚠ No se encontraron resultados para: {producto}")
            continue

        # Procesar solo primeros 3 productos reales
        count = 0
        for card in items:

            # Nombre
            nombre_tag = card.find("div", class_=re.compile("sc-7615cbab-0"))
            if not nombre_tag:
                continue
            nombre_completo = nombre_tag.get_text(strip=True)

            # Precio
            precio_tag = card.find("div", class_=re.compile("sc-95c089b8-11"))
            if precio_tag:
                precio = precio_tag.get_text(strip=True)
            else:
                precio = "No disponible"

            # Separar presentación
            presentacion = "No disponible"
            nombre = nombre_completo

            match = re.search(r"(\d+\.?\d*\s?(g|kg|ml|l|L|pzas|pz|pieza|piezas))$", nombre_completo, re.IGNORECASE)
            if match:
                presentacion = match.group(1)
                nombre = nombre_completo.replace(presentacion, "").strip()

            # Guardar fila
            resultados.append([producto, nombre, precio, presentacion])

            count += 1
            if count >= 3:
                break

        time.sleep(random.uniform(1, 2))

    # Crear DataFrame
    df = pd.DataFrame(
        resultados,
        columns=["Producto buscado", "Nombre", "Precio", "Presentación"]
    )

    # Añadir columna supermercado
    df["Supermercado"] = "Justo"

    os.makedirs("dataset", exist_ok=True)
    df.to_csv("dataset/canasta_justo.csv", index=False)

    print("\n📁 Archivo generado: dataset/canasta_justo.csv\n")

    return df



if __name__ == "__main__":
    #soriana()
    #calimax()
    justo()