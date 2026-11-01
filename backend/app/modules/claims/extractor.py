"""Atomic claim extraction with character offset validation and provenance."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedClaimItem:
    """Atomic claim extracted from raw text with verified character offsets."""

    index: int
    text: str
    start_offset: int
    end_offset: int
    extraction_method: str = "DETERMINISTIC_SYNTACTIC_SEGMENTATION"


class BaseClaimExtractor(ABC):
    """Abstract interface for claim extraction strategies."""

    @abstractmethod
    def extract(self, text: str, max_claims: int = 20) -> list[ExtractedClaimItem]:
        """Extract atomic claims from source text."""
        pass


class DeterministicClaimExtractor(BaseClaimExtractor):
    """Deterministic, rule-based claim extractor.

    Deconstructs multi-sentence or compound inputs into discrete propositional
    statements while computing exact character offsets and guaranteeing
    that `text[start:end] == claim_text`.
    """

    # Common abbreviations to prevent false sentence boundaries
    ABBREVIATIONS = r"\b(?:e\.g|i\.e|dr|mr|mrs|ms|prof|inc|ltd|co|jr|sr|u\.s|u\.k|vs)\."

    def extract(self, text: str, max_claims: int = 20) -> list[ExtractedClaimItem]:
        """Deconstruct input text into validated atomic claims."""
        if not text or not text.strip():
            return []

        # Split text into candidate spans using sentence and clause boundaries
        candidates: list[tuple[int, int]] = []
        for start, end in self._sentence_spans(text):
            # Check if this span contains compound clauses separated by conjunctions
            sub_spans = self._split_compound_clause(text, start, end, text[start:end])
            candidates.extend(sub_spans)

        # Refine candidates: strip whitespace, adjust offsets, enforce invariants
        extracted: list[ExtractedClaimItem] = []
        claim_index = 0

        for start, end in candidates:
            if claim_index >= max_claims:
                break

            span_text = text[start:end]
            # Strip whitespace and trailing boundary punctuation
            l_strip = len(span_text) - len(span_text.lstrip())
            r_strip = len(span_text) - len(span_text.rstrip(" \t\r\n.!?;\u2026"))

            clean_start = start + l_strip
            clean_end = end - r_strip

            if clean_end <= clean_start:
                continue

            clean_text = text[clean_start:clean_end]

            # Minimum viable claim length (ignore single symbols or orphaned words)
            if len(clean_text) < 3:
                continue

            # Strict Invariant: slice must match text exactly
            if text[clean_start:clean_end] != clean_text:
                raise RuntimeError("Claim extraction offset invariant violated")

            extracted.append(
                ExtractedClaimItem(
                    index=claim_index,
                    text=clean_text,
                    start_offset=clean_start,
                    end_offset=clean_end,
                    extraction_method="DETERMINISTIC_SYNTACTIC_SEGMENTATION",
                )
            )
            claim_index += 1

        # Fallback: if entire text could not be segmented into valid sub-claims,
        # extract the whole stripped text as a single atomic claim.
        if not extracted and text.strip():
            s = text.find(text.strip())
            e = s + len(text.strip())
            extracted.append(
                ExtractedClaimItem(
                    index=0,
                    text=text[s:e],
                    start_offset=s,
                    end_offset=e,
                    extraction_method="DETERMINISTIC_FULL_TEXT_FALLBACK",
                )
            )

        return extracted

    def _is_continuation(
        self, full_text: str, prev_span: tuple[int, int], current_start: int
    ) -> bool:
        """Check if current span is an accidental split due to an abbreviation."""
        prev_text = full_text[prev_span[0] : prev_span[1]].rstrip()
        return bool(re.search(self.ABBREVIATIONS, prev_text, re.IGNORECASE))

    # Sentence terminator (. ! ?) followed by whitespace and a sentence starter, or a
    # hard line break / semicolon. Decimals (3.14), URLs (example.com/a.b) and
    # mid-token dots are never followed by whitespace, so they cannot split.
    _SENTENCE_END = re.compile(r"[.!?](?=\s+[\"'(\[]?[A-Z0-9])|[;\n]")
    _ABBREVIATION_WORDS = frozenset(
        {
            "e.g",
            "i.e",
            "dr",
            "mr",
            "mrs",
            "ms",
            "prof",
            "inc",
            "ltd",
            "co",
            "jr",
            "sr",
            "u.s",
            "u.k",
            "vs",
        }
    )

    def _sentence_spans(self, text: str) -> list[tuple[int, int]]:
        """Return non-blank [start, end) sentence spans covering the whole text."""
        spans: list[tuple[int, int]] = []
        start = 0
        for m in self._SENTENCE_END.finditer(text):
            if m.group(0) == "." and self._is_abbreviation_end(text, start, m.start()):
                continue
            spans.append((start, m.end()))
            start = m.end()
        if start < len(text):
            spans.append((start, len(text)))
        return [(s, e) for s, e in spans if text[s:e].strip()]

    def _is_abbreviation_end(self, text: str, span_start: int, dot_pos: int) -> bool:
        """True when the dot at ``dot_pos`` closes a known abbreviation like "Dr."."""
        match = re.search(r"[A-Za-z][A-Za-z.]*$", text[span_start:dot_pos])
        if not match:
            return False
        return match.group(0).lower() in self._ABBREVIATION_WORDS

    def _split_compound_clause(
        self, full_text: str, start: int, end: int, span_text: str
    ) -> list[tuple[int, int]]:
        """Optionally split compound sentences joined by coordinating conjunctions."""
        # Coordinating conjunctions flanked by commas or semicolons
        sub_pattern = re.compile(
            r"(?<=,)\s+(?:and|but|while|whereas|however|although)\s+",
            re.IGNORECASE,
        )
        splits: list[tuple[int, int]] = []
        curr_start = start

        for m in sub_pattern.finditer(span_text):
            split_pos = start + m.start()
            if split_pos > curr_start + 10:  # Ensure reasonable chunk size
                splits.append((curr_start, split_pos))
                curr_start = start + m.end()

        splits.append((curr_start, end))
        return splits
