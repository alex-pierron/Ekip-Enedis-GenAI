import boto3  # API AWS
from botocore.exceptions import ClientError
import os
from nova_llm import PDFLabelisation
import logging
import json

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")


def lambda_handler(event, context):
    logger.info("Lambda function triggered")
    logger.info(f"event result: {event}")
    # Iterate over each SQS message
    for record in event["Records"]:
        # The body of the message
        message_body = json.loads(record["body"])
        logger.info(f"Processing message: {message_body}")
        try:
            path = message_body.get("path", None)
            text = message_body.get("text", "")
            # Initialize the PDFLabelisation object
            if path:
                pdf_labelisation = PDFLabelisation(
                    aws_access_key_id,
                    aws_secret_access_key,
                    "us.amazon.nova-lite-v1:0",
                    text,
                )

                # Call the forward method to get the labelisation
                message_body = pdf_labelisation.forward(path)
                message_body = json.loads(message_body)
                message_body = message_body["body"]
                json.dumps(message_body)
                message = json.dumps(
                    {
                        "date": message_body["date"],
                        "territoire": message_body["territoire"],
                        "sujet": message_body["sujet"],
                        "nb_articles": message_body["nb_articles"],
                        "media": message_body["media"],
                        "article": message_body["article"],
                    }
                )
                logger.info(f"Output: {message}")
                sqs_client = boto3.client("sqs")
                response = sqs_client.send_message(
                    QueueUrl="https://sqs.us-west-2.amazonaws.com/571600845115/NOVA2Mistral",
                    MessageBody=message,
                )
                return {
                    "statusCode": 200,
                }

        except ClientError as e:
            logger.error("Error during the labelisation process: ", exc_info=e)
