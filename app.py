import os
import requests

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

message = """🚀 Job Match Found

🎯 תפקיד: Junior Product Manager
🏢 חברה: Example Tech
📍 מיקום: Tel Aviv, Israel
📊 ציון התאמה: 88/100

למה זה מתאים לך:
• תפקיד ג'וניור
• משלב מוצר, דאטה ועבודה מול צוותים
• רלוונטי למסלול הקריירה שלך

🔗 לינק להגשה:
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
