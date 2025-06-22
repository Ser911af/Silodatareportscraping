from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
from datetime import datetime
import time
import os
import pandas as pd
import glob

# Cargar variables de entorno
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

# Configuración de Chrome
download_dir = os.path.abspath("data")
os.makedirs(download_dir, exist_ok=True)

# Definir nombres de perfiles
PERFIL_FLORIDA = "FRUTTO FOODS LLC."
PERFIL_TEXAS = "FRUTTO FOODS TEXAS LLC"

options = Options()
options.add_experimental_option("prefs", {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})
options.add_argument("--start-maximized")

# Función para iniciar navegador
def start_driver():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver, WebDriverWait(driver, 25)

# Función para iniciar sesión
def login(driver, wait):
    driver.get("https://app.usesilo.com/login")
    wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(EMAIL)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='login-page-submit-button']"))).click()
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-test='user-menu-button']")))

# Función para obtener perfil actual
def obtener_perfil_actual(driver, wait):
    try:
        # Obtener el texto del perfil sin abrir el menú
        perfil_element = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "button[data-test='user-menu-button'] div.chakra-text.css-tzgmcz")
        ))
        return perfil_element.text
    except Exception as e:
        print(f"❌ Error obteniendo perfil actual: {str(e)}")
        return None

# Función para descargar reporte (MODIFICADA)
def descargar_reporte(driver, wait, oficina):
    print(f"⏳ Iniciando descarga para {oficina}...")

    # Guardar estado actual de archivos en la carpeta de descargas
    archivos_antes = set(os.listdir(download_dir))

    # Navegar a reportes
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='reports-nav-button']"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[text()='Sales']"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Item Detail')]"))).click()

    # Establecer fechas
    start_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-test='start-date-input']")))
    end_input = driver.find_element(By.CSS_SELECTOR, "input[data-test='end-date-input']")
    start_input.send_keys(Keys.CONTROL + "a")
    start_input.send_keys("01/01/2021")
    end_input.send_keys(Keys.CONTROL + "a")
    end_input.send_keys(datetime.today().strftime("%m/%d/%Y"))
    end_input.send_keys(Keys.ENTER)

    # Descargar
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='download-report-button']"))).click()
    print(f"📥 Descarga iniciada para {oficina}...")

    # Esperar a que aparezca el nuevo archivo
    tiempo_inicio = time.time()
    archivo_descargado = None
    nombre_final = os.path.join(download_dir, f"FruttoSalesRep_{oficina}.csv")

    while time.time() - tiempo_inicio < 30:  # Esperar máximo 30 segundos
        time.sleep(1)
        archivos_ahora = set(os.listdir(download_dir))
        nuevos_archivos = archivos_ahora - archivos_antes

        # Buscar archivos que coincidan con el patrón esperado
        for archivo in nuevos_archivos:
            if archivo.startswith("sales-by-item-report-") and archivo.endswith(".csv"):
                archivo_descargado = os.path.join(download_dir, archivo)
                break

        if archivo_descargado:
            # Renombrar inmediatamente
            os.rename(archivo_descargado, nombre_final)
            print(f"✅ Archivo renombrado: {nombre_final}")
            return

    print(f"❌ No se encontró archivo descargado para {oficina}")

# Función para cambiar de perfil (versión mejorada)
def cambiar_perfil(driver, wait, nombre_empresa):
    # Solo cambiar si no estamos ya en el perfil deseado
    perfil_actual = obtener_perfil_actual(driver, wait)
    if perfil_actual == nombre_empresa:
        print(f"ℹ️ Ya estás en el perfil {nombre_empresa}, no se realiza cambio")
        return

    # Cerrar cualquier elemento que pueda estar interfiriendo
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
    time.sleep(1)

    # Hacer clic en el menú de usuario usando JavaScript
    menu_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='user-menu-button']")))
    driver.execute_script("arguments[0].click();", menu_button)

    # Esperar a que el menú esté completamente expandido
    time.sleep(1)

    # Intentar encontrar el elemento con diferentes selectores
    selectores = [
        f"//div[text()='{nombre_empresa}' and @data-test='business-menu-item']",
        f"//div[text()='{nombre_empresa}' and @data-test='organization-switcher-org']",
        f"//div[contains(@class, 'chakra-text') and text()='{nombre_empresa}']"
    ]

    encontrado = False
    for selector in selectores:
        try:
            empresa_element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
            driver.execute_script("arguments[0].click();", empresa_element)
            encontrado = True
            break
        except:
            continue

    if not encontrado:
        print(f"❌ No se encontró el perfil: {nombre_empresa}")
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        return

    # Esperar a que se cargue el nuevo perfil usando el nombre
    try:
        wait.until(lambda driver: obtener_perfil_actual(driver, wait) == nombre_empresa)
        print(f"✅ Cambiado a perfil: {nombre_empresa}")
    except:
        print(f"⚠️ Cambio de perfil realizado pero no verificado: {nombre_empresa}")

