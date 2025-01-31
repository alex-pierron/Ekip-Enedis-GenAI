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

prompt = "I hate you so much, you are the worst person."

formatted_prompt = f"<s>[INST] {prompt} [/INST]"

classification_categories = ['positive', 'negatif']


native_request = {
    "prompt": formatted_prompt,
    "max_tokens": 512,
    "temperature": 0.5,
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "sentiment" : {
                    "type": "string",
                    "enum": classification_categories
                }
            },
        }
    },
}

request = json.dumps(native_request)


try:
    response = bedrock.invoke_model(modelId=model_id, body=request)

except (ClientError, Exception) as e:
    print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
    exit(1)

model_response = json.loads(response["body"].read())

response_text = model_response
print(response_text)