"""
Scrape Cedar policy and schema code examples from:
  - Cedar official docs  (docs.cedarpolicy.com)
  - AWS Verified Permissions docs

For each code block, extract:
  - The nearest preceding heading (section context)
  - The nearest preceding paragraph (NL description)
  - The code itself
  - Code type: "policy" (permit/forbid) or "schema" (entity/action)

Output: JSONL files in data/layer1_raw/

Usage:
    python src/data/layer1/scrape_docs.py
    python src/data/layer1/scrape_docs.py --output-dir /custom/path
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
import urllib.error
from html.parser import HTMLParser
from pathlib import Path


# ---------------------------------------------------------------------------
# Target pages
# ---------------------------------------------------------------------------

CEDAR_DOCS_BASE = "https://docs.cedarpolicy.com"

CEDAR_PAGES = [
    "/overview/scenario.html",
    "/auth/authorization.html",
    "/auth/entities-syntax.html",
    "/policies/syntax-policy.html",
    "/policies/syntax-entity.html",
    "/policies/syntax-datatypes.html",
    "/policies/syntax-operators.html",
    "/policies/policy-examples.html",
    "/policies/templates.html",
    "/policies/validation.html",
    "/policies/json-format.html",
    "/schema/human-readable-schema.html",
    "/schema/json-schema.html",
    # Best practices — correct URL pattern
    "/bestpractices/bp-overview.html",
    "/bestpractices/bp-naming-conventions.html",
    "/bestpractices/bp-compound-auth.html",
    "/bestpractices/bp-fine-grained-permissions.html",
    "/bestpractices/bp-relationship-representation.html",
    "/bestpractices/bp-resources-containers.html",
    "/bestpractices/bp-separate-principals.html",
    "/bestpractices/bp-populate-policy-scope.html",
    "/bestpractices/bp-normalize-data-input.html",
    "/bestpractices/bp-using-the-context.html",
    "/bestpractices/bp-meta-permissions.html",
    "/bestpractices/bp-implementing-roles.html",
    "/bestpractices/bp-implementing-roles-groups.html",
    "/bestpractices/bp-implementing-roles-attributes.html",
    "/bestpractices/bp-implementing-roles-templates.html",
]

# AWS AVP docs do not contain inline Cedar code blocks — omitted.
AWS_AVP_BASE = "https://docs.aws.amazon.com"
AWS_AVP_PAGES: list[str] = []


# ---------------------------------------------------------------------------
# HTML parser
# ---------------------------------------------------------------------------

class DocParser(HTMLParser):
    """
    Stateful HTML parser that extracts (heading, paragraph, code) triplets.

    Tracks the current heading and last paragraph, then captures every
    <pre><code> block along with that context.
    """

    def __init__(self) -> None:
        super().__init__()
        self.records: list[dict] = []

        # State
        self._in_heading: str | None = None     # "h2" or "h3"
        self._in_para: bool = False
        self._in_pre: bool = False
        self._in_code: bool = False
        self._code_class: str = ""

        self._current_h2: str = ""
        self._current_h3: str = ""
        self._current_para: str = ""
        self._code_buf: str = ""
        self._para_buf: str = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)

        if tag in ("h2", "h3"):
            self._in_heading = tag
            self._para_buf = ""

        elif tag == "p":
            self._in_para = True
            self._para_buf = ""

        elif tag == "pre":
            self._in_pre = True

        elif tag == "code" and self._in_pre:
            cls = attr_dict.get("class", "") or ""
            self._code_class = cls
            self._in_code = True
            self._code_buf = ""

    def handle_endtag(self, tag: str) -> None:
        if tag in ("h2", "h3") and self._in_heading == tag:
            text = self._para_buf.strip()
            if tag == "h2":
                self._current_h2 = text
                self._current_h3 = ""
            else:
                self._current_h3 = text
            self._in_heading = None
            self._para_buf = ""

        elif tag == "p" and self._in_para:
            self._current_para = self._para_buf.strip()
            self._in_para = False
            self._para_buf = ""

        elif tag == "code" and self._in_code:
            self._in_code = False
            # Only keep Cedar code blocks
            if "cedar" in self._code_class or _looks_like_cedar(self._code_buf):
                self.records.append({
                    "h2": self._current_h2,
                    "h3": self._current_h3,
                    "nl_description": self._current_para,
                    "cedar_code": self._code_buf,
                    "code_class": self._code_class,
                })

        elif tag == "pre":
            self._in_pre = False
            self._in_code = False

    def handle_data(self, data: str) -> None:
        if self._in_heading:
            self._para_buf += data
        elif self._in_para:
            self._para_buf += data
        elif self._in_code:
            self._code_buf += data


# ---------------------------------------------------------------------------
# Code analysis helpers
# ---------------------------------------------------------------------------

_CEDAR_KEYWORDS = re.compile(
    r"\b(permit|forbid|when|unless|principal|action|resource|entity|namespace|"
    r"appliesTo|in|has|like|is|true|false)\b"
)

_POLICY_KEYWORDS = re.compile(r"\b(permit|forbid)\s*\(")
# Schema keywords must appear at the start of a non-comment line to avoid
# matching "entity" inside inline comments like "// matches any principal entity"
_SCHEMA_KEYWORDS = re.compile(
    r"^[ \t]*(entity|namespace|type)\s+\w|"   # entity/type/namespace declarations
    r"^[ \t]*action\s+\w[\w,\s]*appliesTo",    # action declarations
    re.MULTILINE,
)


def _looks_like_cedar(code: str) -> bool:
    """Heuristic: does this code block look like Cedar (policy or schema)?"""
    return bool(_CEDAR_KEYWORDS.search(code))


def _code_type(code: str) -> str | None:
    """
    Return 'policy', 'schema', 'mixed', or None.
    None means the block is not Cedar (skip it).
    """
    has_policy = bool(_POLICY_KEYWORDS.search(code))
    has_schema = bool(_SCHEMA_KEYWORDS.search(code))

    if has_policy and has_schema:
        return "mixed"
    if has_policy:
        return "policy"
    if has_schema:
        return "schema"
    return None


def _split_mixed(code: str) -> list[tuple[str, str]]:
    """
    Split a mixed policy+schema block into separate (type, code) pairs.

    Heuristic: split on blank lines between policy-starting and
    schema-starting statements.
    """
    policy_lines: list[str] = []
    schema_lines: list[str] = []

    current_type: str | None = None
    for line in code.splitlines():
        stripped = line.strip()
        if _POLICY_KEYWORDS.search(stripped):
            current_type = "policy"
        elif _SCHEMA_KEYWORDS.search(stripped):
            current_type = "schema"

        if current_type == "policy":
            policy_lines.append(line)
        elif current_type == "schema":
            schema_lines.append(line)

    results: list[tuple[str, str]] = []
    if policy_lines:
        results.append(("policy", "\n".join(policy_lines).strip()))
    if schema_lines:
        results.append(("schema", "\n".join(schema_lines).strip()))
    return results


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _fetch(url: str, retries: int = 3) -> str | None:
    """Fetch a URL and return the HTML as a string, or None on failure."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; cedar-doc-scraper/1.0)"}
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            print(f"    HTTP {e.code} for {url}")
            return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"    Failed after {retries} attempts: {e}")
                return None
    return None


