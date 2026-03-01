"""Tests for server blueprint export/import."""

from pathlib import Path

from discord_ferry.blueprint import (
    BlueprintCategory,
    BlueprintChannel,
    BlueprintRole,
    ServerBlueprint,
    export_blueprint,
    import_blueprint,
)


def _make_blueprint() -> ServerBlueprint:
    return ServerBlueprint(
        name="Test Server",
        description="A test server",
        roles=[
            BlueprintRole(name="Admin", colour=16711680, permissions=15, rank=2),
            BlueprintRole(name="Member"),
        ],
        categories=[
            BlueprintCategory(
                name="General",
                channels=[
                    BlueprintChannel(name="general"),
                    BlueprintChannel(name="off-topic"),
                ],
            ),
            BlueprintCategory(
                name="Voice",
                channels=[
                    BlueprintChannel(name="voice-chat", type="Voice"),
                ],
            ),
        ],
        uncategorized_channels=[
            BlueprintChannel(name="rules", nsfw=False),
        ],
    )


def test_export_import_roundtrip(tmp_path: Path) -> None:
    bp = _make_blueprint()
    path = tmp_path / "blueprint.json"
    export_blueprint(bp, path)
    loaded = import_blueprint(path)

    assert loaded.name == "Test Server"
    assert loaded.description == "A test server"
    assert len(loaded.roles) == 2
    assert loaded.roles[0].name == "Admin"
    assert loaded.roles[0].colour == 16711680
    assert loaded.roles[0].permissions == 15
    assert loaded.roles[0].rank == 2
    assert loaded.roles[1].name == "Member"
    assert len(loaded.categories) == 2
    assert loaded.categories[0].name == "General"
    assert len(loaded.categories[0].channels) == 2
    assert loaded.categories[1].channels[0].type == "Voice"
    assert len(loaded.uncategorized_channels) == 1
    assert loaded.uncategorized_channels[0].name == "rules"


def test_export_creates_parent_dirs(tmp_path: Path) -> None:
    bp = ServerBlueprint(name="Test")
    nested = tmp_path / "deep" / "dir" / "blueprint.json"
    export_blueprint(bp, nested)
    assert nested.exists()


def test_import_minimal_blueprint(tmp_path: Path) -> None:
    path = tmp_path / "minimal.json"
    path.write_text('{"name": "Minimal"}', encoding="utf-8")
    loaded = import_blueprint(path)
    assert loaded.name == "Minimal"
    assert loaded.roles == []
    assert loaded.categories == []
    assert loaded.uncategorized_channels == []


def test_export_empty_blueprint(tmp_path: Path) -> None:
    bp = ServerBlueprint(name="Empty")
    path = tmp_path / "empty.json"
    export_blueprint(bp, path)
    loaded = import_blueprint(path)
    assert loaded.name == "Empty"
    assert loaded.description == ""


def test_nsfw_channel_roundtrip(tmp_path: Path) -> None:
    bp = ServerBlueprint(
        name="NSFW Test",
        categories=[
            BlueprintCategory(
                name="Adults",
                channels=[BlueprintChannel(name="nsfw-ch", nsfw=True)],
            ),
        ],
    )
    path = tmp_path / "nsfw.json"
    export_blueprint(bp, path)
    loaded = import_blueprint(path)
    assert loaded.categories[0].channels[0].nsfw is True


def test_role_defaults(tmp_path: Path) -> None:
    bp = ServerBlueprint(
        name="Defaults",
        roles=[BlueprintRole(name="Basic")],
    )
    path = tmp_path / "defaults.json"
    export_blueprint(bp, path)
    loaded = import_blueprint(path)
    assert loaded.roles[0].colour == 0
    assert loaded.roles[0].permissions == 0
    assert loaded.roles[0].rank == 0
