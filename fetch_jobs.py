import json
import requests
from bs4 import BeautifulSoup

SEARCH_URL = "https://www.jobmaster.co.il/jobs/?q=Product+Manager"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def calculate_score(title):
    score = 50
    title_lower = title.lower()

    positive_keywords = {
        "product": 15,
        "manager": 15,
        "junior": 20,
        "data": 10,
        "analyst": 10,
        "operations": 8
    }

    negative_keywords = {
        "senior": -25,
        "lead": -20,
        "director": -30,
        "vp": -40,
        "head": -25
    }

    for keyword, points in positive_keywords.items():
        if keyword in title_lower:
            score += points

    for keyword, points in negative_keywords.items():
        if keyword in title_lower:
            score += points

    if score > 100:
        score = 100

    if score < 0:
        score = 0

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

    score = calculate_score(title)

    job = {
        "id": f"jobmaster_{len(jobs) + 1}",
        "title": title,
        "company": "JobMaster listing",
        "location": "Israel",
        "score": score,
        "reasons": [
            "נשלף אוטומטית מ-JobMaster",
            "רלוונטי לחיפוש Product Manager",
            "מועמד לבדיקה ראשונית"
        ],
        "link": full_link
    }

    jobs.append(job)

    if len(jobs) >= 5:
        break

with open("jobs.json", "w", encoding="utf-8") as file:
    json.dump(jobs, file, ensure_ascii=False, indent=2)

print(f"jobs.json created successfully with {len(jobs)} jobs")
