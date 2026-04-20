import os
import requests

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

message = "שלום אורי - app.py רץ מתוך GitHub ושולח הודעה אמיתית דרך Python."

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

payload = {
    "chat_id": chat_id,
    "text": message
}

response = requests.post(url, data=payload)

print("Status code:", response.status_code)
print("Response:", response.text)
