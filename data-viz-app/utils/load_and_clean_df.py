import os
import sys
import pymysql
import boto3
import pandas as pd
from io import StringIO
from botocore.exceptions import NoCredentialsError
from utils.shared_utils import normalize_text

def fetch_table_as_df(host, user, password, db_name, table_name):
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        connect_timeout=10
    )
    try:
        cursor = conn.cursor()
        cursor.execute(f"USE {db_name};")

        # get table data
        query = f"SELECT * FROM {table_name};"
        cursor.execute(query)
        rows = cursor.fetchall()

        # get table column names
        column_query = f"SHOW COLUMNS FROM {table_name};"
        cursor.execute(column_query)
        columns = [col[0] for col in cursor.fetchall()]

        df = pd.DataFrame(rows, columns=columns)
        return df

    finally:
        cursor.close()
        conn.close()


def standardize_columns(df, columns_to_fix):
    for col in columns_to_fix:
        # normalize values into a temp column
        df[f"{col}_normalized"] = df[col].apply(lambda x: normalize_text(x, keep_alphanum=True))
        
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

    # drop columns
    df = df.drop(['id', 'nb_articles'], axis=1)

    # modify column values 
    df["factuel"] = df["factuel"].replace({0: 'Non', 1: 'Oui'})
    df["nuance"] = df["nuance"].replace({0: 'Non', 1: 'Oui'})

    # Modify "sentiment" column using a dictionary mapping
    sentiment_mapping = {
        "POSITIVE": "Positif",
        "NEGATIVE": "Négatif",
        "NEUTRAL": "Neutre"
    }
    df["sentiment"] = df["sentiment"].map(sentiment_mapping)

    # rename columns
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

    # move 'Article' column at the end
    df["Article"] = df.pop("Article") 

    # converts "Date" to datetime (ex: 2023-01-04)
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
    
    # standardize values (ex: réseau and Réseau should be considered as the same)
    columns_to_fix = ['Territoire', 'Thème', 'Média']
    df = standardize_columns(df, columns_to_fix)

    return df


def load_data_from_s3(bucket_name, folder='', aws_region='us-east-1'):
    
    s3 = boto3.client('s3', region_name=aws_region)
    
    try:
        # list S3 bucket objects
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder)
        if 'Contents' not in response:
            raise ValueError("No files found in the bucket with the specified prefix.")
        
        # filter only the .csv files
        csv_files = [content['Key'] for content in response['Contents'] if content['Key'].endswith('.csv')]
        
        df_list = []
        
        for csv_file in csv_files:
            # get csv string data
            csv_obj = s3.get_object(Bucket=bucket_name, Key=csv_file)
            csv_content = csv_obj['Body'].read().decode('utf-8')

            # convert to DataFrame
            df = pd.read_csv(StringIO(csv_content), delimiter=';')
            df_list.append(df)
        
        # concat into a single dataframe
        df_concat = pd.concat(df_list, ignore_index=True)
        
        return df_concat
    
    except NoCredentialsError:
        raise ValueError("No AWS credentials found.")
    except Exception as e:
        raise ValueError(f"Error while loading data from S3: {str(e)}")
    