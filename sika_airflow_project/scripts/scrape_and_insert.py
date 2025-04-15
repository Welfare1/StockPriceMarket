import os
import time
import pandas as pd
from bs4 import BeautifulSoup
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# Configuration des dates
date_from = "15/01/2025"
date_to = "11/04/2025"

# Configuration Selenium en mode headless
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)

# Connexion MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["sika_finance"]
collection = db["historique_cour"]

# URL de base
driver.get("https://www.sikafinance.com/marches/historiques/SDSC.ci")
time.sleep(3)

# Récupération des options de l'action
select_element = wait.until(EC.presence_of_element_located((By.ID, "dpShares")))
select_html = Select(select_element)

options = [(opt.text.strip(), opt.get_attribute("value").strip())
           for opt in select_html.options if opt.get_attribute("value").strip()]

for nom_action, valeur in options:
    print(f"🔍 Traitement de {nom_action} ({valeur})...")

    driver.get(f"https://www.sikafinance.com/marches/historiques/{valeur}")
    time.sleep(3)

    try:
        datefrom_input = wait.until(EC.presence_of_element_located((By.ID, "datefrom")))
        dateto_input = driver.find_element(By.ID, "dateto")

        datefrom_input.clear()
        datefrom_input.send_keys(date_from)
        dateto_input.clear()
        dateto_input.send_keys(date_to)

        driver.find_element(By.ID, "btnChange").click()
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        table = soup.find("table", id="tblhistos")

        if table:
            headers = [th.text.strip() for th in table.find_all("th")]
            rows = [[td.text.strip() for td in tr.find_all("td")] for tr in table.find_all("tr")[1:] if tr.find_all("td")]

            df = pd.DataFrame(rows, columns=headers)
            df["Action"] = nom_action

            data = df.to_dict(orient="records")

            collection.delete_many({"Action": nom_action})
            if data:
                collection.insert_many(data)
                print(f"✅ Données insérées pour {nom_action} ({len(data)} lignes)")
        else:
            print(f"❌ Aucun tableau trouvé pour {nom_action}.")

    except Exception as e:
        print(f"⚠️ Erreur pour {nom_action} : {e}")

    time.sleep(2)

driver.quit()
print("🚀 Scraping terminé et données enregistrées.")
