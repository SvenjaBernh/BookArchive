# Command-line interface

Run the CLI from the project directory with `uv run library-python`. After
installing the project, you can also run `library-python` directly. Get the
overview at any time with:

```console
uv run library-python --help
```

For help on a specific command, append `--help`, for example
`uv run library-python update --help`.

## Arguments and archive

The `add`, `find`, and `update` commands take the book's **title first** and
**author second**. Put quotes around titles or author names that contain spaces:

```console
uv run library-python add "Dune" "Frank Herbert"
```

By default, the CLI reads and writes `~/books.csv` (the current user's home
directory). To select another CSV archive, put `--archive PATH` before the
command:

```console
uv run library-python --archive ./books.csv add "Dune" "Frank Herbert"
uv run library-python --archive ./books.csv list
```

Use the same archive path for each command if you want to work with the same
library.

## Commands

### Add a book

Add a book by passing its title and author in that order:

```console
uv run library-python add "The Left Hand of Darkness" "Ursula K. Le Guin"
```

Titles and author names cannot be empty or whitespace-only. A book with the
same exact title and author already in the archive cannot be added again. Add
does not take rating or comment options; use `update` after adding the book to
set those fields.

### List books

List all books, including any rating or comment:

```console
uv run library-python list
```

### Find a book

Find checks for a book with the exact title **and** author:

```console
uv run library-python find "Dune" "Frank Herbert"
```

Both values must match the archive exactly, including capitalization and
spacing. For example, `"dune"` or a different author name will not match
`"Dune" "Frank Herbert"`.

### Update a book

Update identifies the book with its exact title and author. Supply at least one
field to change:

```console
uv run library-python update "Dune" "Frank Herbert" --rating 4.5
uv run library-python update "Dune" "Frank Herbert" --comment "A great read"
```

You can change both fields in one command:

```console
uv run library-python update "Dune" "Frank Herbert" --rating 4 --comment "A great read"
```

Ratings must be numbers from 1 to 5, inclusive. Comments can contain up to 500
characters. An update only changes the fields named on the command line; any
other existing field is left unchanged.

Clear a field explicitly with its clear option:

```console
uv run library-python update "Dune" "Frank Herbert" --clear-rating
uv run library-python update "Dune" "Frank Herbert" --clear-comment
```

The set and clear options for the same field cannot be used together. You can
also clear one field while setting the other:

```console
uv run library-python update "Dune" "Frank Herbert" --clear-rating --comment "Read again soon"
```

If no book matches the exact title and author, `update` reports that it could
not find the book and makes no changes. Calling `update` without any set or
clear option is an error.
