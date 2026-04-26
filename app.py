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

CARD_WIDTH = 1080
CARD_HEIGHT = 1350

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
    return job.get("source") or job.get("company") or "Unknown"


def get_company_name(job):
    source_name = get_source_name(job)
    company_name = (
        job.get("company_name")
        or job.get("actual_company")
        or job.get("employer")
        or ""
    )

    if company_name and company_name.strip().lower() != source_name.strip().lower():
        return company_name.strip()

    return ""


def get_location(job):
    return job.get("location") or "ישראל"


def get_salary(job):
    return job.get("salary") or "טווח השכר לא מצוין"


def get_score(job):
    return job.get("score") or "0/100"


def get_score_number(score_text):
    try:
        return int(str(score_text).split("/")[0].strip())
    except Exception:
        return 0


def get_theme_by_source(source_name):
    source_lower = source_name.lower()

    if "matrix" in source_lower:
        return {
            "bg_top": (72, 96, 220),
            "bg_bottom": (126, 92, 255),
            "accent": (84, 204, 255),
            "pill": (255, 255, 255, 70),
            "card": (255, 255, 255),
            "text": (22, 28, 45),
            "muted": (95, 103, 125),
            "soft_box": (244, 247, 255),
            "score_box": (239, 248, 255),
            "button": (82, 122, 255),
        }

    return {
        "bg_top": (255, 126, 95),
        "bg_bottom": (254, 180, 123),
        "accent": (255, 255, 255),
        "pill": (255, 255, 255, 70),
        "card": (255, 255, 255),
        "text": (36, 31, 32),
        "muted": (112, 105, 105),
        "soft_box": (255, 246, 241),
        "score_box": (255, 244, 232),
        "button": (225, 91, 54),
    }


def get_font(size, bold=False):
    if bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/Arialbd.ttf",
            "/Library/Fonts/Arial Bold.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
        ]

    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


FONT_BRAND = get_font(28, bold=True)
FONT_BADGE = get_font(26, bold=True)
FONT_TITLE = get_font(62, bold=True)
FONT_SUBTITLE = get_font(24, bold=False)
FONT_LABEL = get_font(24, bold=True)
FONT_VALUE = get_font(31, bold=False)
FONT_VALUE_SMALL = get_font(28, bold=False)
FONT_SCORE_BIG = get_font(74, bold=True)
FONT_SCORE_SMALL = get_font(26, bold=True)
FONT_FOOTER = get_font(24, bold=False)


def create_gradient_background(width, height, top_color, bottom_color):
    background = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(background)

    for y in range(height):
        ratio = y / float(height)
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    return background


def add_background_shapes(image, theme):
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    draw.ellipse((-120, 70, 260, 450), fill=(255, 255, 255, 28))
    draw.ellipse((760, 60, 1160, 430), fill=(255, 255, 255, 24))
    draw.ellipse((820, 980, 1240, 1400), fill=(255, 255, 255, 24))
    draw.ellipse((-130, 1060, 250, 1430), fill=(255, 255, 255, 20))

    for x in range(70, 1000, 190):
        draw.rounded_rectangle((x, 1080, x + 90, 1100), radius=10, fill=(255, 255, 255, 18))

    return Image.alpha_composite(image, overlay)


def draw_shadowed_rounded_rectangle(base_image, box, radius=36, fill=(255, 255, 255), shadow_alpha=55):
    shadow_layer = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    x1, y1, x2, y2 = box
    shadow_box = (x1 + 10, y1 + 16, x2 + 10, y2 + 16)
    shadow_draw.rounded_rectangle(shadow_box, radius=radius, fill=(0, 0, 0, shadow_alpha))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(18))

    combined = Image.alpha_composite(base_image, shadow_layer)

    card_layer = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_layer)
    card_draw.rounded_rectangle(box, radius=radius, fill=fill)

    combined = Image.alpha_composite(combined, card_layer)
    return combined


def draw_pill(draw, xy, text, font, fill, text_fill):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=(y2 - y1) // 2, fill=fill)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = x1 + ((x2 - x1) - tw) / 2
    ty = y1 + ((y2 - y1) - th) / 2 - 2
    draw.text((tx, ty), text, font=font, fill=text_fill)


def fit_text_to_width(draw, text, font, max_width, max_lines):
    words = text.split()
    if not words:
        return [""]

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

    trimmed = lines[:max_lines]
    last_line = trimmed[-1]

    while True:
        candidate = last_line + "..."
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width:
            trimmed[-1] = candidate
            break

        parts = last_line.split()
        if len(parts) <= 1:
            trimmed[-1] = candidate
            break

        last_line = " ".join(parts[:-1])

    return trimmed


def draw_info_box(draw, x, y, w, h, label, value, theme, value_font=None):
    if value_font is None:
        value_font = FONT_VALUE

    draw.rounded_rectangle((x, y, x + w, y + h), radius=28, fill=theme["soft_box"])

    draw.text((x + 26, y + 18), label, font=FONT_LABEL, fill=theme["muted"])

    value_lines = fit_text_to_width(draw, value, value_font, w - 52, 2)
    current_y = y + 58

    for line in value_lines:
        draw.text((x + 26, current_y), line, font=value_font, fill=theme["text"])
        current_y += 36


