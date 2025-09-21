# csv-test-base

A small Python library to load CSV-based Q/A pairs from resource folders for testing and flashcards.

Features:
- Load all CSV files from a resources directory (package data or filesystem)
- Configurable delimiter (e.g., ",", ";", "\t")
- Choose which column is the question and which is the answer
- Category is auto-detected from the CSV file name (without extension)

## Install

Within your project:

```
pip install .
```

or via VCS (after publishing):

```
pip install git+https://github.com/zlatkapod/csv-test-base.git
```

## Quick start

```python
from csv_test_base import CsvTestBase, ColumnRole

# Example: load csvs from the package resources (default path: package resources/csv)
loader = CsvTestBase(
    delimiter=",",
    question_column=ColumnRole.LEFT,   # or ColumnRole.RIGHT, or an index
)

# Load from a directory on filesystem
categories = loader.load_from_directory("./resources/csv")

for cat_name, items in categories.items():
    print(cat_name)
    for q, a in items:
        print(f"Q: {q} -> A: {a}")
```

## API Overview

- CsvTestBase(delimiter=",", question_column=ColumnRole.LEFT, has_header=False)
- load_from_directory(path): loads all CSVs under path (non-recursive), returns dict[str, list[tuple[str,str]]]
- load_from_package(package, resource_path="resources/csv"): loads CSVs embedded as package data

## CSV Format

- CSV file may have 2+ columns; library will use the two specified columns as question/answer.
- Set has_header=True if the first row is a header; it will be skipped.
- Category is derived from file name without extension.

## License
MIT
