import tempfile
from pathlib import Path
from csv_test_base import CsvTestBase, ColumnRole


def write_csv(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


def test_load_from_directory_left_right():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        write_csv(d / "dutch.csv", "hallo,hallo\ndag,day\n")
        write_csv(d / "biz.csv", "kpi,indicator\nroi,return\n")

        loader = CsvTestBase(delimiter=",", question_column=ColumnRole.LEFT)
        result = loader.load_from_directory(d)

        assert set(result.keys()) == {"dutch", "biz"}
        assert ("hallo", "hallo") in result["dutch"]
        assert ("roi", "return") in result["biz"]


def test_load_from_directory_with_header_and_right_question():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        write_csv(d / "terms.csv", "q,a\none,two\nthree,four\n")

        loader = CsvTestBase(delimiter=",", question_column=ColumnRole.RIGHT, has_header=True)
        result = loader.load_from_directory(d)
        pairs = result["terms"]
        assert ("two", "one") in pairs
        assert ("four", "three") in pairs
