import os
import re
import pandas as pd

def load_data(data_folder: str) -> pd.DataFrame:
    """Returns a dataframe containing data from all CSVs of a directory"""
    data_filenames = [filename for filename in os.listdir(data_folder) if filename.endswith('.csv')]
    df_list = []

    # generates a list of dataframes
    for data_filename in data_filenames:
        data_filepath = os.path.join(data_folder, data_filename)
        df = pd.read_csv(data_filepath, delimiter=';')
        df_list.append(df)
    
    # concat them into one df
    df_concat = pd.concat(df_list, ignore_index=True)
    return df_concat


def normalize_text(text):
    return re.sub(r'[^a-zA-Z0-9]', '', text.lower()) if pd.notna(text) else text

def standardize_columns(df, columns_to_fix):
    for col in columns_to_fix:
        # normalize values into a temp column
        df[f"{col}_normalized"] = df[col].apply(normalize_text)

        # get most frequent value for each normalized occurence
        most_frequent_mapping = (
            df.groupby(f"{col}_normalized")[col]
            .agg(lambda x: x.mode()[0]) # get most frequent
            .to_dict()
        )

        # replace values by the most frequent one from the temp column
        df[col] = df[f"{col}_normalized"].map(most_frequent_mapping)

        df = df.drop(columns=[f"{col}_normalized"])
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:

    # converts "Date" to datetime (ex: 2023-01-04)
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
    
    # standardize values (ex: réseau and Réseau should be considered as the same)
    columns_to_fix = ['Thème', 'Territoire', 'Qualité du retour']
    df = standardize_columns(df, columns_to_fix)

    return df