import csv
import os
import tempfile
from enum import Enum, auto
from pathlib import Path
from typing import Literal, TypeAlias
from uuid import uuid4

from library_python.backend.book import Book

_BookField: TypeAlias = Literal["id", "title", "author", "rating", "comment"]
_BookRow: TypeAlias = dict[_BookField, str]


class _Unset(Enum):
    VALUE = auto()


class BookArchive:
    """Store and search books in a CSV file."""

    _FIELDNAMES: tuple[_BookField, ...] = ("id", "title", "author", "rating", "comment")

    def __init__(self, file_path: str | Path | None = None) -> None:
        """Initialize the archive.

        Args:
            file_path: CSV file path. Defaults to ``~/books.csv`` when omitted.
        """
        self.file_path = (
            Path(file_path).expanduser()
            if file_path is not None
            else Path.home() / "books.csv"
        )

    def add_book(self, book: Book) -> str:
        """Add a book and return its unique archive ID.

        Books with the same title and author are rejected because archive
        lookups use that pair to identify a book.

        Args:
            book: Validated book to add.

        Returns:
            UUID string assigned to the new archive row.

        Raises:
            ValueError: If a book with the same title and author exists or the
                existing archive has an invalid structure.
            OSError: If the archive cannot be read or written.
            csv.Error: If CSV reading or writing fails.
        """
        books = self._read_books()
        if self._find_book_id(book.title, book.author, books) is not None:
            raise ValueError("a book with this title and author already exists")

        book_id = str(uuid4())
        books.append(
            {
                "id": book_id,
                "title": book.title,
                "author": book.author,
                "rating": "" if book.rating is None else str(book.rating),
                "comment": book.comment or "",
            }
        )
        self._write_books(books)
        return book_id

    def find_book(self, title: str, author: str) -> bool:
        """Check whether a book with the exact title and author exists.

        Args:
            title: Exact title to search for.
            author: Exact author to search for.

        Returns:
            Whether the archive contains a matching book.

        Raises:
            ValueError: If the archive has an invalid structure.
            OSError: If the archive cannot be read.
            csv.Error: If reading the archive fails.
        """
        return self._find_book_id(title, author) is not None

    def list_books(self) -> list[Book]:
        """Return all books in the archive in their stored order.

        Returns:
            The archived books. Returns an empty list if the archive does not
            exist or contains no books.

        Raises:
            ValueError: If the archive structure or a stored book value is
                invalid.
            OSError: If an existing archive cannot be read.
            csv.Error: If reading the archive fails.
        """
        return [
            Book(
                title=record["title"],
                author=record["author"],
                rating=float(record["rating"]) if record["rating"] else None,
                comment=record["comment"] or None,
            )
            for record in self._read_books()
        ]

    def update_book(
        self,
        title: str,
        author: str,
        *,
        rating: float | None | _Unset = _Unset.VALUE,
        comment: str | None | _Unset = _Unset.VALUE,
    ) -> bool:
        """Update a matching book's rating, comment, or both.

        Omit a field to leave it unchanged. Pass None to clear that field.
        Ratings and comment lengths are validated using the book
        configuration.

        Args:
            title: Exact title of the book to update.
            author: Exact author of the book to update.
            rating: Finite number in the configured inclusive range to set,
                None to clear the rating, or omit to leave it unchanged.
            comment: String within the configured length limit to set, None to
                clear the comment, or omit to leave it unchanged.

        Returns:
            Whether a matching book was found and updated.

        Raises:
            ValueError: If neither field is provided, a supplied value is
                invalid, or the archive structure is invalid.
            OSError: If the archive cannot be read or written.
            csv.Error: If CSV reading or writing fails.
        """
        if rating is _Unset.VALUE and comment is _Unset.VALUE:
            raise ValueError("provide a rating or comment to update")

        books = self._read_books()
        book_id = self._find_book_id(title, author, books)
        if book_id is None:
            return False

        record = next(book for book in books if book["id"] == book_id)
        book = Book(
            title=record["title"],
            author=record["author"],
            rating=float(record["rating"]) if record["rating"] else None,
            comment=record["comment"] or None,
        )
        if rating is not _Unset.VALUE:
            book.set_rating(rating)
        if comment is not _Unset.VALUE:
            book.set_comment(comment)

        record["rating"] = "" if book.rating is None else str(book.rating)
        record["comment"] = book.comment or ""
        self._write_books(books)
        return True

    def _find_book_id(
        self,
        title: str,
        author: str,
        books: list[_BookRow] | None = None,
    ) -> str | None:
        """Find the ID of an exact title-and-author match.

        Args:
            title: Exact title to match.
            author: Exact author to match.
            books: Rows to search, or None to read rows from the archive.

        Returns:
            The matching row's ID, or None if no match exists.

        Raises:
            ValueError: If reading the archive encounters invalid structure.
            OSError: If the archive cannot be read.
            csv.Error: If reading the archive fails.
        """
        if books is None:
            books = self._read_books()

        for book in books:
            if book["title"] == title and book["author"] == author:
                return book["id"]
        return None

    def _read_books(self) -> list[_BookRow]:
        """Read and validate all archive rows.

        Returns:
            Archive rows in stored order, or an empty list if the file does
            not exist or is empty.

        Raises:
            ValueError: If the header or a row does not match the archive
                schema.
            OSError: If an existing archive cannot be read.
            csv.Error: If the file contains invalid CSV data.
        """
        if not self.file_path.exists():
            return []

        with self.file_path.open(encoding="utf-8", newline="") as archive_file:
            reader = csv.reader(archive_file)
            fieldnames = next(reader, None)
            if fieldnames is None:
                return []
            if fieldnames != list(self._FIELDNAMES):
                raise ValueError(f"invalid book archive columns in {self.file_path}")

            books: list[_BookRow] = []
            for row in reader:
                if len(row) != len(self._FIELDNAMES):
                    raise ValueError(f"invalid book archive row in {self.file_path}")
                books.append(dict(zip(self._FIELDNAMES, row, strict=True)))
            return books

    def _write_books(self, books: list[_BookRow]) -> None:
        """Atomically write archive rows, including the table header.

        Args:
            books: Complete archive rows to write.

        Raises:
            OSError: If the destination directory or archive cannot be
                created, written, replaced, or cleaned up.
            csv.Error: If CSV serialization fails.
        """
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=self.file_path.parent,
                prefix=f".{self.file_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as archive_file:
                temporary_path = Path(archive_file.name)
                writer = csv.DictWriter(
                    archive_file,
                    fieldnames=self._FIELDNAMES,
                    extrasaction="raise",
                )
                writer.writeheader()
                writer.writerows(books)

            os.replace(temporary_path, self.file_path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
