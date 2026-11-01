"""Shared lexical analysis primitives for the deterministic judges.

The judges compare a claim with evidence passages at the level of individual
propositions rather than bags of words:

- Numbers are *bound* to the words around them, so "boils at 100" in a passage
  cannot vouch for "freezes at 100" in a claim.
- Proper nouns are tracked so that a claim naming a different entity in the same
  slot as the evidence ("Lyon is the capital" vs "Paris is the capital") is
  detected as a substitution, while a claim whose entities are simply absent
  from the evidence is never treated as supported.
- Negation is evaluated on the evidence sentence that best aligns with the claim.

These are heuristics: they are tuned to fail towards UNKNOWN rather than towards
a confident wrong verdict.
"""

import re
from dataclasses import dataclass

STOP_WORDS = frozenset(
    {
        "a", "an", "the", "and", "or", "but", "nor", "of", "to", "in", "on", "at",
        "by", "for", "with", "from", "into", "onto", "over", "under", "about",
        "as", "is", "are", "was", "were", "be", "been", "being", "am", "has",
        "have", "had", "do", "does", "did", "will", "would", "can", "could",
        "should", "may", "might", "must", "shall", "that", "this", "these",
        "those", "it", "its", "their", "they", "them", "he", "she", "his", "her",
        "we", "our", "you", "your", "i", "me", "my", "which", "who", "whom",
        "whose", "what", "when", "where", "while", "than", "then", "also",
        "very", "just", "some", "any", "each", "other", "such", "only", "same",
        "both", "all", "more", "most", "out", "up", "so", "there", "here",
        "after", "before", "during", "between", "through", "per", "via",
        "approximately", "around", "roughly", "nearly", "almost",
        "exactly", "commonly", "first", "one",
    }
)  # fmt: skip

NEGATION_WORDS = frozenset(
    {
        "not", "never", "no", "none", "neither", "nor", "cannot", "without",
        "isn't", "aren't", "wasn't", "weren't", "doesn't", "don't", "didn't",
        "won't", "can't", "couldn't", "hasn't", "haven't", "hadn't",
    }
)  # fmt: skip

# Explicit falsity markers only count on the evidence side.
EVIDENCE_NEGATION_WORDS = NEGATION_WORDS | {"false", "untrue", "incorrect"}

_TOKEN_RE = re.compile(
    r"\d+(?:,\d{3})*(?:\.\d+)?|[A-Za-z][A-Za-z0-9]*(?:['’][A-Za-z]+)?"
)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?;])\s+|\n+")

# Context weighting for number binding: words before a number usually carry
# the predicate ("freezes at 0"), words after usually carry the unit.
_PRECEDING_WINDOW = 4
_FOLLOWING_WINDOW = 2
_FOLLOWING_WEIGHT = 0.5
# Minimum context score for an evidence number to be considered "about" the
# same quantity as the claim number (roughly one adjacent predicate word).
MIN_BINDING_SCORE = 1.0


@dataclass(frozen=True)
class Token:
    """A lexical token with normalization metadata."""

    text: str
    norm: str
    is_number: bool
    is_capitalized: bool

    @property
    def is_content(self) -> bool:
        return self.is_number or (self.norm not in STOP_WORDS and len(self.norm) > 1)


def _normalize(raw: str) -> str:
    lowered = raw.lower().replace("’", "'")
    if lowered.endswith("'s"):
        lowered = lowered[:-2]
    return lowered


def _number_value(raw: str) -> str:
    """Canonical string for a numeric token ("299,792,458" -> "299792458")."""
    value = float(raw.replace(",", ""))
    return str(int(value)) if value.is_integer() else repr(value)


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    for match in _TOKEN_RE.finditer(text):
        raw = match.group(0)
        is_number = raw[0].isdigit()
        tokens.append(
            Token(
                text=raw,
                norm=_number_value(raw) if is_number else _normalize(raw),
                is_number=is_number,
                is_capitalized=raw[0].isupper(),
            )
        )
    return tokens


def content_tokens(text: str) -> list[Token]:
    return [t for t in tokenize(text) if t.is_content]


def content_terms(text: str) -> set[str]:
    """Lowercased non-numeric content words."""
    return {t.norm for t in content_tokens(text) if not t.is_number}


def numbers(text: str) -> set[str]:
    return {t.norm for t in tokenize(text) if t.is_number}


