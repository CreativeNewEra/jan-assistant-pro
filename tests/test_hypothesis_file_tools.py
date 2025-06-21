from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.core.cache import clear_memory_caches
from src.tools.file_tools import FileTools


@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    file_name=st.text(
        alphabet=st.characters(min_codepoint=97, max_codepoint=122),
        min_size=1,
        max_size=10,
    ),
    content=st.text(
        alphabet=st.characters(min_codepoint=97, max_codepoint=122),
        min_size=1,
        max_size=50,
    ),
)
def test_file_tools_operations(tmp_path, file_name, content):
    clear_memory_caches()
    tools = FileTools()
    path = tmp_path / file_name

    if path.exists():
        path.unlink()

    write = tools.write_file(str(path), content)
    assert write["success"] is True

    read = tools.read_file(str(path))
    assert read["content"] == content

    append_content = content[::-1]
    tools.append_file(str(path), append_content)
    clear_memory_caches()
    read2 = tools.read_file(str(path))
    assert read2["content"] == content + append_content

    delete = tools.delete_file(str(path))
    assert delete["success"] is True
    assert not path.exists()
