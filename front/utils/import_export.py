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


def export_table_to_excel(n_clicks: int, table_data: list[dict]):
    """
    Exports table data to an Excel file when the download button is clicked.
    
    Args:
        n_clicks (int): The number of times the download button has been clicked.
        table_data (list[dict]): The data to be exported, typically in the form of a list of dictionaries.

    Returns:
        dash.Dash.no_update | dcc.SendBytes: 
            - If no click or invalid data, return no_update.
            - If valid data and click, returns a downloadable Excel file as bytes.
    """
    if n_clicks is None or n_clicks == 0 or not table_data:
        return dash.no_update

    # Convert the data back to a pandas DataFrame
    export_df = pd.DataFrame(table_data)
    
    # Write the DataFrame to an in-memory xlsx file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)

    # Prepare the file for download by sending it as bytes
    return dcc.send_bytes(output.read(), "data_table.xlsx")


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a filename by removing non-alphanumeric characters and normalizing accented characters.

    Args:
        filename (str): The original filename that needs sanitizing.

    Returns:
        str: The sanitized filename, which contains only alphanumeric characters and periods.
    """
    # Remove accented characters and normalize the string
    filename = unidecode(filename)
    # Remove all non-alphanumeric characters except for periods
    filename = re.sub(r'[^a-zA-Z0-9.]', '', filename)
    return filename


def import_uploaded_pdf_to_s3(
    contents: list[str], 
    filenames: list[str], 
    bucket_name: str = 's3-bucket-enedis', 
    output_folder: str = 'full_pdf', 
    aws_region: str = 'us-west-2'
) -> None:
    """
    Imports PDF files to a specified AWS S3 bucket after decoding the base64-encoded content.

    Args:
        contents (list[str]): A list of base64-encoded file contents.
        filenames (list[str]): A list of filenames corresponding to each PDF.
        bucket_name (str): The name of the AWS S3 bucket to upload the PDFs to.
        output_folder (str): The folder in the S3 bucket to store the PDFs.
        aws_region (str): The AWS region where the S3 bucket is located.

    Raises:
        PreventUpdate: If no contents are provided, the function does nothing.
    """
    if contents is None:
        raise PreventUpdate

    # Create an AWS S3 client using the specified region
    s3 = boto3.client('s3', region_name=aws_region)

    # Iterate over each file and upload it to the specified S3 bucket
    for content, filename in zip(contents, filenames):
        # Extract the file content and decode it from base64
        content_type, content_string = content.split(',')
        decoded_pdf = base64.b64decode(content_string)

        # Sanitize the filename to remove special characters and accents
        filename = sanitize_filename(filename)

        # Define the S3 object path (including folder structure)
        s3_object_key = os.path.join(output_folder, filename) if output_folder else filename
        try:
            # Upload the decoded PDF to the specified S3 bucket
            s3.put_object(
                Bucket=bucket_name,
                Key=s3_object_key,
                Body=decoded_pdf,
                ContentType='application/pdf'  # Set the content type to PDF
            )
        except Exception as e:
            # Print an error message if the upload fails
            print(f"Error: {str(e)}")

    # No return value needed, as this function performs an upload to S3
    return