def proper_nouns(text: str) -> set[str]:
    """Normalized capitalized content words (sentence-initial words included).

    Sentence-initial common nouns ("Water ...") are included too; they are
    harmless because presence is always checked case-insensitively.
    """
    return {
        t.norm
        for t in content_tokens(text)
        if t.is_capitalized and not t.is_number and t.norm != "i"
    }


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]


def has_negation(text: str, *, evidence: bool = False) -> bool:
    vocabulary = EVIDENCE_NEGATION_WORDS if evidence else NEGATION_WORDS
    return any(_normalize(t.text) in vocabulary for t in tokenize(text))


def best_aligned_sentence(claim: str, passage: str) -> tuple[str, int]:
    """Return the passage sentence sharing the most content words with ``claim``."""
    claim_terms = content_terms(claim) | numbers(claim)
    best, best_overlap = "", 0
    for sentence in split_sentences(passage):
        overlap = len(claim_terms & (content_terms(sentence) | numbers(sentence)))
        if overlap > best_overlap:
            best, best_overlap = sentence, overlap
    return best, best_overlap


# ---------------------------------------------------------------------------
# Number binding
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _NumberContext:
    value: str
    weights: dict[str, float]  # nearby words weighted by proximity
    preceding: frozenset[str]  # every word before the number in its sentence
    sentence: frozenset[str]  # every word in the number's sentence

    def governed_by(self, subject: str) -> bool:
        """True unless the subject appears in this sentence only after the number.

        A sentence that never names the subject inherits it from its passage
        (e.g. a specification heading followed by its values).
        """
        return subject in self.preceding or subject not in self.sentence


def _number_contexts(text: str) -> list[_NumberContext]:
    """For each number, weight the content words around it by proximity.

    Contexts never cross sentence boundaries.
    """
    contexts: list[_NumberContext] = []
    for sentence in split_sentences(text) or [text]:
        toks = content_tokens(sentence)
        words = [(i, t) for i, t in enumerate(toks) if not t.is_number]
        for idx, tok in enumerate(toks):
            if not tok.is_number:
                continue
            weights: dict[str, float] = {}
            before = [t for i, t in words if i < idx]
            for distance, word in enumerate(
                reversed(before[-_PRECEDING_WINDOW:]), start=1
            ):
                weights[word.norm] = max(weights.get(word.norm, 0.0), 1.0 / distance)
            after = [t for i, t in words if i > idx][:_FOLLOWING_WINDOW]
            for distance, word in enumerate(after, start=1):
                weight = _FOLLOWING_WEIGHT / distance
                weights[word.norm] = max(weights.get(word.norm, 0.0), weight)
            contexts.append(
                _NumberContext(
                    value=tok.norm,
                    weights=weights,
                    preceding=frozenset(t.norm for t in before),
                    sentence=frozenset(t.norm for _, t in words),
                )
            )
    return contexts


def _claim_subject(claim: str) -> str | None:
    """The claim's first non-numeric content word, taken as its subject."""
    return next((t.norm for t in content_tokens(claim) if not t.is_number), None)


def _context_score(a: dict[str, float], b: dict[str, float]) -> float:
    return sum(min(weight, b[word]) for word, weight in a.items() if word in b)


@dataclass(frozen=True)
class NumberCheck:
    """Outcome of binding each claim number to the evidence."""

    all_matched: bool
    conflict: tuple[str, str] | None  # (claim value, evidence value)


def check_numbers(claim: str, evidence: str) -> NumberCheck:
    """Bind claim numbers to the evidence number describing the same quantity.

    A claim number is *matched* when no differently-valued evidence number is
    better bound than an equal-valued one. It is in *conflict* when a different
    value is clearly better bound (score >= MIN_BINDING_SCORE) and is governed by
    the claim's subject. Ambiguous numbers are neither matched nor conflicting.
    """
    claim_ctx = _number_contexts(claim)
    if not claim_ctx:
        return NumberCheck(all_matched=True, conflict=None)
    evidence_ctx = _number_contexts(evidence)

    # When the evidence mentions the claim's subject, a differing number can
    # only *contradict* if the subject governs it: "Nitrogen ... 78 percent,
    # followed by oxygen at 21" says nothing about oxygen's share being 78.
    # Matching still competes against every number, so an ungoverned rival
    # blocks support.
    subject = _claim_subject(claim)
    if subject is not None and subject not in content_terms(evidence):
        subject = None

    all_matched = True
    for claim_num in claim_ctx:
        value = claim_num.value
        same: float | None = None
        best_any: float | None = None
        best_governed: tuple[float, str] | None = None
        for ev in evidence_ctx:
            score = _context_score(claim_num.weights, ev.weights)
            if ev.value == value:
                same = score if same is None else max(same, score)
                continue
            best_any = score if best_any is None else max(best_any, score)
            if subject is None or ev.governed_by(subject):
                if best_governed is None or score > best_governed[0]:
                    best_governed = (score, ev.value)

        if same is not None and (best_any is None or same >= best_any):
            continue  # matched (ties favour the literal match)
        all_matched = False
        if (
            best_governed is not None
            and best_governed[0] >= MIN_BINDING_SCORE
            and (same is None or best_governed[0] > same)
        ):
            return NumberCheck(all_matched=False, conflict=(value, best_governed[1]))
    return NumberCheck(all_matched=all_matched, conflict=None)


