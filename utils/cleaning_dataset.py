import os
import re
import csv
import unicodedata
from typing import List, Optional, Union, Any, Dict

import pandas as pd
import pymysql
from dotenv import load_dotenv
import unidecode

# Global mapping remains unchanged.
media_mapping = {
    "20 minutes": "20 minutes",
    "actu": "Actu",
    "bfm": "BFM",
    "bfm - grand lille": "BFM - Grand Lille",
    "bfm business": "BFM BUSINESS",
    "bfm grand lille": "BFM Grand Lille",
    "bfm lille": "BFM Lille",
    "bfm littoral": "BFM LITTORAL",
    "bfmtv grand lille": "BFMTV Grand Lille",
    "call magazine d'info locale": "CALL Magazine d'Info Locale",
    "canal fm": "Canal FM",
    "chantiersdefrance.fr": "Chantiersdefrance.fr",
    "cherie fm": "Cherie FM",
    "contact fm": "Contact FM",
    "croix du nord": "Croix du Nord",
    "croix du nord hebdomadaire chretien regional": "Croix du Nord hebdomadaire chrétien régional",
    "delta fm": "Delta FM",
    "du valenciennois": "Du Valenciennois",
    "echo de la lys": "Echo de la Lys",
    "eco 121": "ECO 121",
    "eco121": "Eco121",
    "energie-today": "Energie-today",
    "france 3": "France 3",
    "france 3 nord pas de calais": "France 3 Nord Pas de Calais",
    "france 3 npdc": "France 3 NPDC",
    "france bleu": "France Bleu",
    "france bleu france 3": "France Bleu/France 3",
    "france bleu nord": "France Bleu Nord",
    "france bleur": "France Bleu",
    "france info": "France Info",
    "france infos": "France Info",
    "horizon": "Horizon",
    "immodurable": "Immodurable",
    "indicateur des flandres": "Indicateur des Flandres",
    "jdl groupe": "JDL Groupe",
    "l'abeille de la ternoise": "L'Abeille de la Ternoise",
    "l'artois l'avenir": "L'Artois l'Avenir",
    "l'avenir de l' artois": "L'Avenir de l'Artois",
    "l'avenir de l'artois": "L'Avenir de l'Artois",
    "l'echo de la lys": "L'Echo de la Lys",
    "l'indacteur des flandres": "L'indicateur des Flandres",
    "l'independant": "L'Independant",
    "l'indicateur des flandres": "L'indicateur des Flandres",
    "l'indocateur des flandres la voix du nord": "L'indicateur des Flandres/La Voix du Nord",
    "l'observateur": "L'Observateur",
    "l'observateur de douaisis": "L'Observateur de Douaisis",
    "l'observateur de l'arrageois": "L'Observateur de l'Arrageois",
    "l'observateur de l'avesnois": "L'Observateur de l'Avesnois",
    "l'observateur douaisis": "L'Observateur de Douaisis",
    "l'observateur du cambresis": "L'Observateur du Cambrésis",
    "l'observateur du douaisis": "L'Observateur du Douaisis",
    "l'observateur du valenciennois": "L'Observateur du Valenciennois",
    "l'observatur de l'arrageois": "L'Observateur de l'Arrageois",
    "l'obvervateur du valenciennois": "L'Observateur du Valenciennois",
    "l'oservateur du cambresis": "L'Observateur du Cambrésis",
    "la gazette": "La Gazette",
    "la gazette nord - pas de calais": "La Gazette Nord - Pas de Calais",
    "la gazette nord pas de calais": "La Gazette Nord Pas de Calais",
    "la gazette nord-pas de calais": "La Gazette Nord-Pas de Calais",
    "la gazette npdc": "La Gazette NPDC",
    "la phare dunkerquois": "La Phare Dunkerquois",
    "la sambre la frontiere": "La Sambre la Frontière",
    "la semaine dans le boulonnais": "La Semaine dans le Boulonnais",
    "la voix du nord": "La Voix du Nord",
    "la voix du nord  nord eclair": "La Voix du Nord/Nord Eclair",
    "la voix du nord (2)": "La Voix du Nord",
    "la voix du nord contact fm": "La Voix du Nord/Contact FM",
    "la voix du nord france 3 npdc croix du nord": "La Voix du Nord/France 3 NPDC/Croix du Nord",
    "la voix du nord le courrier de fourmies l'observateur de l'avesnois": "La Voix du Nord/Le Courrier de Fourmies/L'Observateur de l'Avesnois",
    "la voix du nord nord eclair": "La Voix du Nord/Nord Eclair",
}

