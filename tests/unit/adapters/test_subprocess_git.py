"""Unit tests for SubprocessGitAdapter."""

import subprocess
from unittest.mock import MagicMock, patch

from databricks_contracts.adapters.git.subprocess_adapter import SubprocessGitAdapter


class TestSubprocessGitAdapter:
    def test_get_modified_files_success(self) -> None:
        adapter = SubprocessGitAdapter()
        mock_result = MagicMock()
        mock_result.stdout = "file1.yaml\nfile2.yaml\n"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            files = adapter.get_modified_files("HEAD~1", "HEAD")
            assert files == ["file1.yaml", "file2.yaml"]
            mock_run.assert_called_once()

    def test_get_modified_files_empty(self) -> None:
        adapter = SubprocessGitAdapter()
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result):
            files = adapter.get_modified_files("HEAD~1", "HEAD")
            assert files == []

    def test_get_modified_files_on_error(self) -> None:
        adapter = SubprocessGitAdapter()

        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
            files = adapter.get_modified_files("HEAD~1", "HEAD")
            assert files == []
