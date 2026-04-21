import json
import requests
from bs4 import BeautifulSoup

SEARCH_URL = "https://www.jobmaster.co.il/jobs/?q=Product+Manager"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def score_title(title):
    title_lower = title.lower()
    score = 52

    positive_keywords = {
        "product": 11,
        "manager": 9,
        "data": 7,
        "analyst": 8,
        "business": 6,
        "operations": 6,
        "operation": 5,
        "junior": 16,
        "entry": 12,
        "associate": 7,
        "specialist": 5,
        "ai": 5,
        "strategy": 4
    }

    negative_keywords = {
        "senior": -20,
        "lead": -16,
        "director": -24,
        "vp": -30,
        "head": -22,
        "principal": -18,
        "chief": -26
    }

    for keyword, points in positive_keywords.items():
        if keyword in title_lower:
            score += points

    for keyword, points in negative_keywords.items():
        if keyword in title_lower:
            score += points

    if "product" in title_lower and "manager" in title_lower:
        score += 7

    if "data" in title_lower and "analyst" in title_lower:
        score += 7

    if "business" in title_lower and "operations" in title_lower:
        score += 6

    if "product" in title_lower and "data" in title_lower:
        score += 4

    junior_signals = ["junior", "entry", "associate", "specialist"]
    if not any(word in title_lower for word in junior_signals):
        score -= 5

    return score

def score_description(text):
    text_lower = text.lower()
    score = 0

    positive_keywords = {
        "sql": 6,
        "analytics": 6,
        "analysis": 5,
        "dashboard": 4,
        "data": 5,
        "product": 5,
        "stakeholders": 4,
        "cross-functional": 4,
        "process": 3,
        "operations": 4,
        "strategy": 3,
        "insights": 4,
        "entry": 6,
        "junior": 8,
        "1-2": 4,
        "0-2": 6,
        "1-3": 4
    }

    negative_keywords = {
        "senior": -10,
        "director": -12,
        "vp": -16,
        "leadership": -8,
        "5+ years": -12,
        "7+ years": -16,
        "10+ years": -20,
        "head of": -14
    }

    for keyword, points in positive_keywords.items():
        if keyword in text_lower:
            score += points

    for keyword, points in negative_keywords.items():
        if keyword in text_lower:
            score += points

    return score

def add_variation(title, description):
    combined = (title + " " + description).lower()

    unique_bonus = len(set(combined.split())) % 7
    length_bonus = min(len(combined) // 120, 4)

    variation = unique_bonus + length_bonus
    return variation

def final_score(title, description):
    score = score_title(title)
    score += score_description(description)
    score += add_variation(title, description)

    if score > 97:
        score = 97

    if score < 35:
        score = 35

    return f"{score}/100"

response = requests.get(SEARCH_URL, headers=headers, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

jobs = []
seen_titles = set()

for link in soup.find_all("a"):
    title = link.get_text(" ", strip=True)
    href = link.get("href")

    if not title:
        continue

    if len(title) < 8:
        continue

    if "Product" not in title and "Manager" not in title:
        continue

    if title in seen_titles:
        continue

    seen_titles.add(title)

    full_link = href if href else SEARCH_URL
    if href and href.startswith("/"):
        full_link = "https://www.jobmaster.co.il" + href

    card_text = ""
    parent = link.parent
    if parent:
        card_text = parent.get_text(" ", strip=True)

    score = final_score(title, card_text)

    job = {
        "id": f"jobmaster_{len(jobs) + 1}",
        "title": title,
        "company": "JobMaster listing",
        "location": "Israel",
        "score": score,
        "reasons": [
            "נשלף אוטומטית מ-JobMaster",
            "רלוונטי לחיפוש Product Manager",
            "ציון מבוסס על כותרת, תוכן ושונות"
        ],
        "link": full_link
    }

    jobs.append(job)

    if len(jobs) >= 5:
        break

with open("jobs.json", "w", encoding="utf-8") as file:
    json.dump(jobs, file, ensure_ascii=False, indent=2)

print(f"jobs.json created successfully with {len(jobs)} jobs")
