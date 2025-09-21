from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, Union
import importlib.resources as pkg_resources


class ColumnRole(Enum):
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True)
class LoadResult:
    """Container for loaded Q/A pairs across categories.

    categories: mapping of category name to list of (question, answer) tuples
    """

    categories: Dict[str, List[Tuple[str, str]]]

    def __iter__(self) -> Iterator[Tuple[str, List[Tuple[str, str]]]]:
        return iter(self.categories.items())


ColumnSelector = Union[ColumnRole, int]


class CsvTestBase:
    """Core loader for CSV-based Q/A pairs.

    Parameters:
      - delimiter: CSV delimiter (default ",").
      - question_column: which column acts as question (LEFT, RIGHT, or a zero-based index).
      - answer_column: optional explicit answer column; if None, it is inferred as the other side.
      - has_header: whether to skip the first row as header.
      - encoding: file encoding (default utf-8).
    """

    def __init__(
        self,
        delimiter: str = ",",
        question_column: ColumnSelector = ColumnRole.LEFT,
        answer_column: Optional[ColumnSelector] = None,
        has_header: bool = False,
        encoding: str = "utf-8",
    ) -> None:
        self.delimiter = delimiter
        self.question_column = question_column
        self.answer_column = answer_column
        self.has_header = has_header
        self.encoding = encoding

    def load_from_directory(self, path: Union[str, Path]) -> Dict[str, List[Tuple[str, str]]]:
        """Load all CSV files from a directory (non-recursive).

        Returns a dict mapping category -> list[(question, answer)]
        Category is derived from file name without extension.
        """
        base = Path(path)
        if not base.exists() or not base.is_dir():
            raise FileNotFoundError(f"Directory not found: {base}")

        result: Dict[str, List[Tuple[str, str]]] = {}
        for f in sorted(base.iterdir()):
            if f.is_file() and f.suffix.lower() in {".csv", ".tsv"}:
                category = f.stem
                items = list(self._load_file(f))
                result[category] = items
        return result

    def load_from_files(self, files: Sequence[Union[str, Path]]) -> Dict[str, List[Tuple[str, str]]]:
        """Load from explicit list of file paths. Category from filename."""
        result: Dict[str, List[Tuple[str, str]]] = {}
        for p in files:
            f = Path(p)
            category = f.stem
            items = list(self._load_file(f))
            result[category] = items
        return result

    def load_from_package(self, package: Union[str, object], resource_path: str = "resources/csv") -> Dict[str, List[Tuple[str, str]]]:
        """Load CSVs embedded as package resources under resource_path.

        Example: package=<your package>, resource_path="resources/csv"
        """
        result: Dict[str, List[Tuple[str, str]]] = {}
        try:
            base = pkg_resources.files(package).joinpath(resource_path)
        except Exception as e:
            raise FileNotFoundError(f"Unable to access resources at {package}:{resource_path}: {e}")
        if not base.is_dir():
            raise FileNotFoundError(f"Resource path is not a directory: {package}:{resource_path}")

        for entry in base.iterdir():
            if entry.is_file() and entry.suffix.lower() in {".csv", ".tsv"}:
                category = entry.stem
                with entry.open("r", encoding=self.encoding) as fh:
                    reader = csv.reader(fh, delimiter=self.delimiter)
                    first = True
                    items: List[Tuple[str, str]] = []
                    for row in reader:
                        if not row or all(cell.strip() == "" for cell in row):
                            continue
                        if first and self.has_header:
                            first = False
                            continue
                        first = False
                        q_idx, a_idx = self._resolve_columns(row)
                        q = row[q_idx].strip()
                        a = row[a_idx].strip()
                        if q == "" and a == "":
                            continue
                        items.append((q, a))
                result[category] = items
        return result

    def _resolve_columns(self, row: Sequence[str]) -> Tuple[int, int]:
        # Decide indices for question and answer
        def to_index(sel: ColumnSelector, width: int) -> int:
            if isinstance(sel, int):
                return sel
            if sel == ColumnRole.LEFT:
                return 0
            if sel == ColumnRole.RIGHT:
                return width - 1 if width > 0 else 0
            raise ValueError(f"Unknown column selector: {sel}")

        width = len(row)
        q_idx = to_index(self.question_column, width)
        if self.answer_column is None:
            # Inference: if question is LEFT, answer is RIGHT; if RIGHT, answer is LEFT; else pick opposite if possible
            if isinstance(self.question_column, ColumnRole):
                a_idx = 1 if q_idx == 0 and width > 1 else (0 if width > 1 else 0)
            else:
                a_idx = 0 if q_idx != 0 else (1 if width > 1 else 0)
        else:
            a_idx = to_index(self.answer_column, width)
        if q_idx == a_idx:
            # Try to adjust answer index if possible
            a_idx = 1 if q_idx == 0 and width > 1 else 0
        # Bound checks
        if not (0 <= q_idx < width) or not (0 <= a_idx < width):
            raise IndexError(f"Column indices out of range for row of width {width}: q={q_idx}, a={a_idx}")
        return q_idx, a_idx

    def _load_file(self, path: Path) -> Iterable[Tuple[str, str]]:
        with path.open("r", encoding=self.encoding, newline="") as fh:
            reader = csv.reader(fh, delimiter=self.delimiter)
            first = True
            for row in reader:
                if not row or all(cell.strip() == "" for cell in row):
                    continue
                if first and self.has_header:
                    first = False
                    continue
                first = False
                q_idx, a_idx = self._resolve_columns(row)
                q = row[q_idx].strip()
                a = row[a_idx].strip()
                if q == "" and a == "":
                    continue
                yield q, a
