"""Validate project-scoped CodeGraph and Serena registrations."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_agent_mcp_configs_register_same_nonredundant_servers():
    opencode = json.loads((ROOT / "opencode.json").read_text(encoding="utf-8"))["mcp"]
    vscode = json.loads((ROOT / ".vscode/mcp.json").read_text(encoding="utf-8"))["servers"]
    assert set(opencode) == set(vscode) == {"codegraph", "serena"}
    assert opencode["codegraph"]["command"] == ["codegraph", "serve", "--mcp"]
    assert [vscode["codegraph"]["command"], *vscode["codegraph"]["args"]] == [
        "codegraph",
        "serve",
        "--mcp",
    ]
    assert all(item["type"] == "local" and item["enabled"] for item in opencode.values())
    assert all(item["type"] == "stdio" for item in vscode.values())


def test_serena_ide_mode_scoped_to_current_worktree():
    opencode = json.loads((ROOT / "opencode.json").read_text(encoding="utf-8"))
    vscode = json.loads((ROOT / ".vscode/mcp.json").read_text(encoding="utf-8"))
    commands = [
        opencode["mcp"]["serena"]["command"],
        [vscode["servers"]["serena"]["command"], *vscode["servers"]["serena"]["args"]],
    ]
    for command in commands:
        assert command[:2] == ["serena", "start-mcp-server"]
        assert command[command.index("--context") + 1] == "ide"
        assert "--project-from-cwd" in command
        assert command[command.index("--open-web-dashboard") + 1] == "false"
        assert not any("/home/" in arg or "/Users/" in arg for arg in command)
    assert vscode["servers"]["serena"]["cwd"] == "${workspaceFolder}"
    assert vscode["servers"]["codegraph"]["cwd"] == "${workspaceFolder}"


def test_vscode_ignore_includes_mcp_json_only():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".vscode/*" in ignore
    assert "!.vscode/mcp.json" in ignore
    assert ".vscode/" not in ignore
