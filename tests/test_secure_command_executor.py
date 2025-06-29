import os

from src.tools.secure_command_executor import SecureCommandExecutor


def test_allowed_command(tmp_path):
    with SecureCommandExecutor(allowed_commands=["echo"]) as executor:
        result = executor.execute("echo hello", work_dir=str(tmp_path))
        assert result["success"] is True
        assert "hello" in result["stdout"]


def test_blocked_command():
    with SecureCommandExecutor(
        allowed_commands=["echo"], blocked_commands=["rm"]
    ) as executor:
        result = executor.execute("rm -rf /tmp")
        assert result["success"] is False
        assert "blocked" in result["error"]


def test_dangerous_pattern():
    with SecureCommandExecutor(allowed_commands=["echo"]) as executor:
        result = executor.execute("echo hi && echo bye")
        assert result["success"] is False
        assert "dangerous" in result["error"]


def test_output_truncation(tmp_path):
    with SecureCommandExecutor(
        allowed_commands=["python3"], max_output_bytes=50
    ) as executor:
        cmd = "python3 -c 'print(\"x\"*200)'"
        result = executor.execute(cmd, work_dir=str(tmp_path))
        assert result["success"] is True
        assert len(result["stdout"].encode()) <= 50
        assert "truncated" in result.get("note", "")


def test_working_dir_isolation(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    inside = sandbox / "inside.txt"
    inside.write_text("safe")

    with SecureCommandExecutor(
        allowed_commands=["cat"], work_dir=str(sandbox)
    ) as executor:
        ok = executor.execute("cat inside.txt", work_dir=str(sandbox))
        assert ok["success"] is True
        assert "safe" in ok["stdout"]

        bad = executor.execute("cat ../outside.txt", work_dir=str(sandbox))
        assert bad["success"] is False
        assert "Path traversal" in bad["error"]


def test_cleanup_after_context():
    with SecureCommandExecutor(allowed_commands=["echo"]) as executor:
        result = executor.execute("echo hi")
        exec_dir = result["working_dir"]
        base_dir = executor.base_work_dir
        # execution directory should be removed immediately
        assert not os.path.exists(exec_dir)
        assert os.path.exists(base_dir)
    # after context exit, base directory should be removed
    assert not os.path.exists(base_dir)
