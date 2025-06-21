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
    before = next(sample.value for sample in tool_calls.collect()[0].samples if sample.labels["tool"] == "demo")
    d.ok()
    after = next(sample.value for sample in tool_calls.collect()[0].samples if sample.labels["tool"] == "demo")
    assert after == before + 1


def test_tool_errors_increment():
    d = Dummy()
    before = next(sample.value for sample in tool_errors.collect()[0].samples if sample.labels["tool"] == "demo")
    d.fail()
    after = next(sample.value for sample in tool_errors.collect()[0].samples if sample.labels["tool"] == "demo")
    assert after == before + 1


def test_export_metrics_bytes():
    output = export_metrics()
    assert isinstance(output, bytes)
