import logging

from src.core.request_context import RequestContext


def test_request_context_logs_with_extra(caplog):
    logger = logging.getLogger("test_request")
    with caplog.at_level(logging.INFO, logger="test_request"):
        ctx = RequestContext(logger)
        ctx.log("info", "hello", foo="bar")
    assert "hello" in caplog.text
    record = caplog.records[0]
    assert record.extra_fields["request_id"] == ctx.request_id
    assert record.extra_fields["foo"] == "bar"
