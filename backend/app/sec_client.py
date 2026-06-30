from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from html import unescape
from verification_sources import get_company_cik


IMPORTANT_FORMS = {"10-K", "10-Q", "8-K", "20-F", "6-K"}
DEFAULT_USER_AGENT = "Sunguo AI Butler local prototype contact@example.com"


class SecClientError(RuntimeError):
    pass


def fetch_recent_sec_filings(
    company: dict,
    timeout_seconds: int = 10,
    user_agent: str = DEFAULT_USER_AGENT,
    max_filings: int = 4,
    max_summaries: int = 1,
) -> list[dict]:
    cik = get_company_cik(company)
    if not cik:
        return []

    payload = fetch_sec_submissions(cik, timeout_seconds, user_agent)
    recent = payload.get("filings", {}).get("recent", {})
    rows = normalize_recent_filings(cik, recent)
    for row in rows[:max_summaries]:
        try:
            row["document_summary"] = fetch_filing_document_summary(row["url"], timeout_seconds, user_agent)
        except SecClientError as error:
            row["document_summary"] = {"error": str(error)}
    return rows[:max_filings]


def fetch_sec_submissions(cik: str, timeout_seconds: int, user_agent: str) -> dict:
    padded_cik = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent or DEFAULT_USER_AGENT,
            "Accept-Encoding": "identity",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as error:
        raise SecClientError(f"SEC network error for CIK {cik}: {error}") from error
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise SecClientError(f"SEC returned invalid JSON for CIK {cik}.") from error


def normalize_recent_filings(cik: str, recent: dict) -> list[dict]:
    forms = recent.get("form", [])
    filing_dates = recent.get("filingDate", [])
    report_dates = recent.get("reportDate", [])
    accession_numbers = recent.get("accessionNumber", [])
    primary_documents = recent.get("primaryDocument", [])

    rows = []
    for index, form in enumerate(forms):
        if form not in IMPORTANT_FORMS:
            continue
        accession = value_at(accession_numbers, index)
        document = value_at(primary_documents, index)
        if not accession or not document:
            continue
        rows.append(
            {
                "form": form,
                "filing_date": value_at(filing_dates, index),
                "report_date": value_at(report_dates, index),
                "accession_number": accession,
                "document": document,
                "url": build_sec_document_url(cik, accession, document),
                "use_for": filing_use_for(form),
            }
        )
    return rows


def fetch_filing_document_summary(url: str, timeout_seconds: int, user_agent: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent or DEFAULT_USER_AGENT,
            "Accept-Encoding": "identity",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            html = response.read(300_000).decode("utf-8", errors="replace")
    except urllib.error.URLError as error:
        raise SecClientError(f"SEC filing document network error for {url}: {error}") from error

    text = html_to_text(html)
    return {
        "title": extract_document_title(html, text),
        "items": extract_sec_items(text),
    }


def html_to_text(html: str) -> str:
    cleaned = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", html)
    cleaned = re.sub(r"(?is)<[^>]+>", " ", cleaned)
    cleaned = unescape(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def extract_document_title(html: str, text: str) -> str:
    title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    if title_match:
        return re.sub(r"\s+", " ", unescape(title_match.group(1))).strip()[:180]
    return text[:180]


def extract_sec_items(text: str) -> list[str]:
    found = []
    pattern = re.compile(r"\bItem\s+([0-9]{1,2}\.[0-9]{2})\b\.?\s*([^|]{0,120})", re.IGNORECASE)
    for match in pattern.finditer(text):
        item = f"Item {match.group(1)} {match.group(2).strip()}"
        item = re.sub(r"\s+", " ", item).strip(" .")
        if item not in found:
            found.append(item)
        if len(found) >= 6:
            break
    return found

def build_sec_document_url(cik: str, accession: str, document: str) -> str:
    cik_plain = str(int(cik))
    accession_plain = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik_plain}/{accession_plain}/{document}"


def filing_use_for(form: str) -> str:
    return {
        "10-K": "年度报告，适合核对全年业务、风险因素和财务数据。",
        "10-Q": "季度报告，适合核对季度收入、利润、现金流和风险变化。",
        "8-K": "重大事项公告，适合核对临时事件、业绩发布和管理层变化。",
        "20-F": "境外发行人年度报告，适合核对全年业务和财务数据。",
        "6-K": "境外发行人临时披露，适合核对新闻稿、财报和重大事件。",
    }.get(form, "监管披露文件，适合回到原文核验。")


def value_at(values: list, index: int) -> str:
    if index >= len(values):
        return ""
    value = values[index]
    return "" if value is None else str(value)





