from departement import departements_france
# 📌 Charger les données des villes et codes postaux à partir du fichier CSV

import pandas as pd

# Charger le CSV dans un DataFrame
cities_and_departement = pd.read_csv("./data_city/cities_and_postal_code.csv",delimiter=';')

# Normaliser le nom des villes en minuscules et supprimer les espaces
cities_and_departement["Nom_de_la_commune"] = cities_and_departement["Nom_de_la_commune"].str.strip().str.lower()

# Extraire les deux premiers chiffres du code postal pour obtenir le Departement
cities_and_departement["Departement"] = cities_and_departement["Code_postal"].astype(str).str[:2]

# Gérer les cas particuliers de la Corse (2A et 2B)
cities_and_departement.loc[cities_and_departement["Code_postal"].astype(str).str.startswith("201"), "Departement"] = "2A"
cities_and_departement.loc[cities_and_departement["Code_postal"].astype(str).str.startswith("202"), "Departement"] = "2B"


def get_department(location, df = cities_and_departement):
    location = location.strip().lower()  # Normalisation de l'entrée

    # Vérifier si `location` est un Departement (en comparant avec les codes Departement)
    if location in departements_france.values():
        return location

    # Si `location` est une ville, on récupère son Departement
    if location in df["Nom_de_la_commune"].values:
        department_code = df.loc[df["Nom_de_la_commune"] == location, "Departement"].values[0]
        department_name = departements_france.get(department_code, "Inconnu")
        return department_name
    
    else:
        return "Inconnu"