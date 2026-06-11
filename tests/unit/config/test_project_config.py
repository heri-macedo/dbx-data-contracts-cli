"""Unit tests for ProjectConfig and config loading."""

from pathlib import Path

import pytest

from databricks_contracts.config.project_config_model import (
    ProjectConfig,
    _find_config_file,
    clear_config_cache,
    load_project_config,
)
from databricks_contracts.exceptions import ProjectConfigNotFoundError


class TestProjectConfig:
    def test_get_catalog_dev(self, sample_project_config_data: dict) -> None:
        config = ProjectConfig.model_validate(sample_project_config_data)
        assert config.get_catalog("dev") == "test_catalog"

    def test_get_catalog_prod(self, sample_project_config_data: dict) -> None:
        config = ProjectConfig.model_validate(sample_project_config_data)
        assert config.get_catalog("prod") == "test_catalog_prod"

    def test_get_catalog_unknown_env_falls_back_to_dev(self, sample_project_config_data: dict) -> None:
        config = ProjectConfig.model_validate(sample_project_config_data)
        # Unknown env should fall back to dev
        result = config.get_catalog("staging")
        assert result == "test_catalog"  # dev suffix is ""

    def test_schema_name(self, sample_project_config_data: dict) -> None:
        config = ProjectConfig.model_validate(sample_project_config_data)
        assert config.schema_name == "test_schema"


class TestFindConfigFile:
    def test_find_config_in_cwd(self, tmp_path: Path, monkeypatch) -> None:
        config_file = tmp_path / "datacontract.config.yaml"
        config_file.write_text("domain:\n  name: test\n  sub_domain: sub")
        monkeypatch.chdir(tmp_path)
        result = _find_config_file()
        assert result == config_file

    def test_raises_when_not_found(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ProjectConfigNotFoundError):
            _find_config_file()

    def test_load_project_config_from_file(self, tmp_path: Path, monkeypatch) -> None:
        config_content = """
domain:
  name: my_catalog
  sub_domain: my_schema
environments:
  dev:
    catalog_suffix: ""
  prod:
    catalog_suffix: "_prod"
"""
        config_file = tmp_path / "datacontract.config.yaml"
        config_file.write_text(config_content)
        monkeypatch.chdir(tmp_path)
        clear_config_cache()
        config = load_project_config()
        assert config.get_catalog("prod") == "my_catalog_prod"
        clear_config_cache()
