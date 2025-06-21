from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.core.memory import MemoryManager


@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.text(min_size=1, max_size=20),
        min_size=1,
        max_size=10,
    )
)
def test_memory_roundtrip(tmp_path, entries):
    path = tmp_path / "memory.json"
    with MemoryManager(str(path)) as manager:
        for key, value in entries.items():
            assert manager.remember(key, value)

    with MemoryManager(str(path)) as manager:
        for key, value in entries.items():
            recalled = manager.recall(key)
            assert recalled is not None
            assert recalled["value"] == value
