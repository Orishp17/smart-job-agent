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
    "חיפה": "חיפה",
    "haifa": "חיפה",
    "באר שבע": "באר שבע",
    "beer sheva": "באר שבע",
    "be'er sheva": "באר שבע",
    "ירושלים": "ירושלים",
    "jerusalem": "ירושלים"
}

SHARON_CITIES = {
    "כפר סבא", "רעננה", "הוד השרון", "הרצליה", "נתניה"
}

GUSH_DAN_CITIES = {
    "תל אביב", "רמת גן", "גבעתיים", "בני ברק", "פתח תקווה",
    "חולון", "בת ים", "ראשון לציון", "אור יהודה", "יהוד"
}

ARAB_CITY_KEYWORDS = [
    "אום אל-פחם", "אום אל פחם", "umm al-fahm",
    "נצרת", "nazareth",
    "טייבה", "tayibe", "taybeh",
    "טירה", "tira",
    "סכנין", "sakhnin",
    "שפרעם", "shefa-'amr", "shefa amr", "shfaram",
    "רהט", "rahat",
    "כפר קאסם", "kafr qasim", "kfar qasem",
    "קלנסווה", "qalansawe", "kalansewa",
    "באקה אל-גרבייה", "באקה אל גרבייה", "baqa al-gharbiyye",
    "עראבה", "arraba",
    "מג'ד אל-כרום", "majd al-kurum",
    "טמרה", "tamra"
]

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

def is_blocked_location(location, text):
    text_lower = text.lower()

    if location == "ירושלים":
        return True

    for keyword in ARAB_CITY_KEYWORDS:
        if keyword.lower() in text_lower:
            return True

    return False

def extract_salary(text):
    normalized = text.replace(",", "")
    normalized = normalized.replace("₪", " ")
    normalized = normalized.replace("שח", " ")
    normalized = normalized.replace("ש\"ח", " ")
    normalized = normalized.replace("ש׳ח", " ")

    range_patterns = [
        r'(\d{4,6})\s*[-–]\s*(\d{4,6})',
        r'בין\s*(\d{4,6})\s*ל\s*(\d{4,6})'
    ]

    for pattern in range_patterns:
        match = re.search(pattern, normalized)
        if match:
            min_salary = int(match.group(1))
            max_salary = int(match.group(2))
            return {
                "text": f"{min_salary:,} - {max_salary:,} ₪",
                "min": min_salary,
                "max": max_salary
            }

    single_patterns = [
        r'עד\s*(\d{4,6})',
        r'(\d{4,6})\s*₪'
    ]

    for pattern in single_patterns:
        match = re.search(pattern, normalized)
        if match:
            amount = int(match.group(1))
            return {
                "text": f"{amount:,} ₪",
                "min": amount,
                "max": amount
            }

    return {
        "text": "טווח השכר לא מצוין",
        "min": None,
        "max": None
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
        "insights": 4
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
    elif "mid level" in text_lower or "mid-level" in text_lower or "midlevel" in text_lower:
        score -= 6
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
    if location in {"כפר סבא", "רעננה"}:
        return 14
    if location in SHARON_CITIES:
        return 10
    if location in GUSH_DAN_CITIES or location in {"גוש דן", "אזור השרון"}:
        return 6
    if location == "ישראל":
        return 0
    return -6

def score_salary(salary_info):
    if salary_info["max"] is None:
        return 0
    if salary_info["max"] > 14000:
        return 10
    if salary_info["max"] >= 10000:
        return 0
    return -10

def score_seniority(title, text):
    combined = (title + " " + text).lower()
    score = 0

    junior_terms = ["junior", "entry level", "entry-level", "entry", "graduate", "graduate program", "associate", "trainee"]
    mid_terms = ["mid level", "mid-level", "midlevel"]
    senior_terms = ["senior", "sr.", "sr ", "lead", "director", "vp", "head", "principal", "chief"]

    if any(term in combined for term in junior_terms):
        score += 12

    if any(term in combined for term in mid_terms):
        score -= 6

    if any(term in combined for term in senior_terms):
        score -= 18

    return score

def add_variation(title, description):
    combined = (title + " " + description).lower()
    unique_bonus = len(set(combined.split())) % 7
    length_bonus = min(len(combined) // 120, 4)
    return unique_bonus + length_bonus

def final_score(title, description, location, salary_info):
    score = score_title(title)
    score += score_description(description)
    score += score_experience(description)
    score += score_degree(description)
    score += score_location(location)
    score += score_salary(salary_info)
    score += score_seniority(title, description)
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

        location = extract_location(card_text)

        if is_blocked_location(location, card_text):
            continue

        salary_info = extract_salary(card_text)

        job_id = build_job_id(title, full_link)
        if job_id in seen_ids:
            continue

        seen_ids.add(job_id)

        score = final_score(title, card_text, location, salary_info)

        job = {
            "id": job_id,
            "title": title,
            "company": "JobMaster listing",
            "location": location,
            "salary": salary_info["text"],
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

