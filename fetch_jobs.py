import json
import re
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

CITY_KEYWORDS = {
    "כפר סבא": "כפר סבא",
    "kfar saba": "כפר סבא",
    "רעננה": "רעננה",
    "raanana": "רעננה",
    "ra'anana": "רעננה",
    "תל אביב": "תל אביב",
    "tel aviv": "תל אביב",
    "רמת גן": "רמת גן",
    "ramat gan": "רמת גן",
    "הרצליה": "הרצליה",
    "herzliya": "הרצליה",
    "פתח תקווה": "פתח תקווה",
    "petah tikva": "פתח תקווה",
    "petach tikva": "פתח תקווה",
    "הוד השרון": "הוד השרון",
    "hod hasharon": "הוד השרון",
    "נתניה": "נתניה",
    "netanya": "נתניה",
    "ראשון לציון": "ראשון לציון",
    "rishon lezion": "ראשון לציון",
    "חולון": "חולון",
    "holon": "חולון",
    "בת ים": "בת ים",
    "bat yam": "בת ים",
    "בני ברק": "בני ברק",
    "bnei brak": "בני ברק",
    "גבעתיים": "גבעתיים",
    "givatayim": "גבעתיים",
    "אור יהודה": "אור יהודה",
    "or yehuda": "אור יהודה",
    "יהוד": "יהוד",
    "yehud": "יהוד",
    "אשדוד": "אשדוד",
    "ashdod": "אשדוד",
    "אשקלון": "אשקלון",
    "ashkelon": "אשקלון",
    "ירושלים": "ירושלים",
    "jerusalem": "ירושלים",
    "חיפה": "חיפה",
    "haifa": "חיפה",
    "באר שבע": "באר שבע",
    "beer sheva": "באר שבע",
    "be'er sheva": "באר שבע"
}

SHARON_CITIES = {
    "כפר סבא", "רעננה", "הוד השרון", "הרצליה", "נתניה"
}

GUSH_DAN_CITIES = {
    "תל אביב", "רמת גן", "גבעתיים", "בני ברק", "פתח תקווה",
    "חולון", "בת ים", "ראשון לציון", "אור יהודה", "יהוד"
}

def extract_location(text):
    text_lower = text.lower()

    for keyword, city_hebrew in CITY_KEYWORDS.items():
        if keyword in text_lower:
            return city_hebrew

    if "שרון" in text or "hasharon" in text_lower:
        return "אזור השרון"

    if "גוש דן" in text or "gush dan" in text_lower:
        return "גוש דן"

    return "ישראל"

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
        "junior": 8
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

def score_experience(text):
    text_lower = text.lower()
    score = 0

    if "0 שנות" in text or "0 years" in text_lower or "0-1" in text_lower:
        score += 14
    elif "0-2" in text_lower or "0 עד 2" in text or "עד 2 שנות" in text:
        score += 12
    elif "1-2" in text_lower or "1 עד 2" in text or "1-2 שנות" in text:
        score += 9
    elif "2-3" in text_lower or "2 עד 3" in text or "2-3 שנות" in text:
        score += 5
    elif "3+ years" in text_lower or "3 שנות" in text:
        score -= 8
    elif "4+ years" in text_lower or "4 שנות" in text:
        score -= 12
    elif "5+ years" in text_lower or "5 שנות" in text:
        score -= 16

    return score

def score_degree(text):
    text_lower = text.lower()
    score = 0

    if "bsc" in text_lower or "b.sc" in text_lower or "b.sc." in text_lower:
        score -= 6

    if "ba" in text_lower or "b.a" in text_lower or "b.a." in text_lower:
        score += 2

    return score

def score_location(location):
    score = 0

    if location in {"כפר סבא", "רעננה"}:
        score += 14
    elif location in SHARON_CITIES:
        score += 10
    elif location in GUSH_DAN_CITIES or location in {"גוש דן", "אזור השרון"}:
        score += 6
    elif location == "ישראל":
        score += 0
    else:
        score -= 6

    return score

def add_variation(title, description):
    combined = (title + " " + description).lower()
    unique_bonus = len(set(combined.split())) % 7
    length_bonus = min(len(combined) // 120, 4)
    return unique_bonus + length_bonus

def final_score(title, description, location):
    score = score_title(title)
    score += score_description(description)
    score += score_experience(description)
    score += score_degree(description)
    score += score_location(location)
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

        parent = link.parent
        card_text = parent.get_text(" ", strip=True) if parent else ""

        title_lower = title.lower()
        card_text_lower = card_text.lower()

        if not any(word in title_lower for word in ["product", "manager", "business", "analyst", "data", "operations"]):
            continue

        blocked_title_keywords = ["senior", "lead", "director", "vp", "head", "principal", "chief"]
        blocked_description_keywords = ["5+ years", "7+ years", "10+ years", "senior", "director", "vp", "head of", "leadership"]

        if any(word in title_lower for word in blocked_title_keywords):
            continue

        if any(word in card_text_lower for word in blocked_description_keywords):
            continue

        job_id = build_job_id(title, full_link)
        if job_id in seen_ids:
            continue

        seen_ids.add(job_id)

        location = extract_location(card_text)
        score = final_score(title, card_text, location)

        job = {
            "id": job_id,
            "title": title,
            "company": "JobMaster listing",
            "location": location,
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
