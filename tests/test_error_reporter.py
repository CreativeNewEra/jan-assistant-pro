import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.core import exceptions as exc
from src.core.error_reporter import ErrorReporter


def test_error_reporter_aggregation():
    reporter = ErrorReporter(max_entries=5)
    try:
        raise ValueError("bad")
    except ValueError as e:
        reporter.record_error(e)
    try:
        raise RuntimeError("boom")
    except RuntimeError as e:
        reporter.record_error(e)
    try:
        raise ValueError("again")
    except ValueError as e:
        reporter.record_error(e)

    report = reporter.generate_report()

    assert report["total_errors"] == 3
    assert report["counts"]["ValueError"] == 2
    assert report["counts"]["RuntimeError"] == 1
    assert report["recent"][-1]["message"] == "again"


def test_error_reporter_rolling_log():
    reporter = ErrorReporter(max_entries=2)
    reporter.record_error(Exception("1"))
    reporter.record_error(Exception("2"))
    reporter.record_error(Exception("3"))

    report = reporter.generate_report()
    assert report["total_errors"] == 2
    messages = [e["message"] for e in report["recent"]]
    assert messages == ["2", "3"]


def test_handle_exception_records(monkeypatch):
    captured = []

    def fake_record(err):
        captured.append(err)

    with patch("src.core.exceptions.record_error", fake_record):
        exc.handle_exception(ValueError("boom"))

    assert len(captured) == 1
    assert isinstance(captured[0], ValueError)
