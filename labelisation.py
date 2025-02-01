import json
import boto3 #API AWS 
from botocore.exceptions import ClientError


session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name="us-west-2"
)
bedrock = session.client(service_name="bedrock-runtime")

model_id = "mistral.mistral-large-2402-v1:0" # model ID from Amazon AWS

content = """
Dear Acme Investments,

I am writing to compliment one of your customer service representatives, Shirley Scarry. I recently had the pleasure of speaking with Shirley regarding my account deposit. Shirley was extremely helpful and knowledgeable, and went above and beyond to ensure that all of my questions were answered. Shirley also had Robert Herbford join the call, who wasn't quite as helpful. My wife, Clara Bradford, didn't like him at all.
Shirley's professionalism and expertise were greatly appreciated, and I would be happy to recommend Acme Investments to others based on my experience.
Sincerely,

Carson Bradford
"""

messages = []

message = {
    "role": "user",
    "content": [
        { "text": f"You have to use the sentiment_checker tool to classify the sentiment on the content within the <content> tags.\n\n <content>{content}</content>" }
    ],
}

messages.append(message)

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
                    },
                    "required": [
                        "overall_sentiment",
                    ]
                }
            }
        }
    }
]

response = bedrock.converse(
	modelId=model_id,
	messages=messages,
	inferenceConfig={
        "maxTokens": 512,
        "temperature": 0,
	},
    toolConfig=
    {
        "tools": tool_list,
        "toolChoice":{"any": {}}
    }
)


response_message = response['output']['message']

response_content_blocks = response_message['content']

content_block = next((block for block in response_content_blocks if 'toolUse' in block), None)

tool_use_block = content_block['toolUse']

tool_result_dict = tool_use_block['input']

print(json.dumps(tool_result_dict, indent=4))