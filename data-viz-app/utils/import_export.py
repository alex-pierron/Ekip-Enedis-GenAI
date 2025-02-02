import os 
import io 
import re
import base64
from unidecode import unidecode
import pandas as pd

import dash 
from dash import dcc
from dash.exceptions import PreventUpdate

import boto3


def export_table_to_excel(n_clicks, table_data):
    if n_clicks is None or n_clicks == 0 or not table_data:
        return dash.no_update

    # convert the data back to a DataFrame
    export_df = pd.DataFrame(table_data)
    
    # write it to xlsx file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)

    # prepare the file for download
    return dcc.send_bytes(output.read(), "data_table.xlsx")

def sanitize_filename(filename):
    filename = unidecode(filename)
    filename = re.sub(r'[^a-zA-Z0-9.]', '', filename)
    return filename


def import_uploaded_pdf_to_s3(contents, filenames, bucket_name='s3-bucket-enedis', output_folder='tmp/pdf', aws_region='us-west-2'):
    if contents is None:
        raise PreventUpdate

    # Create a session using AWS credentials
    s3 = boto3.client('s3', region_name=aws_region)

    # iterate over given files
    for content, filename in zip(contents, filenames):
        content_type, content_string = content.split(',')
        decoded_pdf = base64.b64decode(content_string)

        filename = sanitize_filename(filename)

        # define S3 object path
        s3_object_key = os.path.join(output_folder, filename) if output_folder else filename
        try:
            # upload to S3 bucket
            s3.put_object(
                Bucket=bucket_name,
                Key=s3_object_key,
                Body=decoded_pdf,
                ContentType='application/pdf'  # ensure the content is recognized as PDF
            )
        except Exception as e:
            print(f"Erreur : {str(e)}")
    return