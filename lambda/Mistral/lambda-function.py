import json
import boto3  # API AWS
from botocore.exceptions import ClientError
import os
import pymysql
from datetime import datetime
import requests


os.environ["LIBMYSQL_ENABLE_CLEARTEXT_PLUGIN"] = "1"


class TextLabelisation:
    def __init__(self, aws_access_key_id, aws_secret_access_key, model_id):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.session = boto3.Session()
        self.bedrock = self.session.client(service_name="bedrock-runtime")
        self.rds = self.session.client(service_name="rds")
        self.model_id = model_id  # "mistral.mistral-large-2402-v1:0"

    def __model__(self):
        return self.model_id

    def forward(self, article):
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": f"You have to use the sentiment_checker tool to classify the sentiment on the content within the <article> tags.\n\n {self.__create_content__(article)}"
                    }
                ],
            }
        ]

        response = self.bedrock.converse(
            modelId=self.model_id,
            messages=messages,
            inferenceConfig={
                "maxTokens": 512,
                "temperature": 0,
            },
            toolConfig={"tools": self.__getTool__(), "toolChoice": {"any": {}}},
        )

        output = self.__parse_response__(response)
        output = self.__factuel_treshold__(output)
        return output

    def __create_content__(self, article):
        date = article["date"]
        territory = article["territoire"]
        title = article["sujet"]
        media = article["media"]
        content = article["article"]

        return f"""
        <article>
        <date>{date}</date>
        <territory>{territory}</territory>
        <title>{title}</title>
        <media>{media}</media>
        <content>{content}</content>
        </article>
        """

    def __getTool__(self):
        tool_list = [
            {
                "toolSpec": {
                    "name": "sentiment_checker",
                    "description": "Get the sentiment of the article.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "overall_sentiment": {
                                    "type": "string",
                                    "description": "The article overall sentiment.",
                                    "enum": ["POSITIVE", "NEUTRAL", "NEGATIVE"],
                                },
                                "confident_score": {
                                    "type": "number",
                                    "description": "A confident score about the overall sentiment guess.",
                                    "minimum": 0.0,
                                    "maximum": 1.0,
                                },
                                "factuel_checker": {
                                    "type": "boolean",
                                    "description": "Check if the article is factuel.",
                                },
                                "theme": {
                                    "type": "string",
                                    "description": "The principal theme of the overall sentiment.",
                                    "enum": [
                                        "aleas climatiques",
                                        "client",
                                        "divers",
                                        "greves",
                                        "innovation",
                                        "linky",
                                        "marque employeur/rh",
                                        "mobilite electrique",
                                        "partenariats industriels/academiques",
                                        "prevention",
                                        "raccordement",
                                        "reseau",
                                        "rh",
                                        "rh/partenariat/rse",
                                        "rse",
                                        "transition ecologique",
                                    ],
                                },
                            },
                            "required": [
                                "overall_sentiment",
                                "confident_score",
                                "factuel_checker",
                                "theme",
                            ],
                        }
                    },
                }
            }
        ]
        return tool_list

    def __parse_response__(self, response):
        response_message = response["output"]["message"]
        response_content_blocks = response_message["content"]
        content_block = next(
            (block for block in response_content_blocks if "toolUse" in block), None
        )
        tool_use_block = content_block["toolUse"]
        tool_result_dict = tool_use_block["input"]
        tool_result_dict["sentiment"] = tool_result_dict.pop("overall_sentiment")
        tool_result_dict["factuel"] = tool_result_dict.pop("factuel_checker")
        return tool_result_dict

    def __factuel_treshold__(self, output):
        if output["sentiment"] == "NEUTRAL":
            output["nuance"] = False
        else:
            if output["confident_score"] > 0.5:
                output["nuance"] = False
            else:
                output["nuance"] = True
        output.pop("confident_score")
        return output


class Helper:
    def __init__(self, rds):
        self.rds = rds

    def merge_dict(self, article, classifications):
        return article | classifications

    def send_to_SQL(self, dict_output):
        database = self.__database_information__()
        db = pymysql.connect(
            host=database["ENDPOINT"],
            user=database["USER"],
            password=database["PASSWORD"],
            port=database["PORT"],
            database=database["DBNAME"],
        )
        table_name = os.environ.get("RDS_TABLE_NAME")
        columns = ", ".join(dict_output.keys())
        placeholders = ", ".join(["%s"] * len(dict_output))
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        try:
            cursor = db.cursor()
            cursor.execute(sql, tuple(dict_output.values()))
            db.commit()
            print("Data sent to SQL successfully.")
        except Exception as e:
            print("Error sending data to SQL:", e)
            db.rollback()
        finally:
            cursor.close()
            db.close()

    def __database_information__(self):
        return {
            "ENDPOINT": os.environ.get("RDS_ENDPOINT"),
            "USER": os.environ.get("RDS_USER"),
            "PORT": int(os.environ.get("RDS_PORT")),
            "PASSWORD": os.environ.get("RDS_PASSWORD"),
            "DBNAME": os.environ.get("RDS_DBNAME"),
        }


def lambda_handler(event, context):
    article = event["Records"][0]["body"]
    # article = json.loads(article)
    aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")

    try:
        labelisation = TextLabelisation(
            aws_access_key_id, aws_secret_access_key, "mistral.mistral-large-2402-v1:0"
        )
        print("LLM model used: ", labelisation.__model__())
        output = labelisation.forward(article)
    except ClientError as e:
        print("Error during the labelisation process: ", e)
        return {
            "status": 500,
        }

    try:
        helper = Helper(labelisation.rds)
        merged_dict = helper.merge_dict(article, output)
    except Exception as e:
        print("Error during merging the article data and the LLM classification: ", e)
        return {
            "status": 500,
        }

    try:
        helper.send_to_SQL(merged_dict)
    except Exception as e:
        print("Error during the data sending process to SQL: ", e)
        return {
            "status": 500,
        }

    try:
        url = os.environ.get("API_URL")
        requests.post(url)
    except Exception as e:
        print("Error during POST: ", e)
        return {
            "status": 500,
        }

    return {
        "status": 200,
    }
