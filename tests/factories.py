import json
import tempfile
from pathlib import Path
from datetime import datetime

import factory

from src.core.config import Config


class ConfigFactory(factory.Factory):
    """Factory for :class:`Config` objects backed by a temp file."""

    class Meta:
        model = Config

    @classmethod
    def _create(cls, model_class, tmp_dir=None, data=None, **kwargs):
        tmp_dir = Path(tmp_dir or tempfile.mkdtemp())
        config_path = tmp_dir / "config.json"
        if data is None:
            data = {
                "api": {"base_url": "http://test", "api_key": "k", "model": "m"},
                "memory": {"file": str(tmp_dir / "mem.json")},
            }
        config_path.write_text(json.dumps(data))
        return model_class(config_path=str(config_path), **kwargs)


class MemoryEntryFactory(factory.DictFactory):
    """Factory for memory entry dictionaries."""

    key = factory.Sequence(lambda n: f"key{n}")
    value = factory.Faker("sentence")
    category = "general"
    timestamp = factory.LazyFunction(lambda: datetime.now().isoformat())
    access_count = 0
