import asyncio
import json
import os
from pathlib import Path

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, InputFile

BASE_DIR = Path(__file__).resolve().parent

JOBS_FILE = BASE_DIR / "jobs.json"
SENT_FILE = BASE_DIR / "sent_jobs.json"
APPLIED_FILE = BASE_DIR / "applied_jobs.json"
OFFSET_FILE = BASE_DIR / "telegram_update_offset.json"

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
        "👇 לחץ על הכפתורים למטה כדי לצפות במשרה או לסמן שכבר הגשת קו״ח"
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
            "👇 לחץ על הכפתורים למטה כדי לצפות במשרה או לסמן שכבר הגשת קו״ח"
        )

    return caption


def build_keyboard(job):
    job_id = get_job_id(job)
    link = clean_text(job.get("link"), "")

    buttons = []

    if link:
        buttons.append([InlineKeyboardButton("🔎 לצפייה במשרה", url=link)])

    if job_id:
        buttons.append([InlineKeyboardButton("✅ הגשתי קו״ח", callback_data=f"applied:{job_id}")])

    return InlineKeyboardMarkup(buttons) if buttons else None


def build_applied_keyboard(job_link):
    buttons = []

    if job_link:
        buttons.append([InlineKeyboardButton("🔎 לצפייה במשרה", url=job_link)])

    buttons.append([InlineKeyboardButton("✅ סומן שכבר הגשת קו״ח", callback_data="already_applied")])

    return InlineKeyboardMarkup(buttons)


async def process_applied_callbacks(bot):
    applied_jobs = load_json(APPLIED_FILE, [])
    sent_jobs = load_json(SENT_FILE, [])
    offset_data = load_json(OFFSET_FILE, {"offset": None})

    if not isinstance(applied_jobs, list):
        applied_jobs = []

    if not isinstance(sent_jobs, list):
        sent_jobs = []

    applied_set = set(str(item) for item in applied_jobs)
    sent_set = set(str(item) for item in sent_jobs)

    offset = offset_data.get("offset")

    try:
        updates = await bot.get_updates(
            offset=offset,
            timeout=5,
            allowed_updates=["callback_query"]
        )
    except Exception as error:
        print(f"Could not get Telegram updates: {error}")
        return applied_set

    max_update_id = None
    changed = False

    for update in updates:
        max_update_id = update.update_id

        query = update.callback_query
        if not query:
            continue

        data = query.data or ""

        if data == "already_applied":
            try:
                await query.answer("המשרה כבר סומנה כהוגשה")
            except Exception:
                pass
            continue

        if not data.startswith("applied:"):
            continue

        job_id = data.replace("applied:", "").strip()

        if not job_id:
            continue

        applied_set.add(job_id)
        sent_set.add(job_id)
        changed = True

        try:
            await query.answer("סומן שהגשת קו״ח. המשרה לא תישלח שוב.")
        except Exception:
            pass

        try:
            message = query.message
            if message:
                current_markup = message.reply_markup
                job_link = ""

                if current_markup and current_markup.inline_keyboard:
                    for row in current_markup.inline_keyboard:
                        for button in row:
                            if button.url:
                                job_link = button.url
                                break
                        if job_link:
                            break

                await bot.edit_message_reply_markup(
                    chat_id=message.chat_id,
                    message_id=message.message_id,
                    reply_markup=build_applied_keyboard(job_link)
                )
        except Exception as error:
            print(f"Could not edit message markup: {error}")

    if max_update_id is not None:
        save_json(OFFSET_FILE, {"offset": max_update_id + 1})

    if changed:
        save_json(APPLIED_FILE, sorted(applied_set))
        save_json(SENT_FILE, sorted(sent_set))
        print(f"applied_jobs.json updated with {len(applied_set)} job IDs.")

    return applied_set


async def send_job(bot, chat_id, job):
    source = get_source(job)
    image_path = get_source_image(source)
    caption = build_caption(job)
    reply_markup = build_keyboard(job)
    link = clean_text(job.get("link"), "")

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

    bot = Bot(token=token)

    applied_set = await process_applied_callbacks(bot)

    jobs = load_json(JOBS_FILE, [])
    sent_jobs = load_json(SENT_FILE, [])
    applied_jobs = load_json(APPLIED_FILE, [])

    if not isinstance(jobs, list):
        jobs = []

    if not isinstance(sent_jobs, list):
        sent_jobs = []

    if not isinstance(applied_jobs, list):
        applied_jobs = []

    sent_set = set(str(item) for item in sent_jobs)
    applied_set = set(str(item) for item in applied_jobs) | applied_set

    jobs_to_send = []

    for job in jobs:
        job_id = get_job_id(job)

        if not job_id:
            continue

        if job_id in sent_set:
            continue

        if job_id in applied_set:
            continue

        jobs_to_send.append(job)

    if not jobs_to_send:
        print("No new jobs to send.")
        return

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
