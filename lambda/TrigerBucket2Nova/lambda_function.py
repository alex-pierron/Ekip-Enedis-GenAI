import json
import boto3
from PyPDF2 import PdfReader
import io

s3 = boto3.client('s3')


def lambda_handler(event, context):
    bucket = event['Records'][0]["s3"]["bucket"]["name"]
    key = event['Records'][0]["s3"]["object"]["key"]

    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        pdf_content = response["Body"].read()
        reader = PdfReader(io.BytesIO(pdf_content))
        pages_text = []

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
    
    except Exception as e:
        print("Error during extract text from pdf : ", e)
        return {
            'statusCode': 500,
            'body': json.dumps('Internal Server Error.')
        }
    
    message_body = json.dumps({
        'path': key,
        'text': articles[0]
    })
    sqs = boto3.client('sqs')
    response = sqs.send_message(
        QueueUrl="https://sqs.us-west-2.amazonaws.com/571600845115/QueueForNova",
        MessageBody=message_body
    )

    return {
        'statusCode': 200,
    }