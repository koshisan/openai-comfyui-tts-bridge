"""Text preprocessing pipeline.

Currently a no-op passthrough. Hooks are documented in `pipeline.py`.
TODO: implement emoji strip, markdown flattening, number-to-words, custom regex.
"""

from .pipeline import Preprocessor, preprocess

__all__ = ["Preprocessor", "preprocess"]
