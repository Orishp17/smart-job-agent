import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

SEARCHES = [
    "Product Manager",
    "Junior Product Manager",
    "Business Analyst",
    "Data Analyst",
    "Product Operations"
]

JOBMASTER_HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MATRIX_JOBS_URL = "https://www.matrix.co.il/jobs/"
MATRIX_HEADERS = {
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
    "jerusalem": "ירושלים",
    "לוד": "לוד",
    "lod": "לוד"
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

RELEVANT_WORDS = ["product", "manager", "business", "analyst", "data", "operations"]

BLOCKED_TITLE_KEYWORDS = ["senior", "lead", "director", "vp", "head", "principal", "chief"]
BLOCKED_DESCRIPTION_KEYWORDS = [
    "5+ years", "7+ years", "10+ years",
    "senior", "director", "vp", "head of", "leadership"
]


def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_matrix_title(title):
    title = clean_text(title)

    separators = ["|", "•"]
    for sep in separators:
        if sep in title:
            title = title.split(sep)[0].strip()

    title = re.sub(r"\bמשרה\s*מס['\"]?\s*\d+\b", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\bjob\s*id[:\s-]*\d+\b", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\([^)]*\)", "", title)
    title = re.sub(r"\s{2,}", " ", title).strip(" -")

    prefixes = [
        "דרוש/ה",
        "דרושים/ות",
        "למטריקס דרוש/ה",
        "למטריקס דרושים/ות"
    ]

    for prefix in prefixes:
        if title.startswith(prefix):
            title = title[len(prefix):].strip(" -")

    normalized_candidates = [
        ("junior product manager", "Junior Product Manager"),
        ("product manager", "Product Manager"),
        ("business analyst", "Business Analyst"),
        ("data analyst", "Data Analyst"),
        ("bi analyst", "BI Analyst"),
        ("product operations", "Product Operations"),
        ("operations analyst", "Operations Analyst"),
        ("business operations", "Business Operations"),
        ("program manager", "Program Manager"),
    ]

    title_lower = title.lower()
    for raw, normalized in normalized_candidates:
        if raw in title_lower:
            return normalized

    return title


def extract_location(text):
    text_lower = (text or "").lower()

    for keyword, city_hebrew in CITY_KEYWORDS.items():
        if keyword in text_lower:
            return city_hebrew

    if "שרון" in (text or "") or "hasharon" in text_lower:
        return "אזור השרון"

    if "גוש דן" in (text or "") or "gush dan" in text_lower:
        return "גוש דן"

    return "ישראל"


def is_blocked_location(location, text):
    text_lower = (text or "").lower()

    if location == "ירושלים":
        return True

    for keyword in ARAB_CITY_KEYWORDS:
        if keyword.lower() in text_lower:
            return True

    return False


def extract_salary(text):
    text = text or ""
    normalized = text.replace(",", "")
    normalized = normalized.replace("₪", " ")
    normalized = normalized.replace("שח", " ")
    normalized = normalized.replace('ש"ח', " ")
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
    text_lower = (text or "").lower()
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
    text = text or ""
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
    text_lower = (text or "").lower()
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
    combined = (title + " " + (text or "")).lower()
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
    combined = (title + " " + (description or "")).lower()
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


def build_job_id(source, title, link):
    base = f"{source}|{title.strip().lower()}|{link.strip().lower()}"
    return str(abs(hash(base)))[:12]


def is_relevant_title(title):
    title_lower = title.lower()
    return any(word in title_lower for word in RELEVANT_WORDS)


def is_blocked(title, text):
    title_lower = title.lower()
    text_lower = (text or "").lower()

    if any(word in title_lower for word in BLOCKED_TITLE_KEYWORDS):
        return True

    if any(word in text_lower for word in BLOCKED_DESCRIPTION_KEYWORDS):
        return True

    return False


def fetch_jobmaster_jobs():
    jobs = []
    seen_ids = set()

    for search in SEARCHES:
        search_url = f"https://www.jobmaster.co.il/jobs/?q={search.replace(' ', '+')}"
        response = requests.get(search_url, headers=JOBMASTER_HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a", href=True):
            title = clean_text(link.get_text(" ", strip=True))
            href = link.get("href", "")

            if not title or len(title) < 8:
                continue

            full_link = urljoin("https://www.jobmaster.co.il/", href)
            parent = link.parent
            card_text = clean_text(parent.get_text(" ", strip=True) if parent else "")

            if not is_relevant_title(title):
                continue

            if is_blocked(title, card_text):
                continue

            location = extract_location(card_text)
            if is_blocked_location(location, card_text):
                continue

            salary_info = extract_salary(card_text)

            job_id = build_job_id("JobMaster", title, full_link)
            if job_id in seen_ids:
                continue

            seen_ids.add(job_id)

            jobs.append({
                "id": job_id,
                "title": title,
                "company": "JobMaster",
                "source": "JobMaster",
                "location": location,
                "salary": salary_info["text"],
                "score": final_score(title, card_text, location, salary_info),
                "link": full_link
            })

    return jobs


def extract_matrix_category_links(soup):
    category_links = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full_link = urljoin(MATRIX_JOBS_URL, href)

        if "/jobs/%D7%9E%D7%A9%D7%A8%D7%95%D7%AA/" not in full_link and "/jobs/משרות/" not in full_link:
            continue

        if full_link in seen:
            continue

        seen.add(full_link)
        category_links.append(full_link)

    return category_links


def extract_matrix_job_links_from_category(soup):
    job_links = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full_link = urljoin(MATRIX_JOBS_URL, href)

        if "/jobs/%D7%9E%D7%A9%D7%A8%D7%94/" not in full_link and "/jobs/משרה/" not in full_link:
            continue

        if full_link in seen:
            continue

        seen.add(full_link)
        job_links.append(full_link)

    return job_links


def fetch_matrix_jobs():
    jobs = []
    seen_ids = set()

    response = requests.get(MATRIX_JOBS_URL, headers=MATRIX_HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    category_links = extract_matrix_category_links(soup)

    all_job_links = []
    seen_job_links = set()

    for category_link in category_links:
        try:
            category_response = requests.get(category_link, headers=MATRIX_HEADERS, timeout=30)
            category_response.raise_for_status()
            category_soup = BeautifulSoup(category_response.text, "html.parser")
        except Exception:
            continue

        job_links = extract_matrix_job_links_from_category(category_soup)

        for job_link in job_links:
            if job_link in seen_job_links:
                continue
            seen_job_links.add(job_link)
            all_job_links.append(job_link)

    for full_link in all_job_links:
        try:
            details_response = requests.get(full_link, headers=MATRIX_HEADERS, timeout=30)
            details_response.raise_for_status()
            details_soup = BeautifulSoup(details_response.text, "html.parser")
        except Exception:
            continue

        details_text = clean_text(details_soup.get_text(" ", strip=True))

        title = ""
        h1 = details_soup.find("h1")
        if h1:
            title = clean_text(h1.get_text(" ", strip=True))

        if not title and details_soup.title and details_soup.title.string:
            title = clean_text(details_soup.title.string)

        title = normalize_matrix_title(title)

        if not title or len(title) < 8:
            continue

        if not is_relevant_title(title):
            continue

        if is_blocked(title, details_text):
            continue

        location = extract_location(details_text)
        if is_blocked_location(location, details_text):
            continue

        salary_info = extract_salary(details_text)

        job_id = build_job_id("Matrix", title, full_link)
        if job_id in seen_ids:
            continue

        seen_ids.add(job_id)

        jobs.append({
            "id": job_id,
            "title": title,
            "company": "Matrix",
            "source": "Matrix",
            "location": location,
            "salary": salary_info["text"],
            "score": final_score(title, details_text, location, salary_info),
            "link": full_link
        })

    return jobs


def main():
    all_jobs = []
    all_jobs.extend(fetch_jobmaster_jobs())
    all_jobs.extend(fetch_matrix_jobs())

    unique_jobs = {}
    for job in all_jobs:
        unique_jobs[job["id"]] = job

    final_jobs = list(unique_jobs.values())
    final_jobs = sorted(
        final_jobs,
        key=lambda job: int(job["score"].split("/")[0]),
        reverse=True
    )

    final_jobs = final_jobs[:20]

    with open("jobs.json", "w", encoding="utf-8") as file:
        json.dump(final_jobs, file, ensure_ascii=False, indent=2)

    print(f"jobs.json created successfully with {len(final_jobs)} jobs")


if __name__ == "__main__":
    main()
