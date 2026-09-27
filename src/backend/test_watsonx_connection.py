import os
from dotenv import load_dotenv

load_dotenv()

print("USE_LLM:", os.getenv("USE_LLM"))
print("PROJECT_ID:", os.getenv("WATSONX_PROJECT_ID"))
print("URL:", os.getenv("WATSONX_URL"))
print("MODEL_ID:", os.getenv("WATSONX_MODEL_ID"))

api_key = os.getenv("WATSONX_API_KEY")

if api_key:
    print("API KEY: Found")
else:
    print("API KEY: NOT FOUND")