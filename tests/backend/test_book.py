import math

import pytest

from library_python.backend.book import Book, BookValidationError
from library_python.backend.book_config import (
    MAX_COMMENT_LENGTH,
    MAX_RATING,
    MIN_RATING,
)


@pytest.mark.parametrize(
    ("title", "author"),
    [
        ("", "Author"),
        (" \t\n", "Author"),
        ("Title", ""),
        ("Title", " \t\n"),
        (None, "Author"),
        ("Title", 42),
    ],
)
def test_rejects_empty_or_non_string_title_and_author(
    title: str | None, author: str | int
) -> None:
    with pytest.raises(BookValidationError):
        Book(title=title, author=author)  # type: ignore[arg-type]


def test_preserves_non_blank_title_and_author() -> None:
    book = Book(title="  Dune  ", author="Frank Herbert")

    assert book.title == "  Dune  "
    assert book.author == "Frank Herbert"


def test_rating_uses_configured_range() -> None:
    assert Book("Dune", "Frank Herbert", rating=MIN_RATING).rating == MIN_RATING
    assert Book("Dune", "Frank Herbert", rating=MAX_RATING).rating == MAX_RATING

    with pytest.raises(BookValidationError, match="rating must be between"):
        Book("Dune", "Frank Herbert", rating=MIN_RATING - 0.01)
    with pytest.raises(BookValidationError, match="rating must be between"):
        Book("Dune", "Frank Herbert", rating=MAX_RATING + 0.01)


@pytest.mark.parametrize("rating", [True, False, "4", math.nan, math.inf, -math.inf])
def test_rejects_invalid_rating_values(rating: object) -> None:
    with pytest.raises(BookValidationError):
        Book("Dune", "Frank Herbert", rating=rating)  # type: ignore[arg-type]


def test_integer_rating_is_stored_as_float() -> None:
    book = Book("Dune", "Frank Herbert", rating=int(MIN_RATING))

    assert book.rating == float(MIN_RATING)
    assert type(book.rating) is float


def test_rating_setter_preserves_previous_value_when_invalid() -> None:
    book = Book("Dune", "Frank Herbert", rating=4)

    with pytest.raises(BookValidationError):
        book.set_rating(MAX_RATING + 0.01)

    assert book.rating == 4.0
    book.set_rating(None)
    assert book.rating is None


def test_comment_uses_configured_maximum_length() -> None:
    comment = "x" * MAX_COMMENT_LENGTH
    book = Book("Dune", "Frank Herbert", comment=comment)

    assert book.comment == comment

    with pytest.raises(BookValidationError, match="comment must be at most"):
        Book("Dune", "Frank Herbert", comment=comment + "x")


@pytest.mark.parametrize("comment", [42, True, object()])
def test_rejects_non_string_comment(comment: object) -> None:
    with pytest.raises(BookValidationError, match="comment must be a string"):
        Book("Dune", "Frank Herbert", comment=comment)  # type: ignore[arg-type]


def test_comment_setter_updates_and_clears_comment() -> None:
    book = Book("Dune", "Frank Herbert", comment="Initial comment")

    book.set_comment("Updated comment")
    assert book.comment == "Updated comment"

    book.set_comment(None)
    assert book.comment is None
