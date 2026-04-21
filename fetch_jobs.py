import json

jobs = [
    {
        "id": "job_1",
        "title": "Junior Product Manager",
        "company": "Example Tech",
        "location": "Tel Aviv, Israel",
        "score": "88/100",
        "reasons": [
            "תפקיד ג'וניור",
            "משלב מוצר, דאטה ועבודה מול צוותים",
            "רלוונטי למסלול הקריירה שלך"
        ],
        "link": "https://example.com/job-posting-1"
    },
    {
        "id": "job_2",
        "title": "Product Operations Analyst",
        "company": "DataFlow Labs",
        "location": "Herzliya, Israel",
        "score": "84/100",
        "reasons": [
            "משלב אופרציה, אנליזה ותהליכים",
            "מתאים לפרופיל כניסה חזק",
            "קרוב לעולמות מוצר ודאטה"
        ],
        "link": "https://example.com/job-posting-2"
    },
    {
        "id": "job_3",
        "title": "Business Analyst",
        "company": "Insight Works",
        "location": "Ramat Gan, Israel",
        "score": "81/100",
        "reasons": [
            "תפקיד כניסה רלוונטי",
            "כולל ניתוח נתונים ותהליכים",
            "מתאים למסלול משיק למוצר"
        ],
        "link": "https://example.com/job-posting-3"
    },
    {
        "id": "job_4",
        "title": "Junior Data Analyst",
        "company": "Metric Pulse",
        "location": "Petah Tikva, Israel",
        "score": "86/100",
        "reasons": [
            "תפקיד ג'וניור רלוונטי",
            "כולל עבודה עם דאטה וניתוח נתונים",
            "מתאים למסלול קריירה משיק למוצר ואנליזה"
        ],
        "link": "https://example.com/job-posting-4"
    }
]

with open("jobs.json", "w", encoding="utf-8") as file:
    json.dump(jobs, file, ensure_ascii=False, indent=2)

print("jobs.json created successfully")
