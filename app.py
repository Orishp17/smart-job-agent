import os
import json
import requests

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

with open("jobs.json", "r", encoding="utf-8") as file:
    jobs = json.load(file)

with open("sent_jobs.json", "r", encoding="utf-8") as file:
    sent_jobs = json.load(file)

new_jobs = []

for job in jobs:
    if job["id"] not in sent_jobs:
        new_jobs.append(job)

if new_jobs:
    message = "🚀 נמצאו משרות חדשות\n\n"

    for i, job in enumerate(new_jobs, start=1):
        message += f"{i}. {job['title']}\n"
        message += f"🏢 חברה: {job['company']}\n"
        message += f"📍 מיקום: {job['location']}\n"
        message += f"📊 ציון התאמה: {job['score']}\n"
        message += "למה זה מתאים:\n"

        for reason in job["reasons"]:
            message += f"• {reason}\n"

        message += f"🔗 לינק:\n{job['link']}\n"

        if i < len(new_jobs):
            message += "\n--------------------\n\n"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    response = requests.post(url, data=payload)

    print("Status code:", response.status_code)
    print("Response:", response.text)

    for job in new_jobs:
        sent_jobs.append(job["id"])

    with open("sent_jobs.json", "w", encoding="utf-8") as file:
        json.dump(sent_jobs, file, ensure_ascii=False, indent=2)

else:
    print("No new jobs to send.")
