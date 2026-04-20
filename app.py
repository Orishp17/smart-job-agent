import os
import requests

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

message = """🚀 נמצאה משרה חדשה

תפקיד: Junior Product Manager
חברה: Example Tech
מיקום: Tel Aviv, Israel
התאמה: 88/100

למה זה מתאים:
- תפקיד ג'וניור
- כולל עבודה עם מוצר ודאטה
- רלוונטי לפרופיל שלך

לינק:
https://example.com/job-posting
"""

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

payload = {
    "chat_id": chat_id,
    "text": message
}

response = requests.post(url, data=payload)

print("Status code:", response.status_code)
print("Response:", response.text)
