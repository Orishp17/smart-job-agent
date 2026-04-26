import asyncio
import json
import os
from pathlib import Path

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, InputFile

BASE_DIR = Path(__file__).resolve().parent
JOBS_FILE = BASE_DIR / "jobs.json"
SENT_FILE = BASE_DIR / "sent_jobs.json"
ASSETS_DIR = BASE_DIR / "assets"

JOBMASTER_IMAGE = ASSETS_DIR / "jobmaster_logo.png"
MATRIX_IMAGE = ASSETS_DIR / "matrix_logo.png"

MAX_JOBS_PER_RUN = 20


def load_json(file_path, default_value):
    if not file_path.exists():
        return default_value

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default_value


def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def clean_text(value, default="לא צוין"):
    if value is None:
        return default

    text = str(value).strip()
    if not text:
        return default

    return text


def get_job_id(job):
    return clean_text(job.get("id"), "")


def get_source(job):
    source = clean_text(job.get("source"), "")
    company = clean_text(job.get("company"), "")

    combined = f"{source} {company}".lower()

    if "matrix" in combined or "מטריקס" in combined:
        return "Matrix"

    return "JobMaster"


def get_source_image(source):
    if source == "Matrix":
        return MATRIX_IMAGE
    return JOBMASTER_IMAGE


def build_caption(job):
    title = clean_text(job.get("title"), "ללא כותרת")
    company = clean_text(job.get("company"), "לא צוין")
    location = clean_text(job.get("location"), "ישראל")
    salary = clean_text(job.get("salary"), "טווח השכר לא מצוין")
    score = clean_text(job.get("score"), "לא צוין")
    source = get_source(job)

    caption = (
        "🚀 נמצאה משרה חדשה\n\n"
        f"🎯 תפקיד: {title}\n"
        f"🏢 חברה: {company}\n"
        f"📍 מיקום: {location}\n"
        f"💰 שכר: {salary}\n"
        f"📊 ציון התאמה: {score}\n"
        f"🌐 מקור: {source}\n\n"
        "👇 לחץ על הכפתור למטה כדי לצפות במשרה"
    )

    if len(caption) > 1024:
        short_title = title[:120] + "..." if len(title) > 120 else title
        short_company = company[:80] + "..." if len(company) > 80 else company

        caption = (
            "🚀 נמצאה משרה חדשה\n\n"
            f"🎯 תפקיד: {short_title}\n"
            f"🏢 חברה: {short_company}\n"
            f"📍 מיקום: {location}\n"
            f"💰 שכר: {salary}\n"
            f"📊 ציון התאמה: {score}\n"
            f"🌐 מקור: {source}\n\n"
            "👇 לחץ על הכפתור למטה כדי לצפות במשרה"
        )

    return caption


async def send_job(bot, chat_id, job):
    source = get_source(job)
    image_path = get_source_image(source)
    caption = build_caption(job)
    link = clean_text(job.get("link"), "")

    buttons = []
    if link:
        buttons.append([InlineKeyboardButton("לצפייה במשרה", url=link)])

    reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

    if image_path.exists():
        try:
            with open(image_path, "rb") as photo_file:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=InputFile(photo_file),
                    caption=caption,
                    reply_markup=reply_markup,
                )
            return True
        except Exception as error:
            print(f"Error sending photo for job {job.get('id')}: {error}")

    try:
        fallback_text = caption
        if link:
            fallback_text += f"\n\n🔗 קישור: {link}"

        await bot.send_message(
            chat_id=chat_id,
            text=fallback_text,
            reply_markup=reply_markup
        )
        return True
    except Exception as error:
        print(f"Error sending text fallback for job {job.get('id')}: {error}")
        return False


async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")

    jobs = load_json(JOBS_FILE, [])
    sent_jobs = load_json(SENT_FILE, [])

    if not isinstance(jobs, list):
        jobs = []

    if not isinstance(sent_jobs, list):
        sent_jobs = []

    sent_set = set(str(item) for item in sent_jobs)
    jobs_to_send = []

    for job in jobs:
        job_id = get_job_id(job)
        if not job_id:
            continue
        if job_id in sent_set:
            continue
        jobs_to_send.append(job)

    if not jobs_to_send:
        print("No new jobs to send.")
        return

    bot = Bot(token=token)
    sent_any = False

    for job in jobs_to_send[:MAX_JOBS_PER_RUN]:
        was_sent = await send_job(bot, chat_id, job)

        if was_sent:
            job_id = get_job_id(job)
            sent_set.add(job_id)
            sent_any = True

    if sent_any:
        save_json(SENT_FILE, sorted(sent_set))
        print(f"Done. sent_jobs.json updated with {len(sent_set)} job IDs.")
    else:
        print("No jobs were sent successfully.")


if __name__ == "__main__":
    asyncio.run(main())
