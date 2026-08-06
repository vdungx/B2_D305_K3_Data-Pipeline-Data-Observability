<<<<<<< Updated upstream
=======
from __future__ import annotations

import re
import time
>>>>>>> Stashed changes
from dataclasses import asdict, dataclass
from pathlib import Path
import re
import time

import requests

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json

<<<<<<< Updated upstream
=======
CROSSREF_API_URL = "https://api.crossref.org/works"
CONTACT_EMAIL = "bong888ag@gmail.com"
USER_AGENT = f"Day10-Data-Observability-Lab/1.0 (mailto:{CONTACT_EMAIL})"

_RETRY_STATUS_CODES = {429, 503}
_MAX_ATTEMPTS = 5
_INITIAL_BACKOFF_SECONDS = 1.0
_TAG_RE = re.compile(r"<[^>]+>")
>>>>>>> Stashed changes


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


<<<<<<< Updated upstream
def _clean_abstract(raw: str) -> str:
    if not raw:
        return ""
    cleaned = re.sub(r"<[^>]+>", "", raw)
    return normalize_whitespace(cleaned)


def _extract_date(item: dict) -> str:
    for date_key in ("published-print", "published-online", "created", "deposited"):
        date_obj = item.get(date_key, {})
        date_parts = date_obj.get("date-parts", [])
        if date_parts and date_parts[0]:
            parts = date_parts[0]
            year = parts[0] if len(parts) > 0 and parts[0] is not None else 2024
            month = parts[1] if len(parts) > 1 and parts[1] is not None else 1
            day = parts[2] if len(parts) > 2 and parts[2] is not None else 1
            return f"{year:04d}-{month:02d}-{day:02d}"
    return "2024-01-01"


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload into a list of PaperRecord objects."""
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        doi = item.get("DOI", "").strip()
        raw_title = item.get("title", [])
        if isinstance(raw_title, list):
            title = raw_title[0] if raw_title else ""
        else:
            title = str(raw_title)
        title = normalize_whitespace(re.sub(r"<[^>]+>", "", title))

        if not doi or not title:
            continue

        raw_abstract = item.get("abstract", "") or item.get("description", "")
        summary = _clean_abstract(raw_abstract)

        authors_list = item.get("author", [])
        authors: list[str] = []
        if isinstance(authors_list, list):
            for a in authors_list:
                given = a.get("given", "").strip()
                family = a.get("family", "").strip()
                name = f"{given} {family}".strip()
                if name:
                    authors.append(name)

        categories = item.get("subject", [])
        if not categories:
            container = item.get("container-title", [])
            if isinstance(container, list) and container:
                categories = [container[0]]
            else:
                categories = ["Computer Science"]

        primary_category = categories[0] if categories else "Computer Science"
        pub_date = _extract_date(item)
        updated_date = pub_date

        url = item.get("URL", f"https://doi.org/{doi}")
        pdf_url = ""
        for link in item.get("link", []):
            if isinstance(link, dict) and link.get("content-type") == "application/pdf":
                pdf_url = link.get("URL", "")
                break

        publisher = str(item.get("publisher", ""))

        record = PaperRecord(
            paper_id=doi,
            title=title,
            summary=summary,
            authors=authors,
            categories=categories,
            primary_category=primary_category,
            published=pub_date,
            updated=updated_date,
            abs_url=url,
            pdf_url=pdf_url,
            comment=publisher,
        )
        records.append(record)
=======
def _clean_abstract(raw_abstract: str | None) -> str:
    """Xoa the JATS/HTML (vd <jats:p>) va chuan hoa khoang trang."""
    if not raw_abstract:
        return ""
    return normalize_whitespace(_TAG_RE.sub(" ", raw_abstract))


def _extract_authors(item: dict) -> list[str]:
    authors: list[str] = []
    for author in item.get("author") or []:
        given = (author.get("given") or "").strip()
        family = (author.get("family") or "").strip()
        full_name = normalize_whitespace(f"{given} {family}")
        if full_name:
            authors.append(full_name)
    return authors


def _extract_categories(item: dict) -> list[str]:
    categories = [normalize_whitespace(c) for c in (item.get("subject") or []) if c]
    if not categories:
        categories = [normalize_whitespace(c) for c in (item.get("container-title") or []) if c]
    return categories


def _extract_date(item: dict) -> str:
    """Parse ngay xuat ban (uu tien published-print) ve dinh dang ISO YYYY-MM-DD."""
    for key in ("published-print", "published-online", "published", "issued", "created"):
        date_info = item.get(key)
        if not date_info:
            continue
        date_parts = date_info.get("date-parts")
        if not date_parts or not date_parts[0]:
            continue
        parts = date_parts[0]
        year = parts[0] if len(parts) > 0 else None
        if not year:
            continue
        month = parts[1] if len(parts) > 1 else 1
        day = parts[2] if len(parts) > 2 else 1
        try:
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        except (TypeError, ValueError):
            continue
    return ""


def _extract_pdf_url(item: dict) -> str:
    for link in item.get("link") or []:
        content_type = (link.get("content-type") or "").lower()
        url = link.get("URL") or ""
        if url and "pdf" in content_type:
            return url
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thanh list PaperRecord.

    1. Duyet `payload["message"]["items"]`.
    2. Lay DOI, title, abstract, authors, subject, dates, URLs.
    3. Chuan hoa text va bo record khong hop le.
    4. Tra ve list `PaperRecord`.
    """
    items = ((payload or {}).get("message") or {}).get("items") or []
    records: list[PaperRecord] = []

    for item in items:
        paper_id = (item.get("DOI") or "").strip()
        titles = item.get("title") or []
        title = normalize_whitespace(titles[0]) if titles else ""
        if not paper_id or not title:
            continue

        categories = _extract_categories(item)
        published = _extract_date(item)

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=_clean_abstract(item.get("abstract")),
                authors=_extract_authors(item),
                categories=categories,
                primary_category=categories[0] if categories else "",
                published=published,
                updated=published,
                abs_url=item.get("URL") or f"https://doi.org/{paper_id}",
                pdf_url=_extract_pdf_url(item),
                comment=normalize_whitespace(item.get("publisher") or ""),
            )
        )
