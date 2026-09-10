#!/usr/bin/env python3
"""Offline treaty-mention classifier and command-line interface.

The baseline is intentionally transparent: it scores explicit stance phrases,
returns the strongest supported category, and uses ``Needs review`` when the
text is too weak or ambiguous to classify safely.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

SUPPORTING = "Supporting"
OPPOSING = "Opposing"
MIXED_CONDITIONAL = "Mixed / Conditional"
NEUTRAL = "Neutral / Descriptive"
NEEDS_REVIEW = "Needs review"
CATEGORIES = (SUPPORTING, OPPOSING, MIXED_CONDITIONAL, NEUTRAL, NEEDS_REVIEW)

_PATTERNS = {
    SUPPORTING: (
        (r"\b(support|supports|supported|supporting|endorses?|endorsement)\b", 2),
        (r"\b(oppos(e|es|ed|ing)|opposition|against)\s+(to\s+)?(the\s+)?withdraw(al|ing)?\b", 4),
        (r"\b(urge|urges|urged|encourage|encourages|advocate|advocates)\b.{0,30}\b(ratif|implement|join|adopt)", 3),
        (r"\b(ratif(y|ication|ied)|implement(s|ed|ation)?|adopt(s|ed|ion)?|join(s|ed)?)\b", 2),
        (r"\b(commit(s|ted|ment)?|uphold(s|ing)?|approve[sd]?)\b", 2),
    ),
    OPPOSING: (
        (r"\b(oppose[sd]?|opposition|reject(s|ed|ion)?|against)\b(?!\s+(to\s+)?(the\s+)?withdraw(al|ing)?\b)", 3),
        (r"\b(support(s|ed|ing)?|favor(s|ed|ing)?|advocate(s|d|ing)?|call(s|ed|ing)?)\b.{0,20}\b(withdraw|withdrawal|withdrawing)\b", 4),
        (r"\b(block(s|ed|ing)?|undermine[sd]?|abandon)\b", 3),
        (r"\b(do not|does not|should not|must not|cannot)\b.{0,30}\b(ratif|implement|join|adopt)", 3),
        (r"\b(leave|exit|renounce|dismantle)(s|d|ing)?\b", 2),
    ),
    MIXED_CONDITIONAL: (
        (r"\b(if and only if|provided that|on condition that|conditional(ly)?)\b", 4),
        (r"\bbut\b|\bhowever\b|\balthough\b|\bwhile\b", 2),
        (r"\b(some|certain|specific|selected)\b.{0,25}\b(provision|article|clause|aspect)", 3),
        (r"\b(support|favor)\b.{0,40}\b(but|however|unless|only if)\b", 4),
    ),
    NEUTRAL: (
        (r"\b(signed|signing|ratified|entered into force|agreement|treaty)\b", 1),
        (r"\b(describe[sd]?|reported|reports|noted|stated|explained)\b", 1),
        (r"\b(section|article|provision|date|party|parties)\b", 1),
    ),
}


@dataclass(frozen=True)
class Classification:
    """A classification plus the evidence used to reach it."""

    category: str
    confidence: float
    scores: dict[str, int]
    evidence: tuple[str, ...]


def _score(text: str) -> Classification:
    normalized = " ".join(text.lower().split())
    scores = {category: 0 for category in CATEGORIES}
    evidence: list[str] = []

    for category, patterns in _PATTERNS.items():
        for pattern, weight in patterns:
            match = re.search(pattern, normalized)
            if match:
                scores[category] += weight
                evidence.append(f"{category}: {match.group(0)}")

    # A conjunction linking positive and negative language is mixed even when
    # no explicit "conditional" phrase appears.
    if scores[SUPPORTING] and scores[OPPOSING]:
        scores[MIXED_CONDITIONAL] += 4
        evidence.append("Mixed / Conditional: supporting and opposing evidence")

    ranked = sorted(
        ((score, category) for category, score in scores.items() if category != NEEDS_REVIEW),
        reverse=True,
    )
    best_score, best_category = ranked[0]
    second_score = ranked[1][0]
    if best_score < 2 or best_score == second_score or best_score - second_score < 2:
        category = NEEDS_REVIEW
        confidence = 0.0 if best_score == 0 else min(0.49, best_score / 10)
    else:
        category = best_category
        confidence = min(0.99, 0.5 + (best_score - second_score) / 10)
    return Classification(category, round(confidence, 2), scores, tuple(evidence))


def classify_text(text: str) -> Classification:
    """Classify one mention and expose scores/evidence for audits."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text.strip():
        return Classification(NEEDS_REVIEW, 0.0, {c: 0 for c in CATEGORIES}, ())
    return _score(text)


