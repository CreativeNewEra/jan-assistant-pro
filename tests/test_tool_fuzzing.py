from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.tools.tool_registry import ToolRegistry
from tests.test_enhanced_features import MockTool


@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    include_input=st.booleans(),
    input_text=st.text(min_size=0, max_size=20),
    include_count=st.booleans(),
    count_value=st.one_of(st.integers(min_value=0, max_value=5), st.text(), st.none()),
)
def test_tool_registry_fuzz(include_input, input_text, include_count, count_value):
    registry = ToolRegistry()
    registry.register_tool(MockTool)

    params = {}
    if include_input:
        params["input"] = input_text
    if include_count:
        params["count"] = count_value

    result = registry.execute_tool("mock_tool", **params)
    assert "success" in result

    valid = (
        include_input
        and input_text != "error"
        and (not include_count or isinstance(count_value, int))
    )
    if valid:
        expected_count = count_value if include_count else 1
        assert result["success"] is True
        assert result["result"] == input_text * expected_count
    else:
        assert result["success"] is False
