from src.core.metrics import tool_calls, tool_errors, record_tool, export_metrics


class Dummy:
    @record_tool("demo")
    def ok(self):
        return {"success": True}

    @record_tool("demo")
    def fail(self):
        return {"success": False}


def test_tool_counters_increment():
    d = Dummy()
    before = tool_calls.labels(tool="demo")._value.get()
    d.ok()
    after = tool_calls.labels(tool="demo")._value.get()
    assert after == before + 1


def test_tool_errors_increment():
    d = Dummy()
    before = tool_errors.labels(tool="demo")._value.get()
    d.fail()
    after = tool_errors.labels(tool="demo")._value.get()
    assert after == before + 1


def test_export_metrics_bytes():
    output = export_metrics()
    assert isinstance(output, bytes)
