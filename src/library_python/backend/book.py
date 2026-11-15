import math
from dataclasses import dataclass, field

from library_python.backend.book_config import (
    MAX_COMMENT_LENGTH,
    MAX_RATING,
    MIN_RATING,
)


class BookValidationError(ValueError):
    """Raised when a book field contains an invalid value."""


def _validate_required_text(value: str, field_name: str) -> None:
    """Validate non-empty text without changing its value.

    Args:
        value: Text to validate.
        field_name: Field name used in the validation error message.

    Raises:
        BookValidationError: If value is not a string or contains only
            whitespace.
    """
    if not isinstance(value, str):  # type: ignore
        raise BookValidationError(f"{field_name} must be a string")
    if not value.strip():
        raise BookValidationError(f"{field_name} cannot be empty or whitespace")


@dataclass(init=False)
class Book:
    """A book and its optional rating and comment.

    Attributes:
        title: The book's title. Read-only after initialization.
        author: The book's author. Read-only after initialization.
    """

    _title: str = field(repr=False)
    _author: str = field(repr=False)
    _rating: float | None = field(default=None, repr=False)
    _comment: str | None = field(default=None, repr=False)

    def __init__(
        self,
        title: str,
        author: str,
        rating: float | None = None,
        comment: str | None = None,
    ) -> None:
        """Initialize a book, optionally including its rating and comment.

        Args:
            title: The book's non-empty title. Whitespace-only strings are
                rejected; other text is preserved without modification.
            author: The book's non-empty author. Whitespace-only strings are
                rejected; other text is preserved without modification.
            rating: Optional numeric rating within the configured inclusive
                range. Integers are accepted and stored as floats. Pass None
                for no rating.
            comment: Optional comment of at most the configured maximum length.
                Pass None for no comment.

        Raises:
            BookValidationError: If a required text field, rating, or comment is
                invalid.
        """
        _validate_required_text(title, "title")
        _validate_required_text(author, "author")
        self._title = title
        self._author = author
        self._rating = None
        self._comment = None
        self.set_rating(rating)
        self.set_comment(comment)

    @property
    def title(self) -> str:
        """The book's title."""
        return self._title

    @property
    def author(self) -> str:
        """The book's author."""
        return self._author

    @property
    def rating(self) -> float | None:
        """The book's rating, or None if it has not been rated."""
        return self._rating

    def set_rating(self, rating: float | None) -> None:
        """Set the book's rating.

        Pass None to remove the rating. Otherwise, the rating must be between
        1 and 5, inclusive. Integer ratings are stored as floats.

        Args:
            rating: Finite number in the configured inclusive range, or None
                to remove the rating.

        Raises:
            BookValidationError: If the rating is not a finite number within
                the configured inclusive range. Booleans are not accepted.
        """
        if rating is not None:
            # bool is a subclass of int, but True and False are not ratings.
            if isinstance(rating, bool):
                raise BookValidationError("rating must be a number")
            if not isinstance(rating, (int, float)):  # type: ignore
                raise BookValidationError("rating must be a number")
            if not math.isfinite(rating) or not MIN_RATING <= rating <= MAX_RATING:
                raise BookValidationError(
                    f"rating must be between {MIN_RATING:g} and {MAX_RATING:g}"
                )

        self._rating = float(rating) if rating is not None else None

    @property
    def comment(self) -> str | None:
        """The book's comment, or None if it has no comment."""
        return self._comment

    def set_comment(self, comment: str | None) -> None:
        """Set the book's comment.

        Pass None to remove the comment. Otherwise, it must be at most
        ``MAX_COMMENT_LENGTH`` characters, as configured in ``book_config``.

        Args:
            comment: String within the configured maximum length, or None to
                remove the comment.

        Raises:
            BookValidationError: If the comment is not a string or exceeds the
                configured maximum length.
        """
        if comment is not None:
            if not isinstance(comment, str):  # type: ignore
                raise BookValidationError("comment must be a string")
            if len(comment) > MAX_COMMENT_LENGTH:
                raise BookValidationError(
                    f"comment must be at most {MAX_COMMENT_LENGTH} characters"
                )

        self._comment = comment
