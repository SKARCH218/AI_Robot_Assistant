import requests
from apikey import GEMINI_API_KEY

class GeminiClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def send_message(self, prompt):
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        params = {"key": self.api_key}
        response = requests.post(self.base_url, headers=headers, json=data, params=params)
        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"Error: {response.status_code} {response.text}"

if __name__ == "__main__":
    client = GeminiClient(GEMINI_API_KEY)
    prompt = "DOFBOT을 어떻게 움직일 수 있나요?"
    print(client.send_message(prompt))
