from src.core.storage import JSONStorage, SQLiteStorage


def test_json_storage(tmp_path):
    file_path = tmp_path / "store.json"
    storage = JSONStorage(str(file_path))
    storage.save("foo", {"bar": 1})
    assert storage.load("foo") == {"bar": 1}


def test_sqlite_storage(tmp_path):
    db_path = tmp_path / "store.sqlite"
    storage = SQLiteStorage(str(db_path))
    storage.save("alpha", [1, 2, 3])
    assert storage.load("alpha") == [1, 2, 3]
