"""Tests for the workspace manager."""


from singleclaw.workspace.manager import WorkspaceManager


class TestWorkspaceManager:
    def test_initialise_creates_directory(self, tmp_path):
        manager = WorkspaceManager(base_dir=tmp_path)
        manager.initialise()

        assert manager.workspace_dir.is_dir()

    def test_initialise_creates_data_files(self, tmp_path):
        manager = WorkspaceManager(base_dir=tmp_path)
        manager.initialise()

        assert (manager.workspace_dir / "memory.jsonl").exists()
        assert (manager.workspace_dir / "journal.jsonl").exists()
        assert (manager.workspace_dir / "memory_notes.md").exists()
        assert (manager.workspace_dir / "config.json").exists()

    def test_initialise_idempotent(self, tmp_path):
        manager = WorkspaceManager(base_dir=tmp_path)
        manager.initialise()
        manager.initialise()  # second call should not raise

        assert manager.is_initialised()

    def test_is_initialised_false_before_init(self, tmp_path):
        manager = WorkspaceManager(base_dir=tmp_path)
        assert not manager.is_initialised()

    def test_config_default_values(self, tmp_path):
        manager = WorkspaceManager(base_dir=tmp_path)
        manager.initialise()

        config = manager.load_config()
        assert config["guardian_mode"] == "strict"
        assert config["dry_run"] is False

    def test_save_and_load_config(self, tmp_path):
        manager = WorkspaceManager(base_dir=tmp_path)
        manager.initialise()

        manager.save_config({"guardian_mode": "permissive", "dry_run": True})
        config = manager.load_config()

        assert config["guardian_mode"] == "permissive"
        assert config["dry_run"] is True

    def test_custom_workspace_name(self, tmp_path):
        manager = WorkspaceManager(base_dir=tmp_path, workspace_name=".myworkspace")
        manager.initialise()

        assert (tmp_path / ".myworkspace").is_dir()
