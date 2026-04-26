import os
import json
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

JOBS_FILE = "jobs.json"
SENT_JOBS_FILE = "sent_jobs.json"
OUTPUT_DIR = "generated_cards"
ASSETS_DIR = "assets"

CARD_WIDTH = 1080
CARD_HEIGHT = 1080

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_json_file(path, default_value):
    if not os.path.exists(path):
        return default_value

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default_value


def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def get_source_name(job):
    raw_source = (job.get("source") or job.get("company") or "").strip().lower()

    if "matrix" in raw_source:
        return "Matrix"

    if "jobmaster" in raw_source:
        return "JobMaster"

    return "Unknown"


def get_location(job):
    location = (job.get("location") or "").strip()
    return location if location else "ישראל"


def get_salary(job):
    salary = (job.get("salary") or "").strip()
    return salary if salary else "טווח שכר לא מצוין"


def get_score(job):
    score = (job.get("score") or "").strip()
    return score if score else "0/100"


def get_score_number(score_text):
    try:
        return int(str(score_text).split("/")[0].strip())
    except Exception:
        return 0


def get_job_link(job):
    return (job.get("link") or "").strip()


def get_logo_path(source_name):
    if source_name == "JobMaster":
        return os.path.join(ASSETS_DIR, "jobmaster_logo.png")

    if source_name == "Matrix":
        return os.path.join(ASSETS_DIR, "matrix_logo.png")

    return None


def get_theme(source_name):
    if source_name == "Matrix":
        return {
            "bg_top": (236, 243, 255),
            "bg_bottom": (214, 229, 255),
            "main_card": (255, 255, 255),
            "primary": (53, 96, 222),
            "primary_soft": (228, 236, 255),
            "text": (24, 32, 48),
            "muted": (103, 113, 132),
            "line": (226, 232, 243),
            "score_bg": (236, 243, 255),
            "chip_bg": (230, 238, 255),
            "shadow": (0, 0, 0, 42),
        }

    return {
        "bg_top": (255, 246, 236),
        "bg_bottom": (255, 228, 198),
        "main_card": (255, 255, 255),
        "primary": (231, 104, 46),
        "primary_soft": (255, 236, 220),
        "text": (40, 32, 28),
        "muted": (120, 103, 92),
        "line": (243, 229, 217),
        "score_bg": (255, 244, 232),
        "chip_bg": (255, 240, 226),
        "shadow": (0, 0, 0, 42),
    }


def get_font(size, bold=False):
    candidates = []

    if bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/Library/Fonts/Arial Bold.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/Library/Fonts/Arial.ttf",
        ]

    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


FONT_KICKER = get_font(28, bold=True)
FONT_TITLE = get_font(60, bold=True)
FONT_LABEL = get_font(24, bold=True)
FONT_VALUE = get_font(32, bold=False)
FONT_VALUE_BOLD = get_font(32, bold=True)
FONT_SMALL = get_font(22, bold=False)
FONT_SMALL_BOLD = get_font(22, bold=True)
FONT_SCORE = get_font(72, bold=True)
FONT_SCORE_SMALL = get_font(26, bold=True)
FONT_BUTTON = get_font(30, bold=True)


def create_gradient_background(width, height, top_color, bottom_color):
    image = Image.new("RGB", (width, height), top_color)
    draw = ImageDraw.Draw(image)

    for y in range(height):
        ratio = y / float(height)
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    return image


def add_soft_background_shapes(image):
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    draw.ellipse((-120, -40, 320, 360), fill=(255, 255, 255, 45))
    draw.ellipse((770, 40, 1160, 390), fill=(255, 255, 255, 35))
    draw.ellipse((780, 820, 1180, 1180), fill=(255, 255, 255, 30))
    draw.ellipse((-90, 820, 220, 1110), fill=(255, 255, 255, 22))

    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def draw_shadow(base_image, box, radius, shadow_color):
    shadow_layer = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    x1, y1, x2, y2 = box
    shadow_draw.rounded_rectangle(
        (x1 + 8, y1 + 12, x2 + 8, y2 + 12),
        radius=radius,
        fill=shadow_color
    )

    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(18))
    result = Image.alpha_composite(base_image.convert("RGBA"), shadow_layer)
    return result.convert("RGB")


def fit_text_lines(draw, text, font, max_width, max_lines):
    if not text:
        return [""]

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = word if not current_line else current_line + " " + word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]

        if line_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    if len(lines) <= max_lines:
        return lines

    lines = lines[:max_lines]
    last_line = lines[-1]

    while True:
        candidate = last_line + "..."
        bbox = draw.textbbox((0, 0), candidate, font=font)
        line_width = bbox[2] - bbox[0]

        if line_width <= max_width or len(last_line.split()) <= 1:
            lines[-1] = candidate
            break

        last_line = " ".join(last_line.split()[:-1])

    return lines


def paste_logo(base_image, logo_path, x, y, max_width, max_height):
    if not logo_path or not os.path.exists(logo_path):
        return

    logo = Image.open(logo_path).convert("RGBA")
    width, height = logo.size

    scale = min(max_width / width, max_height / height)
    new_width = max(1, int(width * scale))
    new_height = max(1, int(height * scale))

    logo = logo.resize((new_width, new_height), Image.LANCZOS)
    base_image.paste(logo, (x, y), logo)


def draw_chip(draw, x, y, text, theme):
    padding_x = 22
    padding_y = 14

    bbox = draw.textbbox((0, 0), text, font=FONT_SMALL_BOLD)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    chip_width = text_width + padding_x * 2
    chip_height = text_height + padding_y * 2

    draw.rounded_rectangle(
        (x, y, x + chip_width, y + chip_height),
        radius=22,
        fill=theme["chip_bg"]
    )

    draw.text(
        (x + padding_x, y + padding_y - 2),
        text,
        font=FONT_SMALL_BOLD,
        fill=theme["primary"]
    )