# ---------------------------------------------------------------------------
# Entity substitution
# ---------------------------------------------------------------------------


def _neighbours(toks: list[Token], idx: int) -> tuple[str | None, str | None]:
    prev = next((t.norm for t in reversed(toks[:idx]) if not t.is_capitalized), None)
    nxt = next((t.norm for t in toks[idx + 1 :] if not t.is_capitalized), None)
    return prev, nxt


def missing_entities(claim: str, evidence: str) -> set[str]:
    """Claim proper nouns that never appear (case-insensitively) in the evidence."""
    present = content_terms(evidence)
    return proper_nouns(claim) - present


def find_substitution(claim: str, evidence: str) -> tuple[str, str] | None:
    """Detect a claim entity replaced by a different evidence entity in-slot.

    Requires (a) at least one claim proper noun shared with the evidence, so the
    two texts are about the same subject, and (b) a missing claim entity and an
    evidence-only entity that share a neighbouring non-entity word.
    """
    claim_names = proper_nouns(claim)
    if not claim_names or not (claim_names & content_terms(evidence)):
        return None
    missing = missing_entities(claim, evidence)
    if not missing:
        return None

    claim_toks = content_tokens(claim)
    claim_terms = content_terms(claim)
    for sentence in split_sentences(evidence) or [evidence]:
        ev_toks = content_tokens(sentence)
        ev_slots = {
            t.norm: _neighbours(ev_toks, i)
            for i, t in enumerate(ev_toks)
            if t.is_capitalized and not t.is_number and t.norm not in claim_terms
        }
        for i, tok in enumerate(claim_toks):
            if tok.norm not in missing or not tok.is_capitalized:
                continue
            c_prev, c_next = _neighbours(claim_toks, i)
            for ev_name, (e_prev, e_next) in ev_slots.items():
                if (c_prev and c_prev == e_prev) or (c_next and c_next == e_next):
                    return tok.text, ev_name
    return None


# ---------------------------------------------------------------------------
# Year conflicts
# ---------------------------------------------------------------------------

# Calendar years get a dedicated check: dates are often far from their
# predicate in evidence ("landed the Apollo Lunar Module Eagle on July 20,
# 1969"), beyond the reach of positional number binding.
_MIN_YEAR, _MAX_YEAR = 1000, 2100
_MIN_SHARED_PREDICATE_WORDS = 2


def _years(text: str) -> set[str]:
    return {
        t.norm
        for t in tokenize(text)
        if t.is_number
        and t.norm.isdecimal()
        and len(t.norm) == 4
        and _MIN_YEAR <= int(t.norm) <= _MAX_YEAR
    }


def check_year_conflict(claim: str, evidence: str) -> tuple[str, str] | None:
    """Detect a claim year contradicted by a different year for the same event.

    The claim year must be absent from the evidence, and some evidence sentence
    must state a different year while sharing at least two claim content words,
    one of which is a non-entity predicate word (so that "Neil Armstrong was born
    in 1930" is never contradicted by a sentence about his 1969 landing).
    """
    claim_years = _years(claim)
    missing = sorted(claim_years - _years(evidence))
    if not missing:
        return None
    claim_terms = content_terms(claim)
    predicates = {
        t.norm
        for t in content_tokens(claim)
        if not t.is_number and not t.is_capitalized
    }
    for sentence in split_sentences(evidence):
        other_years = sorted(_years(sentence) - claim_years)
        if not other_years:
            continue
        shared = claim_terms & content_terms(sentence)
        if len(shared) >= _MIN_SHARED_PREDICATE_WORDS and shared & predicates:
            return missing[0], other_years[0]
    return None
