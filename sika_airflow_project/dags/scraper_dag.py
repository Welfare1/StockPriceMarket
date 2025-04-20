from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import subprocess

def run_scraping_script():
    subprocess.run(["python", "/app/scrape_and_insert.py"])


default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 4, 16),
    
}

dag = DAG(
    'scraping_sika_finance',
    default_args=default_args,
    description='DAG pour scraper SikaFinance',
    schedule_interval='0 */15 * * *',  # Exécuter toutes les heures
)

start = DummyOperator(
    task_id='start',
    dag=dag,
)

scrape_data = PythonOperator(
    task_id='scrape_data',
    python_callable=run_scraping_script,
    dag=dag,
)

start >> scrape_data
