import csv
from pathlib import Path
from uuid import UUID

import pytest

from library_python.backend.book import Book
from library_python.backend.book_archive import BookArchive
from library_python.backend.book_config import MAX_COMMENT_LENGTH, MAX_RATING


def make_archive(tmp_path: Path) -> BookArchive:
    """Create an archive rooted in pytest's isolated temporary directory."""
    return BookArchive(tmp_path / "nested" / "books.csv")


def test_missing_archive_is_empty_and_is_not_created_by_reads(
    tmp_path: Path,
) -> None:
    archive = make_archive(tmp_path)

    assert archive.list_books() == []
    assert archive.find_book("Dune", "Frank Herbert") is False
    assert not archive.file_path.exists()


def test_add_book_persists_a_unique_id_and_relational_columns(
    tmp_path: Path,
) -> None:
    archive = make_archive(tmp_path)
    book = Book("Dune, Part One", "Frank Herbert", rating=4, comment="A\nclassic")

    book_id = archive.add_book(book)

    assert str(UUID(book_id)) == book_id
    with archive.file_path.open(encoding="utf-8", newline="") as archive_file:
        reader = csv.DictReader(archive_file)
        assert reader.fieldnames == ["id", "title", "author", "rating", "comment"]
        rows = list(reader)
    assert rows == [
        {
            "id": book_id,
            "title": "Dune, Part One",
            "author": "Frank Herbert",
            "rating": "4.0",
            "comment": "A\nclassic",
        }
    ]


def test_add_rejects_duplicate_title_and_author(tmp_path: Path) -> None:
    archive = make_archive(tmp_path)
    archive.add_book(Book("Dune", "Frank Herbert"))

    with pytest.raises(ValueError, match="already exists"):
        archive.add_book(Book("Dune", "Frank Herbert"))

    assert len(archive.list_books()) == 1


def test_find_matches_exact_title_and_author(tmp_path: Path) -> None:
    archive = make_archive(tmp_path)
    archive.add_book(Book("Dune", "Frank Herbert"))

    assert archive.find_book("Dune", "Frank Herbert") is True
    assert archive.find_book("dune", "Frank Herbert") is False
    assert archive.find_book("Dune", "Other Author") is False


def test_list_books_restores_all_book_fields_in_order(tmp_path: Path) -> None:
    archive = make_archive(tmp_path)
    archive.add_book(Book("Dune", "Frank Herbert", 4.5, "Excellent"))
    archive.add_book(Book("Foundation", "Isaac Asimov"))

    books = archive.list_books()

    assert [(book.title, book.author) for book in books] == [
        ("Dune", "Frank Herbert"),
        ("Foundation", "Isaac Asimov"),
    ]
    assert (books[0].rating, books[0].comment) == (4.5, "Excellent")
    assert (books[1].rating, books[1].comment) == (None, None)


def test_update_changes_requested_fields_and_leaves_others_unchanged(
    tmp_path: Path,
) -> None:
    archive = make_archive(tmp_path)
    archive.add_book(Book("Dune", "Frank Herbert", 4, "Initial"))

    assert archive.update_book("Dune", "Frank Herbert", rating=5)
    book = archive.list_books()[0]
    assert (book.rating, book.comment) == (5.0, "Initial")

    assert archive.update_book("Dune", "Frank Herbert", comment="Updated")
    book = archive.list_books()[0]
    assert (book.rating, book.comment) == (5.0, "Updated")


def test_update_can_explicitly_clear_fields(tmp_path: Path) -> None:
    archive = make_archive(tmp_path)
    archive.add_book(Book("Dune", "Frank Herbert", 4, "Initial"))

    assert archive.update_book("Dune", "Frank Herbert", rating=None, comment=None)
    book = archive.list_books()[0]
    assert (book.rating, book.comment) == (None, None)


def test_update_missing_book_returns_false(tmp_path: Path) -> None:
    archive = make_archive(tmp_path)

    assert archive.update_book("Dune", "Frank Herbert", rating=4) is False


def test_update_rejects_missing_fields_and_invalid_values_without_changing_file(
    tmp_path: Path,
) -> None:
    archive = make_archive(tmp_path)
    archive.add_book(Book("Dune", "Frank Herbert", 4, "Initial"))
    original_contents = archive.file_path.read_bytes()

    with pytest.raises(ValueError, match="provide a rating or comment"):
        archive.update_book("Dune", "Frank Herbert")
    with pytest.raises(ValueError, match="rating must be between"):
        archive.update_book("Dune", "Frank Herbert", rating=MAX_RATING + 0.01)
    with pytest.raises(ValueError, match="comment must be at most"):
        archive.update_book(
            "Dune",
            "Frank Herbert",
            comment="x" * (MAX_COMMENT_LENGTH + 1),
        )

    assert archive.file_path.read_bytes() == original_contents


@pytest.mark.parametrize(
    "contents",
    [
        "wrong,header\n",
        "id,title,author,rating,comment\nid-only\n",
    ],
)
def test_read_rejects_malformed_archive_rows(tmp_path: Path, contents: str) -> None:
    archive = make_archive(tmp_path)
    archive.file_path.parent.mkdir(parents=True)
    archive.file_path.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError, match="invalid book archive"):
        archive.list_books()
