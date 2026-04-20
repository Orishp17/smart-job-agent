import os
import requests

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

jobs = [
    {
        "title": "Junior Product Manager",
        "company": "Example Tech",
        "location": "Tel Aviv, Israel",
        "score": "88/100",
        "reasons": [
            "תפקיד ג'וניור",
            "משלב מוצר, דאטה ועבודה מול צוותים",
            "רלוונטי למסלול הקריירה שלך"
        ],
        "link": "https://example.com/job-posting-1"
    },
    {
        "title": "Product Operations Analyst",
        "company": "DataFlow Labs",
        "location": "Herzliya, Israel",
        "score": "84/100",
        "reasons": [
            "משלב אופרציה, אנליזה ותהליכים",
            "מתאים לפרופיל כניסה חזק",
            "קרוב לעולמות מוצר ודאטה"
        ],
        "link": "https://example.com/job-posting-2"
    }
]

message = "🚀 נמצאו משרות חדשות\n\n"

for i, job in enumerate(jobs, start=1):
    message += f"{i}. {job['title']}\n"
    message += f"🏢 חברה: {job['company']}\n"
    message += f"📍 מיקום: {job['location']}\n"
    message += f"📊 ציון התאמה: {job['score']}\n"
    message += "למה זה מתאים:\n"

    for reason in job["reasons"]:
        message += f"• {reason}\n"

    message += f"🔗 לינק:\n{job['link']}\n"

    if i < len(jobs):
        message += "\n--------------------\n\n"

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

payload = {
    "chat_id": chat_id,
    "text": message
}

response = requests.post(url, data=payload)

print("Status code:", response.status_code)
print("Response:", response.text)



