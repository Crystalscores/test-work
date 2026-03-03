from __future__ import annotations

import re
from dataclasses import dataclass, field

SCREEN_TYPES = ("question", "info", "input", "email", "paywall", "other")


@dataclass
class ClassificationResult:
    screen_type: str
    confidence: float
    price_detected: str = ""
    reason: str = ""


@dataclass
class HtmlClassifier:
    llm_enabled: bool = False
    cache: dict[str, ClassificationResult] = field(default_factory=dict)

    def classify(self, url: str, html: str, text: str) -> ClassificationResult:
        cache_key = f"{url}:{hash(text[:3000])}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        lowered = f"{text}\n{html}".lower()
        price = self._extract_price(lowered)

        rules = [
            ("paywall", ["subscribe", "payment", "pay now", "trial", "billing", "$", "€", "₽"]),
            ("email", ["email", "e-mail", "@"]),
            ("input", ["input", "height", "weight", "name", "age", "years old"]),
            ("question", ["question", "quiz", "choose", "select", "option", "answer"]),
            ("info", ["continue", "next", "learn more", "start now"]),
        ]
        for screen_type, tokens in rules:
            if any(token in lowered for token in tokens):
                result = ClassificationResult(
                    screen_type=screen_type,
                    confidence=0.85,
                    price_detected=price,
                    reason="rule-based",
                )
                self.cache[cache_key] = result
                return result

        result = ClassificationResult(screen_type="other", confidence=0.4, price_detected=price, reason="fallback")
        self.cache[cache_key] = result
        return result

    @staticmethod
    def _extract_price(content: str) -> str:
        price_match = re.search(r"(?:\$|€|₽)\s?\d+(?:[.,]\d{1,2})?", content)
        return price_match.group(0) if price_match else ""