# ---------------------------------------------------------------------------
# Scraping pipeline
# ---------------------------------------------------------------------------

def scrape_page(
    url: str,
    source: str,
    page_title: str = "",
) -> list[dict]:
    """Fetch one page and return a list of extracted records."""
    print(f"  Fetching {url}")
    html = _fetch(url)
    if not html:
        return []

    parser = DocParser()
    parser.feed(html)

    records: list[dict] = []
    seen_codes: set[str] = set()

    for raw in parser.records:
        code = raw["cedar_code"].strip()
        if not code or code in seen_codes:
            continue
        seen_codes.add(code)

        nl = _clean_nl(raw["nl_description"])
        section = raw["h3"] or raw["h2"]

        ct = _code_type(code)
        if ct is None:
            continue

        if ct == "mixed":
            for sub_type, sub_code in _split_mixed(code):
                records.append(_make_record(
                    source=source,
                    url=url,
                    page_title=page_title or raw["h2"],
                    section_heading=section,
                    nl_description=nl,
                    cedar_code=sub_code,
                    code_type=sub_type,
                ))
        else:
            records.append(_make_record(
                source=source,
                url=url,
                page_title=page_title or raw["h2"],
                section_heading=section,
                nl_description=nl,
                cedar_code=code,
                code_type=ct,
            ))

    return records


def _clean_nl(text: str) -> str:
    """Strip markdown backticks and collapse whitespace."""
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return " ".join(text.split())


def _make_record(
    source: str,
    url: str,
    page_title: str,
    section_heading: str,
    nl_description: str,
    cedar_code: str,
    code_type: str,
) -> dict:
    return {
        "source": source,
        "page_url": url,
        "page_title": page_title,
        "section_heading": section_heading,
        "nl_description": nl_description,
        "cedar_code": cedar_code,
        "code_type": code_type,
        "needs_expansion": True,
    }


def scrape_site(
    base_url: str,
    pages: list[str],
    source_label: str,
    delay: float = 1.0,
) -> list[dict]:
    """Scrape a list of page paths from a base URL."""
    all_records: list[dict] = []
    for path in pages:
        url = base_url + path
        records = scrape_page(url, source=source_label)
        all_records.extend(records)
        print(f"    -> {len(records)} records")
        time.sleep(delay)
    return all_records


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Cedar doc examples")
    parser.add_argument("--output-dir", default="data/layer1_raw")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Seconds between requests")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Cedar docs ---
    print("Scraping Cedar official docs...")
    cedar_records = scrape_site(
        CEDAR_DOCS_BASE, CEDAR_PAGES, "cedar_docs", delay=args.delay
    )
    cedar_out = out_dir / "cedar_docs.jsonl"
    _write_jsonl(cedar_records, cedar_out)
    print(f"Cedar docs: {len(cedar_records)} records -> {cedar_out}\n")

    # --- AWS AVP docs ---
    print("Scraping AWS Verified Permissions docs...")
    aws_records = scrape_site(
        AWS_AVP_BASE, AWS_AVP_PAGES, "aws_avp_docs", delay=args.delay
    )
    aws_out = out_dir / "aws_avp_docs.jsonl"
    _write_jsonl(aws_records, aws_out)
    print(f"AWS AVP docs: {len(aws_records)} records -> {aws_out}\n")

    # --- Stats ---
    all_records = cedar_records + aws_records
    policy_count = sum(1 for r in all_records if r["code_type"] == "policy")
    schema_count = sum(1 for r in all_records if r["code_type"] == "schema")
    print(f"Total: {len(all_records)} records "
          f"(policy={policy_count}, schema={schema_count})")


def _write_jsonl(records: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
