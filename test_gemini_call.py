import os
from google import genai

client = genai.Client(api_key='AIzaSyDdGVmZsT8_hJJVOXlo9MD5xqQvN6n8lPE')
print("Testing simple call to gemini-2.0-flash...")
try:
    resp = client.models.generate_content(model='gemini-2.0-flash', contents="Say hello")
    print("SUCCESS:", resp.text[:100])
except Exception as e:
    print("FAIL gemini-2.0-flash:", e)

print("\nTesting gemini-2.5-flash...")
try:
    resp = client.models.generate_content(model='models/gemini-2.5-flash', contents="Say hello")
    print("SUCCESS:", resp.text[:100])
except Exception as e:
    print("FAIL gemini-2.5-flash:", e)