def draw_info_box(draw, x, y, width, height, label, value, theme):
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=28,
        fill=theme["primary_soft"]
    )

    draw.text((x + 24, y + 18), label, font=FONT_LABEL, fill=theme["muted"])

    lines = fit_text_lines(draw, value, FONT_VALUE, width - 48, 2)
    current_y = y + 54

    for line in lines:
        draw.text((x + 24, current_y), line, font=FONT_VALUE, fill=theme["text"])
        current_y += 36


def create_job_card(job):
    source_name = get_source_name(job)
    location = get_location(job)
    salary = get_salary(job)
    score_text = get_score(job)
    score_number = get_score_number(score_text)
    title = (job.get("title") or "Untitled Job").strip()

    theme = get_theme(source_name)
    logo_path = get_logo_path(source_name)

    image = create_gradient_background(CARD_WIDTH, CARD_HEIGHT, theme["bg_top"], theme["bg_bottom"])
    image = add_soft_background_shapes(image)
    image = draw_shadow(image, (52, 58, CARD_WIDTH - 52, CARD_HEIGHT - 58), 42, theme["shadow"])

    draw = ImageDraw.Draw(image)

    main_box = (52, 58, CARD_WIDTH - 52, CARD_HEIGHT - 58)
    draw.rounded_rectangle(main_box, radius=42, fill=theme["main_card"])

    draw_chip(draw, 88, 92, "NEW JOB", theme)

    paste_logo(image, logo_path, CARD_WIDTH - 320, 92, 180, 70)

    title_lines = fit_text_lines(draw, title, FONT_TITLE, 760, 3)
    title_y = 220

    for line in title_lines:
        draw.text((88, title_y), line, font=FONT_TITLE, fill=theme["text"])
        title_y += 72

    draw.text((88, title_y + 8), source_name, font=FONT_VALUE_BOLD, fill=theme["primary"])

    score_box = (820, 238, 960, 388)
    draw.rounded_rectangle(score_box, radius=28, fill=theme["score_bg"])
    draw.text((848, 258), "Score", font=FONT_SCORE_SMALL, fill=theme["muted"])
    draw.text((846, 290), str(score_number), font=FONT_SCORE, fill=theme["primary"])

    info_y = 455
    box_gap = 22
    box_width = 430
    box_height = 140

    draw_info_box(draw, 88, info_y, box_width, box_height, "Location", location, theme)
    draw_info_box(draw, 562, info_y, box_width, box_height, "Salary", salary, theme)
    draw_info_box(draw, 88, info_y + box_height + box_gap, box_width, box_height, "Source", source_name, theme)
    draw_info_box(draw, 562, info_y + box_height + box_gap, box_width, box_height, "Match", score_text, theme)

    divider_y = 845
    draw.line((88, divider_y, CARD_WIDTH - 88, divider_y), fill=theme["line"], width=3)

    button_box = (88, 885, CARD_WIDTH - 88, 980)
    draw.rounded_rectangle(button_box, radius=28, fill=theme["primary"])

    button_text = "Open job from Telegram"
    bbox = draw.textbbox((0, 0), button_text, font=FONT_BUTTON)
    text_width = bbox[2] - bbox[0]
    text_x = (CARD_WIDTH - text_width) / 2
    draw.text((text_x, 915), button_text, font=FONT_BUTTON, fill=(255, 255, 255))

    footer_text = "Job Hunter By Ori"
    draw.text((88, 1010), footer_text, font=FONT_SMALL, fill=theme["muted"])

    file_name = f"{job.get('id', 'job')}.jpg"
    output_path = os.path.join(OUTPUT_DIR, file_name)
    image.save(output_path, format="JPEG", quality=95, optimize=True)

    return output_path


def send_job_photo(job, image_path):
    title = (job.get("title") or "Untitled Job").strip()
    source_name = get_source_name(job)
    location = get_location(job)
    salary = get_salary(job)
    score = get_score(job)
    link = get_job_link(job)

    caption = (
        f"נמצאה משרה חדשה 🚀\n\n"
        f"תפקיד: {title}\n"
        f"חברה: {source_name}\n"
        f"מיקום: {location}\n"
        f"שכר: {salary}\n"
        f"ציון התאמה: {score}"
    )

    payload = {
        "chat_id": CHAT_ID,
        "caption": caption,
        "reply_markup": json.dumps({
            "inline_keyboard": [
                [
                    {
                        "text": "לצפייה במשרה",
                        "url": link
                    }
                ]
            ]
        })
    }

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    with open(image_path, "rb") as photo_file:
        response = requests.post(
            url,
            data=payload,
            files={"photo": photo_file},
            timeout=60
        )

    print("Status code:", response.status_code)
    print("Response:", response.text)

    return response.ok


def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        return

    jobs = load_json_file(JOBS_FILE, [])
    sent_jobs = load_json_file(SENT_JOBS_FILE, [])

    if not isinstance(jobs, list):
        jobs = []

    if not isinstance(sent_jobs, list):
        sent_jobs = []

    new_jobs = [job for job in jobs if job.get("id") not in sent_jobs]

    if not new_jobs:
        print("No new jobs to send.")
        return

    updated_sent_jobs = list(sent_jobs)

    for job in new_jobs:
        try:
            image_path = create_job_card(job)
            success = send_job_photo(job, image_path)

            if success:
                updated_sent_jobs.append(job.get("id"))
        except Exception as error:
            print(f"Error sending job {job.get('id')}: {error}")

    save_json_file(SENT_JOBS_FILE, updated_sent_jobs)


if __name__ == "__main__":
    main()
