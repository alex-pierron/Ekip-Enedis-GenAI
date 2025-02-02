import json
import boto3
import io
import logging
from PyPDF2 import PdfReader, PdfWriter

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3 = boto3.client("s3")


def extract_pages_from_memory(pdf_reader, start_page, end_page):
    """
    Extract specific pages from a PdfReader object.
    """
    pdf_writer = PdfWriter()
    for page_num in range(start_page, end_page + 1):
        if page_num < len(pdf_reader.pages):
            pdf_writer.add_page(pdf_reader.pages[page_num])

    # Return the extracted PDF content as bytes
    pdf_output = io.BytesIO()
    pdf_writer.write(pdf_output)
    pdf_output.seek(0)
    return pdf_output


def extract_article_page_ranges_from_pdf(reader):
    """
    Extract page ranges for articles based on specific text markers.
    """
    article_page_ranges = []
    found_first_article = False
    current_article_start = None

    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text()

        if not found_first_article:
            if page_text.strip() == "DR Nord-Pas-de-Calais":
                found_first_article = True
                current_article_start = page_num + 1
                logger.info(
                    f"Found start of the first article at page {current_article_start}"
                )
                continue
        else:
            if "Parution" in page_text:
                if current_article_start is not None:
                    article_page_ranges.append((current_article_start, page_num))
                    logger.info(
                        f"Article detected: Start {current_article_start}, End {page_num}"
                    )
                current_article_start = page_num + 1

    logger.info(f"Extracted article page ranges: {article_page_ranges}")
    return article_page_ranges


def extract_articles_as_pdf_from_memory(pdf_content, output_bucket, output_prefix):
    """
    Extract articles as separate PDFs directly from the in-memory PDF content.
    """
    reader = PdfReader(io.BytesIO(pdf_content))
    article_page_ranges = extract_article_page_ranges_from_pdf(reader)

    output_files = []
    for i, (start_page, end_page) in enumerate(article_page_ranges):
        logger.info(f"Extracting article {i}: Pages {start_page} to {end_page}")
        pdf_output = extract_pages_from_memory(reader, start_page, end_page)
        article_key = f"{output_prefix}/article{i}.pdf"

        # Upload the extracted article to S3
        logger.info(f"Uploading article {i} to S3 with key: {article_key}")
        s3.upload_fileobj(pdf_output, output_bucket, article_key)
        output_files.append(article_key)

    logger.info(f"Uploaded articles to S3: {output_files}")
    return output_files


def lambda_handler(event, context):
    try:
        # Get bucket and object key from the event
        bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
        object_key = event["Records"][0]["s3"]["object"]["key"]
        output_prefix = "input"

        logger.info(f"Received event: {json.dumps(event)}")
        logger.info(f"Processing file from bucket: {bucket_name}, key: {object_key}")

        # Get the PDF content from S3
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        pdf_content = response["Body"].read()

        logger.info(f"Fetched object metadata: {response['Metadata']}")
        logger.info(f"PDF content size: {len(pdf_content)} bytes")

        # Process the PDF content and extract articles
        output_files = extract_articles_as_pdf_from_memory(
            pdf_content, bucket_name, output_prefix
        )

        logger.info(f"Successfully processed PDF. Extracted articles: {output_files}")
        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "PDF processed successfully!", "output_files": output_files}
            ),
        }

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}
