"""Claims decomposition and classification module."""

from app.modules.claims.classifier import ClassificationResult, ContentClassifier
from app.modules.claims.extractor import (
    BaseClaimExtractor,
    DeterministicClaimExtractor,
    ExtractedClaimItem,
)

__all__ = [
    "BaseClaimExtractor",
    "DeterministicClaimExtractor",
    "ExtractedClaimItem",
    "ContentClassifier",
    "ClassificationResult",
]
