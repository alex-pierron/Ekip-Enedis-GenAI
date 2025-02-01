import json
import boto3 #API AWS 
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv('.env')

class TextLabelisation:
    def __init__(self, aws_access_key_id, aws_secret_access_key, model_id):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name="us-west-2"
        )
        self.bedrock = self.session.client(service_name="bedrock-runtime")
        self.model_id = model_id #"mistral.mistral-large-2402-v1:0"
    
    def __model__(self):
        return self.model_id
    
    def forward(self, article):
        messages = [
            {
                "role": "user",
                "content": [
                    { "text": f"You have to use the sentiment_checker tool to classify the sentiment on the content within the <article> tags.\n\n {self.__create_content__(article)}" }
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
        toolConfig=
        {
            "tools": self.__getTool__(),
            "toolChoice":{"any": {}}
        }
    )
        
        output = self.__parse_response__(response)
        return output


    def __create_content__(self, article):
        date = article["date"]
        territory = article["territory"]
        title = article["title"]
        media = article["media"]
        content = article["content"]

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
                                    "enum": ['aleas climatiques', 'client', 'divers', 'greves', 'innovation', 'linky', 'marque employeur/rh', 'mobilite electrique', 'partenariats industriels/academiques', 'prevention', 'raccordement', 'reseau', 'rh', 'rh/partenariat/rse', 'rse', 'transition ecologique']
                                },
                            },
                            "required": [
                                "overall_sentiment",
                                "confident_score",
                                "factuel_checker",
                                "theme",
                            ]
                        }
                    }
                }
            }
        ]
        return tool_list
    
    def __parse_response__(self, response):
        response_message = response['output']['message']
        response_content_blocks = response_message['content']
        content_block = next((block for block in response_content_blocks if 'toolUse' in block), None)
        tool_use_block = content_block['toolUse']
        tool_result_dict = tool_use_block['input']
        return tool_result_dict

    





fake_article = {
    "date": "2022-01-01",
    "territory": "France",
    "title": "Un nouveau projet de loi sur la transition écologique",
    "media": "Le Monde",
    "content": "Le gouvernement a annoncé un nouveau projet de loi sur la transition écologique. Ce projet de loi vise à réduire les émissions de gaz à effet de serre et à promouvoir les énergies renouvelables. Il prévoit également des mesures pour lutter contre la pollution de l'air et de l'eau. Le projet de loi a été salué par les associations environnementales, qui le jugent ambitieux et nécessaire pour atteindre les objectifs de l'accord de Paris sur le climat."
}

aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
try:
    labelisation = TextLabelisation(aws_access_key_id, aws_secret_access_key, "mistral.mistral-large-2402-v1:0")
    print("LLM model used: ", labelisation.__model__())
    output = labelisation.forward(fake_article)
    print(output)
except ClientError as e:
    print("Error during the labelisation process: ", e)







