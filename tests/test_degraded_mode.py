from src.core.degraded_mode import DegradedModeHandler


def test_offline_cached_response():
    handler = DegradedModeHandler()
    handler.cache_response("hi", "cached reply")
    result = handler.handle_offline_request("hi")
    assert "cached reply" in result


def test_offline_help_response():
    handler = DegradedModeHandler()
    result = handler.handle_offline_request("help me")
    assert "Available offline commands" in result


def test_offline_default_message():
    handler = DegradedModeHandler()
    result = handler.handle_offline_request("unknown query")
    assert "offline" in result.lower()
