import os
import json
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

JOBS_FILE = "jobs.json"
SENT_JOBS_FILE = "sent_jobs.json"
OUTPUT_FOLDER = "generated_cards"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def get_source_colors(source_name):
    source_lower = source_name.lower()

    if "matrix" in source_lower:
        return {
            "background": (243, 247, 255),
            "header": (32, 91, 214),
            "accent": (73, 130, 255),
            "text": (28, 28, 35)
        }

    return {
        "background": (247, 250, 242),
        "header": (116, 173, 57),
        "accent": (173, 214, 96),
        "text": (28, 28, 35)
    }

def safe_filename(text):
    cleaned = "".join(c for c in text if c.isalnum() or c in (" ", "_", "-")).strip()
    cleaned = cleaned.replace(" ", "_")
    return cleaned[:50] if cleaned else "job_card"

def wrap_title(title, width=28):
    return textwrap.wrap(title, width=width)

def create_job_card(job):
    width = 1200
    height = 630

    colors = get_source_colors(job["company"])

    image = Image.new("RGB", (width, height), colors["background"])
    draw = ImageDraw.Draw(image)

    title_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()
    small_font = ImageFont.load_default()
    big_font = ImageFont.load_default()

    draw.rectangle([(0, 0), (width, 120)], fill=colors["header"])
    draw.rectangle([(0, height - 24), (width, height)], fill=colors["accent"])

    draw.text((50, 40), "Job Hunter By Ori", fill=(255, 255, 255), font=big_font)
    draw.text((50, 85), f"Source: {job['company']}", fill=(255, 255, 255), font=small_font)

    draw.rounded_rectangle([(60, 170), (1140, 560)], radius=28, fill=(255, 255, 255), outline=colors["accent"], width=4)

    title_lines = wrap_title(job["title"], width=30)
    y = 220
    for line in title_lines[:3]:
        draw.text((100, y), line, fill=colors["text"], font=title_font)
        y += 36

    info_y = 380
    draw.text((100, info_y), f"Location: {job['location']}", fill=colors["text"], font=subtitle_font)
    draw.text((100, info_y + 45), f"Salary: {job.get('salary', 'Not specified')}", fill=colors["text"], font=subtitle_font)
    draw.text((100, info_y + 90), f"Match Score: {job['score']}", fill=colors["text"], font=subtitle_font)

    draw.rounded_rectangle([(860, 395), (1080, 485)], radius=20, fill=colors["header"])
    draw.text((920, 430), job["company"], fill=(255, 255, 255), font=small_font)

    file_name = safe_filename(f"{job['company']}_{job['id']}") + ".png"
    file_path = os.path.join(OUTPUT_FOLDER, file_name)
    image.save(file_path)

    return file_path

with open(JOBS_FILE, "r", encoding="utf-8") as file:
    jobs = json.load(file)

with open(SENT_JOBS_FILE, "r", encoding="utf-8") as file:
    sent_jobs = json.load(file)

new_jobs = []

for job in jobs:
    if job["id"] not in sent_jobs:
        new_jobs.append(job)

if new_jobs:
    send_photo_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

    for job in new_jobs:
        image_path = create_job_card(job)

        caption = f"""🚀 נמצאה משרה חדשה

🎯 תפקיד: {job['title']}
🏢 חברה: {job['company']}
📍 מיקום: {job['location']}
💰 שכר: {job.get('salary', 'טווח השכר לא מצוין')}
📊 ציון התאמה: {job['score']}

🔗 <a href="{job['link']}">לצפייה במשרה</a>"""

        with open(image_path, "rb") as photo_file:
            response = requests.post(
                send_photo_url,
                data={
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": "HTML"
                },
                files={"photo": photo_file}
            )

        print("Status code:", response.status_code)
        print("Response:", response.text)

        sent_jobs.append(job["id"])

    with open(SENT_JOBS_FILE, "w", encoding="utf-8") as file:
        json.dump(sent_jobs, file, ensure_ascii=False, indent=2)

else:
    print("No new jobs to send.")
