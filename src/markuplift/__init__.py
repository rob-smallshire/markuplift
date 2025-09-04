from .formatter import format_doc

__all__ = [
    "format_doc",
]

from collections import namedtuple

Version = namedtuple("Version", ["major", "minor", "patch"])
__version__ = "0.1.0"
__version_info__ = Version(*(__version__.split(".")))
