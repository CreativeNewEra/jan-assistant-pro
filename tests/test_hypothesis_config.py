from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.core.config_validator import ConfigValidator


def valid_config_strategy(tmp_path):
    return st.fixed_dictionaries(
        {
            "api": st.fixed_dictionaries(
                {
                    "base_url": st.sampled_from(
                        ["http://example.com", "https://example.com"]
                    ),
                    "api_key": st.text(min_size=1, max_size=20),
                    "model": st.text(min_size=1, max_size=20),
                    "timeout": st.integers(min_value=1, max_value=300),
                }
            ),
            "memory": st.fixed_dictionaries(
                {"file": st.just(str(tmp_path / "mem.json"))}
            ),
        }
    )


@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.data())
def test_config_validation_generated(tmp_path, data):
    validator = ConfigValidator()
    cfg_strategy = valid_config_strategy(tmp_path)
    config = data.draw(cfg_strategy)
    validated = validator.validate_config_data(config)
    assert validated["api"]["api_key"] == config["api"]["api_key"]
    assert validated["memory"]["file"] == str(tmp_path / "mem.json")
