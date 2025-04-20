# Utiliser une image Python légère
FROM python:3.9-slim

# Empêcher les invites interactives
ENV DEBIAN_FRONTEND=noninteractive

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers requis
COPY scripts/requirements.txt .
COPY scripts/scrape_and_insert.py .
COPY scripts/entrypoint.sh .
COPY . /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    ca-certificates \
    chromium-driver \
    chromium \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Variables d’environnement pour Chromium
ENV CHROMIUM_BIN=/usr/bin/chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_DRIVER=/usr/bin/chromedriver

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Donner les droits d'exécution au script d'entrée
RUN chmod +x /entrypoint.sh

# Définir le point d'entrée
ENTRYPOINT ["/entrypoint.sh"]

# Commande par défaut
CMD ["python", "scrape_and_insert.py"]
