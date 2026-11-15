import argparse
import csv
import sys
from collections.abc import Sequence
from pathlib import Path

from library_python.backend.book import Book
from library_python.backend.book_archive import BookArchive


def _create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser.

    Returns:
        Parser for archive selection and book-management commands.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Manage your book library.\n\n"
            "For add, find, and update, supply the TITLE first and AUTHOR second. "
            "Quote values containing spaces. Find and update match the exact "
            "title and author (including capitalization and spacing). The "
            "--archive option, when used, goes before the command."
        ),
        epilog=(
            "Examples:\n"
            '  library-python add "Dune" "Frank Herbert"\n'
            '  library-python find "Dune" "Frank Herbert"\n'
            '  library-python update "Dune" "Frank Herbert" --rating 4.5\n'
            '  library-python update "Dune" "Frank Herbert" '
            '--comment "A great read"\n'
            '  library-python update "Dune" "Frank Herbert" --clear-rating\n'
            "  library-python --archive ./books.csv list\n\n"
            "Run 'library-python COMMAND --help' for command-specific help."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--archive",
        type=Path,
        metavar="PATH",
        help="CSV archive path; place before the command (default: ~/books.csv)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    add_command = commands.add_parser(
        "add",
        help="add a book to the library",
        description="Add a book. Positional arguments must be TITLE followed by AUTHOR.",
        epilog='Example: library-python add "Dune" "Frank Herbert"',
    )
    add_command.add_argument("title", metavar="TITLE", help="the book's title")
    add_command.add_argument("author", metavar="AUTHOR", help="the book's author")
    commands.add_parser(
        "list",
        help="list all books in the library",
        description="List every book, including its rating and comment if present.",
    )
    find_command = commands.add_parser(
        "find",
        help="find a book by its exact title and author",
        description=(
            "Check whether a book exists by matching its exact title and author. "
            "Capitalization and spacing must match."
        ),
        epilog='Example: library-python find "Dune" "Frank Herbert"',
    )
    find_command.add_argument("title", metavar="TITLE", help="the book's title")
    find_command.add_argument("author", metavar="AUTHOR", help="the book's author")
    update_command = commands.add_parser(
        "update",
        help="update or clear a book's rating and/or comment",
        description=(
            "Update a book selected by its exact TITLE and AUTHOR. Provide at "
            "least one option. You can set or clear the rating and comment in "
            "the same command; any field not mentioned remains unchanged."
        ),
        epilog=(
            "Examples:\n"
            '  library-python update "Dune" "Frank Herbert" --rating 4.5\n'
            '  library-python update "Dune" "Frank Herbert" '
            '--comment "A great read"\n'
            '  library-python update "Dune" "Frank Herbert" '
            '--rating 4 --comment "A great read"\n'
            '  library-python update "Dune" "Frank Herbert" --clear-rating\n'
            '  library-python update "Dune" "Frank Herbert" --clear-comment'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    update_command.add_argument("title", metavar="TITLE", help="the book's title")
    update_command.add_argument("author", metavar="AUTHOR", help="the book's author")
    rating_options = update_command.add_mutually_exclusive_group()
    rating_options.add_argument(
        "--rating",
        type=float,
        metavar="1-5",
        help="set rating from 1 to 5, inclusive",
    )
    rating_options.add_argument(
        "--clear-rating", action="store_true", help="remove the existing rating"
    )
    comment_options = update_command.add_mutually_exclusive_group()
    comment_options.add_argument(
        "--comment",
        metavar="TEXT",
        help="set comment (up to 500 characters)",
    )
    comment_options.add_argument(
        "--clear-comment", action="store_true", help="remove the existing comment"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the book library command-line interface.

    Args:
        argv: Argument strings to parse, or None to use ``sys.argv``.

    Returns:
        Exit status: zero for successful commands, one for an operation or
        lookup failure, and two when an update has no requested fields.

    Raises:
        SystemExit: If argument parsing fails or help is requested.
    """
    parser = _create_parser()
    args = parser.parse_args(argv)
    archive = BookArchive(args.archive)

    if args.command == "add":
        try:
            archive.add_book(Book(title=args.title, author=args.author))
        except ValueError as error:
            print(f"Error: Could not add book: {error}.", file=sys.stderr)
            return 1
        except (OSError, csv.Error) as error:
            print(
                f"Error: Could not write to the book archive: {error}", file=sys.stderr
            )
            return 1

        print(f'Added "{args.title}" by {args.author} to your library.')
        return 0

    if args.command == "list":
        try:
            books = archive.list_books()
        except (OSError, csv.Error, ValueError) as error:
            print(f"Error: Could not read the book archive: {error}", file=sys.stderr)
            return 1

        if not books:
            print("Your library is empty.")
            return 0

        print(f"Your library contains {len(books)} book(s):")
        for index, book in enumerate(books, start=1):
            rating = f"{book.rating:g}/5" if book.rating is not None else "Not rated"
            print(f'\n{index}. "{book.title}" by {book.author}')
            print(f"   Rating: {rating}")
            if book.comment is not None:
                print(f"   Comment: {book.comment}")
        return 0

    if args.command == "find":
        try:
            found = archive.find_book(args.title, args.author)
        except (OSError, csv.Error, ValueError) as error:
            print(f"Error: Could not search the book archive: {error}", file=sys.stderr)
            return 1

        if found:
            print(f'Found "{args.title}" by {args.author} in your library.')
            return 0

        print(f'"{args.title}" by {args.author} is not in your library.')
        return 1

    if args.command == "update":
        has_rating = args.rating is not None or args.clear_rating
        has_comment = args.comment is not None or args.clear_comment
        if not has_rating and not has_comment:
            print(
                "Error: Provide a value to update or explicitly clear "
                "(--rating, --comment, --clear-rating, or --clear-comment).",
                file=sys.stderr,
            )
            return 2

        rating = None if args.clear_rating else args.rating
        comment = None if args.clear_comment else args.comment
        try:
            if has_rating and has_comment:
                updated = archive.update_book(
                    args.title, args.author, rating=rating, comment=comment
                )
            elif has_rating:
                updated = archive.update_book(args.title, args.author, rating=rating)
            else:
                updated = archive.update_book(args.title, args.author, comment=comment)
        except (OSError, csv.Error, TypeError, ValueError) as error:
            print(f"Error: Could not update the book: {error}", file=sys.stderr)
            return 1

        if not updated:
            print(f'Could not update: "{args.title}" by {args.author} was not found.')
            return 1

        print(f'Updated "{args.title}" by {args.author}.')
        return 0

    parser.error("No command was provided.")
    return 2
