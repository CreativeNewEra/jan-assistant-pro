import re
import pytest

from src.core.utils import validate_input
from src.tools.system_tools import SystemTools


def test_validate_input_success():
    @validate_input({"name": {"pattern": re.compile(r"^[a-z]+$"), "max_length": 5}})
    def greet(name):
        return name.upper()

    assert greet(name="hello"[:5]) == "HELLO"


def test_validate_input_length_error():
    @validate_input({"text": {"max_length": 3}})
    def echo(text):
        return text

    with pytest.raises(ValueError):
        echo(text="abcd")


def test_validate_input_pattern_error():
    @validate_input({"value": {"pattern": re.compile(r"^[0-9]+$")}})
    def num(value):
        return int(value)

    with pytest.raises(ValueError):
        num(value="abc")


def test_run_command_validation():
    tools = SystemTools()
    with pytest.raises(ValueError):
        tools.run_command(command="rm -rf /tmp")
