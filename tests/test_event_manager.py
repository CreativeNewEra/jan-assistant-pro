from src.core.event_manager import EventManager


def test_event_manager_basic():
    manager = EventManager()
    data = []

    def listener(value=None):
        data.append(value)

    manager.subscribe("change", listener)
    manager.emit("change", value=42)
    assert data == [42]

    manager.unsubscribe("change", listener)
    manager.emit("change", value=1)
    assert data == [42]
