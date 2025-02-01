import re
from media_ressources import media_dict
from PyPDF2 import PdfReader


def extract_articles_from_pdf(pdf_path, dossier=False):
    """
    Extrait des articles d'un fichier PDF en fonction de son contenu et de l'option 'dossier'.

    Arguments :
    pdf_path (str) : Le chemin du fichier PDF à traiter.
    dossier (bool) : Si True, ignore les pages avant la première page contenant le texte "DR Nord-Pas-de-Calais" et uniquement les pages pertinentes après ce point sont incluses. Par défaut, toutes les pages sont incluses.

    Retourne :
    List[str] : Une liste de chaînes de caractères, chaque chaîne représentant un article extrait du PDF.

    Description :
    Cette fonction parcourt les pages d'un fichier PDF, extrait le texte de chaque page et regroupe les pages en articles.
    Si l'argument `dossier` est True, elle commence à extraire après la première page contenant "DR Nord-Pas-de-Calais" ou un texte non vide pertinent.
    Les articles sont délimités par la présence de la balise "Parution" dans le texte.
    """
    # Initialisation du lecteur de PDF
    reader = PdfReader(pdf_path)

    # Liste pour stocker les pages qui seront incluses dans les articles
    pages_text = []

    # Si dossier=True, ignorer les pages avant la première page contenant 'DR Nord-Pas-de-Calais' uniquement
    if dossier:
        found_first_article = False
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_text = page.extract_text()

            # Si la page contient seulement 'DR Nord-Pas-de-Calais', l'ignorer
            if page_text.strip() == "DR Nord-Pas-de-Calais":
                found_first_article = True
                continue  # Passer à la page suivante sans ajouter cette page

            elif (
                found_first_article
            ):  # Ajouter les pages pertinentes après la première page d'article
                pages_text.append(page_text)
    else:
        # Si dossier=False, on ajoute simplement toutes les pages
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_text = page.extract_text()
            pages_text.append(page_text)

    # Joindre toutes les pages extraites en un seul texte
    # all_text = "\n".join(pages_text)

    # Expression régulière pour identifier les articles en fonction de la balise "Parution"
    # Nous recherchons "Parution" pour délimiter les fins d'article
    articles = []
    current_article = []

    # Séparer le texte sur chaque occurrence de la balise "Parution"
    for page_num, page_text in enumerate(pages_text):
        # Si la page contient la balise "Parution"
        if "Parution" in page_text:
            # Ajouter la page courante contenant la balise "Parution"
            current_article.append(page_text)

            # Ajouter l'article complet à la liste des articles
            articles.append("\n".join(current_article))

            # Réinitialiser pour commencer un nouvel article
            current_article = []
        else:
            # Ajouter la page à l'article en cours
            current_article.append(page_text)

    # Si un article est encore en cours après la dernière page, l'ajouter aussi
    if current_article:
        articles.append("\n".join(current_article))

    # Nettoyer les articles en enlevant les espaces superflus
    articles = [article.strip() for article in articles if article.strip()]

    return articles


# Fonction pour extraire la date en pleine lettre dans le texte
def extract_date_from_text(text):
    """
    Extrait une date en pleine lettre (jour, mois, année) à partir d'un texte donné.

    Arguments :
    text (str) : Le texte contenant potentiellement une date à extraire.

    Retourne :
    str : La date extraite sous forme de chaîne de caractères au format "MM/JJ/AAAA" (mois/jour/année).
    Si aucune date n'est trouvée, retourne None.

    Description :
    Cette fonction utilise une expression régulière pour rechercher une date au format complet (jour de la semaine, jour, mois, année) dans le texte.
    Le mois est converti de son nom en format numérique.
    """
    # Expression régulière pour capturer la date en pleine lettre (jour, mois, année)
    date_pattern = r"\b(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\s+(\d{1,2})\s+([a-zA-Zéàôù]+)\s+(\d{4})\b"

    # Recherche de la date avec l'expression régulière
    match = re.search(date_pattern, text)

    if match:
        # Extraire le jour, le mois et l'année
        day, month, year = match.groups()

        # Convertir le mois en texte à son format numérique
        months = {
            "janvier": "01",
            "février": "02",
            "mars": "03",
            "avril": "04",
            "mai": "05",
            "juin": "06",
            "juillet": "07",
            "août": "08",
            "septembre": "09",
            "octobre": "10",
            "novembre": "11",
            "décembre": "12",
        }

        # Récupérer le mois au format numérique
        month_num = months.get(month.lower())

        if month_num:
            # Construire la date au format mois/jour/année
            date_str = f"{month_num}/{int(day):02d}/{year}"

            # Retourner la date formatée
            return date_str

    # Si aucune date n'est trouvée
    return None


