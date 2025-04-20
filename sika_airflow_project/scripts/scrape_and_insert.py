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
from datetime import datetime, timedelta

# Connexion MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["sika_finance"]
collection = db["historique_actions"]

def get_last_record_date():
    # Récupère le dernier enregistrement de la collection triée par date, en supposant que les données sont déjà triées
    last_record = collection.find_one(sort=[("historique.Date", -1)])  # Tri par date descendante
    
    if last_record:
        # Récupère la dernière date de l'historique et la convertit en datetime
        last_date_str = last_record["historique"][-1]["Date"]
        
        try:
            last_date = datetime.strptime(last_date_str, "%d/%m/%Y")  # Format de la date dans la base
            return last_date
        except ValueError:
            print(f"Erreur de format pour la date: {last_date_str}")
            return None
    return None  # Si aucune donnée existante

# Calcul des dates pour la récupération des données
last_date_str = get_last_record_date()

# Si des données existent déjà, commence à partir de la dernière date, sinon récupère depuis une date spécifique
if last_date_str:
    date_from = (last_date_str + timedelta(days=1)).strftime("%d/%m/%Y")
else:
    # Si aucune donnée dans la base, on commence depuis une date spécifique (par exemple, 1er janvier 2025)
    date_from = "01/01/2025"
    date_from = datetime.strptime(date_from, "%d/%m/%Y")

date_to = datetime.now().strftime("%d/%m/%Y")

print(f"Récupération des données de {date_from} à {date_to}")

# Configuration Selenium en mode headless
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)

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
        datefrom_input.send_keys(date_from.strftime("%d/%m/%Y"))
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
            df["Date"] = datetime.strptime(date_from.strftime("%d/%m/%Y"), "%d/%m/%Y")  # Convertir la date au format datetime

            data = df.to_dict(orient="records")

            # Trier les données par date (si la base est vide, ce tri est important)
            data.sort(key=lambda x: datetime.strptime(x["Date"], "%d/%m/%Y"))

            # Mettre à jour ou insérer les nouvelles données dans la base
            collection.update_one(
                {"action": nom_action},
                {"$push": {"historique": {"$each": data}}},  # Ajouter les nouvelles données à l'historique
                upsert=True  # Si l'action n'existe pas, on l'ajoute
            )
            print(f"✅ Données insérées pour {nom_action} ({len(data)} lignes)")
        else:
            print(f"❌ Aucun tableau trouvé pour {nom_action}.")
    except Exception as e:
        print(f"⚠️ Erreur pour {nom_action} : {e}")

    time.sleep(2)

driver.quit()
print("🚀 Scraping terminé et données enregistrées.")
