import pymysql
import pandas as pd
from utils.shared_utils import normalize_text

def fetch_table_as_df(host: str, user: str, password: str, db_name: str, table_name: str) -> pd.DataFrame:
    """
    Fetches data from a MySQL database table and returns it as a pandas DataFrame.

    Args:
        host (str): The host address of the MySQL server.
        user (str): The username to authenticate with the MySQL server.
        password (str): The password to authenticate with the MySQL server.
        db_name (str): The name of the database to connect to.
        table_name (str): The name of the table to fetch data from.

    Returns:
        pd.DataFrame: A DataFrame containing the table data.
    
    Raises:
        pymysql.MySQLError: If an error occurs while interacting with the MySQL database.
    """
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        connect_timeout=10
    )
    try:
        cursor = conn.cursor()
        cursor.execute(f"USE {db_name};")

        # Query to fetch all rows from the table
        query = f"SELECT * FROM {table_name};"
        cursor.execute(query)
        rows = cursor.fetchall()

        # Query to get table column names
        column_query = f"SHOW COLUMNS FROM {table_name};"
        cursor.execute(column_query)
        columns = [col[0] for col in cursor.fetchall()]

        # Convert rows into a pandas DataFrame
        df = pd.DataFrame(rows, columns=columns)
        return df

    finally:
        # Ensure that the cursor and connection are closed even if an error occurs
        cursor.close()
        conn.close()


def standardize_columns(df: pd.DataFrame, columns_to_fix: list) -> pd.DataFrame:
    """
    Standardizes the values in the specified columns by normalizing the text and 
    replacing values with the most frequent occurrence for each normalized value.

    Args:
        df (pd.DataFrame): The DataFrame to process.
        columns_to_fix (list): A list of column names to standardize.

    Returns:
        pd.DataFrame: A DataFrame with standardized values in the specified columns.
    """
    for col in columns_to_fix:
        # Normalize the values into a temporary column
        df[f"{col}_normalized"] = df[col].apply(lambda x: normalize_text(x, keep_alphanum=True))
        
        # Get the most frequent value for each normalized occurrence
        most_frequent_mapping = (
            df.groupby(f"{col}_normalized")[col]
            .agg(lambda x: x.mode()[0])  # Get the most frequent value
            .to_dict()
        )

        # Replace values in the original column by the most frequent one from the normalized column
        df[col] = df[f"{col}_normalized"].map(most_frequent_mapping)

        # Drop the temporary normalized column
        df = df.drop(columns=[f"{col}_normalized"])
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and processes the DataFrame by renaming columns, replacing specific values,
    and performing data normalization and transformation.

    Args:
        df (pd.DataFrame): The DataFrame to clean and process.

    Returns:
        pd.DataFrame: A cleaned and transformed DataFrame.
    """
    # Drop unnecessary columns
    df = df.drop(['id', 'nb_articles'], axis=1)

    # Replace values in the "factuel" and "nuance" columns with 'Oui' and 'Non'
    df["factuel"] = df["factuel"].replace({0: 'Non', 1: 'Oui'})
    df["nuance"] = df["nuance"].replace({0: 'Non', 1: 'Oui'})

    # Replace sentiment values with more readable terms
    sentiment_mapping = {
        "POSITIVE": "Positif",
        "NEGATIVE": "Négatif",
        "NEUTRAL": "Neutre"
    }
    df["sentiment"] = df["sentiment"].map(sentiment_mapping)

    # Rename columns to more user-friendly names
    rename_dict = {
        "date": "Date",
        "territoire": "Territoire",
        "sujet": "Sujet",
        "media": "Média",
        "theme": "Thème",
        "factuel": "Factuel",
        "sentiment": "Sentiment",
        "nuance": "Nuancé",
        "article": "Article",
    }
    df = df.rename(columns=rename_dict)

    # Move the 'Article' column to the end
    df["Article"] = df.pop("Article") 

    # Convert the "Date" column to datetime format
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
    
    # Standardize values in the specified columns
    columns_to_fix = ['Territoire', 'Thème', 'Média']
    df = standardize_columns(df, columns_to_fix)

    return df
