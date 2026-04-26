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
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    for job in new_jobs:
        salary_text = job.get("salary", "טווח השכר לא מצוין")

        message = f"""🚀 נמצאה משרה חדשה

🎯 תפקיד: {job['title']}
🏢 חברה: {job['company']}
📍 מיקום: {job['location']}
💰 שכר: {salary_text}
📊 ציון התאמה: {job['score']}

🔗 לינק להגשה:
{job['link']}"""

        payload = {
            "chat_id": chat_id,
            "text": message
        }

        response = requests.post(url, data=payload)

        print("Status code:", response.status_code)
        print("Response:", response.text)

        sent_jobs.append(job["id"])

    with open("sent_jobs.json", "w", encoding="utf-8") as file:
        json.dump(sent_jobs, file, ensure_ascii=False, indent=2)

else:
    print("No new jobs to send.")

