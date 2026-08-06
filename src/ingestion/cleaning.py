from __future__ import annotations

from datetime import datetime
import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord



def _parse_date(date_str: str, default_date: datetime) -> datetime:
    if not date_str:
        return default_date
    date_str_clean = date_str.split("T")[0].strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(date_str_clean, fmt)
        except ValueError:
            continue
    return default_date


import html
import re


def _clean_text(raw: str) -> str:
    if not raw:
        return ""
    # Strip HTML/XML tags e.g. <jats:p>, <b>, etc. and unescape HTML entities (&amp;, &lt;)
    cleaned = re.sub(r"<[^>]+>", "", str(raw))
    cleaned = html.unescape(cleaned)
    return normalize_whitespace(cleaned)



def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records into a pandas DataFrame ready for embedding and indexing."""
    if not records:
        return pd.DataFrame(
            columns=[
                "paper_id",
                "title",
                "summary",
                "authors",
                "categories",
                "primary_category",
                "published",
                "updated",
                "abs_url",
                "pdf_url",
                "comment",
                "authors_joined",
                "categories_joined",
                "summary_chars",
                "age_days",
                "text_for_embedding",
            ]
        )

    rows = []
    run_date_naive = run_date.replace(tzinfo=None)

    for rec in records:
        paper_id = (rec.paper_id or "").strip()
        title = _clean_text(rec.title or "")
        summary = _clean_text(rec.summary or "")

        if not paper_id or not title:
            continue

        authors_list = rec.authors if isinstance(rec.authors, list) else []
        authors_clean = [_clean_text(a) for a in authors_list if a and _clean_text(a)]
        authors_joined = ", ".join(authors_clean) if authors_clean else "Unknown Author"

        categories_list = rec.categories if isinstance(rec.categories, list) else []
        categories_clean = [_clean_text(c) for c in categories_list if c and _clean_text(c)]
        categories_joined = ", ".join(categories_clean) if categories_clean else "General"

        primary_category = _clean_text(rec.primary_category or (categories_clean[0] if categories_clean else "General"))

        pub_dt = _parse_date(rec.published, run_date_naive)
        pub_str = pub_dt.strftime("%Y-%m-%d")
        updated_dt = _parse_date(rec.updated, pub_dt)
        updated_str = updated_dt.strftime("%Y-%m-%d")

        age_days = max(0, (run_date_naive.date() - pub_dt.date()).days)
        summary_chars = len(summary)

        # Standard format for semantic embedding
        text_for_embedding = f"Title: {title} | Authors: {authors_joined} | Summary: {summary}"

        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors_clean,
                "categories": categories_clean,
                "primary_category": primary_category,
                "published": pub_str,
                "updated": updated_str,
                "abs_url": rec.abs_url or f"https://doi.org/{paper_id}",
                "pdf_url": rec.pdf_url or "",
                "comment": rec.comment or "",
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Filter invalid/short summary rows (< 100 characters)
    df = df[df["summary_chars"] >= 100]

    # Drop duplicates by paper_id and title
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df.drop_duplicates(subset=["title"], keep="first")

    # Sort by published date descending
    df = df.sort_values(by="published", ascending=False).reset_index(drop=True)
    return df


