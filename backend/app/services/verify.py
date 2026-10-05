# checks the quotes the model gives us against the real source text
import re
from difflib import SequenceMatcher
from typing import List, Optional

VERIFIED, PARTIAL, UNSUPPORTED, NONE = "verified", "partial", "unsupported", "none"


def norm(s: str) -> str:
    s = (s or "").lower()
    s = s.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"').replace("\u2013", "-").replace("\u2014", "-")
    s = re.sub(r"[^\w\s@./%:'\"-]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


class SourceIndex:
    def __init__(self, text: str):
        self.text = text
        self.norm_text = norm(text)
        lines = [l for l in re.split(r"\n+", text) if l.strip()]
        sentences: List[str] = []
        for l in lines:
            sentences.extend(re.split(r"(?<=[.!?])\s+", l))
        sentences = [norm(s) for s in sentences if len(s.strip()) > 2]
        windows = list(sentences)
        windows += [f"{a} {b}" for a, b in zip(sentences, sentences[1:])]
        self.windows = windows

    def score(self, evidence: Optional[str]) -> float:
        if not evidence or not evidence.strip():
            return 0.0
        fragments = [f for f in re.split(r"\.\.\.|\u2026", evidence) if len(norm(f)) >= 4] or [evidence]
        scores = [self._score_one(norm(f)) for f in fragments]
        return min(scores)

    def _score_one(self, e: str) -> float:
        if not e:
            return 0.0
        if e in self.norm_text:
            return 1.0
        best = 0.0
        for w in self.windows:
            if abs(len(w) - len(e)) > max(len(e), len(w)) * 3 and len(w) < len(e) * 0.4:
                continue
            sm = SequenceMatcher(None, e, w, autojunk=False)
            covered = sum(b.size for b in sm.get_matching_blocks()) / len(e)
            if covered > best:
                best = covered
                if best >= 0.99:
                    break
        return best

    def status(self, evidence: Optional[str]) -> str:
        if not evidence or not evidence.strip():
            return NONE
        sc = self.score(evidence)
        if sc >= 0.92:
            return VERIFIED
        if sc >= 0.7:
            return PARTIAL
        return UNSUPPORTED


def adjust_confidence(conf: str, status: str) -> str:
    order = ["low", "medium", "high"]
    if status == UNSUPPORTED:
        return "low"
    if status == PARTIAL:
        return order[min(order.index(conf if conf in order else "medium"), 1)]  # cap at medium
    return conf if conf in order else "medium"