def check_media_in_text(text):
    """
    Analyse un texte donné pour détecter des noms de médias en fonction d'un dictionnaire `media_dict`.

    La fonction vérifie également la présence de l'expression "Tous droits réservés" (ou ses variantes).

    - Si "Tous droits réservés" apparaît **avant** une mention de média, la fonction retourne uniquement `["Tous droits réservés"]`.
    - Sinon, elle retourne la liste des médias détectés dans le texte.

    Paramètres :
    ------------
    text : str
        Le texte à analyser.

    Retourne :
    ----------
    list
        Une liste contenant les noms des médias détectés.
        Si "Tous droits réservés" est trouvé **avant** toute mention de média, la fonction retourne `["Tous droits réservés"]`.
        Si aucun média n'est trouvé, elle retourne une liste vide `[]`.

    Exemples :
    ----------
    >>> media_dict = {
    ...     "Le Monde": ["Le Monde", "Lemonde.fr"],
    ...     "BBC": ["BBC", "BBC News"]
    ... }
    >>> check_media_in_text("Cet article de Le Monde est très intéressant.")
    ['Le Monde']

    >>> check_media_in_text("Tous droits réservés. Cet article provient de la BBC.")
    ['Tous droits réservés']

    >>> check_media_in_text("Aucune mention spécifique ici.")
    []
    """

    # Normalisation du texte pour une comparaison insensible à la casse
    text_lower = text.lower()

    # Liste des variantes de "Tous droits réservés" à détecter
    reserved_rights_variations = [
        "tous droits réservés",
        "t ous droits réservés",  # Erreur typographique avec espace en trop
        "tous droits reserve",  # Sans accent
        "tous droits réservée",  # Erreur grammaticale possible
        "tous droit réservé",  # Singulier
        "tous droit réservés",  # Mélange singulier/pluriel
        "© tous droits réservés",  # Avec le symbole copyright
        "(c) tous droits réservés",
        "tous droits réservés.",  # Avec un point final
        "tous droits réservés :",
    ]

    # Trouver la première occurrence de "Tous droits réservés" parmi ses variantes
    reserved_rights_index = -1
    for variant in reserved_rights_variations:
        index = text_lower.find(variant)
        if index != -1 and (
            reserved_rights_index == -1 or index < reserved_rights_index
        ):
            reserved_rights_index = index

    # Liste des médias trouvés
    found_media = []

    # Vérification de chaque média dans le dictionnaire
    for media, variations in media_dict.items():
        for variation in variations:
            # Vérification d'une correspondance exacte de chaque variation dans le texte
            variation_lower = variation.lower()
            index = text_lower.find(variation_lower)

            if index != -1:  # Si la variation est trouvée dans le texte
                if reserved_rights_index != -1 and index > reserved_rights_index:
                    # Si "Tous droits réservés" précède ce média, on retourne uniquement celui-ci
                    return ["Tous droits réservés"]
                found_media.append(media)
                break  # Une fois le média trouvé, on passe au suivant

    return found_media  # Retourne la liste complète si "Tous droits réservés" n'est pas trouvé
