"""Unit tests for Settings properties."""

from databricks_contracts.config.settings import Settings


class TestSettingsProperties:
    def test_is_production_true(self, monkeypatch) -> None:
        monkeypatch.setenv("ENVIRONMENT", "prod")
        settings = Settings()
        assert settings.is_production is True

    def test_is_production_false(self, monkeypatch) -> None:
        monkeypatch.setenv("ENVIRONMENT", "dev")
        settings = Settings()
        assert settings.is_production is False

    def test_has_purview_configuration_true(self, monkeypatch) -> None:
        monkeypatch.setenv("PURVIEW_ACCOUNT_NAME", "account")
        monkeypatch.setenv("PURVIEW_CLIENT_ID", "client-id")
        monkeypatch.setenv("PURVIEW_CLIENT_SECRET", "secret")
        monkeypatch.setenv("PURVIEW_TENANT_ID", "tenant-id")
        settings = Settings()
        assert settings.has_purview_configuration is True

    def test_has_purview_configuration_false(self) -> None:
        # Use model_construct to bypass env/dotenv loading
        settings = Settings.model_construct(
            PURVIEW_ACCOUNT_NAME=None,
            PURVIEW_CLIENT_ID=None,
            PURVIEW_CLIENT_SECRET=None,
            PURVIEW_TENANT_ID=None,
        )
        assert settings.has_purview_configuration is False
