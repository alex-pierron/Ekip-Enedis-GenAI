import boto3
from location import get_department
import io
import json
from PyPDF2 import PdfReader


class PDFLabelisation:
    def __init__(self, aws_access_key_id, aws_secret_access_key, model_id, text=""):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.session = boto3.Session()
        self.bedrock = self.session.client(service_name="bedrock-runtime")
        self.model_id = model_id  # "mistral.mistral-large-2402-v1:0"
        self.text = text
        self.s3_client = boto3.client("s3")
        self.bucket = "s3-bucket-enedis"

    def __model__(self):
        return self.model_id

    def forward(self, path):
        response = self.s3_client.get_object(Bucket=self.bucket, Key=path)
        pdf_content = response["Body"].read()

        message = [
            {
                "role": "user",
                "content": [
                    {
                        "document": {
                            "name": "DocumentPDFmessages",
                            "format": "pdf",
                            "source": {"bytes": pdf_content},
                        }
                    },
                    {
                        "text": "Based on the document, given the key value usin the tool json_format"
                    },
                ],
            }
        ]

        response = self.bedrock.converse(
            modelId=self.model_id,
            messages=message,
            inferenceConfig={
                "maxTokens": 512,
                "temperature": 0,
            },
            toolConfig={
                "tools": self.__getTool__(),
            },
        )
        output = self.__parse_response__(response)

        return output

    def __getTool__(self):
        tool_list = [
            {
                "toolSpec": {
                    "name": "json_format",
                    "description": "Get the values of the article.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "date": {
                                    "type": "string",
                                    "description": "The article date. In the format YYYY-MM-DD.",
                                    "pattern": "^(\\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$",
                                },
                                "media": {
                                    "type": "string",
                                    "description": "You are an expert about french medias. Give the name of the media that wrote this article. Only answer with the name of the media and nothing else.",
                                },
                                "title": {
                                    "type": "string",
                                    "description": "You are an expert journalist. Give the title of this french press article. Be concise and very pragmatic.",
                                },
                                "location": {
                                    "type": "string",
                                    "description": "French Department where the story of the article is located.You are an expert in french geography and know exactly in which department is located each town and village. If the location is not in the list, give the nearest department. You have to give the most precise department as possible. You can only give back a location in the given list and no additionnal verbose.",
                                    "enum": [
                                        "Aisne",
                                        "Aube",
                                        "Calvados",
                                        "Cantal",
                                        "Eure-et-Loire",
                                        "Ille-et-Vilaine",
                                        "Jura",
                                        "Landes",
                                        "Loire",
                                        "Loiret",
                                        "Lot-et-Garonne",
                                        "Meuse",
                                        "Orne",
                                        "Pas-de-Calais",
                                        "Puy-de-Dôme",
                                        "Bas-Rhin",
                                        "Haut-Rhin",
                                        "Seine-Maritime",
                                        "Yonne",
                                        "Seine-Saint-Denis",
                                        "Alpes-de-Haute-Provence",
                                        "Hautes-Alpes",
                                        "Ardèche",
                                        "Ardennes",
                                        "Ariège",
                                        "Charente-Maritime",
                                        "Corrèze",
                                        "Dordogne",
                                        "Eure",
                                        "Indre-et-Loire",
                                        "Lozère",
                                        "Nièvre",
                                        "Oise",
                                        "Pyrénées-Atlantiques",
                                        "Rhône",
                                        "Saône-et-Loire",
                                        "Paris",
                                        "Yvelines",
                                        "Tarn",
                                        "Tarn-et-Garonne",
                                        "Var",
                                        "Vendée",
                                        "Haute-Vienne",
                                        "Vosges",
                                        "Hauts-de-Seine",
                                        "Allier",
                                        "Alpes-Maritimes",
                                        "Aude",
                                        "Corse-du-Sud",
                                        "Côtes-d'Armor",
                                        "Creuse",
                                        "Doubs",
                                        "Finistère",
                                        "Gard",
                                        "Gironde",
                                        "Indre",
                                        "Isère",
                                        "Marne",
                                        "Haute-Marne",
                                        "Moselle",
                                        "Hautes-Pyrénées",
                                        "Pyrénées-Orientales",
                                        "Savoie",
                                        "Haute-Savoie",
                                        "Seine-et-Marne",
                                        "Vaucluse",
                                        "Vienne",
                                        "Val-de-Marne",
                                        "Ain",
                                        "Aveyron",
                                        "Bouches-du-Rhône",
                                        "Charente",
                                        "Cher",
                                        "Haute-Corse",
                                        "Côte-d'Or",
                                        "Drôme",
                                        "Haute-Garonne",
                                        "Gers",
                                        "Hérault",
                                        "Haute-Loire",
                                        "Loire-Atlantique",
                                        "Lot",
                                        "Maine-et-Loire",
                                        "Manche",
                                        "Morbihan",
                                        "Nord",
                                        "Haute-Saône",
                                        "Sarthe",
                                        "Somme",
                                        "Essonne",
                                        "Val-d'Oise",
                                        "Loir-et-Cher",
                                        "Mayenne",
                                        "Meurthe-et-Moselle",
                                        "Deux-Sèvres",
                                        "Territoire de Belfort",
                                    ],
                                },
                            },
                            "required": ["date", "media", "title", "location"],
                        }
                    },
                }
            }
        ]
        return tool_list

    def format_anwser(self, tool_use_block):
        location = tool_use_block.get("location", "")
        if location != "":
            location = get_department(location)
        return json.dumps(
            {
                "body": {
                    "date": tool_use_block.get("date", ""),
                    "territoire": location,
                    "sujet": tool_use_block.get("title", ""),
                    "nb_articles": 1,
                    "media": tool_use_block.get("media", ""),
                    "article": self.text,
                }
            }
        )

    def __parse_response__(self, response):
        try:
            response_message = response.get("output", {}).get("message", {})
            response_content_blocks = response_message.get("content", [])
            # Find the first content block with 'toolUse'
            content_block = next(
                (block for block in response_content_blocks if "toolUse" in block), None
            )

            if not content_block:
                return {}  # Or return {} if you prefer an empty dict

            tool_use_block = content_block.get("toolUse", {}).get("input", {})

            return self.format_anwser(tool_use_block)

        except Exception as e:
            print(f"Error parsing response: {e}")
            return None  # Or handle the error in another way