def classify_treaty(text: str, max_attempts: int = 1) -> str:
    """Return the category name (compatible with the original public API).

    ``max_attempts`` is accepted for callers of the former provider-backed
    implementation; the offline baseline does not retry or make network calls.
    """
    del max_attempts
    return classify_text(text).category


def _read_rows(file_path: str) -> Iterable[tuple[str, str]]:
    path = Path(file_path)
    encodings = ("utf-8", "cp1252", "latin-1")
    last_error: Optional[Exception] = None
    for encoding in encodings:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                first_line = handle.readline()
                if "|" in first_line and "," not in first_line:
                    first_identifier, separator, first_text = first_line.rstrip("\n\r").partition("|")
                    has_header = separator and first_identifier.casefold() in {"id", "speech_id"}
                    if has_header:
                        next(handle, None)
                    elif separator:
                        yield first_identifier, first_text
                    for line_number, line in enumerate(handle, 2):
                        identifier, separator, text = line.rstrip("\n\r").partition("|")
                        if separator:
                            yield identifier, text
                else:
                    handle.seek(0)
                    reader = csv.DictReader(handle)
                    fieldnames = {
                        (field or "").strip().lstrip("\ufeff").casefold()
                        for field in (reader.fieldnames or [])
                    }
                    identifier_columns = {"speech_id", "id"} & fieldnames
                    text_columns = {"mention", "text"} & fieldnames
                    if not identifier_columns or not text_columns:
                        raise ValueError(
                            f"Invalid CSV headers in {file_path}: expected an identifier "
                            "(Speech_ID or id) and text (Mention or text) column"
                        )
                    for index, row in enumerate(reader, 2):
                        normalized_row = {
                            (key or "").strip().lstrip("\ufeff").casefold(): value
                            for key, value in row.items()
                            if key is not None
                        }
                        identifier = str(
                            normalized_row.get("speech_id")
                            or normalized_row.get("id")
                            or index
                        )
                        text = str(
                            normalized_row.get("mention")
                            or normalized_row.get("text")
                            or ""
                        )
                        yield identifier, text
                return
        except UnicodeDecodeError as error:
            last_error = error
    raise ValueError(f"Unable to decode {file_path}: {last_error}")


def process_file(
    file_path: str,
    search_term: str,
    batch_size: int = 5,
    check_running: Optional[Callable[[], bool]] = None,
) -> list[dict[str, object]]:
    """Find mentions in a pipe-delimited or CSV file and classify them."""
    if not search_term.strip():
        raise ValueError("search_term cannot be empty")
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    if not os.path.isfile(file_path):
        raise FileNotFoundError(file_path)
    check_running = check_running or (lambda: True)
    results: list[dict[str, object]] = []
    term = search_term.casefold()
    for speech_id, text in _read_rows(file_path):
        if not check_running():
            break
        if term in text.casefold():
            result = classify_text(text)
            results.append({
                "Speech_ID": speech_id,
                "Mention": text,
                "Category": result.category,
                "Confidence": result.confidence,
                "Evidence": "; ".join(result.evidence),
            })
    return results


def command_line_main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Classify treaty mentions offline.")
    parser.add_argument("file", nargs="?", help="Pipe-delimited or CSV input file")
    parser.add_argument("search_term", nargs="?", help="Treaty name or keyword")
    parser.add_argument("-o", "--output", help="Output CSV path")
    parser.add_argument("-l", "--limit", type=int, default=0, help="Maximum matching mentions (0 means all)")
    parser.add_argument("-b", "--batch-size", type=int, default=5, help="Compatibility option; must be positive")
    parser.add_argument("--text", help="Classify one text directly instead of reading a file")
    args = parser.parse_args(argv)

    if args.batch_size < 1 or args.limit < 0:
        parser.error("--batch-size must be positive and --limit cannot be negative")
    if args.text is not None:
        result = classify_text(args.text)
        print(f"Category: {result.category}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Evidence: {'; '.join(result.evidence) or 'none'}")
        return 0
    if not args.file or not args.search_term:
        parser.error("file and search_term are required unless --text is used")

    rows = process_file(args.file, args.search_term, args.batch_size)
    if args.limit:
        rows = rows[:args.limit]
    if not rows:
        print("No matching mentions found.")
        return 0
    output = args.output or f"{Path(args.file).stem}_{args.search_term}_classified.csv"
    with open(output, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Classified {len(rows)} mention(s). Results saved to {output}")
    for category in CATEGORIES:
        count = sum(row["Category"] == category for row in rows)
        if count:
            print(f"{category}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(command_line_main())
