import json
import requests
from bs4 import BeautifulSoup

SEARCHES = [
    "Product Manager",
    "Junior Product Manager",
    "Business Analyst",
    "Data Analyst",
    "Product Operations"
]

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

    return unique_bonus + length_bonus

def final_score(title, description):
    score = score_title(title)
    score += score_description(description)
    score += add_variation(title, description)

    if score > 97:
        score = 97

    if score < 35:
        score = 35

    return f"{score}/100"

def build_job_id(title, link):
    base = (title.strip().lower() + "|" + link.strip().lower())
    return str(abs(hash(base)))[:12]

all_jobs = []
seen_ids = set()

for search in SEARCHES:
    search_url = f"https://www.jobmaster.co.il/jobs/?q={search.replace(' ', '+')}"

    response = requests.get(search_url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for link in soup.find_all("a"):
        title = link.get_text(" ", strip=True)
        href = link.get("href")

        if not title:
            continue

        if len(title) < 8:
            continue

        full_link = href if href else search_url
        if href and href.startswith("/"):
            full_link = "https://www.jobmaster.co.il" + href

        title_lower = title.lower()
        if not any(word in title_lower for word in ["product", "manager", "business", "analyst", "data", "operations"]):
            continue

        parent = link.parent
        card_text = parent.get_text(" ", strip=True) if parent else ""

        job_id = build_job_id(title, full_link)
        if job_id in seen_ids:
            continue

        seen_ids.add(job_id)

        score = final_score(title, card_text)

        job = {
            "id": job_id,
            "title": title,
            "company": "JobMaster listing",
            "location": "Israel",
            "score": score,
            "reasons": [],
            "link": full_link
        }

        all_jobs.append(job)

all_jobs = sorted(
    all_jobs,
    key=lambda job: int(job["score"].split("/")[0]),
    reverse=True
)

all_jobs = all_jobs[:15]

with open("jobs.json", "w", encoding="utf-8") as file:
    json.dump(all_jobs, file, ensure_ascii=False, indent=2)

print(f"jobs.json created successfully with {len(all_jobs)} jobs")
