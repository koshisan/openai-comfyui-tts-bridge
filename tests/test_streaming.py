"""Unit tests for text splitter."""
from __future__ import annotations

from tts_bridge.streaming import chunk_sentences, split_sentences


def test_split_simple():
    assert split_sentences("Hallo Welt. Wie geht's dir? Gut!") == [
        "Hallo Welt.",
        "Wie geht's dir?",
        "Gut!",
    ]


def test_split_at_period_then_newline():
    """Bullet lines that end with `.` split into individual chunks — fine for TTS."""
    parts = split_sentences("Punkt eins.\nPunkt zwei.\nPunkt drei.")
    assert parts == ["Punkt eins.", "Punkt zwei.", "Punkt drei."]


def test_split_keeps_unterminated_line_attached():
    """Line without terminal punctuation stays glued to the next sentence."""
    parts = split_sentences("Zeile eins ohne Punkt\nZeile zwei.")
    # No `.!?` before the `\n` → no split there.
    assert parts == ["Zeile eins ohne Punkt\nZeile zwei."]


def test_split_paragraph_breaks():
    text = "Absatz eins.\n\nAbsatz zwei."
    assert split_sentences(text) == ["Absatz eins.", "Absatz zwei."]


def test_split_empty():
    assert split_sentences("") == []
    assert split_sentences("   ") == []


def test_chunk_sentences_groups():
    sents = ["Eins.", "Zwei.", "Drei.", "Vier."]
    assert chunk_sentences(sents, 1) == sents
    assert chunk_sentences(sents, 2) == ["Eins. Zwei.", "Drei. Vier."]
    assert chunk_sentences(sents, 3) == ["Eins. Zwei. Drei.", "Vier."]
