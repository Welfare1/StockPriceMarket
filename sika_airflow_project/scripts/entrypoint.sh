#!/bin/bash

# Initialisation de la base Airflow si nécessaire
airflow db init

# Création d’un utilisateur admin
airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Lancement des composants Airflow
airflow scheduler &
exec airflow webserver
