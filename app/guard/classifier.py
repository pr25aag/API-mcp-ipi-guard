"""
The guard hook — sits between tool execution and the agent's next
reasoning step (proposal Section 5.1). Scores a tool output and returns
a verdict. Automatically uses the trained DeBERTa checkpoint when
GUARD_MODEL_PATH is set and loadable; otherwise falls back to the
heuristic scorer so the service is always usable.
"""
from __future__ import annotations
from app.config import settings
from app.guard.heuristic import heuristic_score

_model = None
_tokenizer = None
_backend = "heuristic"
_load_error: str | None = None


def _try_load_deberta():
    global _model, _tokenizer, _backend, _load_error
    if not settings.guard_model_path:
        return
    try:
        import torch  # noqa: F401
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        _tokenizer = AutoTokenizer.from_pretrained(settings.guard_model_path)
        _model = AutoModelForSequenceClassification.from_pretrained(settings.guard_model_path)
        _model.eval()
        _backend = "deberta"
    except Exception as e:  # noqa: BLE001 — deliberately broad: any failure
        # here must be non-fatal, we fall back to the heuristic instead of
        # crashing the whole API.
        _load_error = str(e)
        _model = None
        _tokenizer = None
        _backend = "heuristic"


_try_load_deberta()


class GuardVerdict:
    def __init__(self, label: str, score: float, category: str | None, backend: str):
        self.label = label            # "benign" | "injected"
        self.score = score            # 0..1, higher = more likely injected
        self.category = category      # best-guess attack category, if any
        self.backend = backend        # "heuristic" | "deberta"

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "score": self.score,
            "category": self.category,
            "backend": self.backend,
            "threshold": settings.guard_threshold,
        }


def score_text(text: str) -> GuardVerdict:
    if _backend == "deberta" and _model is not None:
        import torch

        with torch.no_grad():
            inputs = _tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            logits = _model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)[0]
            score = float(probs[1]) if probs.shape[0] > 1 else float(probs[0])
        label = "injected" if score >= settings.guard_threshold else "benign"
        return GuardVerdict(label, score, None, "deberta")

    score, category = heuristic_score(text)
    label = "injected" if score >= settings.guard_threshold else "benign"
    return GuardVerdict(label, score, category, "heuristic")


def guard_status() -> dict:
    return {
        "backend": _backend,
        "guard_model_path": settings.guard_model_path,
        "load_error": _load_error,
    }
