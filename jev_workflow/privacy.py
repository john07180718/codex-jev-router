"""Best-effort blocking, NOT a complete data-loss-prevention system."""
from __future__ import annotations
import re

PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]{16,})\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{8,}", re.I),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r'''["']?(?:api[_-]?key|password|secret|access[_-]?token|cookie)["']?\s*[:=]\s*["']?[A-Za-z0-9+/=_-]{8,}''', re.I),
)

def sensitive(payload: bytes, api_key: str = "") -> bool:
    content = payload.decode("utf-8")
    if api_key and api_key in content:
        return True
    return any(p.search(content) for p in PATTERNS)
