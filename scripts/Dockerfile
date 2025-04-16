# Utiliser une image de base Python
FROM python:3.9-slim



# Définir le répertoire de travail
WORKDIR /app

COPY scripts/requirements.txt .
COPY scripts/scrape_and_insert.py .

# Copier le script et les fichiers nécessaires dans le container
COPY . /app

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Installer le driver Chrome et les outils nécessaires pour Selenium
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    chromium-driver

# Définir les options pour Chromium
ENV CHROMIUM_BIN=/usr/bin/chromium
ENV CHROME_DRIVER=/usr/bin/chromium-driver


# Exécuter le script de scraping
CMD ["python", "scrape_and_insert.py"]
