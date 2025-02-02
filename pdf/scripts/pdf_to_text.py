import re
from media_ressources import media_dict
from PyPDF2 import PdfReader


def extract_articles_from_pdf(pdf_path, dossier=False):
    """
    Extracts articles from a PDF file based on its content and the 'dossier' option.

    Arguments:
    ----------
    pdf_path (str): The path to the PDF file to be processed.
    dossier (bool):
        - If True, ignores pages before the first occurrence of "DR Nord-Pas-de-Calais"
          and includes only relevant pages after that point.
        - If False (default), all pages are included.

    Returns:
    --------
    List[str]: A list of strings, where each string represents an extracted article.

    Description:
    ------------
    This function scans the pages of a PDF file, extracts the text from each page,
    and groups pages into articles.
    - If `dossier=True`, extraction starts after the first occurrence of
      "DR Nord-Pas-de-Calais" or another relevant non-empty page.
    - Articles are identified and separated using the keyword **"Parution"** as a delimiter.
    """
    reader = PdfReader(pdf_path)

    pages_text = []

    if dossier:
        found_first_article = False
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_text = page.extract_text()

            if page_text.strip() == "DR Nord-Pas-de-Calais":
                found_first_article = True
                continue

            elif found_first_article:
                pages_text.append(page_text)
    else:
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_text = page.extract_text()
            pages_text.append(page_text)

    articles = []
    current_article = []

    for page_num, page_text in enumerate(pages_text):
        if "Parution" in page_text:
            current_article.append(page_text)

            articles.append("\n".join(current_article))

            current_article = []
        else:
            current_article.append(page_text)

    if current_article:
        articles.append("\n".join(current_article))

    articles = [article.strip() for article in articles if article.strip()]

    return articles


def extract_date_from_text(text):
    """
    Extracts a fully written-out date (day, month, year) from a given text in french.

    Arguments:
    ----------
    text (str): The text that may contain a date.

    Returns:
    --------
    str: The extracted date in the format "MM/DD/YYYY" (month/day/year).
         If no date is found, returns None.

    Description:
    ------------
    Uses a regular expression to search for a date in full format
    (day of the week, day, month, year). Converts the month name to its numeric format.

    Example:
    --------
    "Mardi 5 Janvier 2023" → "01/05/2023"
    """

    date_pattern = r"\b(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\s+(\d{1,2})\s+([a-zA-Zéàôù]+)\s+(\d{4})\b"

    match = re.search(date_pattern, text)

    if match:
        day, month, year = match.groups()

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

        month_num = months.get(month.lower())

        if month_num:
            date_str = f"{month_num}/{int(day):02d}/{year}"

            return date_str

    return None


def check_media_in_text(text):
    """
    Analyzes a given text to detect media names based on a predefined dictionary (`media_dict`).

    Function Behavior:
    ------------------
    - If the phrase "Tous droits réservés" (or a variation) appears **before** any media mention,
      the function returns `["Tous droits réservés"]`.
    - Otherwise, it returns a list of detected media names.

    Arguments:
    ----------
    text (str): The text to analyze.
    media_dict (dict): A dictionary mapping media names to their variations.

    Returns:
    --------
    list:
        - A list containing the names of detected media sources.
        - If "Tous droits réservés" appears **before** any media mention,
          returns `["Tous droits réservés"]`.
        - If no media is found, returns an empty list `[]`.

    Example Usage:
    --------------
    >>> media_dict = {
    ...     "Le Monde": ["Le Monde", "Lemonde.fr"],
    ...     "BBC": ["BBC", "BBC News"]
    ... }
    >>> check_media_in_text("This article from Le Monde is very interesting.", media_dict)
    ['Le Monde']

    >>> check_media_in_text("Tous droits réservés. This article comes from the BBC.", media_dict)
    ['Tous droits réservés']

    >>> check_media_in_text("No specific mention here.", media_dict)
    []
    """

    text_lower = text.lower()

    reserved_rights_variations = [
        "tous droits réservés",
        "t ous droits réservés",
        "tous droits reserve",
        "tous droits réservée",
        "tous droit réservé",
        "tous droit réservés",
        "© tous droits réservés",
        "(c) tous droits réservés",
        "tous droits réservés.",
        "tous droits réservés :",
    ]

    reserved_rights_index = -1
    for variant in reserved_rights_variations:
        index = text_lower.find(variant)
        if index != -1 and (
            reserved_rights_index == -1 or index < reserved_rights_index
        ):
            reserved_rights_index = index

    found_media = []

    for media, variations in media_dict.items():
        for variation in variations:
            variation_lower = variation.lower()
            index = text_lower.find(variation_lower)

            if index != -1:
                if reserved_rights_index != -1 and index > reserved_rights_index:
                    return ["Tous droits réservés"]
                found_media.append(media)
                break

    return found_media