# ----------------- Atomic utilities -----------------


def normalize(text: str) -> str:
    """Remove accents, lowercase, and trim spaces."""
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .lower()
        .strip()
    )


def clean_using_dict(text: str, replace_dict: Dict[str, str]) -> str:
    for old, new in replace_dict.items():
        text = text.replace(old, new)
    return text


# ----------------- Splitting utilities -----------------


def get_delimiter_pattern(delimiters: List[str]) -> str:
    return "|".join(map(re.escape, delimiters))


def split_value_by_delimiters(value: Any, delimiters: List[str]) -> List[Any]:
    if isinstance(value, str):
        pattern = get_delimiter_pattern(delimiters)
        if re.search(pattern, value):
            return re.split(pattern, value)
    return [value]


def split_series_by_delimiters(series: pd.Series, delimiters: List[str]) -> pd.Series:
    return series.apply(lambda x: split_value_by_delimiters(x, delimiters))


# ----------------- Database utilities -----------------


def connect_to_rds() -> Optional[pymysql.Connection]:
    try:
        return pymysql.connect(
            host=os.getenv("RDS_HOST_WRITER"),
            user=os.getenv("RDS_USER"),
            password=os.getenv("RDS_PASSWORD"),
            database=os.getenv("RDS_DB"),
        )
    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def load_csv_to_mysql(csv_file_path: Union[str, os.PathLike]) -> None:
    connection = connect_to_rds()
    if not connection:
        print("Connection failed.")
        return

    cursor = connection.cursor()
    with open(csv_file_path, mode="r", encoding="utf-8") as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header
        for row in csv_reader:
            try:
                cursor.execute(
                    f"""
                    INSERT INTO {os.getenv("RDS_TABLE")}
                    (date, territoire, sujet, theme, nb_articles, media, article, nuance, sentiment, factuel)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    row,
                )
            except pymysql.MySQLError as e:
                print(f"Error inserting row {row}: {e}")
        try:
            connection.commit()
            print("Data inserted successfully.")
        except pymysql.MySQLError as e:
            print(f"Error during commit: {e}")
        finally:
            cursor.close()
            connection.close()


# ----------------- Transformation functions -----------------


def transform_media(
    df: pd.DataFrame, delimiters: List[str] = ["/", " et ", "+"]
) -> pd.DataFrame:
    df["media"] = split_series_by_delimiters(df["media"], delimiters)
    df["media"] = df.apply(lambda row: row["media"][: row["nb_articles"]], axis=1)
    # Adjust article count based on split length
    df["nb_articles"] = df["nb_articles"] // df["media"].apply(len)
    df = df.explode("media", ignore_index=True)
    df["media"] = df["media"].apply(normalize).map(media_mapping)
    return df


def restructure_theme_list(themes: List[str], nb_articles: int) -> List[str]:
    if len(themes) >= nb_articles:
        return themes[: nb_articles - 1] + ["/".join(themes[nb_articles - 1 :])]
    return themes


def transform_theme(df: pd.DataFrame, delimiters: List[str] = ["/"]) -> pd.DataFrame:
    # Replace whitespace in theme values and then split by delimiter.
    df["theme"] = df["theme"].str.replace(r"\s+", "_", regex=True)
    df["theme"] = split_series_by_delimiters(df["theme"], delimiters)
    df["theme"] = df.apply(
        lambda row: (
            restructure_theme_list(row["theme"], row.nb_articles)
            if isinstance(row["theme"], list)
            else row["theme"]
        ),
        axis=1,
    )
    df["nb_articles"] = df["nb_articles"] // df["theme"].apply(len)
    df = df.explode("theme", ignore_index=True)
    return df


def clean_tonalite(df: pd.DataFrame) -> pd.DataFrame:
    # Clean the nuance column and set flags for nuance and factuel.
    df["nuance"] = df["nuance"].str.strip().str.replace(r"\s+", " ", regex=True)
    nuance_map = {
        "factuel": False,
        "factuel négatif": False,
        "négatif": False,
        "positif": False,
        "factuel positif": False,
        "positif nuancé": True,
        "négatif nuancé": True,
    }
    df["nuance"] = df["nuance"].map(nuance_map)
    df["factuel"] = df["factuel"].astype(int)
    df["nuance"] = df["nuance"].astype(int)
    df["sentiment"] = df["sentiment"].map(
        {"neutre": "NEUTRAL", "positif": "POSITIVE", "negatif": "NEGATIVE"}
    )
    return df


def convert_date(df: pd.DataFrame) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    return df


# ----------------- Preprocessing functions -----------------


def preprocess_theme_column(df: pd.DataFrame) -> pd.DataFrame:
    # Clean the theme column: remove accents, lowercase and trim spaces.
    df["theme"] = df["theme"].apply(
        lambda x: unidecode.unidecode(str(x).lower().strip())
    )
    # Make explicit replacements to standardize theme texts.
    replacements = {
        "clients": "client",
        "cleints": "client",
        "partenariats industriels / academiques": "partenariats industriels/academiques",
        "rh - partenariat - rse": "rh/partenariat/rse",
        "aleas climatique": "aleas climatiques",
        "aleas climatiquess": "aleas climatiques",
        "marque employeur / rh": "marque employeur/rh",
    }
    for old, new in replacements.items():
        df["theme"] = df["theme"].str.replace(old, new, regex=False)
    return df


def preprocess_territoire_column(df: pd.DataFrame) -> pd.DataFrame:
    # Standardize territoire values
    replace_dict = {
        "nord pas-de-calais": "Hauts-de-France",
        "nord pas-de-calais ": "Hauts-de-France",
        "nord pas de calais": "Hauts-de-France",
        "nord pas de calais ": "Hauts-de-France",
        "nord-pas de calais": "Hauts-de-France",
        "nord-pas-de-calais": "Hauts-de-France",
        "nord": "Nord",
        "nord ": "Nord",
        "nord  ": "Nord",
        "Nord ": "Nord",
        "Nord  ": "Nord",
        "nord - pas-de-calais": "Hauts-de-France",
        "Nord - pas de calais": "Hauts-de-France",
        "Nord pas-de-calais": "Hauts-de-France",
        "Nord pas-de-calais ": "Hauts-de-France",
        " pas-de-calais": "Pas-de-Calais",
        "Pas-de-Calais": "Pas-de-Calais",
        "Pas-de-Calais ": "Pas-de-Calais",
        "pas-de-calais": "Pas-de-Calais",
        "pas-de-calais ": "Pas-de-Calais",
        "pas de calais": "Pas-de-Calais",
        "pas de calais ": "Pas-de-Calais",
        "hauts-de-france": "Hauts-de-France",
        "hauts-de-france ": "Hauts-de-France",
    }
    df["territoire"] = (
        df["territoire"].str.lower().apply(lambda x: clean_using_dict(x, replace_dict))
    )
    return df


def preprocess_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess the DataFrame by cleaning the 'theme' and 'territoire' columns.
    This function provides explicit, step-by-step transformations.
    """
    df = preprocess_theme_column(df)
    df = preprocess_territoire_column(df)
    return df


def sanitize_and_label_responses(df: pd.DataFrame) -> pd.DataFrame:
    df["Qualité du retour"] = df["Qualité du retour"].apply(
        lambda x: unidecode.unidecode(x.lower())
    )
    df["Qualité du retour"] = df["Qualité du retour"].str.strip()

    df["sentiment"] = df["Qualité du retour"].apply(
        lambda x: (
            "positif" if "positif" in x else ("negatif" if "negatif" in x else "neutre")
        )
    )

    df["factuel"] = df["Qualité du retour"].apply(
        lambda x: True if "factuel" in x else False
    )

    return df


# ----------------- Main script -----------------

if __name__ == "__main__":
    load_dotenv()
    # Load CSV into DataFrame and rename columns
    df = pd.read_csv("data/Data.csv")

    df.rename(
        columns={
            "Date": "date",
            "Territoire": "territoire",
            "Sujet": "sujet",
            "Thème": "theme",
            "Nbre d'article": "nb_articles",
            "Média": "media",
            "Articles": "article",
            "Tonalité": "nuance",
        },
        inplace=True,
    )
    df["nb_articles"] = df["nb_articles"].fillna(1).astype(int)

    # Process media and theme columns
    df = transform_media(df)
    df = transform_theme(df)

    # Clean tonalite, convert date then apply explicit preprocessing for theme and territoire.
    df = sanitize_and_label_responses(df)
    df = clean_tonalite(df)
    df = convert_date(df)
    df = preprocess_df(df)

    df.drop_duplicates(inplace=True)
    df = df.dropna(how="all")
    df = df.drop(columns=["Qualité du retour2", "Qualité du retour"])

    print(df.head())

    df.to_csv("data/Data_cleaned.csv", index=False)
    # load_csv_to_mysql("updated_file.csv")
    print("Process completed.")