>>>>>>> Stashed changes

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
<<<<<<< Updated upstream
    """Fetch source API data, save raw response HTTP, parse and save records."""
    headers = {"User-Agent": "Day10LabStudent/1.0 (mailto:student@example.com)"}
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    url = "https://api.crossref.org/works"

    if not settings.refresh_source and settings.paths.raw_api_response.exists():
        payload = read_json(settings.paths.raw_api_response)
    else:
        payload = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, params=params, headers=headers, timeout=15)
                if resp.status_code == 200:
                    payload = resp.json()
                    # Save raw HTTP response payload (for audit)
                    write_json(settings.paths.raw_api_response, payload)
                    break
                elif resp.status_code in (429, 503):
                    time.sleep(2 * (attempt + 1))
                else:
                    resp.raise_for_status()
            except Exception:
                if attempt == max_retries - 1:
                    if settings.paths.raw_api_response.exists():
                        payload = read_json(settings.paths.raw_api_response)
                    else:
                        raise

    if payload is None:
        if settings.paths.raw_api_response.exists():
            payload = read_json(settings.paths.raw_api_response)
        else:
            payload = {"message": {"items": []}}

    records = parse_crossref_payload(payload)
    records_dict = [asdict(r) for r in records]
    # Save flat records JSON according to PaperRecord structure
    write_json(settings.paths.raw_records_json, records_dict)
=======
    """Goi Crossref API, luu raw response, parse thanh records.

    1. Tao params tu `settings.source_query`, `settings.source_filter`, `settings.max_results`.
    2. Goi API voi retry cho cac status code nhu 429/503.
    3. Luu raw response vao `settings.paths.raw_api_response`.
    4. Parse payload bang `parse_crossref_payload`.
    5. Luu records vao `settings.paths.raw_records_json`.
    """
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    headers = {"User-Agent": USER_AGENT}

    response: requests.Response | None = None
    backoff_seconds = _INITIAL_BACKOFF_SECONDS
    last_error: Exception | None = None

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            response = requests.get(CROSSREF_API_URL, params=params, headers=headers, timeout=30)
        except requests.RequestException as exc:
            last_error = exc
            if attempt == _MAX_ATTEMPTS:
                raise
            time.sleep(backoff_seconds)
            backoff_seconds *= 2
            continue

        if response.status_code in _RETRY_STATUS_CODES and attempt < _MAX_ATTEMPTS:
            time.sleep(backoff_seconds)
            backoff_seconds *= 2
            continue

        response.raise_for_status()
        last_error = None
        break

    if response is None:
        raise last_error or RuntimeError("Failed to fetch Crossref records.")

    payload = response.json()
    write_json(settings.paths.raw_api_response, payload)

    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])

>>>>>>> Stashed changes
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
<<<<<<< Updated upstream
    """Load JSON snapshot and map into list of `PaperRecord`."""
    data = read_json(path)
    records = [PaperRecord(**item) for item in data]
    return records

=======
    """Doc file JSON snapshot va map cac dict thanh danh sach `PaperRecord`."""
    raw_items = read_json(path)
    return [PaperRecord(**item) for item in raw_items]
>>>>>>> Stashed changes
