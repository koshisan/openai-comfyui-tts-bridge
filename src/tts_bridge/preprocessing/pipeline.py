"""Preprocessing pipeline scaffold.

Design intent (not yet implemented):

    Preprocessor(rules=[
        StripEmoji(),
        FlattenMarkdown(),
        NumberToWords(lang="de"),
        RegexReplace(pattern=r"\\bLLM\\b", replacement="Sprachmodell"),
    ]).apply(text) -> cleaned_text

Each rule is a callable `str -> str`. The pipeline applies them left-to-right.
Rules are pluggable so voice presets can select their own subsets.
"""
from __future__ import annotations

from collections.abc import Callable

from ..config import PreprocessingConfig

# A preprocessing rule: takes text, returns text. Rules are composed left-to-right.
Rule = Callable[[str], str]


class Preprocessor:
    def __init__(self, rules: list[Rule] | None = None):
        self.rules = rules or []

    def apply(self, text: str) -> str:
        for r in self.rules:
            text = r(text)
        return text


def build_default_preprocessor(config: PreprocessingConfig) -> Preprocessor:
    """Build the preprocessor from config. Currently returns a no-op pipeline."""
    if not config.enabled:
        return Preprocessor(rules=[])
    # TODO: assemble rules based on config once implemented.
    return Preprocessor(rules=[])


def preprocess(text: str, config: PreprocessingConfig) -> str:
    """Convenience wrapper: build a preprocessor and apply it once."""
    return build_default_preprocessor(config).apply(text)