# Función para verificar y combinar archivos (MODIFICADA para eliminar última fila)
def combinar_y_verificar_archivos():
    tx_path = os.path.join(download_dir, "FruttoSalesRep_Texas.csv")
    fl_path = os.path.join(download_dir, "FruttoSalesRep_Florida.csv")

    if not os.path.exists(tx_path) or not os.path.exists(fl_path):
        print("❌ Error: No se encontraron los archivos de ambas oficinas")
        return False

    try:
        # Leer archivos y eliminar la última fila si contiene "Total"
        df_tx = pd.read_csv(tx_path)
        if str(df_tx.iloc[-1, 0]).strip().lower() == "total":
            df_tx = df_tx.iloc[:-1]

        df_fl = pd.read_csv(fl_path)
        if str(df_fl.iloc[-1, 0]).strip().lower() == "total":
            df_fl = df_fl.iloc[:-1]

        # Verificar estructura de datos
        print("\n🔍 Verificando estructura de datos:")
        print(f"Archivo Texas: {df_tx.shape[0]} filas, {df_tx.shape[1]} columnas")
        print(f"Archivo Florida: {df_fl.shape[0]} filas, {df_fl.shape[1]} columnas")

        # Agregar columna de oficina
        df_tx['Oficina'] = 'Texas'
        df_fl['Oficina'] = 'Florida'

        # Combinar archivos
        df_combined = pd.concat([df_tx, df_fl], ignore_index=True)
        print(f"\n📊 Total registros combinados: {len(df_combined)}")

        # Verificar total esperado
        total_esperado = len(df_tx) + len(df_fl)
        if len(df_combined) != total_esperado:
            print(f"⚠️ Advertencia: Total de registros ({len(df_combined)}) no coincide con la suma esperada ({total_esperado})")

        # Guardar combinado
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        final_path = os.path.join(download_dir, f"reportSalesFrutto_{fecha_actual}.csv")
        df_combined.to_csv(final_path, index=False)
        print(f"✅ Reporte combinado guardado en: {final_path}")

        # Eliminar archivos temporales
        os.remove(tx_path)
        os.remove(fl_path)
        print("🧹 Archivos temporales eliminados")

        return True

    except Exception as e:
        print(f"❌ Error combinando archivos: {str(e)}")
        return False

# Función principal
def main():
    driver, wait = start_driver()

    try:
        # Paso 1: Login
        login(driver, wait)
        print("🔑 Sesión iniciada correctamente")

        # Obtener perfil actual
        perfil_actual = obtener_perfil_actual(driver, wait)
        print(f"🔍 Perfil actual: {perfil_actual}")

        # Determinar qué perfiles necesitamos descargar
        perfiles_a_descargar = []
        if perfil_actual == PERFIL_FLORIDA:
            perfiles_a_descargar.append(("Florida", PERFIL_FLORIDA))
            perfiles_a_descargar.append(("Texas", PERFIL_TEXAS))
        elif perfil_actual == PERFIL_TEXAS:
            perfiles_a_descargar.append(("Texas", PERFIL_TEXAS))
            perfiles_a_descargar.append(("Florida", PERFIL_FLORIDA))
        else:
            print("❌ Perfil no reconocido. Descargando ambos perfiles por defecto")
            perfiles_a_descargar.append(("Florida", PERFIL_FLORIDA))
            perfiles_a_descargar.append(("Texas", PERFIL_TEXAS))

        # Descargar reportes en el orden necesario
        for oficina, perfil in perfiles_a_descargar:
            # Si ya estamos en el perfil correcto, no necesitamos cambiar
            if obtener_perfil_actual(driver, wait) != perfil:
                cambiar_perfil(driver, wait, perfil)

            # Descargar reporte
            descargar_reporte(driver, wait, oficina)

        # Cerrar navegador
        driver.quit()
        print("🧹 Navegador cerrado")

        # Combinar reportes
        combinar_y_verificar_archivos()

    except Exception as e:
        print(f"❌ Error crítico: {str(e)}")
        driver.quit()

if __name__ == "__main__":
    main()
