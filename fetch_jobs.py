import json
import requests
from bs4 import BeautifulSoup

SEARCH_URL = "https://www.jobmaster.co.il/jobs/?q=Product+Manager"

headers = {
    "User-Agent": "Mozilla/5.0"
}

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

    job = {
        "id": f"jobmaster_{len(jobs) + 1}",
        "title": title,
        "company": "JobMaster listing",
        "location": "Israel",
        "score": "80/100",
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
