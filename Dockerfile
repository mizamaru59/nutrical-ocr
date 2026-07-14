FROM python:3.13-slim

WORKDIR /app

# Évite les fichiers .pyc et force les logs à s'afficher immédiatement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Dépendances système utiles à OpenCV/Pillow
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copier les dépendances
COPY requirements.txt .

# Mettre pip à jour
RUN pip install --upgrade pip

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le projet
COPY . .

# Railway fournit PORT automatiquement
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT}"