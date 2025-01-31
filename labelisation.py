import json
import boto3 #API AWS 


session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name="us-west-2"
)
bedrock = session.client(service_name="bedrock-runtime")

model_id = "mistral.mistral-large-2402-v1:0" # model ID from Amazon AWS

messages_list = []

text = "Blablabla" # Edenis text
initial_message = {
	"role":"user",
	"content": [
		{"text": text}
	],
}

messages_list.append(initial_message)

response = bedrock.converse(
	modelId=model_id,
	messages=messages_list,
	inferenceConfig={
		"stopSequences": [ "POSITIF", "NEGATIF" ],
		"maxTokens": 512,
		"temperature": 0.5,
		"topP": 0.9,
	},
	system=[{"text":"You are a NLP expert with a PhD. Signal 'POSITIF' if you think that the sentiment analyse is positif, otherwise 'NEGATIF'."}]
)


print(response)
# out = response["additionalModelResponseFields"]["stop_sequence"] #surement pas ça mais équivalent