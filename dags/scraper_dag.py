from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

def scrape_and_store():
    mongo_uri = os.getenv("MONGO_URI")
    client = MongoClient(mongo_uri)
    db = client["sika_finance"]
    collection = db["historique_actions"]

    # Dates dynamiques : la veille (au format dd/mm/yyyy)
    date_from = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    date_to = datetime.now().strftime("%d/%m/%Y")

    # Selenium config
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    driver.get("https://www.sikafinance.com/marches/historiques/SDSC.ci")
    time.sleep(3)

    select_element = wait.until(EC.presence_of_element_located((By.ID, "dpShares")))
    select_html = Select(select_element)

    options_list = [(opt.text.strip(), opt.get_attribute("value").strip())
                    for opt in select_html.options if opt.get_attribute("value").strip()]

    all_data = []

    for nom_action, valeur in options_list:
        print(f"🔍 {nom_action} ({valeur})")
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
                rows = []
                for tr in table.find_all("tr")[1:]:
                    cols = [td.text.strip() for td in tr.find_all("td")]
                    if cols:
                        rows.append(cols)

                df = pd.DataFrame(rows, columns=headers)
                df["Action"] = nom_action
                all_data.append(df)
            else:
                print(f"❌ Pas de tableau pour {nom_action}")

        except Exception as e:
            print(f"⚠️ Erreur avec {nom_action} : {e}")

        time.sleep(2)

    driver.quit()

    # Insertion MongoDB sans doublons
    if all_data:
        full_df = pd.concat(all_data)
        records = full_df.to_dict(orient='records')

        new_records = []
        for r in records:
            if not collection.find_one({"Date": r["Date"], "Action": r["Action"]}):
                new_records.append(r)

        if new_records:
            collection.insert_many(new_records)
            print(f"✅ {len(new_records)} nouvelles lignes insérées pour la date {date_from}.")
        else:
            print("ℹ️ Aucune nouvelle donnée à insérer, tout est déjà à jour.")


with DAG(
    dag_id='scraper_sikafinance_dag',
    default_args=default_args,
    start_date=datetime(2025, 4, 14),
    schedule_interval='*/1 * * * *',  # toutes les 15 minutes
    catchup=False,
    tags=['sikafinance', 'scraping', 'mongodb']
) as dag:

    run_scraping = PythonOperator(
        task_id='scrape_and_store_task',
        python_callable=scrape_and_store
    )

    run_scraping
