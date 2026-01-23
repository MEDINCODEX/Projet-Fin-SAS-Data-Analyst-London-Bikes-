# ---------------------------------------------
# Projet Fin SAS : Data Analyst (London Bikes)
# ---------------------------------------------

#  Importer les bibliothèques
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv

# ---------------------------
# 1️ Charger les variables d'environnement
# ---------------------------
# Le fichier .env contient les informations de connexion à PostgreSQL
# Ne jamais mettre le mot de passe directement dans le script
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "nom_base")
DB_USER = os.getenv("DB_USER", "utilisateur")
DB_PASSWORD = os.getenv("DB_PASSWORD", "motdepasse")

# ---------------------------
# 2️ Charger le CSV original
# ---------------------------
file_path = r'C:\Users\gomyx\Downloads\projet fin saas\london_merged.csv'
df = pd.read_csv(file_path)

# ---------------------------
# 3️ Aperçu des données
# ---------------------------
print("Nombre de lignes et colonnes:", df.shape)
print("Types de données:", df.dtypes)
print("Valeurs manquantes:", df.isnull().sum())
print("Nombre de doublons:", df.duplicated().sum())

# ---------------------------
# 4️ Renommer les colonnes
# ---------------------------
df = df.rename(columns={
    'cnt': 'Nombre de trajets',
    't1': 'Température réelle (°C)',
    't2': 'Température ressentie (°C)',
    'hum': 'Humidité',
    'wind_speed': 'Vitesse du vent (km/h)',
    'weather_code': 'Météo',
    'season': 'Saison'
})

# -------------------------------------------
# 5️ Nettoyage et transformation des données |
# -------------------------------------------

# Convertir l'humidité de % à une valeur entre 0 et 1
df['Humidité'] = df['Humidité'] / 100

# Convertir timestamp en type datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Transformer les codes numériques en valeurs lisibles
season_mapping = {0: 'Printemps', 1: 'Été', 2: 'Automne', 3: 'Hiver'}
weather_mapping = {
    1: 'Clair',
    2: 'Nuages épars',
    3: 'Nuages fragmentés',
    4: 'Couvert',
    7: 'Pluie',
    10: 'Pluie avec orage',
    26: 'Neige'
}

df['Saison'] = df['Saison'].map(season_mapping)
df['Météo'] = df['Météo'].map(weather_mapping)

# Vérifier les valeurs manquantes après transformation
print("Valeurs manquantes après transformation:", df.isnull().sum())

# -----------------------------
# 6️ Statistiques descriptives |
# -----------------------------
print("Statistiques descriptives des colonnes numériques:")
print(df[['Température réelle (°C)',
          'Température ressentie (°C)',
          'Humidité',
          'Vitesse du vent (km/h)']].agg(['min', 'max', 'mean', 'std']))

# ---------------------------
# 7️ Export des données nettoyées
# ---------------------------
csv_output = r"C:\Users\gomyx\Downloads\projet fin saas\london_bikes_final.csv"
excel_output = r"C:\Users\gomyx\Downloads\projet fin saas\london_bikes_final.xlsx"
df.to_csv(csv_output, index=False)
df.to_excel(excel_output, index=False)
print("\n Dataset nettoyé exporté vers CSV et Excel avec succès !")

# ---------------------------
# 8️ Connexion à PostgreSQL
# ---------------------------
password_encoded = quote_plus(DB_PASSWORD)
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Tester la connexion
with engine.connect() as conn:
    version = conn.execute(text("SELECT version();")).fetchone()[0]
    print(" Connexion réussie à PostgreSQL:", version)

# ---------------------------
# 9️ Créer la table et insérer les données
# ---------------------------
table_name = "london_bikes_final"
df.to_sql(table_name, engine, if_exists="replace", index=False)  # 'replace' ou 'append'
print(f" Données insérées dans la table: {table_name}")

# Vérifier le nombre de lignes
with engine.connect() as conn:
    count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name};")).fetchone()[0]
    print(f" Nombre de lignes dans la table: {count}")

# ---------------------------
# 10 Requêtes SQL analytiques
# ---------------------------
with engine.connect() as conn:
    # Total de trajets par saison
    print("--- Total de trajets par Saison ---")
    result = conn.execute(text(f"SELECT \"Saison\", SUM(\"Nombre de trajets\") as total_trajets FROM {table_name} GROUP BY \"Saison\";"))
    for row in result:
        print(row)

    # Total de trajets par météo
    print("--- Total de trajets par Météo ---")
    result = conn.execute(text(f"SELECT \"Météo\", SUM(\"Nombre de trajets\") as total_trajets FROM {table_name} GROUP BY \"Météo\";"))
    for row in result:
        print(row)

    # Moyenne de trajets par jour de la semaine
    print("--- Moyenne de trajets par jour de la semaine ---")
    result = conn.execute(text(f"""
        SELECT EXTRACT(DOW FROM timestamp) as jour_semaine,
               AVG("Nombre de trajets") as moyenne_trajets
        FROM {table_name}
        GROUP BY jour_semaine
        ORDER BY jour_semaine;
    """))
    for row in result:
        print(row)

    # Top 5 heures avec le plus de trajets
    print("--- Top 5 heures avec le plus de trajets ---")
    result = conn.execute(text(f"""
        SELECT EXTRACT(HOUR FROM timestamp) as heure,
               SUM("Nombre de trajets") as total_trajets
        FROM {table_name}
        GROUP BY heure
        ORDER BY total_trajets DESC
        LIMIT 5;
    """))
    for row in result:
        print(row)

    # Comparaison Week-end vs Semaine
    print("--- Comparaison Week-end vs Semaine ---")
    result = conn.execute(text(f"""
        SELECT is_weekend, AVG("Nombre de trajets") as moyenne_trajets
        FROM {table_name}
        GROUP BY is_weekend;
    """))
    for row in result:
        print(row)
        