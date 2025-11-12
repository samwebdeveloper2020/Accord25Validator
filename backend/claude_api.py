import requests
import json
import os

def get_claude_token(token_file="claude_token.txt"):
    token_path = os.path.join(os.path.dirname(__file__), token_file)
    with open(token_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def call_claude_custom(prompt, conversation_name="My Chat"):
    print(prompt)

    url = "https://api.dev.env.apps.vertafore.com/shirley/v1/PLATFORM-ADMIN-WEB-UI/VERTAFORE/entities/VERTAFORE/conversations"
    token = get_claude_token()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "conversationName": conversation_name,
        "entityId": "VERTAFORE",
        "tenantId": "VERTAFORE",
        "useCaseName": "CHATBOT",
        "useCaseVersion": "0.0.1",
        "serviceProfileName": "CLAUDE-SONNET-3.5",
        "serviceProfileVersion": "0.0.1",
        "currentMessage": {
            "content": [
                {"text": prompt}
            ],
            "role": "user"
        },
        "serviceUseParameters": {}
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=60)
        # if response.status_code != 200:
        #     return f"Claude API error: {response.status_code} {response.text}"
        resp_json = response.json()
        return resp_json["content"]["currentMessage"]["content"][0]["text"]
    except Exception as e:
        return f"Claude API error: {e}\nRaw response: {getattr(response, 'text', '')}"
