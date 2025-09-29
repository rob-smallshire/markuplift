"""DOCTYPE strategy pattern for format-specific DOCTYPE handling.

This module provides a strategy pattern for handling DOCTYPE declarations
in different document formats (HTML5, XML, etc.). Each strategy determines
the appropriate DOCTYPE behavior for its format, including default DOCTYPEs
and whether DOCTYPEs should be ensured for complete documents.
"""

from abc import ABC, abstractmethod


class DoctypeStrategy(ABC):
    """Abstract base class for DOCTYPE handling strategies.

    DOCTYPE strategies determine how DOCTYPE declarations should be handled
    for different document formats. They provide format-specific defaults
    and rules for when DOCTYPEs should be automatically applied.
    """

    @abstractmethod
    def get_default_doctype(self) -> str | None:
        """Return the default DOCTYPE declaration for this format.

        Returns:
            The default DOCTYPE string for this format, or None if no
            default should be applied.

        Example:
            >>> strategy = Html5DoctypeStrategy()
            >>> strategy.get_default_doctype()
            '<!DOCTYPE html>'
        """
        pass

    @abstractmethod
    def should_ensure_doctype(self) -> bool:
        """Return whether this format requires a DOCTYPE to be present.

        When True, the strategy will replace existing DOCTYPEs with its
        default if they don't match the expected format. When False,
        existing DOCTYPEs are preserved unless explicitly overridden.

        Returns:
            True if this format should ensure a specific DOCTYPE is present,
            False if existing DOCTYPEs should be preserved.

        Example:
            >>> strategy = Html5DoctypeStrategy()
            >>> strategy.should_ensure_doctype()
            True
        """
        pass


class Html5DoctypeStrategy(DoctypeStrategy):
    """DOCTYPE strategy for HTML5 documents.

    HTML5 requires the simplified `<!DOCTYPE html>` declaration to ensure
    browsers operate in standards mode rather than quirks mode. This strategy
    provides the HTML5 DOCTYPE and ensures it's present for complete documents.

    According to the HTML5 specification, the DOCTYPE is required and must
    be the first thing in the document (before the <html> element).
    """

    def get_default_doctype(self) -> str:
        """Return the HTML5 DOCTYPE declaration.

        Returns:
            The standard HTML5 DOCTYPE: '<!DOCTYPE html>'
        """
        return "<!DOCTYPE html>"

    def should_ensure_doctype(self) -> bool:
        """Return True since HTML5 requires a DOCTYPE.

        HTML5 documents should always have the correct DOCTYPE to ensure
        standards mode in browsers. This strategy will replace any existing
        DOCTYPE with the HTML5 version.

        Returns:
            True - HTML5 requires a specific DOCTYPE
        """
        return True


class XmlDoctypeStrategy(DoctypeStrategy):
    """DOCTYPE strategy for XML documents.

    XML documents do not require DOCTYPE declarations in most cases.
    This strategy preserves any existing DOCTYPEs but does not add
    one automatically. XML DTDs are optional and often not needed
    for modern XML processing.
    """

    def get_default_doctype(self) -> None:
        """Return None since XML doesn't require a default DOCTYPE.

        Returns:
            None - XML documents don't need automatic DOCTYPE insertion
        """
        return None

    def should_ensure_doctype(self) -> bool:
        """Return False since XML doesn't require specific DOCTYPEs.

        XML documents can have various DTDs or no DTD at all. This strategy
        preserves existing DOCTYPEs and doesn't enforce any specific format.

        Returns:
            False - XML preserves existing DOCTYPEs without enforcement
        """
        return False


class NullDoctypeStrategy(DoctypeStrategy):
    """DOCTYPE strategy that maintains current MarkupLift behavior.

    This strategy provides no default DOCTYPE and preserves any existing
    DOCTYPEs without modification. It's used to maintain backward compatibility
    with the existing Formatter behavior.
    """

    def get_default_doctype(self) -> None:
        """Return None to maintain current behavior.

        Returns:
            None - no automatic DOCTYPE insertion
        """
        return None

    def should_ensure_doctype(self) -> bool:
        """Return False to preserve existing DOCTYPEs.

        Returns:
            False - preserve existing DOCTYPEs without modification
        """
        return False
