"""Confident Security Python SDK.

A drop-in replacement for the OpenAI Python SDK that provides secure and anonymous
AI inference via Confident Security.
"""

from ._version import __version__, LIBCONFSEC_VERSION
from .client import ConfsecClient

__all__ = ["__version__", "LIBCONFSEC_VERSION", "ConfsecClient"]
