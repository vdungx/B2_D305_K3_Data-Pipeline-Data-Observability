from dataclasses import asdict, dataclass
import re
import time

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


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

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
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
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load JSON snapshot and map into list of `PaperRecord`."""
    data = read_json(path)
    records = [PaperRecord(**item) for item in data]
    return records

