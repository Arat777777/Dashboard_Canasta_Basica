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
    "Aceite ",
    "Arroz ",
    "Atún",
    "Azúcar morena",
    "Bistec de res",
    "Cebolla ",
    "Chile jalapeño",
    "Chuleta de puerco",
    "Frijol",
    "Huevo de gallina blanco",
    "Jabón de tocador",
    "Jitomate saladet",
    "Leche ",
    "Limón",
    "Manzana",
    "Naranja",
    "Pan de caja",
    "Papa",
    "Papel higiénico",
    "Pasta para sopa",
    "Pollo entero",
    "Sardina en lata",
    "Tortilla de maíz",
    "Zanahoria"
]

def parse_price(p):
    """Convierte '$33.90' → 33.90"""
    if pd.isna(p):
        return None
    s = str(p).replace('$', '').replace(',', '').strip()
    try:
        return float(re.findall(r"\d+\.?\d*", s)[0])
    except:
        return None


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

        print(f"\n Buscando → {producto}")

        time.sleep(random.uniform(2, 4))

        try:
            buscador = WebDriverWait(navegador, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input.search-field")
                )
            )
        except:
            print(" No se encontró el buscador.")
            continue

        buscador.clear()
        buscador.send_keys(producto)
        time.sleep(1)
        buscador.send_keys(Keys.ENTER)

        time.sleep(random.uniform(4, 6))

        items = navegador.find_elements(By.CSS_SELECTOR, "a.plp-link")

        if not items:
            print(f"No se encontraron resultados para: {producto}")
            continue

        for item in items[:3]:

            nombre_completo = item.text.strip()
            presentacion = "No disponible"
            nombre = nombre_completo

            match = re.search(r"(\d+\.?\d*\s?(g|kg|ml|l|L|pzas|pz|pieza|piezas))$", nombre_completo, re.IGNORECASE)
            if match:
                presentacion = match.group(1)
                nombre = nombre_completo.replace(presentacion, "").strip()

            try:
                price_element = item.find_element(By.XPATH, "../../..//span[contains(@class,'price')]")
                precio = price_element.text.strip()
            except:
                precio = "No disponible"

            resultados.append([producto, nombre, precio, presentacion])

        time.sleep(random.uniform(1, 2))

    df = pd.DataFrame(
        resultados,
        columns=["Producto buscado", "Nombre", "Precio", "Presentación"]
    )

    df["Supermercado"] = "Soriana"



    os.makedirs("dataset", exist_ok=True)
    df.to_csv("dataset/canasta_soriana.csv", index=False)

    print("\n Archivo generado: dataset/canasta_soriana.csv\n")

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

        print(f"\n Buscando → {producto}")

        time.sleep(random.uniform(2, 4))

        search_url = f"{base_url}{producto.replace(' ', '%20')}?_q={producto.replace(' ', '%20')}&map=ft"
        navegador.get(search_url)
        time.sleep(random.uniform(4, 6))

        html = navegador.page_source
        soup = BeautifulSoup(html, "html.parser")

        items = soup.find_all("a", href=True)

        if not items:
            print(f" No se encontraron resultados para: {producto}")
            continue

        count = 0
        for a in items:
            text = a.get_text(separator=" ").strip()

            if re.search(r"\$\s*\d+", text):

                precio_match = re.search(r"\$\s*[\d\.,]+", text)
                precio = precio_match.group(0) if precio_match else "No disponible"

                presentacion = "No disponible"
                m = re.search(r"(\d+\.?\d*\s?(g|kg|ml|l|L|pza|pzas|pieza|piezas))", text, re.IGNORECASE)
                if m:
                    presentacion = m.group(1)

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

    print("\n Archivo generado: dataset/canasta_calimax.csv\n")

    navegador.quit()
    return df

# EJECUCIÓN
# ============================================================
if __name__ == "__main__":
    calimax()
    soriana()