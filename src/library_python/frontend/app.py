import csv
from pathlib import Path

from nicegui import ui
from nicegui.elements.column import Column
from nicegui.elements.input import Input
from nicegui.elements.number import Number
from nicegui.elements.textarea import Textarea

from library_python.backend.book import Book, BookValidationError
from library_python.backend.book_archive import BookArchive
from library_python.backend.book_config import (
    MAX_COMMENT_LENGTH,
    MAX_RATING,
    MIN_RATING,
)


class LibraryPage:
    """Build and handle interactions for the library page."""

    def __init__(self, archive_path: Path | None = None) -> None:
        """Initialize the page and its archive.

        Args:
            archive_path: CSV archive path, or None to use the default
                ``~/books.csv``.
        """
        self.archive = BookArchive(archive_path)
        self.title_input: Input | None = None
        self.author_input: Input | None = None
        self.rating_input: Number | None = None
        self.comment_input: Textarea | None = None
        self.archive_container: Column | None = None

    def build(self) -> None:
        """Build the page controls and render the initial archive view."""
        ui.label("Book Library").classes("text-h4")
        ui.label(f"Archive: {self.archive.file_path}").classes("text-caption")

        with ui.row().classes("w-full items-center"):
            self.title_input = ui.input("Title").classes("grow")
            self.author_input = ui.input("Author").classes("grow")

        with ui.row().classes("w-full items-center"):
            self.rating_input = ui.number(
                "Rating",
                min=MIN_RATING,
                max=MAX_RATING,
                step=0.1,
            ).classes("grow")
            self.rating_input.props(
                f'placeholder="Optional ({MIN_RATING:g}-{MAX_RATING:g})"'
            )
            self.comment_input = (
                ui.textarea("Comment")
                .props(
                    f"maxlength={MAX_COMMENT_LENGTH} "
                    f'placeholder="Optional, up to {MAX_COMMENT_LENGTH} characters"'
                )
                .classes("grow")
            )

        ui.button("Add book", on_click=self.add_book, icon="add")
        self.archive_container = ui.column().classes("w-full")
        self.refresh_archive()

    def refresh_archive(self) -> None:
        """Reload and render the current archive contents.

        Raises:
            RuntimeError: If called before the page has been built.
        """
        if self.archive_container is None:
            raise RuntimeError("The library page has not been built")

        self.archive_container.clear()
        with self.archive_container:
            if not self.archive.file_path.exists():
                ui.label("No archive yet. Add a book to create your library.").classes(
                    "text-subtitle1"
                )
                return

            try:
                books = self.archive.list_books()
            except (OSError, csv.Error, ValueError) as error:
                ui.label(f"Could not read the book archive: {error}").classes(
                    "text-negative"
                )
                return

            if not books:
                ui.label("The archive exists, but it contains no books.").classes(
                    "text-subtitle1"
                )
                return

            rows: list[dict[str, str | int]] = [
                {
                    "key": index,
                    "title": book.title,
                    "author": book.author,
                    "rating": f"{book.rating:g}/5"
                    if book.rating is not None
                    else "Not rated",
                    "comment": book.comment or "",
                }
                for index, book in enumerate(books)
            ]
            columns = [
                {"name": "title", "label": "Title", "field": "title", "align": "left"},
                {
                    "name": "author",
                    "label": "Author",
                    "field": "author",
                    "align": "left",
                },
                {
                    "name": "rating",
                    "label": "Rating",
                    "field": "rating",
                    "align": "left",
                },
                {
                    "name": "comment",
                    "label": "Comment",
                    "field": "comment",
                    "align": "left",
                },
            ]
            ui.table(columns=columns, rows=rows, row_key="key").classes("w-full")

    def add_book(self) -> None:
        """Validate the form and add its book to the archive.

        Empty title or author values and invalid review fields are reported
        through the UI without writing to the archive. Archive and validation
        failures are also shown to the user; successful additions clear the
        form, refresh the table, and show a confirmation.

        Raises:
            RuntimeError: If called before the page controls have been built.
        """
        if (
            self.title_input is None
            or self.author_input is None
            or self.rating_input is None
            or self.comment_input is None
        ):
            raise RuntimeError("The library page has not been built")

        title = (self.title_input.value or "").strip()
        author = (self.author_input.value or "").strip()
        if not title or not author:
            ui.notify("Please enter both a title and an author.", type="warning")
            return

        try:
            book = Book(
                title=title,
                author=author,
                rating=self.rating_input.value,
                comment=(self.comment_input.value or "").strip() or None,
            )
        except BookValidationError as error:
            ui.notify(f"Please check the rating and comment: {error}.", type="negative")
            return

        try:
            self.archive.add_book(book)
        except ValueError as error:
            ui.notify(f"Could not add book: {error}.", type="negative")
            return
        except (OSError, csv.Error) as error:
            ui.notify(f"Could not write to the archive: {error}", type="negative")
            return

        self.title_input.set_value("")
        self.author_input.set_value("")
        self.rating_input.set_value(None)
        self.comment_input.set_value("")
        self.refresh_archive()
        ui.notify(f'Added "{title}" by {author}.', type="positive")


def run_frontend(
    archive_path: Path | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 8080,
) -> None:
    """Run the book library browser frontend.

    Args:
        archive_path: CSV archive to display, or None to use ``~/books.csv``.
        host: Network interface on which to serve the frontend.
        port: TCP port on which to serve the frontend.
    """
    page = LibraryPage(archive_path)
    ui.page("/")(page.build)
    # NiceGUI's public runner exposes partially unknown types to Pylance.
    ui.run(  # type: ignore[reportUnknownMemberType]
        title="Book Library", host=host, port=port, reload=False
    )
