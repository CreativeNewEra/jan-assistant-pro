import asyncio

from src.core.command_bus import Command, CommandBus, Result


class EchoHandler:
    async def handle(self, command: Command) -> Result:
        return Result.ok({"echo": command.params.get("msg")})


class FailingHandler:
    async def handle(self, command: Command) -> Result:
        raise ValueError("boom")


async def test_command_bus_success():
    bus = CommandBus()
    bus.register("echo", EchoHandler())
    result = await bus.execute(Command(name="echo", params={"msg": "hi"}))
    assert result.success is True
    assert result.data == {"echo": "hi"}


async def test_command_bus_unknown():
    bus = CommandBus()
    result = await bus.execute(Command(name="missing", params={}))
    assert result.success is False
    assert "Unknown" in result.error


async def test_command_bus_handler_error():
    bus = CommandBus()
    bus.register("fail", FailingHandler())
    result = await bus.execute(Command(name="fail", params={}))
    assert result.success is False
    assert "boom" in result.error
