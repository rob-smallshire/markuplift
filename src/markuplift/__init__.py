from .formatter import Formatter, DocumentFormatter

__all__ = [
    "Formatter",
    "DocumentFormatter"
]

from collections import namedtuple

Version = namedtuple("Version", ["major", "minor", "patch"])
__version__ = "1.0.0"
__version_info__ = Version(*(__version__.split(".")))
