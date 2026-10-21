"""Unit tests for UrbanTwin configuration and environment settings."""

from config.settings import DataMode, settings


def test_settings_defaults() -> None:
    """Verify default project settings and Pune bounding coordinates."""
    assert settings.APP_NAME == "UrbanTwin"
    assert settings.PUNE_BBOX_MIN_LAT < settings.PUNE_BBOX_MAX_LAT
    assert settings.PUNE_BBOX_MIN_LON < settings.PUNE_BBOX_MAX_LON
    assert settings.H3_RESOLUTION == 7


def test_data_mode_path_resolution() -> None:
    """Verify that active_data_dir switches appropriately based on DATA_MODE."""
    if settings.DATA_MODE == DataMode.SYNTHETIC:
        assert "synthetic" in str(settings.active_data_dir)
    else:
        assert "real" in str(settings.active_data_dir)
