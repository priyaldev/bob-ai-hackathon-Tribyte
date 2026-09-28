import os
from dotenv import load_dotenv

load_dotenv()

from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

url = os.getenv("WATSONX_URL")
api_key = os.getenv("WATSONX_API_KEY")
model_id = os.getenv("WATSONX_MODEL_ID")
project_id = os.getenv("WATSONX_PROJECT_ID")

print("=" * 60)
print("TESTING SAME WATSONX CONFIGURATION")
print("=" * 60)

print("URL:", url)
print("MODEL:", model_id)
print("PROJECT:", project_id)
print("API KEY PRESENT:", bool(api_key))
print("API KEY LENGTH:", len(api_key) if api_key else 0)

try:
    credentials = Credentials(
        url=url,
        api_key=api_key,
    )

    print("\nCredentials object created successfully.")

    model = ModelInference(
        model_id=model_id,
        credentials=credentials,
        project_id=project_id,
    )

    print("ModelInference object created successfully.")

    response = model.chat(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Return only the word: TEST"},
        ],
        params={
            "max_new_tokens": 20,
            "temperature": 0.0,
        },
    )

    text = response["choices"][0]["message"]["content"]
    print("\nMODEL RESPONSE:")
    print(repr(text))

except Exception as e:
    print("\nERROR:")
    print(type(e).__name__)
    print(str(e))

print("=" * 60)