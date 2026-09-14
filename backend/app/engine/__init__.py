"""VerifAI verification engine package.

Phase 2D: real claim verification pipeline.

Components:
    models      — shared internal data structures
    providers   — LLM and search provider abstractions
    extractor   — claim extraction from raw text
    classifier  — domain classification
    searcher    — web source search and normalization
    scorer      — source quality scoring
    judge       — LLM-as-judge evidence evaluation
    decision    — confidence calculation and final verdict
    engine      — top-level orchestrator (entry point)
"""

from app.engine.engine import VerificationEngine, verification_engine

__all__ = ["VerificationEngine", "verification_engine"]
