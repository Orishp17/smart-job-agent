import os
import requests

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

message = """🚀 נמצאו משרות חדשות

1. Junior Product Manager
🏢 חברה: Example Tech
📍 מיקום: Tel Aviv, Israel
📊 ציון התאמה: 88/100
למה זה מתאים:
• תפקיד ג'וניור
• משלב מוצר, דאטה ועבודה מול צוותים
• רלוונטי למסלול הקריירה שלך
🔗 לינק:
https://example.com/job-posting-1

--------------------

2. Product Operations Analyst
🏢 חברה: DataFlow Labs
📍 מיקום: Herzliya, Israel
📊 ציון התאמה: 84/100
למה זה מתאים:
• משלב אופרציה, אנליזה ותהליכים
• מתאים לפרופיל כניסה חזק
• קרוב לעולמות מוצר ודאטה
🔗 לינק:
https://example.com/job-posting-2
"""

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

payload = {
    "chat_id": chat_id,
    "text": message
}

response = requests.post(url, data=payload)

print("Status code:", response.status_code)
print("Response:", response.text)