def create_job_card(job):
    source_name = get_source_name(job)
    company_name = get_company_name(job)
    location = get_location(job)
    salary = get_salary(job)
    score_text = get_score(job)
    score_number = get_score_number(score_text)
    title = job.get("title", "Untitled Job")

    theme = get_theme_by_source(source_name)

    image = create_gradient_background(CARD_WIDTH, CARD_HEIGHT, theme["bg_top"], theme["bg_bottom"])
    image = add_background_shapes(image, theme)

    card_box = (54, 95, CARD_WIDTH - 54, CARD_HEIGHT - 80)
    image = draw_shadowed_rounded_rectangle(
        image,
        card_box,
        radius=44,
        fill=(255, 255, 255, 255),
        shadow_alpha=58
    )

    draw = ImageDraw.Draw(image)

    draw.text((88, 125), "Job Hunter By Ori", font=FONT_BRAND, fill=(255, 255, 255, 235))
    draw.text((88, 160), "Fresh job alert", font=FONT_SUBTITLE, fill=(255, 255, 255, 215))

    draw_pill(
        draw,
        (88, 210, 265, 262),
        "NEW JOB",
        FONT_BADGE,
        (255, 255, 255, 230),
        theme["button"]
    )

    source_pill_width = 220
    draw_pill(
        draw,
        (CARD_WIDTH - 88 - source_pill_width, 210, CARD_WIDTH - 88, 262),
        source_name,
        FONT_BADGE,
        (255, 255, 255, 235),
        theme["button"]
    )

    content_left = 95
    content_right = CARD_WIDTH - 95
    content_width = content_right - content_left

    title_lines = fit_text_to_width(draw, title, FONT_TITLE, content_width - 40, 3)

    title_y = 335
    for line in title_lines:
        draw.text((content_left, title_y), line, font=FONT_TITLE, fill=theme["text"])
        title_y += 76

    if company_name:
        draw.text(
            (content_left, title_y + 10),
            company_name,
            font=FONT_VALUE_SMALL,
            fill=theme["muted"]
        )
        info_top = title_y + 85
    else:
        info_top = title_y + 55

    score_box = (CARD_WIDTH - 300, 330, CARD_WIDTH - 110, 520)
    draw.rounded_rectangle(score_box, radius=36, fill=theme["score_box"])

    draw.text((score_box[0] + 32, score_box[1] + 24), "Match score", font=FONT_SCORE_SMALL, fill=theme["muted"])
    draw.text((score_box[0] + 32, score_box[1] + 72), str(score_number), font=FONT_SCORE_BIG, fill=theme["button"])
    draw.text((score_box[0] + 120, score_box[1] + 108), "/100", font=FONT_SCORE_SMALL, fill=theme["muted"])

    box_gap = 22
    box_width = int((content_width - box_gap) / 2)
    box_height = 140

    first_row_y = info_top
    second_row_y = info_top + box_height + box_gap

    draw_info_box(draw, content_left, first_row_y, box_width, box_height, "Source", source_name, theme)
    draw_info_box(draw, content_left + box_width + box_gap, first_row_y, box_width, box_height, "Location", location, theme)
    draw_info_box(draw, content_left, second_row_y, box_width, box_height, "Salary", salary, theme, value_font=FONT_VALUE_SMALL)
    draw_info_box(draw, content_left + box_width + box_gap, second_row_y, box_width, box_height, "Open in Telegram", "Use the button below", theme, value_font=FONT_VALUE_SMALL)

    divider_y = second_row_y + box_height + 50
    draw.line((content_left, divider_y, content_right, divider_y), fill=(233, 233, 239), width=3)

    footer_text = "Clean card • Big title • Easy to read"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=FONT_FOOTER)
    footer_width = footer_bbox[2] - footer_bbox[0]
    draw.text(
        ((CARD_WIDTH - footer_width) / 2, divider_y + 32),
        footer_text,
        font=FONT_FOOTER,
        fill=theme["muted"]
    )

    file_name = f"{job.get('id', 'job')}.jpg"
    file_path = os.path.join(OUTPUT_DIR, file_name)

    image = image.convert("RGB")
    image.save(file_path, format="JPEG", quality=95, optimize=True)

    return file_path


def send_job_photo(job, image_path):
    source_name = get_source_name(job)
    location = get_location(job)
    salary = get_salary(job)
    score_text = get_score(job)
    title = job.get("title", "Untitled Job")
    job_link = job.get("link", "")

    caption_lines = [
        "נמצאה משרה חדשה 🚀",
        "",
        f"תפקיד: {title}",
        f"מקור: {source_name}",
        f"מיקום: {location}",
        f"שכר: {salary}",
        f"ציון התאמה: {score_text}",
    ]

    caption = "\n".join(caption_lines)

    payload = {
        "chat_id": CHAT_ID,
        "caption": caption,
        "reply_markup": json.dumps({
            "inline_keyboard": [
                [
                    {
                        "text": "לצפייה במשרה",
                        "url": job_link
                    }
                ]
            ]
        })
    }

    send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    with open(image_path, "rb") as photo_file:
        response = requests.post(
            send_url,
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
            sent_successfully = send_job_photo(job, image_path)

            if sent_successfully:
                updated_sent_jobs.append(job.get("id"))

        except Exception as error:
            print(f"Error while sending job {job.get('id')}: {error}")

    save_json_file(SENT_JOBS_FILE, updated_sent_jobs)


if __name__ == "__main__":
    main()
