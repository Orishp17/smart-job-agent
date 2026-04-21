import json
import requests
from bs4 import BeautifulSoup

SEARCH_URL = "https://www.jobmaster.co.il/jobs/?q=Product+Manager"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(SEARCH_URL, headers=headers, timeout=30)
response.raise_for_status()

html = response.text
soup = BeautifulSoup(html, "html.parser")

jobs = []

for i, line in enumerate(html.splitlines()):
    if "פורסם לפני" in line and i > 0:
        title = html.splitlines()[i - 1].strip()
        posted = line.strip()

        job = {
            "id": f"jobmaster_pm_{i}",
            "title": title,
            "company": "JobMaster listing",
            "location": "Israel",
            "score": "80/100",
            "reasons": [
                "נשלף אוטומטית מ-JobMaster",
                "רלוונטי לחיפוש Product Manager",
                "מועמד לבדיקה ראשונית"
            ],
            "link": SEARCH_URL,
            "posted": posted
        }

        jobs.append(job)

    if len(jobs) >= 5:
        break

with open("jobs.json", "w", encoding="utf-8") as file:
    json.dump(jobs, file, ensure_ascii=False, indent=2)

print(f"jobs.json created successfully with {len(jobs)} jobs")
